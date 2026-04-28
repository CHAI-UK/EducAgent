from __future__ import annotations

import re
from typing import Iterator

from src.agents.prompts import load_prompt

_IMAGE_MARKER_RE = re.compile(r"\[(CONTEXT_IMAGE|PEDAGOGICAL_IMAGE|IMAGE):\s*([^\]]+)\]")
_LAYOUT_DIRECTIVE_RE = re.compile(
    r"^\s*Layout:\s*(?P<aspect>\d+:\d+)(?:\s+[^.]*)?\.\s*(?P<body>.+?)\s*$",
    flags=re.IGNORECASE,
)

_VALID_TIERS = frozenset({"beginner", "intermediate", "advanced"})
_IMAGE_PROMPT_CFG = load_prompt("passive_image_generation")


def _normalize_marker_kind(kind: str) -> str:
    if kind == "IMAGE":
        return "PEDAGOGICAL_IMAGE"
    return kind


def _normalize_tier(depth_tier: str | None) -> str:
    if depth_tier and depth_tier.lower() in _VALID_TIERS:
        return depth_tier.lower()
    return "intermediate"


def _default_aspect_ratio(kind: str) -> str:
    normalized_kind = _normalize_marker_kind(kind)
    defaults = _IMAGE_PROMPT_CFG.get("default_aspect_ratios", {})
    return _normalize_aspect_ratio(str(defaults.get(normalized_kind, "4:3")))


def _normalize_aspect_ratio(aspect_ratio: str) -> str:
    """Canonicalize aspect ratios and prefer landscape when non-square.

    The image APIs expect ratios in ``width:height`` form. Some content prompts
    historically emitted portrait directives such as ``4:5``; normalize those to
    ``5:4`` so generated assets stay wider than tall unless explicitly square.
    """
    match = re.fullmatch(r"\s*(\d+)\s*:\s*(\d+)\s*", aspect_ratio or "")
    if not match:
        return re.sub(r"\s+", "", aspect_ratio or "").strip()

    width = int(match.group(1))
    height = int(match.group(2))
    if width <= 0 or height <= 0:
        return f"{width}:{height}"
    if width < height:
        width, height = height, width
    return f"{width}:{height}"


def _style_block(depth_tier: str, kind: str) -> str:
    presets = _IMAGE_PROMPT_CFG.get("style_presets", {})
    return str(presets[depth_tier][kind])


def _prefix_block(kind: str) -> str:
    prefixes = _IMAGE_PROMPT_CFG.get("prefixes", {})
    return str(prefixes[_normalize_marker_kind(kind)])


def _layout_block(aspect_ratio: str) -> str:
    guidance = _IMAGE_PROMPT_CFG.get("layout_guidance", {})
    match = re.fullmatch(r"(\d+):(\d+)", aspect_ratio)
    if match:
        width = int(match.group(1))
        height = int(match.group(2))
        if height > 0 and (width / height) >= 1.6:
            return str(guidance["wide"])
        if width < height:
            return str(guidance["portrait"])
        return str(guidance["compact"])
    if aspect_ratio == "16:9":
        return str(guidance["wide"])
    if aspect_ratio in {"3:4", "4:5"}:
        return str(guidance["portrait"])
    return str(guidance["compact"])


def image_layout_metadata(
    kind: str,
    description: str,
) -> dict[str, str]:
    """Extract layout metadata and a cleaned description from marker text."""
    normalized_kind = _normalize_marker_kind(kind)
    normalized_description = re.sub(r"\s+", " ", description or "").strip()
    match = _LAYOUT_DIRECTIVE_RE.match(normalized_description)
    if match:
        clean_description = match.group("body").strip()
        aspect_ratio = _normalize_aspect_ratio(match.group("aspect"))
    else:
        clean_description = normalized_description
        aspect_ratio = _default_aspect_ratio(normalized_kind)
    return {
        "aspect_ratio": aspect_ratio,
        "clean_description": clean_description,
    }


def strip_image_layout(description: str, *, kind: str = "PEDAGOGICAL_IMAGE") -> str:
    """Remove the leading layout directive from a marker description."""
    return image_layout_metadata(kind, description)["clean_description"]


def parse_image_marker(
    marker: str, *, strip_layout_directive: bool = True
) -> tuple[str, str] | None:
    """Parse a typed image marker into ``(kind, description)``.

    Rendering wants clean captions, while image generation needs the original
    layout directive so aspect-ratio metadata is not lost.
    """
    match = _IMAGE_MARKER_RE.fullmatch(marker.strip())
    if not match:
        return None
    kind = _normalize_marker_kind(match.group(1))
    description = re.sub(r"\s+", " ", match.group(2)).strip()
    if strip_layout_directive:
        description = strip_image_layout(description, kind=kind)
    return kind, description


def iter_image_markers(
    text: str, *, strip_layout_directive: bool = True
) -> Iterator[tuple[str, str]]:
    """Yield typed image markers found inline in a text block."""
    for match in _IMAGE_MARKER_RE.finditer(text or ""):
        kind = _normalize_marker_kind(match.group(1))
        description = re.sub(r"\s+", " ", match.group(2)).strip()
        if strip_layout_directive:
            description = strip_image_layout(description, kind=kind)
        yield kind, description


def format_image_marker(kind: str, description: str) -> str:
    """Format a typed image marker string."""
    normalized_kind = _normalize_marker_kind(kind)
    return f"[{normalized_kind}: {description}]"


def image_generation_brief(
    kind: str,
    description: str,
    *,
    depth_tier: str | None = None,
) -> str:
    """Return a generation prompt tuned to the marker kind and depth tier.

    ``depth_tier`` drives a cross-run style preset so that all images for a
    given tier share a coherent visual language:

    - ``beginner``: warm, friendly flat illustration; rounded shapes; wider
      strokes; generous colour. Aim for approachability.
    - ``intermediate``: editorial information-graphic register (HBR / The
      Economist); neutral palette plus one accent; medium strokes.
    - ``advanced``: publication-grade figure (IEEE / Nature); near-monochrome;
      strict geometry; italic for variables. Aim for rigour.

    Unknown or missing tiers fall back to ``intermediate``.
    """
    normalized_kind = _normalize_marker_kind(kind)
    normalized_tier = _normalize_tier(depth_tier)
    layout = image_layout_metadata(normalized_kind, description)
    aspect_ratio = layout["aspect_ratio"]
    clean_description = layout["clean_description"]
    prefix = _prefix_block(normalized_kind)
    style_block = _style_block(normalized_tier, normalized_kind)
    layout_block = _layout_block(aspect_ratio)
    shared_boilerplate = str(_IMAGE_PROMPT_CFG.get("shared_boilerplate", ""))

    return (
        f"{prefix}\n\n"
        f"Domain: visual explanation for a causal inference learning node.\n"
        f"Requested aspect ratio: {aspect_ratio}.\n"
        f"{layout_block}\n"
        f"Illustration brief: {clean_description}\n\n"
        f"{style_block}\n\n"
        f"{shared_boilerplate}"
    )
