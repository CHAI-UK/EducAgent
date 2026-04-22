from __future__ import annotations

import re
from typing import Any

_ESCAPED_MARKDOWN_TOKENS = ("\\n", "\\r", "\\t", '\\"', "\\\\")
_MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)\n```", re.IGNORECASE | re.DOTALL)
_MCQ_OPTION_RE = re.compile(r"(?m)^(\s*)([A-D])[\)\.]\s+(.*)$")
_DISPLAY_MATH_LINE_RE = re.compile(r"(?m)^[ \t]*(\$\$.*?\$\$)[ \t]*$")

_MERMAID_INLINE_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\$"), ""),
    (re.compile(r"\\mathcal\{([^{}]+)\}"), r"\1"),
    (re.compile(r"\\mathrm\{([^{}]+)\}"), r"\1"),
    (re.compile(r"\\operatorname\{([^{}]+)\}"), r"\1"),
    (re.compile(r"\\text\{([^{}]+)\}"), r"\1"),
    (re.compile(r"\\left"), ""),
    (re.compile(r"\\right"), ""),
    (re.compile(r"\\to"), "→"),
    (re.compile(r"\\rightarrow"), "→"),
    (re.compile(r"\\mid"), " | "),
    (re.compile(r"\\cdot"), "·"),
    (re.compile(r"\\otimes"), "⊗"),
    (re.compile(r"\\delta"), "delta"),
    (re.compile(r"\\\{"), "{"),
    (re.compile(r"\\\}"), "}"),
)

_MERMAID_BRACED_SUBSCRIPT_RE = re.compile(r"([A-Za-z0-9_]+)_\{([^{}]+)\}")
_MERMAID_BRACED_SUPERSCRIPT_RE = re.compile(r"([A-Za-z0-9_]+)\^\{([^{}]+)\}")
_MERMAID_COMMAND_RE = re.compile(r"\\([A-Za-z]+)")


def _simplify_mermaid_index(match: re.Match[str], operator: str) -> str:
    """Render Mermaid subscripts/superscripts as readable plain text."""
    base = match.group(1)
    index = " ".join(match.group(2).split())
    if re.fullmatch(r"[A-Za-z0-9_]+", index):
        return f"{base}{operator}{index}"
    return f"{base}{operator}({index})"


def decode_overescaped_text(value: str) -> str:
    """Decode strings that were JSON-escaped one extra time by the model.

    The passive content generator expects markdown text, but some model
    responses encode section bodies as a JSON string inside the JSON payload.
    That leaves literals like ``\\n``, ``\\"`` and doubled LaTeX backslashes in
    the parsed result. We only decode when the string looks suspicious and the
    decoded output clearly reduces those escape markers.
    """
    if not value or not any(token in value for token in _ESCAPED_MARKDOWN_TOKENS):
        return value

    actual_newlines = value.count("\n")
    literal_newlines = value.count("\\n")
    if actual_newlines and literal_newlines <= actual_newlines:
        return value

    decoded_chars: list[str] = []
    changed = False
    i = 0
    while i < len(value):
        ch = value[i]
        if ch != "\\" or i + 1 >= len(value):
            decoded_chars.append(ch)
            i += 1
            continue

        next_ch = value[i + 1]
        if next_ch == "n":
            decoded_chars.append("\n")
            changed = True
            i += 2
            continue
        if next_ch == "r":
            decoded_chars.append("\r")
            changed = True
            i += 2
            continue
        if next_ch == "t":
            decoded_chars.append("\t")
            changed = True
            i += 2
            continue
        if next_ch == "b":
            decoded_chars.append("\b")
            changed = True
            i += 2
            continue
        if next_ch == "f":
            decoded_chars.append("\f")
            changed = True
            i += 2
            continue
        if next_ch in {'"', "\\", "/"}:
            decoded_chars.append(next_ch)
            changed = True
            i += 2
            continue

        decoded_chars.append(ch)
        i += 1

    if not changed:
        return value

    decoded = "".join(decoded_chars)
    escape_reduced = any(
        decoded.count(token) < value.count(token) for token in _ESCAPED_MARKDOWN_TOKENS
    )
    formatting_recovered = (
        decoded.count("\n") > value.count("\n")
        or decoded.count("\t") > value.count("\t")
        or decoded.count('"') > value.count('"')
    )

    return decoded if escape_reduced or formatting_recovered else value


def _normalize_mermaid_code(code: str) -> str:
    """Replace label-internal newlines with Mermaid-safe <br/> markers."""
    # Pre-pass: convert literal \n (backslash + n) to real newlines so the
    # character loop can handle them uniformly.  The LLM sometimes writes \\n
    # in JSON (literal backslash-n) to represent line breaks inside Mermaid
    # labels.  After JSON parsing that becomes the two-character sequence \ + n
    # which the character loop below would not recognise as a newline.
    code = code.replace("\\n", "\n")

    parts: list[str] = []
    in_square = 0
    in_curly = 0
    in_pipe = False

    for ch in code:
        if ch == "\n":
            if in_square > 0 or in_curly > 0 or in_pipe:
                parts.append("<br/>")
            else:
                parts.append("\n")
            continue

        if ch == "[":
            in_square += 1
        elif ch == "]" and in_square > 0:
            in_square -= 1
        elif ch == "{":
            in_curly += 1
        elif ch == "}" and in_curly > 0:
            in_curly -= 1
        elif ch == "|" and in_square == 0 and in_curly == 0:
            in_pipe = not in_pipe

        parts.append(ch)

    normalized = "".join(parts)
    for pattern, replacement in _MERMAID_INLINE_REPLACEMENTS:
        normalized = pattern.sub(replacement, normalized)
    normalized = _MERMAID_BRACED_SUBSCRIPT_RE.sub(
        lambda m: _simplify_mermaid_index(m, "_"), normalized
    )
    normalized = _MERMAID_BRACED_SUPERSCRIPT_RE.sub(
        lambda m: _simplify_mermaid_index(m, "^"), normalized
    )
    normalized = _MERMAID_COMMAND_RE.sub(r"\1", normalized)
    return normalized


def _normalize_mermaid_blocks(value: str) -> str:
    """Normalize Mermaid blocks so common LLM formatting remains renderable."""

    def repl(match: re.Match[str]) -> str:
        code = match.group(1).strip("\n")
        return f"```mermaid\n{_normalize_mermaid_code(code)}\n```"

    return _MERMAID_BLOCK_RE.sub(repl, value)


def _normalize_display_math_blocks(value: str) -> str:
    """Ensure single-line display math blocks are separated by blank lines."""

    def repl(match: re.Match[str]) -> str:
        return f"\n{match.group(1)}\n"

    normalized = _DISPLAY_MATH_LINE_RE.sub(repl, value)
    return re.sub(r"\n{3,}", "\n\n", normalized)


def _standardize_mcq_option_markers(value: str) -> str:
    """Normalize multiple-choice option prefixes to A./B./C./D. style."""
    return _MCQ_OPTION_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}. {m.group(3)}", value)


def normalize_section_markdown(section: str, content: str) -> str:
    """Normalize section markdown for renderer-safe output."""
    normalized = _normalize_display_math_blocks(content)
    normalized = _normalize_mermaid_blocks(normalized)
    if "check your understanding" in section.strip().lower():
        normalized = _standardize_mcq_option_markers(normalized)
    return normalized


def normalize_llm_payload(value: Any) -> Any:
    """Recursively normalize over-escaped strings inside parsed LLM payloads."""
    if isinstance(value, str):
        return decode_overescaped_text(value)
    if isinstance(value, list):
        return [normalize_llm_payload(item) for item in value]
    if isinstance(value, dict):
        normalized = {key: normalize_llm_payload(item) for key, item in value.items()}
        section = normalized.get("section")
        content = normalized.get("content")
        if isinstance(section, str) and isinstance(content, str):
            normalized["content"] = normalize_section_markdown(section, content)
        return normalized
    return value
