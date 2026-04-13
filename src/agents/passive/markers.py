from __future__ import annotations

import re
from typing import Iterator

_IMAGE_MARKER_RE = re.compile(r"\[(CONTEXT_IMAGE|PEDAGOGICAL_IMAGE|IMAGE):\s*([^\]]+)\]")


def _normalize_marker_kind(kind: str) -> str:
    if kind == "IMAGE":
        return "PEDAGOGICAL_IMAGE"
    return kind


def parse_image_marker(marker: str) -> tuple[str, str] | None:
    """Parse a typed image marker into ``(kind, description)``."""
    match = _IMAGE_MARKER_RE.fullmatch(marker.strip())
    if not match:
        return None
    kind = _normalize_marker_kind(match.group(1))
    description = re.sub(r"\s+", " ", match.group(2)).strip()
    return kind, description


def iter_image_markers(text: str) -> Iterator[tuple[str, str]]:
    """Yield typed image markers found inline in a text block."""
    for match in _IMAGE_MARKER_RE.finditer(text or ""):
        kind = _normalize_marker_kind(match.group(1))
        description = re.sub(r"\s+", " ", match.group(2)).strip()
        yield kind, description


def format_image_marker(kind: str, description: str) -> str:
    """Format a typed image marker string."""
    normalized_kind = _normalize_marker_kind(kind)
    return f"[{normalized_kind}: {description}]"


def image_generation_brief(kind: str, description: str) -> str:
    """Return a generation prompt tuned to the marker kind."""
    normalized_kind = _normalize_marker_kind(kind)
    if normalized_kind == "CONTEXT_IMAGE":
        prefix = (
            "Generate a scene-setting illustration that supports the narrative hook. "
            "Prioritize atmosphere, characters, setting, and emotional engagement."
        )
    else:
        prefix = (
            "Generate a pedagogical illustration that breaks down the concept. "
            "Prioritize structural relationships, labeled components, arrows, panels, "
            "and clear visual metaphors."
        )

    return (
        f"{prefix}\n\n"
        f"Domain: visual explanation for a causal inference learning node.\n"
        f"Illustration brief: {description}\n\n"
        "Style: Clean, minimal, suitable for a university-level textbook. "
        "Use simple colors and clear labels."
    )
