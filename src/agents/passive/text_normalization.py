from __future__ import annotations

from typing import Any

_ESCAPED_MARKDOWN_TOKENS = ("\\n", "\\r", "\\t", '\\"', "\\\\")


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


def normalize_llm_payload(value: Any) -> Any:
    """Recursively normalize over-escaped strings inside parsed LLM payloads."""
    if isinstance(value, str):
        return decode_overescaped_text(value)
    if isinstance(value, list):
        return [normalize_llm_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_llm_payload(item) for key, item in value.items()}
    return value
