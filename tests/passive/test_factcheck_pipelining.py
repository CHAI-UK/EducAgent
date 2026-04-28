"""Tests for node-level fact-check pipelining inside content generation."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from src.agents.passive import graph as graph_mod


class _FakeUsage:
    def __init__(self, prompt_tokens: int = 11, completion_tokens: int = 7) -> None:
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content

    def model_dump(self) -> dict[str, object]:
        return {"content": self.content}


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.finish_reason = "stop"
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.choices = [_FakeChoice(json.dumps(payload))]
        self.usage = _FakeUsage()


class _ContentClient:
    def __init__(self, *, delays_by_title: dict[str, float], events: list[str]) -> None:
        self.delays_by_title = delays_by_title
        self.events = events
        self.chat = self
        self.completions = self

    async def create(self, *, messages, **kwargs):  # type: ignore[no-untyped-def]
        user_msg = next(msg["content"] for msg in messages if msg["role"] == "user")
        title = user_msg.split("node=", 1)[1]
        await asyncio.sleep(self.delays_by_title.get(title, 0))
        self.events.append(f"content_done:{title}")
        return _FakeResponse(
            {
                "sections": [
                    {
                        "section": "Definition",
                        "content": f"A formal definition for {title}.",
                        "markers": [],
                        "part": "definition",
                    }
                ]
            }
        )


def _state(*titles: str) -> dict[str, Any]:
    return {
        "adaptation_ctx": {},
        "concept_ctx": {"concept_id": "dag", "prerequisite": []},
        "outline": [{"title": title, "summary": "", "rag_focus": ""} for title in titles],
        "grounded_chunks": [],
        "progress_ctx": {"mastery_scores": {}},
        "confusion_fwd": [],
        "depth_tier": "beginner",
    }


def _config(*, content_concurrency: int, fact_concurrency: int) -> dict[str, Any]:
    return {
        "api_key_env": "OPENROUTER_API_KEY",
        "base_url_env": "OPENROUTER_BASE_URL",
        "base_url_default": "https://openrouter.ai/api/v1",
        "request_timeout_s": 300,
        "heartbeat_interval_s": 15,
        "max_wait_s": 360,
        "outline": {"model": "x", "temperature": 0, "max_tokens": 256},
        "content": {
            "model": "content",
            "temperature": 0,
            "max_tokens": 256,
            "concurrency": content_concurrency,
            "retry_delays_s": [0],
        },
        "fact_check": {
            "enabled": True,
            "pipeline_with_content": True,
            "model": "critic",
            "temperature": 0,
            "max_tokens": 256,
            "regenerate_on_critical": False,
            "max_regeneration_attempts": 1,
            "targeted_recheck": False,
            "concurrency": fact_concurrency,
        },
        "image": {"enabled": False, "model": "x", "fallback_model": None},
    }


def test_pipelined_fact_check_starts_before_all_nodes_finish(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    client = _ContentClient(
        delays_by_title={"Fast": 0.0, "Slow": 0.08},
        events=events,
    )
    monkeypatch.setattr(graph_mod, "_config", _config(content_concurrency=2, fact_concurrency=1))
    monkeypatch.setattr(graph_mod, "_get_client", lambda: client)

    async def _direct(awaitable, **kwargs):
        return await awaitable

    async def _critique(**kwargs):
        title = kwargs["node"]["node_title"]
        events.append(f"critique_start:{title}")
        await asyncio.sleep(0.01)
        return []

    monkeypatch.setattr(graph_mod, "_await_with_heartbeat", _direct)
    monkeypatch.setattr(graph_mod, "_critique_node", _critique)

    result = asyncio.run(
        graph_mod._content_gen_impl(
            _state("Fast", "Slow"),
            system_prompt="content-system",
            user_template="node={node_title}",
        )
    )

    assert events.index("critique_start:Fast") < events.index("content_done:Slow")
    assert result["fact_check_completed"] is True
    assert result["run_metrics"]["fact_check"]["pipelined_with_content"] is True


def test_pipelined_fact_check_respects_shared_concurrency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    client = _ContentClient(delays_by_title={}, events=events)
    monkeypatch.setattr(graph_mod, "_config", _config(content_concurrency=5, fact_concurrency=2))
    monkeypatch.setattr(graph_mod, "_get_client", lambda: client)

    active = 0
    max_active = 0

    async def _direct(awaitable, **kwargs):
        return await awaitable

    async def _critique(**kwargs):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        try:
            await asyncio.sleep(0.03)
            return []
        finally:
            active -= 1

    monkeypatch.setattr(graph_mod, "_await_with_heartbeat", _direct)
    monkeypatch.setattr(graph_mod, "_critique_node", _critique)

    result = asyncio.run(
        graph_mod._content_gen_impl(
            _state("A", "B", "C", "D", "E"),
            system_prompt="content-system",
            user_template="node={node_title}",
        )
    )

    assert max_active == 2
    assert [entry["node_title"] for entry in result["qa_log"]] == ["A", "B", "C", "D", "E"]
    assert [node["node_title"] for node in result["nodes"]] == ["A", "B", "C", "D", "E"]


def test_fact_checker_skips_after_pipelined_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(graph_mod, "_config", _config(content_concurrency=1, fact_concurrency=1))

    async def _should_not_run(**kwargs):
        raise AssertionError("fact_checker should not duplicate pipelined QA")

    monkeypatch.setattr(graph_mod, "_critique_node", _should_not_run)

    result = asyncio.run(
        graph_mod.fact_checker(
            {
                "fact_check_completed": True,
                "fact_check_issues": [{"node_title": "A", "severity": "minor"}],
                "qa_log": [{"node_title": "A", "qa_path": "critic-ran"}],
            }
        )
    )

    assert result["fact_check_issues"] == [{"node_title": "A", "severity": "minor"}]
    assert result["qa_log"] == [{"node_title": "A", "qa_path": "critic-ran"}]
