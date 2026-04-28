"""Tests for tier-aware image_generation_brief style injection."""

from __future__ import annotations

import pytest

from src.agents.passive.markers import image_generation_brief, image_layout_metadata


def test_brief_defaults_to_intermediate_style() -> None:
    out = image_generation_brief("PEDAGOGICAL_IMAGE", "A DAG with X -> Y")
    # Intermediate pedagogical style uses the HBR / Economist register wording.
    assert "editorial information graphic" in out


def test_brief_beginner_style_is_friendly() -> None:
    out = image_generation_brief("PEDAGOGICAL_IMAGE", "A DAG with X -> Y", depth_tier="beginner")
    assert "friendly educational diagram" in out
    assert "Warm" in out or "warm" in out


def test_brief_advanced_style_is_publication_quality() -> None:
    out = image_generation_brief("PEDAGOGICAL_IMAGE", "A DAG with X -> Y", depth_tier="advanced")
    assert "publication-quality" in out
    assert "monochrome" in out.lower()


def test_brief_kind_changes_wording() -> None:
    pedagogical = image_generation_brief(
        "PEDAGOGICAL_IMAGE", "A DAG with X -> Y", depth_tier="beginner"
    )
    context = image_generation_brief(
        "CONTEXT_IMAGE", "A researcher at a workstation", depth_tier="beginner"
    )
    assert "pedagogical illustration" in pedagogical
    assert "scene-setting illustration" in context


def test_brief_shared_boilerplate_present_everywhere() -> None:
    """All tier/kind combinations must embed the shared 'never' rules."""
    for tier in ("beginner", "intermediate", "advanced"):
        for kind in ("CONTEXT_IMAGE", "PEDAGOGICAL_IMAGE"):
            brief = image_generation_brief("PEDAGOGICAL_IMAGE", "x", depth_tier=tier)
            assert "Do NOT produce" in brief
            assert "watermarks" in brief


def test_brief_unknown_tier_falls_back_to_intermediate() -> None:
    out = image_generation_brief("PEDAGOGICAL_IMAGE", "x", depth_tier="expert-plus-plus")
    assert "editorial information graphic" in out


def test_brief_legacy_IMAGE_kind_routes_to_pedagogical() -> None:
    out = image_generation_brief("IMAGE", "x", depth_tier="advanced")
    assert "pedagogical illustration" in out
    assert "publication-quality" in out


def test_context_images_default_to_landscape_ratio() -> None:
    layout = image_layout_metadata("CONTEXT_IMAGE", "A researcher at a workstation")
    assert layout["aspect_ratio"] == "4:3"


def test_portrait_layout_directives_are_normalized_to_landscape() -> None:
    layout = image_layout_metadata(
        "CONTEXT_IMAGE",
        "Layout: 4:5 tall scene. A clinician reviews two monitors.",
    )
    assert layout["aspect_ratio"] == "5:4"
    assert layout["clean_description"] == "A clinician reviews two monitors."


def test_brief_requests_landscape_ratio_after_normalization() -> None:
    out = image_generation_brief(
        "PEDAGOGICAL_IMAGE",
        "Layout: 9:16 tall derivation. Two stacked panels with equations.",
        depth_tier="advanced",
    )
    assert "Requested aspect ratio: 16:9." in out
    assert "wide horizontal canvas" in out
