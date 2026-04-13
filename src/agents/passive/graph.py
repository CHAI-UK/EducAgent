"""
passive_course_agent — LangGraph pipeline.

Architecture:
  ┌─ ① mock_profile_loader  ─┐
  │                           │
  ├─ ② mock_progress_loader ──┼──▶ ④a outline_gen ──▶ ④b content_gen ──▶ ④c image_gen ──▶ cache_writer
  │                           │
  └─ ③ mock_concept_loader  ──┘

Phase 1 (④a): LLM slices concept into learning nodes (outline)
Phase 2 (④b): LLM generates content for each node (sequential)
Phase 3 (④c): Image model generates illustrations for typed image markers
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from typing import Any

try:
    import json_repair
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    json_repair = None

from langgraph.graph import END, START, StateGraph
from openai import AsyncOpenAI

from .markers import (
    image_generation_brief,
    iter_image_markers,
    parse_image_marker,
)
from .mock_data import get_mock_input, get_passive_images_dir
from .prompts import (
    CONTENT_SYSTEM_PROMPT,
    CONTENT_USER_TEMPLATE,
    OUTLINE_SYSTEM_PROMPT,
    OUTLINE_USER_TEMPLATE,
)
from .state import PipelineState
from .text_normalization import normalize_llm_payload

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
        _client = AsyncOpenAI(api_key=api_key, base_url=base_url)
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


def _log_response_metadata(stage: str, response: Any) -> None:
    """Log finish reason and token usage for debugging truncation/format issues."""
    choices = getattr(response, "choices", None) or []
    choice = choices[0] if choices else None
    finish_reason = getattr(choice, "finish_reason", None) or "unknown"

    usage = getattr(response, "usage", None)
    prompt_tokens = getattr(usage, "prompt_tokens", None)
    completion_tokens = getattr(usage, "completion_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)

    logger.info(
        "%s finish_reason=%s usage(prompt=%s, completion=%s, total=%s)",
        stage,
        finish_reason,
        prompt_tokens if prompt_tokens is not None else "?",
        completion_tokens if completion_tokens is not None else "?",
        total_tokens if total_tokens is not None else "?",
    )
    if finish_reason == "length":
        logger.warning("%s model stopped because of token limit", stage)


async def _repair_json_response(
    *,
    client: AsyncOpenAI,
    model: str,
    max_tokens: int,
    raw: str,
    node_title: str,
) -> Any:
    """Retry once by asking the model to rewrite malformed JSON as valid JSON."""
    logger.warning(
        "[④b]   Node '%s': retrying once with JSON repair prompt...",
        node_title,
    )
    repair_response = await client.chat.completions.create(
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
                    "Rewrite the following malformed JSON as a valid JSON array. "
                    "Do not add or remove sections. "
                    'Ensure each object has keys "section", "content", and "markers".\n\n'
                    f"{_strip_fences(raw)}"
                ),
            },
        ],
        temperature=0,
        max_tokens=max_tokens,
    )
    _log_response_metadata("[④b]   JSONRepair", repair_response)
    repaired_raw = _extract_text_content(repair_response.choices[0].message.content)
    return _parse_json(repaired_raw)


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
    response = await client.chat.completions.create(
        model=cfg["model"],
        messages=[
            {"role": "system", "content": OUTLINE_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=cfg["temperature"],
        max_tokens=cfg["max_tokens"],
        response_format={"type": "json_object"},
    )
    _log_response_metadata("[④a] OutlineGenerator", response)

    outline = _parse_json(_extract_text_content(response.choices[0].message.content))
    logger.info("[④a] OutlineGenerator: %d learning nodes", len(outline))
    return {"outline": outline}


# ---------------------------------------------------------------------------
# Node functions — Phase 2: Content (per node)
# ---------------------------------------------------------------------------


async def content_generator(state: PipelineState) -> dict[str, Any]:
    """Node ④b — generate content for each learning node sequentially."""
    logger.info("[④b] ContentGenerator: generating content for each node...")

    ctx = state.get("adaptation_ctx", {})
    concept = state.get("concept_ctx", {})
    outline = state.get("outline", [])
    chunks = state.get("grounded_chunks", [])
    progress = state.get("progress_ctx", {})
    confusion = state.get("confusion_fwd", [])
    depth_tier = state.get("depth_tier", "intermediate")

    mastery = progress.get("mastery_scores", {})
    prereqs = concept.get("prerequisite", [])
    gaps = [p for p in prereqs if mastery.get(p, 0.0) < 0.5]

    chunks_text = "\n\n".join(
        f"[{c['source']}] (relevance: {c['score']})\n{c['text']}" for c in chunks
    )

    cfg = _load_config()["content"]
    client = _get_client()
    all_nodes: list[dict[str, Any]] = []
    all_image_prompts: list[dict[str, Any]] = []

    for i, node in enumerate(outline):
        node_title = node.get("title", f"Node {i + 1}")
        previous = [n.get("title", "") for n in outline[:i]]

        logger.info("[④b]   Node %d/%d: %s", i + 1, len(outline), node_title)

        user_msg = CONTENT_USER_TEMPLATE.format(
            node_title=node_title,
            node_summary=node.get("summary", ""),
            rag_focus=node.get("rag_focus", ""),
            node_index=i + 1,
            total_nodes=len(outline),
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

        response = await client.chat.completions.create(
            model=cfg["model"],
            messages=[
                {"role": "system", "content": CONTENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=cfg["temperature"],
            max_tokens=cfg["max_tokens"],
        )
        _log_response_metadata(f"[④b]   Node {i + 1}/{len(outline)}", response)

        raw_content = _extract_text_content(response.choices[0].message.content)
        try:
            sections = _parse_json(raw_content)
        except json.JSONDecodeError as e:
            logger.warning("[④b]   Node %d/%d parse failed: %s", i + 1, len(outline), e)
            logger.warning("[④b]   Raw preview: %s", _strip_fences(raw_content)[:300])
            sections = await _repair_json_response(
                client=client,
                model=cfg["model"],
                max_tokens=cfg["max_tokens"],
                raw=raw_content,
                node_title=node_title,
            )

        # Collect typed image markers from both content text and markers array
        for sec in sections:
            seen: set[tuple[str, str]] = set()
            # First: from inline content (exact text the renderer will match)
            for kind, desc in iter_image_markers(sec.get("content", "")):
                key = (kind, desc)
                if key not in seen:
                    seen.add(key)
                    all_image_prompts.append(
                        {
                            "node_title": node_title,
                            "description": desc,
                            "kind": kind,
                            "section": sec.get("section", ""),
                        }
                    )
            # Second: from markers array (if LLM put it there but not inline)
            for marker in sec.get("markers", []):
                parsed = parse_image_marker(marker)
                if not parsed:
                    continue
                kind, desc = parsed
                key = (kind, desc)
                if key not in seen:
                    seen.add(key)
                    all_image_prompts.append(
                        {
                            "node_title": node_title,
                            "description": desc,
                            "kind": kind,
                            "section": sec.get("section", ""),
                        }
                    )

        all_nodes.append(
            {
                "node_title": node_title,
                "sections": sections,
            }
        )

    logger.info(
        "[④b] ContentGenerator: %d nodes, %d image prompts", len(all_nodes), len(all_image_prompts)
    )
    return {
        "nodes": all_nodes,
        "image_prompts": all_image_prompts,
    }


# ---------------------------------------------------------------------------
# Node functions — Phase 3: Image generation
# ---------------------------------------------------------------------------


async def image_generator(state: PipelineState) -> dict[str, Any]:
    """Node ④c — generate images for typed image markers via Gemini image model."""
    prompts = state.get("image_prompts", [])
    if not prompts:
        logger.info("[④c] ImageGenerator: no image prompts, skipping")
        return {"image_refs": []}

    logger.info("[④c] ImageGenerator: generating %d images...", len(prompts))

    cfg = _load_config()["image"]
    client = _get_client()
    image_refs: list[dict[str, str]] = []

    user_id = state.get("user_id", "unknown_user")
    concept_id = state.get("concept_ctx", {}).get("concept_id") or state.get(
        "concept_id", "unknown_concept"
    )
    img_dir = get_passive_images_dir(user_id, concept_id)
    img_dir.mkdir(parents=True, exist_ok=True)

    for ip in prompts:
        desc = ip["description"]
        kind = ip.get("kind", "PEDAGOGICAL_IMAGE")
        logger.info("[④c]   Generating: %s", desc[:80])

        for model in [cfg["model"], cfg.get("fallback_model")]:
            if not model:
                continue
            try:
                response = await client.chat.completions.create(
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
                                break
                    else:
                        logger.warning("[④c]   %s: images field present but no data URL", model)
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
                    break

                logger.warning("[④c]   %s returned no image data", model)

            except Exception as e:
                logger.warning("[④c]   %s failed: %s", model, str(e)[:200])
                continue

    logger.info("[④c] ImageGenerator: generated %d / %d images", len(image_refs), len(prompts))
    return {"image_refs": image_refs}


# ---------------------------------------------------------------------------
# Cache writer
# ---------------------------------------------------------------------------


def cache_writer(state: PipelineState) -> dict[str, Any]:
    """Terminal node — compute cache key and log output."""
    concept_id = state.get("concept_ctx", {}).get("concept_id", "unknown")
    profile_sig = state.get("profile_sig", "unknown")
    cache_key = f"{concept_id}:{profile_sig}"

    outline = state.get("outline", [])
    nodes = state.get("nodes", [])
    images = state.get("image_refs", [])

    logger.info(
        "[cache] cache_key=%s | %d outline nodes | %d content nodes | %d images",
        cache_key,
        len(outline),
        len(nodes),
        len(images),
    )
    return {"cache_key": cache_key, "cache_hit": False}


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_graph() -> StateGraph:
    """
    Construct the ContentGenerator pipeline.

    Fan-out:  START → [①, ②, ③] (parallel)
    Fan-in:   [①, ②, ③] → ④a → ④b → ④c → cache_writer → END
    """
    builder = StateGraph(PipelineState)

    builder.add_node("mock_profile_loader", mock_profile_loader)
    builder.add_node("mock_progress_loader", mock_progress_loader)
    builder.add_node("mock_concept_loader", mock_concept_loader)
    builder.add_node("outline_generator", outline_generator)
    builder.add_node("content_generator", content_generator)
    builder.add_node("image_generator", image_generator)
    builder.add_node("cache_writer", cache_writer)

    # Parallel fan-out
    builder.add_edge(START, "mock_profile_loader")
    builder.add_edge(START, "mock_progress_loader")
    builder.add_edge(START, "mock_concept_loader")

    # Fan-in → sequential chain
    builder.add_edge("mock_profile_loader", "outline_generator")
    builder.add_edge("mock_progress_loader", "outline_generator")
    builder.add_edge("mock_concept_loader", "outline_generator")

    builder.add_edge("outline_generator", "content_generator")
    builder.add_edge("content_generator", "image_generator")
    builder.add_edge("image_generator", "cache_writer")
    builder.add_edge("cache_writer", END)

    return builder


def compile_graph():
    """Build and compile the pipeline, ready for .ainvoke()."""
    return build_graph().compile()
