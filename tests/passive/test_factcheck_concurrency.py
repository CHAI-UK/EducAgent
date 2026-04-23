"""Tests for parallel fact_checker execution (fact_check.concurrency)."""

from __future__ import annotations

import asyncio

import pytest

from src.agents.passive import graph as graph_mod


def _enabled_config(*, concurrency: int) -> dict:
    return {
        "api_key_env": "OPENROUTER_API_KEY",
        "base_url_env": "OPENROUTER_BASE_URL",
        "base_url_default": "https://openrouter.ai/api/v1",
        "request_timeout_s": 300,
        "heartbeat_interval_s": 15,
        "max_wait_s": 360,
        "outline": {"model": "x", "temperature": 0, "max_tokens": 256},
        "content": {
            "model": "x",
            "temperature": 0,
            "max_tokens": 256,
            "concurrency": 1,
            "retry_delays_s": [0],
        },
        "fact_check": {
            "enabled": True,
            "model": "x",
            "temperature": 0,
            "max_tokens": 256,
            "regenerate_on_critical": False,
            "max_regeneration_attempts": 1,
            "targeted_recheck": False,
            "concurrency": concurrency,
        },
        "image": {"enabled": False, "model": "x", "fallback_model": None},
    }


def _high_risk_state(n: int) -> dict:
    # `part == "definition"` makes _classify_node_risk return "high" so each
    # node triggers the critic — exactly the expensive path we want to parallelise.
    return {
        "nodes": [
            {
                "node_title": f"Formal node {i}",
                "sections": [
                    {
                        "section": "Formal",
                        "content": f"Definition #{i}.",
                        "markers": [],
                        "part": "definition",
                    }
                ],
            }
            for i in range(n)
        ],
        "concept_ctx": {"concept_id": "ate"},
        "adaptation_ctx": {},
        "progress_ctx": {"mastery_scores": {}},
        "confusion_fwd": [],
        "grounded_chunks": [],
        "outline": [{"title": f"Formal node {i}"} for i in range(n)],
        "depth_tier": "intermediate",
    }


class _Concurrency:
    """Tracks concurrent in-flight critic calls and their completion order."""

    def __init__(self, delay_s: float = 0.05) -> None:
        self.delay_s = delay_s
        self.current = 0
        self.max_active = 0
        self.calls: list[str] = []
        self.completions: list[str] = []

    async def critique(self, **kwargs):
        title = kwargs["node"]["node_title"]
        self.calls.append(title)
        self.current += 1
        self.max_active = max(self.max_active, self.current)
        try:
            await asyncio.sleep(self.delay_s)
            return []  # no issues → no rewrite → no recheck
        finally:
            self.current -= 1
            self.completions.append(title)


def test_factcheck_concurrency_respected(monkeypatch: pytest.MonkeyPatch) -> None:
    """With concurrency=3 and 5 high-risk nodes, max_active should stay at 3."""
    tracker = _Concurrency(delay_s=0.05)
    monkeypatch.setattr(graph_mod, "_config", _enabled_config(concurrency=3))
    monkeypatch.setattr(graph_mod, "_critique_node", tracker.critique)
    monkeypatch.setattr(graph_mod, "_get_client", lambda: None)

    result = asyncio.run(graph_mod.fact_checker(_high_risk_state(5)))

    assert tracker.max_active == 3
    assert len(tracker.calls) == 5
    qa_log = result["qa_log"]
    assert [e["node_title"] for e in qa_log] == [f"Formal node {i}" for i in range(5)]


def test_factcheck_concurrency_one_preserves_serial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """concurrency=1 keeps the previous one-at-a-time behavior."""
    tracker = _Concurrency(delay_s=0.02)
    monkeypatch.setattr(graph_mod, "_config", _enabled_config(concurrency=1))
    monkeypatch.setattr(graph_mod, "_critique_node", tracker.critique)
    monkeypatch.setattr(graph_mod, "_get_client", lambda: None)

    asyncio.run(graph_mod.fact_checker(_high_risk_state(4)))
    assert tracker.max_active == 1


def test_factcheck_output_order_matches_outline_even_when_first_is_slow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Node 0 finishes last but its qa_log entry + issues still come first."""
    delays_by_title = {
        "Formal node 0": 0.10,
        "Formal node 1": 0.02,
        "Formal node 2": 0.04,
    }

    async def _slow_by_title(**kwargs):
        title = kwargs["node"]["node_title"]
        await asyncio.sleep(delays_by_title.get(title, 0))
        # Return an issue so qa_log[i]["issues"] is populated (and ordered).
        return [
            {
                "section": "Formal",
                "claim": title,
                "problem": f"issue from {title}",
                "severity": "minor",
                "suggestion": "n/a",
            }
        ]

    monkeypatch.setattr(graph_mod, "_config", _enabled_config(concurrency=3))
    monkeypatch.setattr(graph_mod, "_critique_node", _slow_by_title)
    monkeypatch.setattr(graph_mod, "_get_client", lambda: None)

    result = asyncio.run(graph_mod.fact_checker(_high_risk_state(3)))

    titles_in_qa = [e["node_title"] for e in result["qa_log"]]
    assert titles_in_qa == ["Formal node 0", "Formal node 1", "Formal node 2"]
    # fact_check_issues are collected by extending qa-order — claim verbatim.
    issue_order = [i["node_title"] for i in result["fact_check_issues"]]
    assert issue_order == ["Formal node 0", "Formal node 1", "Formal node 2"]


def test_factcheck_low_risk_nodes_bypass_semaphore(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Low-risk nodes must not occupy a semaphore slot (they make no LLM call)."""
    tracker = _Concurrency(delay_s=0.10)

    async def _fake_critique(**kwargs):
        return await tracker.critique(**kwargs)

    monkeypatch.setattr(graph_mod, "_config", _enabled_config(concurrency=2))
    monkeypatch.setattr(graph_mod, "_critique_node", _fake_critique)
    monkeypatch.setattr(graph_mod, "_get_client", lambda: None)

    state = {
        "nodes": [
            {
                "node_title": "Gentle hook",
                "sections": [
                    {
                        "section": "Hook",
                        "content": "Let us imagine a trip.",
                        "markers": [],
                        "part": "hook",
                    }
                ],
            },
            {
                "node_title": "Formal A",
                "sections": [
                    {
                        "section": "Formal",
                        "content": "Definition A.",
                        "markers": [],
                        "part": "definition",
                    }
                ],
            },
            {
                "node_title": "Formal B",
                "sections": [
                    {
                        "section": "Formal",
                        "content": "Definition B.",
                        "markers": [],
                        "part": "definition",
                    }
                ],
            },
        ],
        "concept_ctx": {"concept_id": "ate"},
        "adaptation_ctx": {},
        "progress_ctx": {"mastery_scores": {}},
        "confusion_fwd": [],
        "grounded_chunks": [],
        "outline": [
            {"title": "Gentle hook"},
            {"title": "Formal A"},
            {"title": "Formal B"},
        ],
        "depth_tier": "intermediate",
    }
    result = asyncio.run(graph_mod.fact_checker(state))

    # 2 high-risk nodes critiqued under concurrency=2 → both in flight at once.
    assert tracker.calls == ["Formal A", "Formal B"]
    assert tracker.max_active == 2
    # qa_log must still contain all 3 nodes (1 rule-only + 2 critic-ran).
    qa_log = result["qa_log"]
    assert [e["qa_path"] for e in qa_log] == ["rule-only", "critic-ran", "critic-ran"]
