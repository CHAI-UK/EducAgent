from __future__ import annotations

import re
from typing import Iterator

_IMAGE_MARKER_RE = re.compile(r"\[(CONTEXT_IMAGE|PEDAGOGICAL_IMAGE|IMAGE):\s*([^\]]+)\]")

_VALID_TIERS = frozenset({"beginner", "intermediate", "advanced"})


# Style presets keyed by (depth_tier, kind). Every entry shares the same
# "never" rules via _STYLE_SHARED_BOILERPLATE so cross-tier consistency is
# guaranteed regardless of what the per-tier block says.
_STYLE_SHARED_BOILERPLATE = (
    "Do NOT produce: 3D renderings, photorealism, lens/camera effects, drop "
    "shadows, gradients, gloss, textured backgrounds, watermarks, visible "
    "brand logos, AI-generated visual tropes (chromatic aberration, "
    "over-saturated neon, melting edges). Always use a plain light-neutral "
    "background. All text in the image must be in English and legible."
)

_STYLE_PRESETS: dict[tuple[str, str], str] = {
    # ── BEGINNER ────────────────────────────────────────────────────────
    ("beginner", "PEDAGOGICAL_IMAGE"): (
        "Style: friendly educational diagram for an introductory textbook. "
        "Flat-vector illustration. Warm, welcoming palette (soft blues, "
        "greens, oranges on a white or cream background). Rounded node "
        "shapes (circles or rounded rectangles) with medium-thick strokes "
        "(2-3px). Sans-serif labels, medium weight, generously spaced. "
        "Directed arrows as clean solid lines with simple triangular "
        "arrowheads. Prioritise clarity and visual warmth; generous "
        "whitespace; no visual clutter."
    ),
    ("beginner", "CONTEXT_IMAGE"): (
        "Style: friendly flat-vector illustration suitable for an "
        "introductory educational book — think O'Reilly head-first or a "
        "modern explainer-style picture book. Warm palette (soft blues, "
        "oranges, greens). Stylised characters with approachable, "
        "engaged expressions. Clean composition focused on the scenario. "
        "Avoid photorealism and avoid cartoon slapstick. Plain or gently "
        "tinted background."
    ),
    # ── INTERMEDIATE ────────────────────────────────────────────────────
    ("intermediate", "PEDAGOGICAL_IMAGE"): (
        "Style: professional editorial information graphic in the visual "
        "register of Harvard Business Review or The Economist. Restrained "
        "palette: neutral greys and a single accent colour. White "
        "background. Medium-weight sans-serif labels. Medium strokes "
        "(1.5-2px). Strict grid alignment. Panels (if any) separated by "
        "thin rules or whitespace. Directed arrows as straight solid "
        "lines with triangular heads. No decorative elements."
    ),
    ("intermediate", "CONTEXT_IMAGE"): (
        "Style: clean editorial illustration. Sophisticated but not "
        "austere. Restrained palette (neutral greys plus one accent "
        "colour). Characters depicted professionally in plausible "
        "domain-appropriate working environments. Flat-illustration "
        "style — avoid both photorealism and overly playful cartoon "
        "aesthetics. Plain or neutral background."
    ),
    # ── ADVANCED ────────────────────────────────────────────────────────
    ("advanced", "PEDAGOGICAL_IMAGE"): (
        "Style: publication-quality technical figure suitable for a "
        "peer-reviewed journal (IEEE, Nature, Journal of the Royal "
        "Statistical Society). Near-monochrome: black/greyscale with at "
        "most one or two accent colours reserved for essential "
        "distinctions. Thin strokes (1-1.5px). Strict geometric "
        "alignment. Sans-serif labels for identifiers; italic for "
        "variables and mathematical symbols. Panel boundaries explicit "
        "via thin rules. Directed arrows as solid lines with small "
        "triangular arrowheads. No decorative elements."
    ),
    ("advanced", "CONTEXT_IMAGE"): (
        "Style: restrained, near-monochrome editorial illustration. "
        "Minimal decorative elements. Characters depicted in authentic, "
        "domain-accurate working environments with realistic detail. "
        "Flat-illustration style with a technical, professional tone. "
        "Plain white or light-grey background."
    ),
}


def _normalize_marker_kind(kind: str) -> str:
    if kind == "IMAGE":
        return "PEDAGOGICAL_IMAGE"
    return kind


def _normalize_tier(depth_tier: str | None) -> str:
    if depth_tier and depth_tier.lower() in _VALID_TIERS:
        return depth_tier.lower()
    return "intermediate"


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

    if normalized_kind == "CONTEXT_IMAGE":
        prefix = (
            "Generate a scene-setting illustration that supports the narrative "
            "hook. Prioritize atmosphere, characters, setting, and emotional "
            "engagement."
        )
    else:
        prefix = (
            "Generate a pedagogical illustration that breaks down the concept. "
            "Prioritize structural relationships, labeled components, arrows, "
            "panels, and clear visual metaphors."
        )

    style_block = _STYLE_PRESETS[(normalized_tier, normalized_kind)]

    return (
        f"{prefix}\n\n"
        f"Domain: visual explanation for a causal inference learning node.\n"
        f"Illustration brief: {description}\n\n"
        f"{style_block}\n\n"
        f"{_STYLE_SHARED_BOILERPLATE}"
    )
