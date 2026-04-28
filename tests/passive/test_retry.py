"""Tests for _llm_call_with_retry exponential backoff (Story 5.3 AC-13)."""

from __future__ import annotations

import asyncio
import json

from openai import RateLimitError
import pytest

from src.agents.passive import graph as graph_mod


def _make_rate_limit_error() -> RateLimitError:
    """Construct a RateLimitError without touching the SDK's private request shape.

    ``RateLimitError.__init__`` requires a real HTTP response object; bypass it
    via ``__new__`` so tests don't need to construct a fake httpx.Response.
    """
    err = RateLimitError.__new__(RateLimitError)
    Exception.__init__(err, "429 too many requests")
    return err


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


class _FakeClient:
    def __init__(
        self,
        *,
        delays_by_title: dict[str, float] | None = None,
        fail_titles: set[str] | None = None,
    ) -> None:
        self.delays_by_title = delays_by_title or {}
        self.fail_titles = fail_titles or set()
        self.chat = self
        self.completions = self
        self.current_active = 0
        self.max_active = 0
        self.calls_by_title: dict[str, int] = {}

    async def create(self, *, messages, **kwargs):  # type: ignore[no-untyped-def]
        user_msg = next(msg["content"] for msg in messages if msg["role"] == "user")
        title = user_msg.split("node=", 1)[1]
        self.calls_by_title[title] = self.calls_by_title.get(title, 0) + 1
        self.current_active += 1
        self.max_active = max(self.max_active, self.current_active)
        try:
            await asyncio.sleep(self.delays_by_title.get(title, 0))
            if title in self.fail_titles:
                raise _make_rate_limit_error()
            return _FakeResponse(
                {
                    "sections": [
                        {
                            "section": "Hook",
                            "content": f"Intro for {title}.",
                            "markers": [],
                            "part": "hook",
                        },
                        {
                            "section": "Checkpoint",
                            "content": "Check your understanding.",
                            "markers": [],
                            "part": "checkpoint",
                        },
                    ]
                }
            )
        finally:
            self.current_active -= 1


class _CaptureClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.last_user_message = ""
        self.chat = self
        self.completions = self

    async def create(self, *, messages, **kwargs):  # type: ignore[no-untyped-def]
        self.last_user_message = next(msg["content"] for msg in messages if msg["role"] == "user")
        return _FakeResponse(self.payload)


def _content_state(*titles: str) -> dict[str, object]:
    return {
        "adaptation_ctx": {},
        "concept_ctx": {"concept_id": "dag", "prerequisite": []},
        "outline": [{"title": title, "summary": "", "rag_focus": ""} for title in titles],
        "grounded_chunks": [],
        "progress_ctx": {"mastery_scores": {}},
        "confusion_fwd": [],
        "depth_tier": "beginner",
    }


def _content_config(concurrency: int) -> dict[str, object]:
    return {
        "api_key_env": "OPENROUTER_API_KEY",
        "base_url_env": "OPENROUTER_BASE_URL",
        "base_url_default": "https://openrouter.ai/api/v1",
        "request_timeout_s": 300,
        "heartbeat_interval_s": 15,
        "max_wait_s": 360,
        "outline": {"model": "x", "temperature": 0, "max_tokens": 1024},
        "content": {
            "model": "x",
            "temperature": 0,
            "max_tokens": 1024,
            "concurrency": concurrency,
            "retry_delays_s": [0, 0],
        },
        "fact_check": {"enabled": False},
        "image": {"enabled": False, "model": "x", "fallback_model": None},
    }


def test_retry_succeeds_after_one_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """After one 429 the second attempt should succeed."""
    calls = {"n": 0}

    async def _factory():
        calls["n"] += 1
        if calls["n"] == 1:
            raise _make_rate_limit_error()
        return "ok"

    monkeypatch.setattr(
        graph_mod, "_load_config", lambda: {"content": {"retry_delays_s": [0, 0, 0]}}
    )

    # Replace the heartbeat wrapper with a direct await so tests stay fast.
    async def _direct(awaitable, **kwargs):
        return await awaitable

    monkeypatch.setattr(graph_mod, "_await_with_heartbeat", _direct)

    result = asyncio.run(
        graph_mod._llm_call_with_retry(_factory, stage="test"),
    )
    assert result == "ok"
    assert calls["n"] == 2


def test_retry_raises_after_exhausting_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    """If every attempt raises, the final attempt should surface the error."""
    calls = {"n": 0}

    async def _factory():
        calls["n"] += 1
        raise _make_rate_limit_error()

    monkeypatch.setattr(graph_mod, "_load_config", lambda: {"content": {"retry_delays_s": [0, 0]}})

    async def _direct(awaitable, **kwargs):
        return await awaitable

    monkeypatch.setattr(graph_mod, "_await_with_heartbeat", _direct)

    with pytest.raises(RateLimitError):
        asyncio.run(
            graph_mod._llm_call_with_retry(_factory, stage="test"),
        )
    # max_attempts = len(delays) + 1 = 3
    assert calls["n"] == 3


def test_retry_does_not_catch_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-retryable errors (e.g. ValueError) must NOT trigger retries."""
    calls = {"n": 0}

    async def _factory():
        calls["n"] += 1
        raise ValueError("not retryable")

    monkeypatch.setattr(
        graph_mod, "_load_config", lambda: {"content": {"retry_delays_s": [0, 0, 0]}}
    )

    async def _direct(awaitable, **kwargs):
        return await awaitable

    monkeypatch.setattr(graph_mod, "_await_with_heartbeat", _direct)

    with pytest.raises(ValueError):
        asyncio.run(
            graph_mod._llm_call_with_retry(_factory, stage="test"),
        )
    assert calls["n"] == 1  # only tried once


def test_content_concurrency_preserves_outline_order(monkeypatch: pytest.MonkeyPatch) -> None:
    """concurrency=2 may finish out of order, but final nodes must keep outline order."""
    client = _FakeClient(delays_by_title={"Node A": 0.02, "Node B": 0.0, "Node C": 0.01})
    monkeypatch.setattr(graph_mod, "_config", _content_config(2))
    monkeypatch.setattr(graph_mod, "_get_client", lambda: client)

    async def _direct(awaitable, **kwargs):
        return await awaitable

    monkeypatch.setattr(graph_mod, "_await_with_heartbeat", _direct)

    result = asyncio.run(
        graph_mod._content_gen_impl(
            _content_state("Node A", "Node B", "Node C"),
            system_prompt="content-system",
            user_template="node={node_title}",
        )
    )

    assert [node["node_title"] for node in result["nodes"]] == ["Node A", "Node B", "Node C"]
    assert client.max_active == 2


def test_content_concurrency_one_preserves_serial_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    """concurrency=1 should behave like the old serial path."""
    client = _FakeClient(delays_by_title={"Node A": 0.01, "Node B": 0.0})
    monkeypatch.setattr(graph_mod, "_config", _content_config(1))
    monkeypatch.setattr(graph_mod, "_get_client", lambda: client)

    async def _direct(awaitable, **kwargs):
        return await awaitable

    monkeypatch.setattr(graph_mod, "_await_with_heartbeat", _direct)

    result = asyncio.run(
        graph_mod._content_gen_impl(
            _content_state("Node A", "Node B"),
            system_prompt="content-system",
            user_template="node={node_title}",
        )
    )

    assert [node["node_title"] for node in result["nodes"]] == ["Node A", "Node B"]
    assert client.max_active == 1


def test_content_retry_exhaustion_salvages_failed_node(monkeypatch: pytest.MonkeyPatch) -> None:
    """If a node keeps hitting 429s, the run should continue with a fallback node payload."""
    client = _FakeClient(fail_titles={"Node B"})
    monkeypatch.setattr(graph_mod, "_config", _content_config(2))
    monkeypatch.setattr(graph_mod, "_get_client", lambda: client)

    async def _direct(awaitable, **kwargs):
        return await awaitable

    monkeypatch.setattr(graph_mod, "_await_with_heartbeat", _direct)

    result = asyncio.run(
        graph_mod._content_gen_impl(
            _content_state("Node A", "Node B"),
            system_prompt="content-system",
            user_template="node={node_title}",
        )
    )

    assert [node["node_title"] for node in result["nodes"]] == ["Node A", "Node B"]
    failed_node = result["nodes"][1]
    assert failed_node["sections"][0]["section"] == "Temporary issue"
    assert failed_node["sections"][0]["part"] == "extra"

    metrics = result["run_metrics"]["content"]
    assert metrics["failed_count"] == 1
    assert metrics["failed_nodes"][0]["node_title"] == "Node B"
    assert metrics["failed_nodes"][0]["failed"] is True
    assert client.calls_by_title["Node B"] == 3


def test_repair_prompt_requires_part_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """Repair prompt must preserve the Story 5.3 part field, not regress to 3-key schema."""
    client = _CaptureClient(
        {
            "sections": [
                {
                    "section": "Hook",
                    "content": "Recovered content.",
                    "markers": [],
                    "part": "hook",
                }
            ]
        }
    )

    async def _direct(awaitable, **kwargs):
        return await awaitable

    monkeypatch.setattr(graph_mod, "_await_with_heartbeat", _direct)

    parsed = asyncio.run(
        graph_mod._repair_json_response(
            client=client,
            model="x",
            max_tokens=256,
            raw='{"broken": true}',
            node_title="Node A",
        )
    )

    assert parsed[0]["part"] == "hook"
    assert '"part"' in client.last_user_message
    assert (
        "hook, recall, definition, intuition, visual, checkpoint, extra" in client.last_user_message
    )
