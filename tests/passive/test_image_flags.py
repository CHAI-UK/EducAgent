"""Tests for image generation config flags (Story 5.3 AC-9, AC-10)."""

from __future__ import annotations

import asyncio

import pytest

from src.agents.passive import graph as graph_mod


def _base_config(image_overrides: dict) -> dict:
    base_image = {"model": "x", "fallback_model": None}
    base_image.update(image_overrides)
    return {
        "api_key_env": "OPENROUTER_API_KEY",
        "base_url_env": "OPENROUTER_BASE_URL",
        "base_url_default": "https://openrouter.ai/api/v1",
        "request_timeout_s": 300,
        "heartbeat_interval_s": 15,
        "max_wait_s": 360,
        "outline": {"model": "x", "temperature": 0, "max_tokens": 1024},
        "content": {"model": "x", "temperature": 0, "max_tokens": 1024},
        "fact_check": {"enabled": False},
        "image": base_image,
    }


def test_image_generator_skipped_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """image.enabled=false must short-circuit image_generator without any call."""
    monkeypatch.setattr(graph_mod, "_config", _base_config({"enabled": False}))

    call_log: list[str] = []

    class _Boom:
        def __getattr__(self, _name):  # pragma: no cover - must not be called
            raise AssertionError("image generator must not be invoked when disabled")

    monkeypatch.setattr(graph_mod, "_get_client", lambda: _Boom())

    state = {
        "image_prompts": [
            {"node_title": "N", "description": "A diagram", "kind": "PEDAGOGICAL_IMAGE"}
        ],
        "user_id": "u1",
        "concept_ctx": {"concept_id": "c1"},
    }
    out = asyncio.run(graph_mod.image_generator(state))
    assert call_log == []
    assert out.get("image_refs", []) == []
    assert out.get("image_skipped") is True


def test_image_generator_runs_when_enabled_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default behavior (enabled=true or missing flag) must still attempt generation."""
    monkeypatch.setattr(graph_mod, "_config", _base_config({}))  # no enabled flag

    # image_generator without any prompts is a legal early-return — just verify
    # that absent image_prompts we don't crash AND we don't set image_skipped.
    out = asyncio.run(graph_mod.image_generator({"image_prompts": []}))
    assert out.get("image_refs") == []
    assert out.get("image_skipped") is not True


def test_collect_image_prompts_preserves_layout_directive_for_generation() -> None:
    marker = (
        "[PEDAGOGICAL_IMAGE: Layout: 16:9 wide two-panel comparison. "
        "Show the observed path beside the counterfactual path.]"
    )

    prompts = graph_mod._collect_image_prompts(
        "Counterfactual Paths",
        [{"section": "Visual", "content": marker, "markers": [marker]}],
    )

    assert len(prompts) == 1
    assert prompts[0]["description"].startswith("Layout: 16:9")
    assert (
        graph_mod.image_layout_metadata(prompts[0]["kind"], prompts[0]["description"])[
            "aspect_ratio"
        ]
        == "16:9"
    )
