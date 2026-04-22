"""Tests for risk-based QA routing (Story 5.3 AC-6, AC-7, AC-8)."""

from __future__ import annotations

import asyncio

import pytest

from src.agents.passive import graph as graph_mod


# ---------------------------------------------------------------------------
# _classify_node_risk — pure function
# ---------------------------------------------------------------------------


def test_classify_low_risk_plain_content() -> None:
    """A node with no formal markers or risky keywords is low risk."""
    node = {
        "node_title": "Gentle intro",
        "sections": [
            {
                "section": "Hook",
                "content": "Let us think about planning a trip. Imagine you had to choose a route...",
                "markers": [],
                "part": "hook",
            }
        ],
    }
    assert graph_mod._classify_node_risk(node) == "low"


def test_classify_high_risk_on_formula_marker() -> None:
    node = {
        "node_title": "Formal treatment",
        "sections": [
            {
                "section": "Definition",
                "content": "The SCM is given by [FORMULA: $Y_x(u)$].",
                "markers": ["[FORMULA: $Y_x(u)$]"],
                "part": "definition",
            }
        ],
    }
    assert graph_mod._classify_node_risk(node) == "high"


def test_classify_high_risk_on_causal_keyword() -> None:
    node = {
        "node_title": "Treatment effect",
        "sections": [
            {
                "section": "Intuition",
                "content": "The causal effect of treatment X on outcome Y is measured by...",
                "markers": [],
                "part": "intuition",
            }
        ],
    }
    assert graph_mod._classify_node_risk(node) == "high"


def test_classify_high_risk_on_part_definition() -> None:
    node = {
        "node_title": "Formal claim",
        "sections": [
            {
                "section": "Formal statement",
                "content": "We state the theorem precisely here.",
                "markers": [],
                "part": "definition",
            }
        ],
    }
    assert graph_mod._classify_node_risk(node) == "high"


def test_classify_high_risk_on_clinical_keyword() -> None:
    node = {
        "node_title": "Radiology use case",
        "sections": [
            {
                "section": "Hook",
                "content": "A clinical scenario: the patient presents with...",
                "markers": [],
                "part": "hook",
            }
        ],
    }
    assert graph_mod._classify_node_risk(node) == "high"


def test_classify_low_risk_uses_word_boundaries() -> None:
    """'treaty' must NOT match the 'treatment' keyword pattern."""
    node = {
        "node_title": "Treaty history",
        "sections": [
            {
                "section": "Hook",
                "content": "A treaty is a formal agreement between nations.",
                "markers": [],
                "part": "hook",
            }
        ],
    }
    assert graph_mod._classify_node_risk(node) == "low"


# ---------------------------------------------------------------------------
# fact_checker integration — selective QA with mocked LLM
# ---------------------------------------------------------------------------


def _enabled_config() -> dict:
    return {
        "api_key_env": "OPENROUTER_API_KEY",
        "base_url_env": "OPENROUTER_BASE_URL",
        "base_url_default": "https://openrouter.ai/api/v1",
        "request_timeout_s": 300,
        "heartbeat_interval_s": 15,
        "max_wait_s": 360,
        "outline": {"model": "x", "temperature": 0, "max_tokens": 1024},
        "content": {"model": "x", "temperature": 0, "max_tokens": 1024},
        "fact_check": {
            "enabled": True,
            "model": "x",
            "temperature": 0,
            "max_tokens": 512,
            "regenerate_on_critical": False,
            "max_regeneration_attempts": 1,
            "targeted_recheck": False,
        },
        "image": {"model": "x", "fallback_model": None},
    }


def test_fact_checker_skips_critique_on_low_risk_node(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Low-risk nodes must NOT trigger _critique_node (no LLM cost)."""
    call_log: list[str] = []

    async def _fake_critique(**kwargs):
        call_log.append(kwargs["node"]["node_title"])
        return []

    monkeypatch.setattr(graph_mod, "_config", _enabled_config())
    monkeypatch.setattr(graph_mod, "_critique_node", _fake_critique)
    monkeypatch.setattr(graph_mod, "_get_client", lambda: None)

    state = {
        "nodes": [
            {
                "node_title": "Low-risk gentle intro",
                "sections": [
                    {
                        "section": "Hook",
                        "content": "Let us imagine a trip planning scenario.",
                        "markers": [],
                        "part": "hook",
                    }
                ],
            }
        ],
        "concept_ctx": {"concept_id": "trip"},
        "adaptation_ctx": {"background": "CS", "role": "student"},
        "progress_ctx": {"mastery_scores": {}},
        "confusion_fwd": [],
        "grounded_chunks": [],
        "outline": [{"title": "Low-risk gentle intro"}],
        "depth_tier": "beginner",
    }
    result = asyncio.run(graph_mod.fact_checker(state))

    assert call_log == []
    qa_log = result.get("qa_log", [])
    assert len(qa_log) == 1
    assert qa_log[0]["qa_path"] == "rule-only"
    assert qa_log[0]["node_title"] == "Low-risk gentle intro"


def test_fact_checker_runs_critique_on_high_risk_node(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """High-risk nodes MUST trigger _critique_node."""
    call_log: list[str] = []

    async def _fake_critique(**kwargs):
        call_log.append(kwargs["node"]["node_title"])
        return []

    monkeypatch.setattr(graph_mod, "_config", _enabled_config())
    monkeypatch.setattr(graph_mod, "_critique_node", _fake_critique)
    monkeypatch.setattr(graph_mod, "_get_client", lambda: None)

    state = {
        "nodes": [
            {
                "node_title": "Formal definition node",
                "sections": [
                    {
                        "section": "Formal",
                        "content": "The causal effect of a treatment X on Y is defined.",
                        "markers": [],
                        "part": "definition",
                    }
                ],
            }
        ],
        "concept_ctx": {"concept_id": "ate"},
        "adaptation_ctx": {},
        "progress_ctx": {"mastery_scores": {}},
        "confusion_fwd": [],
        "grounded_chunks": [],
        "outline": [{"title": "Formal definition node"}],
        "depth_tier": "intermediate",
    }
    result = asyncio.run(graph_mod.fact_checker(state))

    assert call_log == ["Formal definition node"]
    qa_log = result.get("qa_log", [])
    assert len(qa_log) == 1
    assert qa_log[0]["qa_path"] == "critic-ran"


def test_fact_checker_disabled_skips_all(monkeypatch: pytest.MonkeyPatch) -> None:
    """When fact_check.enabled is False the node is a no-op (same as before)."""
    monkeypatch.setattr(graph_mod, "_config", {"fact_check": {"enabled": False}})
    result = asyncio.run(graph_mod.fact_checker({"nodes": [{"node_title": "X"}]}))
    assert result.get("fact_check_issues", []) == []
