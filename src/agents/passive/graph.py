"""
passive_course_agent — LangGraph pipeline.

Architecture:
  START
    └─ ① mock_profile_loader
         └─ ② mock_progress_loader
              └─ ③ mock_concept_loader
                   └─ cache_reader ── hit ─▶ cache_writer
                                    └─ miss ─▶ ④a outline_gen ─▶ router ───▶┬─ content_gen_beginner ────┐
                                                                             ├─ content_gen_intermediate ─┼─▶ ④b.5 fact_check ─▶ ④c image_gen ─▶ cache_writer
                                                                             └─ content_gen_advanced ────┘

Phase 1 (④a):   LLM slices concept into learning nodes (outline)
Phase 2 (④b):   Router selects tier-specific content generator by depth_tier:
                  beginner     — rich analogies, no formal math, warm tone
                  intermediate — balanced depth, formulas where helpful
                  advanced     — full formal treatment, proof sketches, terse
Phase 2.5 (④b.5): Critic LLM reviews each node for domain-specific factual
                  errors; "critical" issues optionally trigger regeneration
                  of the offending section.
Phase 3 (④c):   Image model generates illustrations for typed image markers
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
import time
from typing import Any

from langgraph.graph import END, START, StateGraph
from openai import AsyncOpenAI
from pydantic import ValidationError

try:
    import json_repair
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    json_repair = None

try:  # openai >=1.0 exposes typed errors; fall back to Exception on older SDKs
    from openai import APIConnectionError, APITimeoutError, RateLimitError
except ImportError:  # pragma: no cover — SDK version mismatch
    RateLimitError = APITimeoutError = APIConnectionError = Exception  # type: ignore[misc,assignment]

from .markers import (
    image_generation_brief,
    iter_image_markers,
    parse_image_marker,
)
from .mock_data import (
    get_mock_input,
    get_passive_course_dir,
    get_passive_images_dir,
)
from .prompts import (
    FACT_CHECK_SYSTEM_PROMPT,
    FACT_CHECK_USER_TEMPLATE,
    OUTLINE_SYSTEM_PROMPT,
    OUTLINE_USER_TEMPLATE,
    TIER_CONTENT_PROMPTS,
)
from .schemas import ContentResponse, FactCheckResponse
from .state import PipelineState
from .text_normalization import normalize_llm_payload

# Section objects must contain exactly these keys. Anything else means the LLM
# either invented a key or — far more commonly — produced unescaped quotes
# inside a string value, and json_repair salvaged the broken JSON by inventing
# bogus keys like "earlier." or "CT?". See schemas.py for context.
# ``part`` is the canonical pedagogical-part enum introduced in Story 5.3; it
# is optional on input (defaults to "extra" via the pydantic model).
_ALLOWED_SECTION_KEYS = frozenset({"section", "content", "markers", "part"})

# Valid values for the ``part`` field — kept in sync with schemas.PedagogicalPart.
# We avoid importing the enum members into a set comprehension at module load
# to keep this file cheap to import from tests.
_VALID_PART_VALUES = frozenset(
    {"hook", "recall", "definition", "intuition", "visual", "checkpoint", "extra"}
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

_config: dict | None = None


def _load_config() -> dict:
    global _config
    if _config is None:
        from src.agents.config import load_agent_config

        _config = load_agent_config("passive_content_generator")
    return _config


# ---------------------------------------------------------------------------
# OpenRouter LLM client (lazy singleton)
# ---------------------------------------------------------------------------

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        cfg = _load_config()
        api_key = os.environ.get(cfg["api_key_env"]) or os.environ.get("LLM_API_KEY", "")
        base_url = os.environ.get(cfg.get("base_url_env", ""), cfg["base_url_default"])
        timeout_s = cfg.get("request_timeout_s")
        _client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout_s)
    return _client


def _strip_fences(raw: str) -> str:
    """Strip markdown code fences from LLM output."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
    return raw


# Characters that form valid JSON escape sequences: \" \\ \/ \b \f \n \r \t
# Note: \uXXXX is also valid but handled separately.
_VALID_JSON_ESCAPE_CHARS = frozenset('"\\bfnrt/')

# Regex: unescaped `"` inside markdown italics within a JSON string value.
# Matches patterns like  *"some text"*  where the quotes are NOT escaped.
# We replace the inner " with curly quotes so JSON parsing succeeds.
_ITALIC_UNESCAPED_QUOTE_RE = re.compile(
    r'(?<=\*)"([^"*]{1,200})"(?=\*)'
)


def _sanitize_italic_quotes(raw: str) -> str:
    r"""Replace ``*"text"*`` with ``*\u201ctext\u201d*`` in raw JSON.

    The LLM frequently writes straight double-quotes inside italic markdown
    phrases (``*"Did we need that?"*``). These unescaped quotes break JSON
    parsing because the ``"`` terminates the JSON string prematurely.

    This runs BEFORE json.loads so the string never gets corrupted.
    """
    return _ITALIC_UNESCAPED_QUOTE_RE.sub(
        lambda m: "\u201c" + m.group(1) + "\u201d", raw
    )


def _repair_json_escapes(chunk: str) -> str:
    """Repair invalid JSON escape sequences inside string values.

    LLM-generated content often contains LaTeX (``\\mathcal``, ``\\alpha``)
    whose backslashes are not valid JSON escapes.  This function doubles
    those backslashes so ``json.loads`` can parse the result.
    Literal control characters (newline, tab, carriage return) inside
    strings are also escaped.
    """
    parts: list[str] = []
    in_string = False
    i = 0
    length = len(chunk)
    while i < length:
        ch = chunk[i]

        # -- Outside a JSON string: just pass through ----------------
        if not in_string:
            if ch == '"':
                in_string = True
            parts.append(ch)
            i += 1
            continue

        # -- Inside a JSON string ------------------------------------
        if ch == "\\" and i + 1 < length:
            next_ch = chunk[i + 1]
            if next_ch in _VALID_JSON_ESCAPE_CHARS:
                # Valid simple escape (\n, \t, \\, \", etc.) — keep as-is
                parts.append(ch)
                parts.append(next_ch)
                i += 2
                continue
            if next_ch == "u":
                # Could be valid \uXXXX or LaTeX like \underset
                if i + 5 < length and all(
                    c in "0123456789abcdefABCDEF" for c in chunk[i + 2 : i + 6]
                ):
                    # Valid unicode escape — pass all 6 chars
                    parts.append(chunk[i : i + 6])
                    i += 6
                    continue
                # Invalid \u... (LaTeX) — double the backslash
                parts.append("\\\\")
                i += 1
                continue
            # Any other char after backslash is invalid JSON escape
            # (e.g. \m from \mathcal, \a from \alpha).  Double the
            # backslash to make it a literal backslash in the JSON string.
            parts.append("\\\\")
            i += 1
            continue

        if ch == '"':
            in_string = False
            parts.append(ch)
            i += 1
            continue

        # Literal control characters inside a string
        if ch == "\n":
            parts.append("\\n")
            i += 1
            continue
        if ch == "\t":
            parts.append("\\t")
            i += 1
            continue
        if ch == "\r":
            parts.append("\\r")
            i += 1
            continue

        parts.append(ch)
        i += 1

    return "".join(parts)


def _extract_json_payload(raw: str) -> Any:
    """Unwrap ``{"sections": [...]}`` / ``{"nodes": [...]}`` wrappers
    that ``response_format=json_object`` may produce, returning the
    inner list.  If the input is already a list, return it directly."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in ("sections", "nodes", "outline"):
            if key in raw and isinstance(raw[key], list):
                return raw[key]
        # Single-key dict whose value is a list
        values = list(raw.values())
        if len(values) == 1 and isinstance(values[0], list):
            return values[0]
        return raw
    return raw


def _finalize_json_payload(raw: Any) -> Any:
    """Unwrap common JSON envelopes and normalize over-escaped string content."""
    return normalize_llm_payload(_extract_json_payload(raw))


def _parse_json(raw: str) -> Any:
    """Parse JSON from LLM output, with fallback for common issues."""
    raw = _strip_fences(raw)
    raw = _sanitize_italic_quotes(raw)

    # Try direct parse first
    try:
        return _finalize_json_payload(json.loads(raw))
    except json.JSONDecodeError:
        pass

    # Try robust repair for common LLM JSON failures:
    # - invalid backslash escapes from LaTeX
    # - unescaped quotes inside string values
    # - minor structural issues (missing commas/brackets)
    if json_repair is not None:
        try:
            return _finalize_json_payload(json_repair.loads(raw))
        except Exception:
            pass

    # Try to find the outermost JSON structure (object or array)
    obj_start = raw.find("{")
    arr_start = raw.find("[")

    # Prefer object (response_format wraps in object) over bare array
    if obj_start != -1 and (arr_start == -1 or obj_start < arr_start):
        end = raw.rfind("}")
        if end > obj_start:
            chunk = raw[obj_start : end + 1]
            try:
                return _finalize_json_payload(json.loads(chunk))
            except json.JSONDecodeError:
                pass
            # Try robust repair on extracted object chunk
            if json_repair is not None:
                try:
                    return _finalize_json_payload(json_repair.loads(chunk))
                except Exception:
                    pass
            # Last chance: legacy custom escape repair
            try:
                return _finalize_json_payload(json.loads(_repair_json_escapes(chunk)))
            except json.JSONDecodeError:
                pass

    # Fall back to array extraction
    if arr_start != -1:
        end = raw.rfind("]")
        if end > arr_start:
            chunk = raw[arr_start : end + 1]
            try:
                return _finalize_json_payload(json.loads(chunk))
            except json.JSONDecodeError:
                pass
            # Try robust repair on extracted array chunk
            if json_repair is not None:
                try:
                    return _finalize_json_payload(json_repair.loads(chunk))
                except Exception:
                    pass
            # Last chance: legacy custom escape repair
            try:
                return _finalize_json_payload(json.loads(_repair_json_escapes(chunk)))
            except json.JSONDecodeError as e:
                logger.error("JSON parse failed even after escape repair: %s", e)
                logger.error("First 500 chars: %s", chunk[:500])
                raise

    raise json.JSONDecodeError("No valid JSON found in model output", raw, 0)


def _extract_text_content(content: Any) -> str:
    """Normalize SDK message content into plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
            else:
                text = getattr(item, "text", None)
            if text:
                parts.append(text)
        return "\n".join(parts)
    if content is None:
        return ""
    return str(content)


def _log_llm_call_start(stage: str, model: str, *, extra: str = "") -> float:
    """Log the moment we hand off to the LLM and return a start timestamp.

    Long-running pipelines were silent for minutes; this gives a clear
    "we're waiting on model X right now" signal so the user can tell that
    the run is alive.
    """
    suffix = f" — {extra}" if extra else ""
    logger.info("%s → calling %s...%s", stage, model, suffix)
    return time.perf_counter()


def _log_response_metadata(stage: str, response: Any, *, started_at: float | None = None) -> None:
    """Log finish reason, token usage, and (optionally) elapsed time."""
    choices = getattr(response, "choices", None) or []
    choice = choices[0] if choices else None
    finish_reason = getattr(choice, "finish_reason", None) or "unknown"

    usage = getattr(response, "usage", None)
    prompt_tokens = getattr(usage, "prompt_tokens", None)
    completion_tokens = getattr(usage, "completion_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)

    elapsed_str = ""
    if started_at is not None:
        elapsed_str = f" elapsed={time.perf_counter() - started_at:.1f}s"

    logger.info(
        "%s ← finish=%s tokens(prompt=%s, completion=%s, total=%s)%s",
        stage,
        finish_reason,
        prompt_tokens if prompt_tokens is not None else "?",
        completion_tokens if completion_tokens is not None else "?",
        total_tokens if total_tokens is not None else "?",
        elapsed_str,
    )
    if finish_reason == "length":
        logger.warning("%s model stopped because of token limit", stage)


def _response_usage_metrics(response: Any) -> dict[str, int]:
    """Extract token counts from an SDK response, defaulting missing fields to 0."""
    usage = getattr(response, "usage", None)
    prompt_tokens = getattr(usage, "prompt_tokens", None)
    completion_tokens = getattr(usage, "completion_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)

    prompt = int(prompt_tokens or 0)
    completion = int(completion_tokens or 0)
    total = int(total_tokens or (prompt + completion))
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
    }


def _new_llm_metrics() -> dict[str, Any]:
    """Create an accumulator for token / retry / failure telemetry."""
    return {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "llm_calls": 0,
        "attempts": 0,
        "failed_calls": 0,
        "errors": [],
    }


def _record_llm_success(
    metrics: dict[str, Any] | None,
    response: Any,
    *,
    call_stats: dict[str, Any] | None = None,
    stage: str,
) -> None:
    """Accumulate usage + retry metadata for one successful LLM call."""
    if metrics is None:
        return
    usage = _response_usage_metrics(response)
    metrics["prompt_tokens"] = int(metrics.get("prompt_tokens", 0)) + usage["prompt_tokens"]
    metrics["completion_tokens"] = int(metrics.get("completion_tokens", 0)) + usage["completion_tokens"]
    metrics["total_tokens"] = int(metrics.get("total_tokens", 0)) + usage["total_tokens"]
    metrics["llm_calls"] = int(metrics.get("llm_calls", 0)) + 1
    metrics["attempts"] = int(metrics.get("attempts", 0)) + int((call_stats or {}).get("attempts", 1))


def _record_llm_failure(
    metrics: dict[str, Any] | None,
    *,
    call_stats: dict[str, Any] | None = None,
    error: str,
    stage: str,
) -> None:
    """Accumulate retry metadata for one failed LLM call."""
    if metrics is None:
        return
    metrics["failed_calls"] = int(metrics.get("failed_calls", 0)) + 1
    metrics["attempts"] = int(metrics.get("attempts", 0)) + int((call_stats or {}).get("attempts", 1))
    errors = list(metrics.get("errors") or [])
    errors.append({"stage": stage, "error": error})
    metrics["errors"] = errors


def _merge_llm_metrics(target: dict[str, Any] | None, source: dict[str, Any] | None) -> None:
    """Fold one LLM metrics accumulator into another in place."""
    if target is None or source is None:
        return
    for key in ("prompt_tokens", "completion_tokens", "total_tokens", "llm_calls", "attempts", "failed_calls"):
        target[key] = int(target.get(key, 0)) + int(source.get(key, 0))
    errors = list(target.get("errors") or [])
    errors.extend(source.get("errors") or [])
    target["errors"] = errors


def _fallback_outline(state: PipelineState) -> list[dict[str, str]]:
    """Return a one-node outline when the outline model exhausts retries."""
    concept = state.get("concept_ctx", {})
    concept_id = concept.get("concept_id") or state.get("concept_id") or "unknown"
    title = concept.get("title") or concept_id.replace("-", " ").title()
    summary = (
        concept.get("summary")
        or concept.get("definition")
        or f"Core explanation of {title}."
    )
    return [{"title": title, "summary": summary, "rag_focus": concept_id}]


def _failed_node_sections(node_title: str, error_summary: str) -> list[dict[str, Any]]:
    """Produce a minimal valid node payload when drafting cannot recover."""
    return [
        {
            "section": "Temporary issue",
            "content": (
                f"Content generation for '{node_title}' was skipped after repeated transient "
                f"LLM failures ({error_summary}). Re-run the pipeline to regenerate this node."
            ),
            "markers": [],
            "part": "extra",
        }
    ]


# Exceptions considered "retryable" when calling an LLM provider via OpenRouter.
# httpx.ReadTimeout / httpx.ConnectTimeout surface as APITimeoutError /
# APIConnectionError from the SDK. RateLimitError covers upstream 429s.
_RETRYABLE_EXCEPTIONS: tuple[type[BaseException], ...] = (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    asyncio.TimeoutError,
    TimeoutError,
)


async def _llm_call_with_retry(
    factory,
    *,
    stage: str,
    delays_s: list[float] | None = None,
    max_attempts: int | None = None,
    stats: dict[str, Any] | None = None,
):
    """Call an async LLM factory with exponential backoff on transient errors.

    Story 5.3 AC-13: wraps ``client.chat.completions.create(...)`` calls so a
    single 429 from the upstream provider does not fail the whole run. The
    ``factory`` must be a zero-arg callable returning a fresh awaitable on
    every invocation — coroutines are single-use, so the caller cannot just
    pass a coroutine object.
    """
    if delays_s is None:
        cfg = _load_config().get("content", {})
        delays_s = list(cfg.get("retry_delays_s") or [1, 2, 4])
    if max_attempts is None:
        max_attempts = len(delays_s) + 1  # final attempt raises on failure
    last_exc: BaseException | None = None
    for attempt in range(max_attempts):
        try:
            response = await _await_with_heartbeat(factory(), stage=stage)
            if stats is not None:
                stats["attempts"] = attempt + 1
                stats["failed"] = False
                stats["error"] = ""
            return response
        except _RETRYABLE_EXCEPTIONS as exc:
            last_exc = exc
            if attempt >= max_attempts - 1:
                if stats is not None:
                    stats["attempts"] = attempt + 1
                    stats["failed"] = True
                    stats["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
                logger.error(
                    "[%s] giving up after %d attempts: %s (%s)",
                    stage,
                    attempt + 1,
                    type(exc).__name__,
                    str(exc)[:200],
                )
                raise
            delay = delays_s[min(attempt, len(delays_s) - 1)]
            logger.warning(
                "[%s] retryable error %s — sleeping %.1fs before retry %d/%d",
                stage,
                type(exc).__name__,
                delay,
                attempt + 2,
                max_attempts,
            )
            await asyncio.sleep(delay)
    # Unreachable, but keeps type checkers happy.
    assert last_exc is not None
    raise last_exc


async def _await_with_heartbeat(
    awaitable: Any,
    *,
    stage: str,
    interval_s: float | None = None,
    max_wait_s: float | None = None,
) -> Any:
    """Await a slow async operation while logging periodic heartbeats."""
    cfg = _load_config()
    interval_s = float(interval_s if interval_s is not None else cfg.get("heartbeat_interval_s", 15.0))
    max_wait_s = float(max_wait_s if max_wait_s is not None else cfg.get("max_wait_s", 360.0))
    task = asyncio.create_task(awaitable)
    started_at = time.perf_counter()
    while True:
        elapsed = time.perf_counter() - started_at
        remaining = max_wait_s - elapsed
        if remaining <= 0:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            raise TimeoutError(
                f"{stage} exceeded max wait of {max_wait_s:.0f}s; cancelling stalled model call"
            )
        try:
            return await asyncio.wait_for(asyncio.shield(task), timeout=min(interval_s, remaining))
        except asyncio.TimeoutError:
            logger.info("%s … still waiting (elapsed %.1fs)", stage, time.perf_counter() - started_at)


def _validate_sections(parsed: Any) -> list[dict[str, Any]]:
    """Validate parsed content payload and return a clean list of section dicts.

    Raises ``ValueError`` if the payload is structurally broken — typically the
    "unescaped quote inside italic" failure, where ``json_repair`` salvages the
    bad JSON by inventing keys like ``"earlier."`` or ``"CT?"``. Catching this
    here triggers the existing repair-retry path in ``content_generator``.
    """
    raw_sections: list[Any]
    if isinstance(parsed, dict) and isinstance(parsed.get("sections"), list):
        raw_sections = parsed["sections"]
    elif isinstance(parsed, list):
        raw_sections = parsed
    else:
        raise ValueError(f"expected object with 'sections' or a list, got {type(parsed).__name__}")

    bad_keys: list[str] = []
    trailing_star: list[str] = []
    for sec in raw_sections:
        if not isinstance(sec, dict):
            raise ValueError(f"section is not an object: {type(sec).__name__}")
        extras = set(sec.keys()) - _ALLOWED_SECTION_KEYS
        if extras:
            bad_keys.extend(sorted(extras))
        content = sec.get("content")
        if isinstance(content, str) and content.rstrip().endswith("*"):
            stripped = content.rstrip()
            # A lone trailing `*` (italic open with no close) almost always
            # means the rest of the string was lost to an unescaped quote.
            if not stripped.endswith("**"):
                trailing_star.append(sec.get("section", "<unknown>"))

    if bad_keys:
        raise ValueError(
            "section(s) contain unexpected keys "
            f"(likely unescaped-quote corruption): {bad_keys[:5]}"
        )
    if trailing_star:
        raise ValueError(
            "section(s) end with a lone '*' — likely truncated by an unescaped "
            f"quote inside an italic phrase: {trailing_star}"
        )

    # Final pydantic pass — catches missing fields / wrong types and invalid
    # ``part`` enum values. Missing ``part`` falls back to the model default
    # (``extra``), preserving backward compatibility with older payloads.
    try:
        validated = ContentResponse(sections=raw_sections)
    except ValidationError as e:
        raise ValueError(f"Pydantic validation failed: {e}") from e

    return [s.model_dump(mode="json") for s in validated.sections]


def _salvage_sections(parsed: Any) -> list[dict[str, Any]]:
    """Last-ditch recovery when both validation passes fail.

    Drops unknown keys, fills missing fields with empty defaults, and skips
    entries that can't be coerced into a usable section. Used only as a
    fallback so a single bad node doesn't crash the whole pipeline.

    Also coerces the ``part`` field to ``"extra"`` when missing or invalid —
    salvage is best-effort, so we prefer preserving the section over dropping
    it on a bad enum value.
    """
    raw = parsed.get("sections") if isinstance(parsed, dict) else parsed
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        section = item.get("section")
        content = item.get("content")
        if not isinstance(section, str) or not isinstance(content, str):
            continue
        # Fix lone trailing '*' (truncated italic) — better than dropping the section
        stripped = content.rstrip()
        if stripped.endswith("*") and not stripped.endswith("**"):
            content = stripped[:-1].rstrip()
        markers = item.get("markers")
        if not isinstance(markers, list):
            markers = []
        part = item.get("part")
        if not isinstance(part, str) or part not in _VALID_PART_VALUES:
            part = "extra"
        out.append(
            {"section": section, "content": content, "markers": markers, "part": part}
        )
    return out


async def _repair_json_response(
    *,
    client: AsyncOpenAI,
    model: str,
    max_tokens: int,
    raw: str,
    node_title: str,
    metrics: dict[str, Any] | None = None,
) -> Any:
    """Retry once by asking the model to rewrite malformed JSON as valid JSON."""
    logger.warning(
        "[④b]   Node '%s': retrying once with JSON repair prompt...",
        node_title,
    )
    def _make_call():
        return client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You repair malformed JSON. "
                        "Return only valid JSON with no markdown fences or commentary. "
                        "Preserve the original content as closely as possible."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Rewrite the following malformed JSON as a valid JSON object. "
                        "Do not add or remove sections. "
                        'Return exactly one top-level key named "sections". '
                        'Ensure each section object has keys "section", "content", "markers", and "part". '
                        'The "part" value must be one of: hook, recall, definition, intuition, visual, checkpoint, extra.\n\n'
                        f"{_strip_fences(raw)}"
                    ),
                },
            ],
            temperature=0,
            max_tokens=max_tokens,
        )

    call_stats: dict[str, Any] = {}
    try:
        repair_response = await _llm_call_with_retry(
            _make_call,
            stage="[④b]   JSONRepair",
            stats=call_stats,
        )
    except _RETRYABLE_EXCEPTIONS as exc:
        _record_llm_failure(
            metrics,
            call_stats=call_stats,
            error=f"{type(exc).__name__}: {str(exc)[:200]}",
            stage="json_repair",
        )
        raise
    _record_llm_success(metrics, repair_response, call_stats=call_stats, stage="json_repair")
    _log_response_metadata("[④b]   JSONRepair", repair_response)
    repaired_raw = _extract_text_content(repair_response.choices[0].message.content)
    return _parse_json(repaired_raw)


async def _regenerate_node_json(
    *,
    client: AsyncOpenAI,
    cfg: dict[str, Any],
    system_prompt: str,
    user_msg: str,
    node_title: str,
    node_index: int,
    total_nodes: int,
    metrics: dict[str, Any] | None = None,
) -> Any:
    """Regenerate a node from the original prompt after repair still looks broken."""
    logger.warning(
        "[④b]   Node '%s': regenerating from original prompt with stricter JSON constraints...",
        node_title,
    )
    retry_user_msg = (
        user_msg
        + "\n\nIMPORTANT: The previous attempt produced malformed or truncated JSON."
        + "\nRegenerate this node from scratch."
        + '\nReturn ONLY a valid JSON object with one top-level key "sections".'
        + '\nEvery section object must have exactly "section", "content", "markers", and "part".'
        + '\nThe "part" field must be one of: hook, recall, definition, intuition, visual, checkpoint, extra.'
        + '\nUse escaped newlines (\\n) inside JSON strings.'
        + '\nEscape any internal straight double quotes as \\\\".'
        + '\nNever use straight double quotes inside italic markdown phrases; use single or curly quotes instead.'
    )
    stage_label = f"[④b]   Node {node_index}/{total_nodes} retry"
    started = _log_llm_call_start(stage_label, cfg["model"], extra="temperature=0 retry")
    def _make_call():
        return client.chat.completions.create(
            model=cfg["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": retry_user_msg},
            ],
            temperature=0,
            max_tokens=cfg["max_tokens"],
            response_format={"type": "json_object"},
        )

    call_stats: dict[str, Any] = {}
    try:
        response = await _llm_call_with_retry(_make_call, stage=stage_label, stats=call_stats)
    except _RETRYABLE_EXCEPTIONS as exc:
        _record_llm_failure(
            metrics,
            call_stats=call_stats,
            error=f"{type(exc).__name__}: {str(exc)[:200]}",
            stage="node_regenerate",
        )
        raise
    _record_llm_success(metrics, response, call_stats=call_stats, stage="node_regenerate")
    _log_response_metadata(stage_label, response, started_at=started)
    regenerated_raw = _extract_text_content(response.choices[0].message.content)
    return _parse_json(regenerated_raw)


def _format_adaptation_ctx(ctx: dict[str, Any]) -> str:
    """Format structured adaptation_ctx dict into prompt-friendly text."""
    parts = []
    if ctx.get("background"):
        parts.append(f"Background: {ctx['background']}")
    if ctx.get("role"):
        parts.append(f"Role: {ctx['role']}")
    if ctx.get("prior_knowledge"):
        pk = ctx["prior_knowledge"]
        parts.append(f"Prior knowledge: {', '.join(pk) if isinstance(pk, list) else pk}")
    if ctx.get("learning_goal"):
        parts.append(f"Learning goal: {ctx['learning_goal']}")
    if ctx.get("domain_framing"):
        parts.append(f"Domain: {ctx['domain_framing']}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Node functions — Mock loaders
# ---------------------------------------------------------------------------


def mock_profile_loader(state: PipelineState) -> dict[str, Any]:
    """Node ① — load profile from mock JSON."""
    logger.info("[①] ProfileLoader (mock)")
    data = get_mock_input(state.get("user_id"), state.get("concept_id"))
    return {
        "adaptation_ctx": data["adaptation_ctx"],
        "depth_tier": data["depth_tier"],
        "profile_sig": data["profile_sig"],
    }


def mock_progress_loader(state: PipelineState) -> dict[str, Any]:
    """Node ② — load progress from mock JSON."""
    logger.info("[②] ProgressLoader (mock)")
    data = get_mock_input(state.get("user_id"), state.get("concept_id"))
    return {
        "progress_ctx": data["progress_ctx"],
        "confusion_fwd": data["confusion_fwd"],
    }


def mock_concept_loader(state: PipelineState) -> dict[str, Any]:
    """Node ③ — load concept + RAG chunks from mock JSON."""
    logger.info("[③] ConceptLoader (mock)")
    data = get_mock_input(state.get("user_id"), state.get("concept_id"))
    return {
        "concept_ctx": data["concept_ctx"],
        "grounded_chunks": data["grounded_chunks"],
    }


# ---------------------------------------------------------------------------
# Node functions — Phase 1: Outline
# ---------------------------------------------------------------------------


async def outline_generator(state: PipelineState) -> dict[str, Any]:
    """Node ④a — LLM slices the concept into learning nodes."""
    logger.info("[④a] OutlineGenerator: slicing concept into learning nodes...")

    ctx = state.get("adaptation_ctx", {})
    concept = state.get("concept_ctx", {})
    progress = state.get("progress_ctx", {})
    confusion = state.get("confusion_fwd", [])
    chunks = state.get("grounded_chunks", [])
    depth_tier = state.get("depth_tier", "intermediate")

    mastery = progress.get("mastery_scores", {})
    prereqs = concept.get("prerequisite", [])
    gaps = [p for p in prereqs if mastery.get(p, 0.0) < 0.5]

    chunks_text = "\n\n".join(
        f"[{c['source']}] (relevance: {c['score']})\n{c['text']}" for c in chunks
    )

    user_msg = OUTLINE_USER_TEMPLATE.format(
        concept_id=concept.get("concept_id", "unknown"),
        prerequisites=", ".join(prereqs) if prereqs else "none",
        prereq_gaps=", ".join(gaps) if gaps else "none",
        background=ctx.get("background", ""),
        role=ctx.get("role", ""),
        prior_knowledge=", ".join(ctx.get("prior_knowledge", [])),
        learning_goal=ctx.get("learning_goal", ""),
        domain_framing=ctx.get("domain_framing", "general"),
        depth_tier=depth_tier,
        confusion_fwd=", ".join(confusion) if confusion else "none",
        chunks_text=chunks_text,
    )

    cfg = _load_config()["outline"]
    client = _get_client()
    started = _log_llm_call_start(
        "[④a] OutlineGenerator",
        cfg["model"],
        extra=f"depth={depth_tier} chunks={len(chunks)}",
    )
    def _make_call():
        return client.chat.completions.create(
            model=cfg["model"],
            messages=[
                {"role": "system", "content": OUTLINE_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=cfg["temperature"],
            max_tokens=cfg["max_tokens"],
            response_format={"type": "json_object"},
        )

    failed = False
    error_summary = ""
    usage_metrics = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    call_stats: dict[str, Any] = {}
    try:
        response = await _llm_call_with_retry(
            _make_call,
            stage="[④a] OutlineGenerator",
            stats=call_stats,
        )
        _log_response_metadata("[④a] OutlineGenerator", response, started_at=started)
        usage_metrics = _response_usage_metrics(response)
        outline = _parse_json(_extract_text_content(response.choices[0].message.content))
    except _RETRYABLE_EXCEPTIONS as exc:
        failed = True
        error_summary = f"{type(exc).__name__}: {str(exc)[:160]}"
        logger.error("[④a] OutlineGenerator exhausted retries: %s", error_summary)
        outline = _fallback_outline(state)

    logger.info("[④a] OutlineGenerator: produced %d learning nodes", len(outline))
    for i, node in enumerate(outline, 1):
        logger.info("[④a]   %d. %s", i, node.get("title", "?"))
    return {
        "outline": outline,
        "run_metrics": _merge_run_metrics(
            state,
            "outline",
            {
                "duration_s": round(time.perf_counter() - started, 3),
                "nodes": len(outline),
                "model": cfg["model"],
                "failed": failed,
                "error": error_summary,
                "attempts": int(call_stats.get("attempts", 0)),
                "prompt_tokens": usage_metrics["prompt_tokens"],
                "completion_tokens": usage_metrics["completion_tokens"],
                "total_tokens": usage_metrics["total_tokens"],
            },
        ),
    }


# ---------------------------------------------------------------------------
# Node functions — Phase 2: Content (per node)
# ---------------------------------------------------------------------------


def route_by_level(state: PipelineState) -> str:
    """Router — select content generator node based on depth_tier."""
    tier = state.get("depth_tier", "intermediate")
    if tier in ("beginner", "intermediate", "advanced"):
        return tier
    logger.warning("Unknown depth_tier '%s', falling back to intermediate", tier)
    return "intermediate"


async def _content_gen_impl(
    state: PipelineState,
    system_prompt: str,
    user_template: str,
) -> dict[str, Any]:
    """Core content generation logic shared by all tier-specific nodes.

    Story 5.3 AC-13/14: LLM calls route through ``_llm_call_with_retry`` for
    429 resilience; outline nodes draft under an ``asyncio.Semaphore`` whose
    size is ``content.concurrency`` (default 2). Output order is preserved by
    sorting the gathered results by outline index — concurrency must never
    shuffle the final narrative.
    """
    depth_tier = state.get("depth_tier", "intermediate")
    logger.info("[④b] ContentGenerator (%s): generating content for each node...", depth_tier)

    ctx = state.get("adaptation_ctx", {})
    concept = state.get("concept_ctx", {})
    outline = state.get("outline", [])
    chunks = state.get("grounded_chunks", [])
    progress = state.get("progress_ctx", {})
    confusion = state.get("confusion_fwd", [])

    mastery = progress.get("mastery_scores", {})
    prereqs = concept.get("prerequisite", [])
    gaps = [p for p in prereqs if mastery.get(p, 0.0) < 0.5]

    chunks_text = "\n\n".join(
        f"[{c['source']}] (relevance: {c['score']})\n{c['text']}" for c in chunks
    )

    cfg = _load_config()["content"]
    client = _get_client()
    stage_started = time.perf_counter()

    concurrency = max(1, int(cfg.get("concurrency", 1)))
    semaphore = asyncio.Semaphore(concurrency)
    total_nodes = len(outline)
    logger.info(
        "[④b] drafting %d nodes with concurrency=%d", total_nodes, concurrency
    )

    async def _draft_one(
        i: int, node: dict[str, Any]
    ) -> tuple[int, dict[str, Any], list[dict[str, Any]], float, dict[str, Any]]:
        node_title = node.get("title", f"Node {i + 1}")
        previous = [n.get("title", "") for n in outline[:i]]
        node_metrics = _new_llm_metrics()
        async with semaphore:
            logger.info("[④b]   Node %d/%d: %s", i + 1, total_nodes, node_title)
            node_started = _log_llm_call_start(
                f"[④b]   Node {i + 1}/{total_nodes}",
                cfg["model"],
                extra=f"max_tokens={cfg['max_tokens']}",
            )

            user_msg = user_template.format(
                node_title=node_title,
                node_summary=node.get("summary", ""),
                rag_focus=node.get("rag_focus", ""),
                node_index=i + 1,
                total_nodes=total_nodes,
                concept_id=concept.get("concept_id", "unknown"),
                previous_nodes=", ".join(previous) if previous else "none (this is the first node)",
                background=ctx.get("background", ""),
                role=ctx.get("role", ""),
                prior_knowledge=", ".join(ctx.get("prior_knowledge", [])),
                learning_goal=ctx.get("learning_goal", ""),
                domain_framing=ctx.get("domain_framing", "general"),
                depth_tier=depth_tier,
                prereq_gaps=", ".join(gaps) if gaps else "none",
                confusion_fwd=", ".join(confusion) if confusion else "none",
                chunks_text=chunks_text,
            )

            def _make_call():
                return client.chat.completions.create(
                    model=cfg["model"],
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_msg},
                    ],
                    temperature=cfg["temperature"],
                    max_tokens=cfg["max_tokens"],
                    response_format={"type": "json_object"},
                )

            try:
                call_stats: dict[str, Any] = {}
                response = await _llm_call_with_retry(
                    _make_call,
                    stage=f"[④b]   Node {i + 1}/{total_nodes}",
                    stats=call_stats,
                )
                _log_response_metadata(
                    f"[④b]   Node {i + 1}/{total_nodes}", response, started_at=node_started
                )
                _record_llm_success(node_metrics, response, call_stats=call_stats, stage="draft")

                raw_content = _extract_text_content(response.choices[0].message.content)
                parsed: Any = None
                try:
                    parsed = _parse_json(raw_content)
                    sections = _validate_sections(parsed)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(
                        "[④b]   Node %d/%d parse/validate failed: %s", i + 1, total_nodes, e
                    )
                    logger.warning("[④b]   Raw preview: %s", _strip_fences(raw_content)[:300])
                    repaired: Any | None = None
                    try:
                        repaired = await _repair_json_response(
                            client=client,
                            model=cfg["model"],
                            max_tokens=cfg["max_tokens"],
                            raw=raw_content,
                            node_title=node_title,
                            metrics=node_metrics,
                        )
                        sections = _validate_sections(repaired)
                    except _RETRYABLE_EXCEPTIONS as te:
                        logger.error(
                            "[④b]   Node %d/%d repair exhausted retries/timed out: %s — salvaging",
                            i + 1,
                            total_nodes,
                            te,
                        )
                        sections = _salvage_sections(
                            parsed if isinstance(parsed, dict) else {"sections": []}
                        )
                    except ValueError as e2:
                        logger.warning(
                            "[④b]   Node %d/%d still invalid after repair: %s",
                            i + 1,
                            total_nodes,
                            e2,
                        )
                        regenerated: Any | None = None
                        try:
                            regenerated = await _regenerate_node_json(
                                client=client,
                                cfg=cfg,
                                system_prompt=system_prompt,
                                user_msg=user_msg,
                                node_title=node_title,
                                node_index=i + 1,
                                total_nodes=total_nodes,
                                metrics=node_metrics,
                            )
                            sections = _validate_sections(regenerated)
                        except (json.JSONDecodeError, ValueError, RateLimitError, APITimeoutError, APIConnectionError, asyncio.TimeoutError, TimeoutError) as e3:
                            logger.error(
                                "[④b]   Node %d/%d regeneration also failed: %s — using best-effort payload",
                                i + 1,
                                total_nodes,
                                e3,
                            )
                            salvage_source = (
                                regenerated if regenerated is not None else repaired
                            )
                            sections = _salvage_sections(
                                salvage_source
                                if salvage_source is not None
                                else {"sections": []}
                            )
                failed = False
                error_summary = ""
            except _RETRYABLE_EXCEPTIONS as exc:
                error_summary = f"{type(exc).__name__}: {str(exc)[:160]}"
                _record_llm_failure(
                    node_metrics,
                    call_stats=call_stats,
                    error=error_summary,
                    stage="draft",
                )
                logger.error(
                    "[④b]   Node %d/%d exhausted retries: %s — inserting fallback section",
                    i + 1,
                    total_nodes,
                    error_summary,
                )
                sections = _failed_node_sections(node_title, error_summary)
                failed = True

            node_duration = time.perf_counter() - node_started

        # Collect typed image markers (seen-set keeps duplicates out).
        image_prompts_for_node: list[dict[str, Any]] = []
        for sec in sections:
            seen: set[tuple[str, str]] = set()
            for kind, desc in iter_image_markers(sec.get("content", "")):
                key = (kind, desc)
                if key not in seen:
                    seen.add(key)
                    image_prompts_for_node.append(
                        {
                            "node_title": node_title,
                            "description": desc,
                            "kind": kind,
                            "section": sec.get("section", ""),
                        }
                    )
            for marker in sec.get("markers", []):
                parsed_marker = parse_image_marker(marker)
                if not parsed_marker:
                    continue
                kind, desc = parsed_marker
                key = (kind, desc)
                if key not in seen:
                    seen.add(key)
                    image_prompts_for_node.append(
                        {
                            "node_title": node_title,
                            "description": desc,
                            "kind": kind,
                            "section": sec.get("section", ""),
                        }
                    )

        return (
            i,
            {"node_title": node_title, "sections": sections},
            image_prompts_for_node,
            node_duration,
            {
                "node_title": node_title,
                "duration_s": round(node_duration, 3),
                "failed": failed,
                "error": error_summary,
                "attempts": int(node_metrics["attempts"]),
                "llm_calls": int(node_metrics["llm_calls"]),
                "failed_calls": int(node_metrics["failed_calls"]),
                "prompt_tokens": int(node_metrics["prompt_tokens"]),
                "completion_tokens": int(node_metrics["completion_tokens"]),
                "total_tokens": int(node_metrics["total_tokens"]),
                "errors": list(node_metrics["errors"]),
            },
        )

    tasks = [_draft_one(i, node) for i, node in enumerate(outline)]
    gathered = await asyncio.gather(*tasks)
    # Preserve outline order even if drafting completed out-of-order (AC-14).
    gathered.sort(key=lambda r: r[0])
    all_nodes: list[dict[str, Any]] = [r[1] for r in gathered]
    all_image_prompts: list[dict[str, Any]] = [p for r in gathered for p in r[2]]
    per_node_durations: list[float] = [r[3] for r in gathered]
    per_node_metrics: list[dict[str, Any]] = [r[4] for r in gathered]
    failed_nodes = [m for m in per_node_metrics if m.get("failed")]
    content_metrics = _new_llm_metrics()
    for metrics in per_node_metrics:
        _merge_llm_metrics(content_metrics, metrics)

    total_duration = time.perf_counter() - stage_started
    logger.info(
        "[④b] ContentGenerator: %d nodes, %d image prompts (total %.1fs)",
        len(all_nodes),
        len(all_image_prompts),
        total_duration,
    )
    return {
        "nodes": all_nodes,
        "image_prompts": all_image_prompts,
        "run_metrics": _merge_run_metrics(
            state,
            "content",
            {
                "duration_s": round(total_duration, 3),
                "nodes": len(all_nodes),
                "per_node_durations_s": [round(d, 3) for d in per_node_durations],
                "per_node": per_node_metrics,
                "image_prompts_collected": len(all_image_prompts),
                "tier": depth_tier,
                "model": cfg["model"],
                "prompt_tokens": int(content_metrics["prompt_tokens"]),
                "completion_tokens": int(content_metrics["completion_tokens"]),
                "total_tokens": int(content_metrics["total_tokens"]),
                "llm_calls": int(content_metrics["llm_calls"]),
                "attempts": int(content_metrics["attempts"]),
                "failed_calls": int(content_metrics["failed_calls"]),
                "errors": list(content_metrics["errors"]),
                "failed_nodes": failed_nodes,
                "failed_count": len(failed_nodes),
            },
        ),
    }


def _make_content_gen_node(tier: str):
    """Factory — create a content-generator node bound to a specific depth tier."""
    prompts = TIER_CONTENT_PROMPTS[tier]

    async def _node(state: PipelineState) -> dict[str, Any]:
        return await _content_gen_impl(state, prompts["system"], prompts["user"])

    _node.__name__ = f"content_gen_{tier}"
    _node.__qualname__ = f"content_gen_{tier}"
    return _node


# ---------------------------------------------------------------------------
# Node functions — Phase 2.5: Fact-check (domain critic)
# ---------------------------------------------------------------------------


async def _critique_node(
    *,
    client: AsyncOpenAI,
    cfg: dict[str, Any],
    ctx: dict[str, Any],
    depth_tier: str,
    concept_id: str,
    node: dict[str, Any],
    metrics: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Run the critic LLM on a single node's sections and return its issues."""
    sections_payload = json.dumps(
        [
            {"section": s.get("section", ""), "content": s.get("content", "")}
            for s in node.get("sections", [])
        ],
        ensure_ascii=False,
    )
    user_msg = FACT_CHECK_USER_TEMPLATE.format(
        background=ctx.get("background", ""),
        role=ctx.get("role", ""),
        domain_framing=ctx.get("domain_framing", "general"),
        depth_tier=depth_tier,
        concept_id=concept_id,
        node_title=node.get("node_title", ""),
        sections_json=sections_payload,
    )
    stage_label = f"[④b.5] FactCheck '{node.get('node_title', '')[:40]}'"
    started = _log_llm_call_start(stage_label, cfg["model"])
    def _make_call():
        return client.chat.completions.create(
            model=cfg["model"],
            messages=[
                {"role": "system", "content": FACT_CHECK_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=cfg["temperature"],
            max_tokens=cfg["max_tokens"],
            response_format={"type": "json_object"},
        )

    call_stats: dict[str, Any] = {}
    try:
        response = await _llm_call_with_retry(_make_call, stage=stage_label, stats=call_stats)
    except _RETRYABLE_EXCEPTIONS as exc:
        _record_llm_failure(
            metrics,
            call_stats=call_stats,
            error=f"{type(exc).__name__}: {str(exc)[:200]}",
            stage="critic",
        )
        raise
    _record_llm_success(metrics, response, call_stats=call_stats, stage="critic")
    _log_response_metadata(stage_label, response, started_at=started)
    raw = _extract_text_content(response.choices[0].message.content)
    try:
        parsed = _parse_json(raw)
    except json.JSONDecodeError as e:
        logger.warning("[④b.5]   parse failed: %s — treating as no issues", e)
        return []
    payload = parsed.get("issues") if isinstance(parsed, dict) else parsed
    if not isinstance(payload, list):
        return []
    try:
        validated = FactCheckResponse(issues=payload)
    except ValidationError as e:
        logger.warning("[④b.5]   schema invalid: %s — dropping payload", e)
        return []
    return [issue.model_dump() for issue in validated.issues]


async def _regenerate_section_with_critique(
    *,
    client: AsyncOpenAI,
    cfg: dict[str, Any],
    ctx: dict[str, Any],
    depth_tier: str,
    concept_id: str,
    chunks_text: str,
    gaps: list[str],
    confusion: list[str],
    outline: list[dict[str, str]],
    node_idx: int,
    node: dict[str, Any],
    section_idx: int,
    section: dict[str, Any],
    critiques: list[dict[str, Any]],
    content_system_prompt: str,
    content_user_template: str,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Re-ask the content LLM to rewrite a single section, given critic notes."""
    critique_text = "\n".join(
        f"- {c['problem']} (suggestion: {c['suggestion']})" for c in critiques
    )
    previous = [n.get("title", "") for n in outline[:node_idx]]
    base_user = content_user_template.format(
        node_title=node.get("node_title", ""),
        node_summary=outline[node_idx].get("summary", "") if node_idx < len(outline) else "",
        rag_focus=outline[node_idx].get("rag_focus", "") if node_idx < len(outline) else "",
        node_index=node_idx + 1,
        total_nodes=len(outline),
        concept_id=concept_id,
        previous_nodes=", ".join(previous) if previous else "none (this is the first node)",
        background=ctx.get("background", ""),
        role=ctx.get("role", ""),
        prior_knowledge=", ".join(ctx.get("prior_knowledge", [])),
        learning_goal=ctx.get("learning_goal", ""),
        domain_framing=ctx.get("domain_framing", "general"),
        depth_tier=depth_tier,
        prereq_gaps=", ".join(gaps) if gaps else "none",
        confusion_fwd=", ".join(confusion) if confusion else "none",
        chunks_text=chunks_text,
    )
    repair_user = (
        base_user
        + "\n\n## CRITIC FEEDBACK ON A PREVIOUS DRAFT — fix in the new draft\n"
        + f"The section titled '{section.get('section', '')}' was flagged with:\n"
        + critique_text
        + "\n\nReturn the SAME JSON object as before, but with the flagged section "
        + "rewritten to address every critique. Keep all other sections intact."
    )
    stage_label = f"[④b.5]   Regen '{section.get('section', '')[:40]}'"
    started = _log_llm_call_start(stage_label, cfg["model"])
    def _make_call():
        return client.chat.completions.create(
            model=cfg["model"],
            messages=[
                {"role": "system", "content": content_system_prompt},
                {"role": "user", "content": repair_user},
            ],
            temperature=cfg["temperature"],
            max_tokens=cfg["max_tokens"],
            response_format={"type": "json_object"},
        )

    call_stats: dict[str, Any] = {}
    try:
        response = await _llm_call_with_retry(_make_call, stage=stage_label, stats=call_stats)
    except _RETRYABLE_EXCEPTIONS as exc:
        _record_llm_failure(
            metrics,
            call_stats=call_stats,
            error=f"{type(exc).__name__}: {str(exc)[:200]}",
            stage="rewrite",
        )
        raise
    _record_llm_success(metrics, response, call_stats=call_stats, stage="rewrite")
    _log_response_metadata(stage_label, response, started_at=started)
    raw = _extract_text_content(response.choices[0].message.content)
    try:
        parsed = _parse_json(raw)
        new_sections = _validate_sections(parsed)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("[④b.5]   regenerated section failed validation: %s", e)
        return None
    # Find the rewritten section by heading match; fall back to positional.
    target = section.get("section", "")
    for ns in new_sections:
        if ns.get("section") == target:
            return ns
    if 0 <= section_idx < len(new_sections):
        return new_sections[section_idx]
    return None


# ---------------------------------------------------------------------------
# Risk classification — rule-based routing for selective QA (Story 5.3 AC-6/7)
# ---------------------------------------------------------------------------

# Keywords whose presence in a drafted node's content flips it to high risk.
# Matched with word boundaries (``\b...\b``) so "treaty" does NOT match
# "treatment". Kept deterministic on purpose — no LLM, no embedding lookup.
_HIGH_RISK_KEYWORDS = frozenset(
    {
        "causes",
        "caused",
        "causing",
        "effect of",
        "effects of",
        "clinical",
        "medical",
        "treatment",
        "treatments",
        "patient",
        "patients",
        "confound",
        "confounder",
        "confounding",
        "confounders",
        "counterfactual",
        "counterfactuals",
    }
)

# Pre-compiled word-boundary pattern. Longer keywords first so multi-word
# phrases like "effect of" win before the single-word "effect" would.
_HIGH_RISK_PATTERN = re.compile(
    r"\b("
    + "|".join(re.escape(kw) for kw in sorted(_HIGH_RISK_KEYWORDS, key=len, reverse=True))
    + r")\b",
    re.IGNORECASE,
)


def _classify_node_risk(node: dict[str, Any]) -> str:
    """Deterministic rule-based risk classification (Story 5.3 AC-6).

    Returns ``"high"`` if ANY section of the node satisfies:
      1. ``part == "definition"`` — formal statement, theorem, or rigorous claim
      2. Contains a ``[FORMULA: ...]`` marker (in markers list or inline content)
      3. Content matches one of ``_HIGH_RISK_KEYWORDS`` under word boundaries

    Otherwise returns ``"low"`` — safe to skip the critic LLM and save a call.

    Pure function: no I/O, no config lookup. Used by ``fact_checker`` to route
    each drafted node to either the rule-only fast path or the LLM critic.
    """
    sections = node.get("sections", [])
    if not isinstance(sections, list):
        return "low"
    for sec in sections:
        if not isinstance(sec, dict):
            continue
        if sec.get("part") == "definition":
            return "high"
        markers = sec.get("markers") or []
        if isinstance(markers, list):
            for m in markers:
                if isinstance(m, str) and m.lstrip().startswith("[FORMULA:"):
                    return "high"
        content = sec.get("content") or ""
        if not isinstance(content, str):
            continue
        if "[FORMULA:" in content:
            return "high"
        if _HIGH_RISK_PATTERN.search(content):
            return "high"
    return "low"


async def fact_checker(state: PipelineState) -> dict[str, Any]:
    """Node ④b.5 — domain critic LLM reviews each generated node.

    Selective QA (Story 5.3 AC-6/7): each node is first classified as low- or
    high-risk by ``_classify_node_risk``. Low-risk nodes skip the critic entirely
    and are recorded in ``qa_log`` with ``qa_path="rule-only"``. High-risk nodes
    route to the critic; on critical severity the offending section is
    regenerated (``regenerate_on_critical``), and if ``targeted_recheck`` is
    enabled a single re-critique runs on the rewrite (AC-8) without looping.

    The node is a no-op when ``fact_check.enabled`` is false.
    """
    cfg = _load_config().get("fact_check", {})
    if not cfg.get("enabled", False):
        logger.info("[④b.5] FactChecker: disabled, skipping")
        return {"fact_check_issues": []}

    nodes = state.get("nodes", [])
    if not nodes:
        return {"fact_check_issues": []}

    stage_started = time.perf_counter()
    logger.info("[④b.5] FactChecker: critiquing %d nodes...", len(nodes))

    ctx = state.get("adaptation_ctx", {})
    concept = state.get("concept_ctx", {})
    progress = state.get("progress_ctx", {})
    confusion = state.get("confusion_fwd", [])
    chunks = state.get("grounded_chunks", [])
    outline = state.get("outline", [])
    depth_tier = state.get("depth_tier", "intermediate")
    concept_id = concept.get("concept_id", "unknown")

    mastery = progress.get("mastery_scores", {})
    prereqs = concept.get("prerequisite", [])
    gaps = [p for p in prereqs if mastery.get(p, 0.0) < 0.5]
    chunks_text = "\n\n".join(
        f"[{c['source']}] (relevance: {c['score']})\n{c['text']}" for c in chunks
    )

    client = _get_client()
    content_cfg = _load_config()["content"]
    tier_prompts = TIER_CONTENT_PROMPTS.get(depth_tier, TIER_CONTENT_PROMPTS["intermediate"])
    regen_critical = bool(cfg.get("regenerate_on_critical", False))
    max_attempts = int(cfg.get("max_regeneration_attempts", 1))

    targeted_recheck = bool(cfg.get("targeted_recheck", False))

    all_issues: list[dict[str, Any]] = []
    qa_log: list[dict[str, Any]] = []
    fact_check_metrics = _new_llm_metrics()
    for node_idx, node in enumerate(nodes):
        node_title = node.get("node_title", f"Node {node_idx + 1}")
        node_metrics = _new_llm_metrics()

        # Rule-based risk classification runs first — low-risk nodes skip the
        # expensive critic call entirely (Story 5.3 AC-6).
        risk = _classify_node_risk(node)
        if risk == "low":
            logger.info(
                "[④b.5]   Node %d/%d: LOW risk — skipping critic (rule-only)",
                node_idx + 1,
                len(nodes),
            )
            qa_log.append(
                {
                    "node_title": node_title,
                    "qa_path": "rule-only",
                    "risk": "low",
                    "issues": 0,
                    "critical": 0,
                    "rewrites": 0,
                    "attempts": 0,
                    "llm_calls": 0,
                    "failed_calls": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                }
            )
            continue

        logger.info(
            "[④b.5]   Node %d/%d: HIGH risk — critiquing '%s'",
            node_idx + 1,
            len(nodes),
            node_title,
        )
        try:
            issues = await _critique_node(
                client=client,
                cfg=cfg,
                ctx=ctx,
                depth_tier=depth_tier,
                concept_id=concept_id,
                node=node,
                metrics=node_metrics,
            )
        except Exception as e:
            logger.warning("[④b.5]   critique failed for '%s': %s", node_title, str(e)[:200])
            qa_log.append(
                {
                    "node_title": node_title,
                    "qa_path": "critic-failed",
                    "risk": "high",
                    "issues": 0,
                    "critical": 0,
                    "rewrites": 0,
                    "attempts": int(node_metrics["attempts"]),
                    "llm_calls": int(node_metrics["llm_calls"]),
                    "failed_calls": int(node_metrics["failed_calls"]),
                    "prompt_tokens": int(node_metrics["prompt_tokens"]),
                    "completion_tokens": int(node_metrics["completion_tokens"]),
                    "total_tokens": int(node_metrics["total_tokens"]),
                    "errors": list(node_metrics["errors"]),
                }
            )
            _merge_llm_metrics(fact_check_metrics, node_metrics)
            continue

        rewrite_count = 0
        if issues:
            for issue in issues:
                issue["node_title"] = node_title
            all_issues.extend(issues)
            crit = sum(1 for i in issues if i.get("severity") == "critical")
            minor = len(issues) - crit
            logger.info(
                "[④b.5]   Node %d/%d: %d critical, %d minor",
                node_idx + 1,
                len(nodes),
                crit,
                minor,
            )
            for issue in issues:
                logger.info(
                    "[④b.5]     [%s] %s — %s",
                    issue.get("severity", "?"),
                    issue.get("section", "?")[:40],
                    issue.get("problem", "")[:120],
                )

            if regen_critical:
                critical_by_section: dict[str, list[dict[str, Any]]] = {}
                for issue in issues:
                    if issue.get("severity") == "critical":
                        critical_by_section.setdefault(
                            issue.get("section", ""), []
                        ).append(issue)

                for section_idx, section in enumerate(node.get("sections", [])):
                    sec_title = section.get("section", "")
                    critiques = critical_by_section.get(sec_title)
                    if not critiques:
                        continue
                    for attempt in range(max_attempts):
                        logger.info(
                            "[④b.5]   Regenerating '%s' / '%s' (attempt %d)",
                            node_title,
                            sec_title,
                            attempt + 1,
                        )
                        rewritten = await _regenerate_section_with_critique(
                            client=client,
                            cfg=content_cfg,
                            ctx=ctx,
                            depth_tier=depth_tier,
                            concept_id=concept_id,
                            chunks_text=chunks_text,
                            gaps=gaps,
                            confusion=confusion,
                            outline=outline,
                            node_idx=node_idx,
                            node=node,
                            section_idx=section_idx,
                            section=section,
                            critiques=critiques,
                            content_system_prompt=tier_prompts["system"],
                            content_user_template=tier_prompts["user"],
                            metrics=node_metrics,
                        )
                        if rewritten:
                            node["sections"][section_idx] = rewritten
                            rewrite_count += 1
                            break
        else:
            logger.info("[④b.5]   Node %d/%d: no issues", node_idx + 1, len(nodes))

        # Targeted re-critique (Story 5.3 AC-8): if we rewrote at least one
        # section AND the operator opted in, run the critic ONCE more on the
        # updated node. Any residual issues are logged but do not trigger
        # another rewrite — this caps per-node cost at 3 critic calls.
        recheck_ran = False
        if targeted_recheck and rewrite_count > 0:
            logger.info(
                "[④b.5]   Node %d/%d: targeted re-check after %d rewrite(s)",
                node_idx + 1,
                len(nodes),
                rewrite_count,
            )
            try:
                recheck_issues = await _critique_node(
                    client=client,
                    cfg=cfg,
                    ctx=ctx,
                    depth_tier=depth_tier,
                    concept_id=concept_id,
                    node=node,
                    metrics=node_metrics,
                )
                recheck_ran = True
                if recheck_issues:
                    for issue in recheck_issues:
                        issue["node_title"] = node_title
                        issue["phase"] = "recheck"
                    all_issues.extend(recheck_issues)
            except Exception as e:
                logger.warning(
                    "[④b.5]   recheck failed for '%s': %s", node_title, str(e)[:200]
                )

        if rewrite_count > 0 and recheck_ran:
            qa_path = "critic-ran+rewrite+recheck"
        elif rewrite_count > 0:
            qa_path = "critic-ran+rewrite"
        else:
            qa_path = "critic-ran"
        qa_log.append(
            {
                "node_title": node_title,
                "qa_path": qa_path,
                "risk": "high",
                "issues": len(issues),
                "critical": sum(1 for i in issues if i.get("severity") == "critical"),
                "rewrites": rewrite_count,
                "attempts": int(node_metrics["attempts"]),
                "llm_calls": int(node_metrics["llm_calls"]),
                "failed_calls": int(node_metrics["failed_calls"]),
                "prompt_tokens": int(node_metrics["prompt_tokens"]),
                "completion_tokens": int(node_metrics["completion_tokens"]),
                "total_tokens": int(node_metrics["total_tokens"]),
                "errors": list(node_metrics["errors"]),
            }
        )
        _merge_llm_metrics(fact_check_metrics, node_metrics)

    fact_check_duration = time.perf_counter() - stage_started
    logger.info(
        "[④b.5] FactChecker: %d issues across all nodes (total %.1fs)",
        len(all_issues),
        fact_check_duration,
    )
    return {
        "fact_check_issues": all_issues,
        "nodes": nodes,
        "qa_log": qa_log,
        "run_metrics": _merge_run_metrics(
            state,
            "fact_check",
            {
                "duration_s": round(fact_check_duration, 3),
                "total_issues": len(all_issues),
                "critical_issues": sum(
                    1 for i in all_issues if i.get("severity") == "critical"
                ),
                "minor_issues": sum(
                    1 for i in all_issues if i.get("severity") != "critical"
                ),
                "prompt_tokens": int(fact_check_metrics["prompt_tokens"]),
                "completion_tokens": int(fact_check_metrics["completion_tokens"]),
                "total_tokens": int(fact_check_metrics["total_tokens"]),
                "llm_calls": int(fact_check_metrics["llm_calls"]),
                "attempts": int(fact_check_metrics["attempts"]),
                "failed_calls": int(fact_check_metrics["failed_calls"]),
                "errors": list(fact_check_metrics["errors"]),
                "per_node": qa_log,
                "qa_path_counts": {
                    path: sum(1 for e in qa_log if e["qa_path"] == path)
                    for path in {e["qa_path"] for e in qa_log}
                },
                "nodes_reviewed": len(qa_log),
            },
        ),
    }


# ---------------------------------------------------------------------------
# Node functions — Phase 3: Image generation
# ---------------------------------------------------------------------------


async def image_generator(state: PipelineState) -> dict[str, Any]:
    """Node ④c — generate images for typed image markers via Gemini image model.

    Respects two Story 5.3 config flags on ``image`` in
    ``passive_content_generator.yaml``:

    - ``enabled: false`` (AC-9) — skip image generation entirely. Returns
      ``image_refs=[]`` and flags ``image_skipped=True``. No LLM calls are
      issued, even if ``image_prompts`` is non-empty.
    - ``mode: "deferred"`` (AC-10) — the graph topology places this node AFTER
      ``cache_writer`` so text + cache persistence complete first. The node
      itself behaves the same; see ``build_graph`` for the wiring.
    """
    cfg = _load_config().get("image", {})
    # AC-9 — hard disable (cost-sensitive / demo without images)
    if cfg.get("enabled", True) is False:
        logger.info("[④c] ImageGenerator: disabled via config, skipping")
        return {
            "image_refs": [],
            "image_skipped": True,
            "run_metrics": _merge_run_metrics(
                state,
                "image",
                {"duration_s": 0.0, "generated": 0, "prompts": 0, "skipped": True},
            ),
        }

    prompts = state.get("image_prompts", [])
    if not prompts:
        logger.info("[④c] ImageGenerator: no image prompts, skipping")
        return {
            "image_refs": [],
            "run_metrics": _merge_run_metrics(
                state,
                "image",
                {"duration_s": 0.0, "generated": 0, "prompts": 0, "skipped": False},
            ),
        }

    logger.info("[④c] ImageGenerator: generating %d images...", len(prompts))
    stage_started = time.perf_counter()
    per_image_durations: list[float] = []
    image_metrics = _new_llm_metrics()
    failed_prompts: list[dict[str, Any]] = []

    client = _get_client()
    image_refs: list[dict[str, str]] = []

    user_id = state.get("user_id", "unknown_user")
    concept_id = state.get("concept_ctx", {}).get("concept_id") or state.get(
        "concept_id", "unknown_concept"
    )
    img_dir = get_passive_images_dir(user_id, concept_id)
    img_dir.mkdir(parents=True, exist_ok=True)

    for img_idx, ip in enumerate(prompts, 1):
        desc = ip["description"]
        kind = ip.get("kind", "PEDAGOGICAL_IMAGE")
        prompt_errors: list[str] = []
        prompt_succeeded = False
        eta_str = ""
        if per_image_durations:
            avg = sum(per_image_durations) / len(per_image_durations)
            remaining = avg * (len(prompts) - img_idx + 1)
            eta_str = f" (ETA ~{remaining:.0f}s)"
        logger.info(
            "[④c]   Image %d/%d [%s]: %s%s",
            img_idx,
            len(prompts),
            kind,
            desc[:80],
            eta_str,
        )
        img_started = time.perf_counter()

        for model in [cfg["model"], cfg.get("fallback_model")]:
            if not model:
                continue
            call_stats: dict[str, Any] = {}
            try:
                _log_llm_call_start(f"[④c]   Image {img_idx}/{len(prompts)}", model)
                def _make_call():
                    return client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "user",
                                "content": image_generation_brief(kind, desc),
                            }
                        ],
                        extra_body={"modalities": ["image", "text"]},
                        max_tokens=1024,
                    )

                response = await _llm_call_with_retry(
                    _make_call,
                    stage=f"[④c]   Image {img_idx}/{len(prompts)}",
                    stats=call_stats,
                )
                _record_llm_success(
                    image_metrics,
                    response,
                    call_stats=call_stats,
                    stage=f"image:{model}",
                )

                msg = response.choices[0].message
                raw = msg.model_dump() if hasattr(msg, "model_dump") else {}

                # Gemini returns images in msg.images as [{image_url: {url: "data:..."}}]
                images = getattr(msg, "images", None) or raw.get("images", [])
                if images:
                    for img_data in images:
                        data_url = ""
                        if isinstance(img_data, dict):
                            data_url = img_data.get("image_url", {}).get("url", "")
                        if data_url and data_url.startswith("data:image"):
                            # Extract base64 and save
                            b64_part = data_url.split(",", 1)[1] if "," in data_url else ""
                            if b64_part:
                                fname = f"img_{len(image_refs):02d}.png"
                                img_path = img_dir / fname
                                with open(img_path, "wb") as f:
                                    f.write(base64.b64decode(b64_part))
                                image_refs.append(
                                    {
                                        "node_title": ip["node_title"],
                                        "description": desc,
                                        "kind": kind,
                                        "section": ip.get("section", ""),
                                        "url": str(img_path),
                                        "model": model,
                                    }
                                )
                                logger.info("[④c]   Saved: %s", fname)
                                prompt_succeeded = True
                                break
                    else:
                        logger.warning("[④c]   %s: images field present but no data URL", model)
                        prompt_errors.append(f"{model}: no data URL in images field")
                        continue
                    break  # success, skip fallback

                # Fallback: check content for data URLs
                content = msg.content or ""
                b64_match = re.search(r"data:image/[^;]+;base64,([A-Za-z0-9+/=]+)", content)
                if b64_match:
                    fname = f"img_{len(image_refs):02d}.png"
                    img_path = img_dir / fname
                    with open(img_path, "wb") as f:
                        f.write(base64.b64decode(b64_match.group(1)))
                    image_refs.append(
                        {
                            "node_title": ip["node_title"],
                            "description": desc,
                            "kind": kind,
                            "section": ip.get("section", ""),
                            "url": str(img_path),
                            "model": model,
                        }
                    )
                    logger.info("[④c]   Saved (from content): %s", fname)
                    prompt_succeeded = True
                    break

                logger.warning("[④c]   %s returned no image data", model)
                prompt_errors.append(f"{model}: no image data returned")

            except Exception as e:
                _record_llm_failure(
                    image_metrics,
                    call_stats=call_stats,
                    error=f"{type(e).__name__}: {str(e)[:200]}",
                    stage=f"image:{model}",
                )
                logger.warning("[④c]   %s failed: %s", model, str(e)[:200])
                prompt_errors.append(f"{model}: {type(e).__name__}: {str(e)[:120]}")
                continue

        if not prompt_succeeded:
            failed_prompts.append(
                {
                    "node_title": ip["node_title"],
                    "description": desc,
                    "kind": kind,
                    "section": ip.get("section", ""),
                    "errors": prompt_errors,
                }
            )
        per_image_durations.append(time.perf_counter() - img_started)

    image_duration = time.perf_counter() - stage_started
    logger.info(
        "[④c] ImageGenerator: generated %d / %d images (total %.1fs)",
        len(image_refs),
        len(prompts),
        image_duration,
    )

    # Story 5.3 AC-10 — deferred mode: update the cached artifact in place
    # so the on-disk JSON reflects both text and images once images arrive.
    # (In inline mode the cache_writer runs after this node and handles it.)
    if cfg.get("mode") == "deferred":
        deferred_state = dict(state)
        deferred_state["image_refs"] = image_refs
        _persist_cache(deferred_state)
        logger.info("[④c] ImageGenerator: deferred mode — updated cache with image_refs")

    return {
        "image_refs": image_refs,
        "run_metrics": _merge_run_metrics(
            state,
            "image",
            {
                "duration_s": round(image_duration, 3),
                "generated": len(image_refs),
                "prompts": len(prompts),
                "failed_count": len(failed_prompts),
                "failed_prompts": failed_prompts,
                "prompt_tokens": int(image_metrics["prompt_tokens"]),
                "completion_tokens": int(image_metrics["completion_tokens"]),
                "total_tokens": int(image_metrics["total_tokens"]),
                "llm_calls": int(image_metrics["llm_calls"]),
                "attempts": int(image_metrics["attempts"]),
                "failed_calls": int(image_metrics["failed_calls"]),
                "errors": list(image_metrics["errors"]),
                "per_image_durations_s": [round(d, 3) for d in per_image_durations],
                "mode": cfg.get("mode", "inline"),
                "skipped": False,
            },
        ),
    }


# ---------------------------------------------------------------------------
# Cache reader + writer
# ---------------------------------------------------------------------------


def _cache_path_for(state: PipelineState) -> "Path":  # noqa: F821 — forward ref for mypy
    """Resolve the content.json cache path for this learner + concept."""
    from pathlib import Path  # local import keeps module-level cheap
    user_id = state.get("user_id") or "unknown"
    concept_id = (
        state.get("concept_ctx", {}).get("concept_id")
        or state.get("concept_id")
        or "unknown"
    )
    course_dir: Path = get_passive_course_dir(user_id, concept_id)
    return course_dir / "content.json"


def _resolve_concept_id(state: PipelineState) -> str:
    return (
        state.get("concept_ctx", {}).get("concept_id")
        or state.get("concept_id")
        or "unknown"
    )


def cache_reader(state: PipelineState) -> dict[str, Any]:
    """Node — check disk cache before running the generation pipeline.

    On hit, populate ``outline`` / ``nodes`` / ``image_refs`` from the cached
    JSON and set ``cache_hit=True`` so the conditional edge short-circuits to
    ``cache_writer``. On miss, return ``cache_hit=False`` so the pipeline
    proceeds to ``outline_generator``.

    Any read error (missing file, corrupt JSON, stale profile signature) is
    treated as a miss — we prefer regeneration over serving wrong content.
    """
    concept_id = _resolve_concept_id(state)
    profile_sig = state.get("profile_sig", "unknown")
    cache_key = f"{concept_id}:{profile_sig}"

    cache_path = _cache_path_for(state)
    if not cache_path.exists():
        logger.info("[cache] miss: %s (no file)", cache_key)
        return {"cache_hit": False, "cache_key": cache_key}

    try:
        data = json.loads(cache_path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("[cache] miss: could not read %s — %s", cache_path, exc)
        return {"cache_hit": False, "cache_key": cache_key}

    cached_key = data.get("cache_key")
    if cached_key != cache_key:
        logger.info(
            "[cache] miss: stale signature %r vs %r", cached_key, cache_key
        )
        return {"cache_hit": False, "cache_key": cache_key}

    logger.info("[cache] hit: %s", cache_key)
    return {
        "cache_hit": True,
        "cache_key": cache_key,
        "outline": data.get("outline", []),
        "nodes": data.get("nodes", []),
        "image_refs": data.get("image_refs", []),
    }


def route_after_cache_reader(state: PipelineState) -> str:
    """Conditional edge: hit -> cache_writer; miss -> outline_generator."""
    return "cache_writer" if state.get("cache_hit") else "outline_generator"


def _merge_run_metrics(
    state: PipelineState | dict[str, Any], phase: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Return an updated ``run_metrics`` dict with ``phase`` entry added.

    Each phase node calls this to append its metrics without clobbering the
    entries written by earlier phases. Story 5.3 AC-11.
    """
    merged = dict(state.get("run_metrics") or {})
    merged[phase] = payload
    return merged


def _persist_run_metrics(state: PipelineState) -> None:
    """Write run_metrics.json next to content.json (Story 5.3 AC-12)."""
    metrics = state.get("run_metrics") or {}
    if not metrics:
        return
    cache_path = _cache_path_for(state)
    metrics_path = cache_path.parent / "run_metrics.json"
    try:
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2))
        logger.info("[metrics] wrote %s", metrics_path)
    except OSError as exc:
        logger.warning("[metrics] write failed for %s: %s", metrics_path, exc)


def _persist_cache(state: PipelineState) -> None:
    """Best-effort write of the generation artifact to disk.

    Shared helper used by ``cache_writer`` and by ``image_generator`` in
    ``image.mode == "deferred"``, so the cache file can be updated with
    ``image_refs`` once image generation completes.
    """
    concept_id = _resolve_concept_id(state)
    profile_sig = state.get("profile_sig", "unknown")
    cache_key = f"{concept_id}:{profile_sig}"
    cache_path = _cache_path_for(state)
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "cache_key": cache_key,
            "concept_id": concept_id,
            "profile_sig": profile_sig,
            "outline": state.get("outline", []),
            "nodes": state.get("nodes", []),
            "image_refs": state.get("image_refs", []),
        }
        cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    except OSError as exc:
        logger.warning("[cache] write failed for %s: %s", cache_path, exc)


def cache_writer(state: PipelineState) -> dict[str, Any]:
    """Terminal node — persist the generated content and log a summary.

    When ``cache_hit`` is already True (the reader short-circuited), we skip
    the write to avoid overwriting the source with downstream enrichment.
    """
    concept_id = _resolve_concept_id(state)
    profile_sig = state.get("profile_sig", "unknown")
    cache_key = f"{concept_id}:{profile_sig}"

    outline = state.get("outline", [])
    nodes = state.get("nodes", [])
    images = state.get("image_refs", [])
    issues = state.get("fact_check_issues", [])

    cache_hit = bool(state.get("cache_hit"))
    if cache_hit:
        logger.info(
            "[cache] cache_key=%s | hit — skipping write | %d content nodes | %d images",
            cache_key,
            len(nodes),
            len(images),
        )
        return {"cache_key": cache_key, "cache_hit": True}

    _persist_cache(state)
    _persist_run_metrics(state)
    logger.info(
        "[cache] cache_key=%s | wrote %s | %d outline nodes | %d content nodes | %d images | %d fact-check issues",
        cache_key,
        _cache_path_for(state),
        len(outline),
        len(nodes),
        len(images),
        len(issues),
    )

    return {"cache_key": cache_key, "cache_hit": False}


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


_TIERS = ("beginner", "intermediate", "advanced")


def _syncify_async_node(async_fn):
    """Adapt an async LangGraph node to a sync callable for invoke()-based runtimes."""
    def _wrapped(state: PipelineState) -> dict[str, Any]:
        return asyncio.run(async_fn(state))

    _wrapped.__name__ = getattr(async_fn, "__name__", "sync_node")
    _wrapped.__qualname__ = getattr(async_fn, "__qualname__", _wrapped.__name__)
    return _wrapped


def build_graph(*, sync_mode: bool = False) -> StateGraph:
    """
    Construct the ContentGenerator pipeline.

    Loaders:  START → ① → ② → ③ → cache_reader
              (kept sequential because the current LangGraph runtime in this
               repo does not reliably schedule the intended 3-way join)
    Flow:     cache_reader → (hit → cache_writer | miss → ④a)
              ④a → router → content_gen_{tier} → ④b.5 → ④c → cache_writer → END
    """
    builder = StateGraph(PipelineState)
    outline_node = _syncify_async_node(outline_generator) if sync_mode else outline_generator
    fact_checker_node = _syncify_async_node(fact_checker) if sync_mode else fact_checker
    image_node = _syncify_async_node(image_generator) if sync_mode else image_generator

    builder.add_node("mock_profile_loader", mock_profile_loader)
    builder.add_node("mock_progress_loader", mock_progress_loader)
    builder.add_node("mock_concept_loader", mock_concept_loader)
    builder.add_node("cache_reader", cache_reader)
    builder.add_node("outline_generator", outline_node)
    for tier in _TIERS:
        content_node = _make_content_gen_node(tier)
        if sync_mode:
            content_node = _syncify_async_node(content_node)
        builder.add_node(f"content_gen_{tier}", content_node)
    builder.add_node("fact_checker", fact_checker_node)
    builder.add_node("image_generator", image_node)
    builder.add_node("cache_writer", cache_writer)

    # Loader chain. These loaders write disjoint parts of the state; the
    # original design intended a 3-way parallel fan-out / fan-in, but the
    # current LangGraph version in this repo does not reliably schedule the
    # join node afterward. A sequential chain preserves correctness and keeps
    # Story 5.3's cache-reader placement intact.
    builder.add_edge(START, "mock_profile_loader")
    builder.add_edge("mock_profile_loader", "mock_progress_loader")
    builder.add_edge("mock_progress_loader", "mock_concept_loader")
    builder.add_edge("mock_concept_loader", "cache_reader")

    # Cache hit short-circuits straight to cache_writer (which will skip the write)
    builder.add_conditional_edges(
        "cache_reader",
        route_after_cache_reader,
        {"cache_writer": "cache_writer", "outline_generator": "outline_generator"},
    )

    # Depth-tier router → tier-specific content generator
    builder.add_conditional_edges(
        "outline_generator",
        route_by_level,
        {tier: f"content_gen_{tier}" for tier in _TIERS},
    )

    # All tiers converge on fact_checker.
    for tier in _TIERS:
        builder.add_edge(f"content_gen_{tier}", "fact_checker")

    # Story 5.3 AC-10: in "deferred" mode, cache_writer runs BEFORE
    # image_generator so text becomes available immediately and images are
    # layered into the cache file afterward. In "inline" mode (default),
    # image_generator runs first so cache_writer's single write includes images.
    image_cfg = _load_config().get("image", {})
    image_mode = image_cfg.get("mode", "inline")
    if image_mode == "deferred":
        builder.add_edge("fact_checker", "cache_writer")
        builder.add_edge("cache_writer", "image_generator")
        builder.add_edge("image_generator", END)
    else:
        builder.add_edge("fact_checker", "image_generator")
        builder.add_edge("image_generator", "cache_writer")
        builder.add_edge("cache_writer", END)

    return builder


def compile_graph(*, sync_mode: bool = False):
    """Build and compile the pipeline for either sync or async execution."""
    return build_graph(sync_mode=sync_mode).compile()
