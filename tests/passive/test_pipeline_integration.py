"""End-to-end compiled-graph integration test for Story 5.3."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.agents.passive import graph as graph_mod


class _FakeUsage:
    def __init__(self, prompt_tokens: int = 13, completion_tokens: int = 17) -> None:
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


class _PipelineClient:
    def __init__(self) -> None:
        self.chat = self
        self.completions = self
        self.calls: list[tuple[str, str]] = []

    async def create(self, *, messages, **kwargs):  # type: ignore[no-untyped-def]
        system = next(msg["content"] for msg in messages if msg["role"] == "system")
        user = next(msg["content"] for msg in messages if msg["role"] == "user")
        self.calls.append((system, user))

        if system == "outline-system":
            return _FakeResponse(
                {
                    "outline": [
                        {"title": "Why DAGs matter", "summary": "Gentle setup", "rag_focus": "dag basics"},
                        {"title": "Reading arrows carefully", "summary": "Formal reading", "rag_focus": "edge semantics"},
                    ]
                }
            )

        if system == "fact-check-system":
            return _FakeResponse({"issues": []})

        if system != "content-system":
            raise AssertionError(f"Unexpected system prompt: {system!r}")

        title = user.split("node=", 1)[1]
        if title == "Why DAGs matter":
            return _FakeResponse(
                {
                    "sections": [
                        {
                            "section": "The Big Idea",
                            "content": "A DAG gives a compact picture of assumptions.",
                            "markers": [],
                            "part": "hook",
                        },
                        {
                            "section": "Intuition",
                            "content": "Arrows help you reason about which paths can carry information.",
                            "markers": [],
                            "part": "intuition",
                        },
                        {
                            "section": "Checkpoint",
                            "content": "Ask which directions information can flow.",
                            "markers": ["[QUIZ_SLOT]"],
                            "part": "checkpoint",
                        },
                    ]
                }
            )

        if title == "Reading arrows carefully":
            return _FakeResponse(
                {
                    "sections": [
                        {
                            "section": "Start Here",
                            "content": "Arrow direction is meaningful.",
                            "markers": [],
                            "part": "hook",
                        },
                        {
                            "section": "Definition",
                            "content": "A directed edge X -> Y states that X is a direct parent of Y.",
                            "markers": [],
                            "part": "definition",
                        },
                        {
                            "section": "Checkpoint",
                            "content": "Identify parent and child in one edge.",
                            "markers": [],
                            "part": "checkpoint",
                        },
                    ]
                }
            )

        raise AssertionError(f"Unexpected node title in user prompt: {title!r}")


@pytest.fixture
def tmp_course_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr("src.agents.passive.mock_data.PROJECT_ROOT", tmp_path)
    return tmp_path


def test_pipeline_roundtrip_uses_cache_and_persists_metrics(
    tmp_course_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Compiled graph should write cache+metrics, then short-circuit on cache hit."""
    mock_input = {
        "user_id": "learner_50",
        "concept_id": "directed-acyclic-graph-dag",
        "profile_sig": "CS-BEGINNER",
        "adaptation_ctx": {
            "background": "CS undergrad",
            "role": "student",
            "prior_knowledge": ["graphs"],
            "learning_goal": "Understand DAG basics",
            "domain_framing": "general",
        },
        "depth_tier": "beginner",
        "progress_ctx": {"mastery_scores": {}},
        "confusion_fwd": [],
        "concept_ctx": {
            "concept_id": "directed-acyclic-graph-dag",
            "prerequisite": [],
            "title": "Directed Acyclic Graphs",
        },
        "grounded_chunks": [
            {"source": "chunk-1", "score": 0.4, "text": "DAGs use directed edges and no cycles."}
        ],
    }

    monkeypatch.setattr(graph_mod, "_config", {
        "api_key_env": "OPENROUTER_API_KEY",
        "base_url_env": "OPENROUTER_BASE_URL",
        "base_url_default": "https://openrouter.ai/api/v1",
        "request_timeout_s": 300,
        "heartbeat_interval_s": 15,
        "max_wait_s": 360,
        "outline": {"model": "outline-model", "temperature": 0, "max_tokens": 1024},
        "content": {
            "model": "content-model",
            "temperature": 0,
            "max_tokens": 1024,
            "concurrency": 2,
            "retry_delays_s": [0, 0],
        },
        "fact_check": {
            "enabled": True,
            "model": "fact-check-model",
            "temperature": 0,
            "max_tokens": 512,
            "regenerate_on_critical": False,
            "max_regeneration_attempts": 1,
            "targeted_recheck": False,
        },
        "image": {"enabled": False, "mode": "inline", "model": "image-model", "fallback_model": None},
    })
    monkeypatch.setattr(graph_mod, "OUTLINE_SYSTEM_PROMPT", "outline-system")
    monkeypatch.setattr(graph_mod, "OUTLINE_USER_TEMPLATE", "concept={concept_id}")
    monkeypatch.setattr(graph_mod, "FACT_CHECK_SYSTEM_PROMPT", "fact-check-system")
    monkeypatch.setattr(graph_mod, "FACT_CHECK_USER_TEMPLATE", "sections={sections_json}")
    monkeypatch.setitem(
        graph_mod.TIER_CONTENT_PROMPTS,
        "beginner",
        {"system": "content-system", "user": "node={node_title}"},
    )
    monkeypatch.setattr(graph_mod, "get_mock_input", lambda user_id, concept_id: mock_input)

    async def _direct(awaitable, **kwargs):
        return await awaitable

    monkeypatch.setattr(graph_mod, "_await_with_heartbeat", _direct)

    client = _PipelineClient()
    monkeypatch.setattr(graph_mod, "_get_client", lambda: client)
    initial_state = {
        "user_id": "learner_50",
        "concept_id": "directed-acyclic-graph-dag",
    }

    compiled = graph_mod.compile_graph(sync_mode=True)
    first = compiled.invoke(initial_state)

    assert first["cache_hit"] is False
    assert first["image_skipped"] is True
    assert first["run_metrics"]["image"]["skipped"] is True
    assert first["run_metrics"]["outline"]["nodes"] == 2
    assert first["run_metrics"]["content"]["nodes"] == 2
    assert first["run_metrics"]["content"]["prompt_tokens"] > 0
    assert first["run_metrics"]["fact_check"]["nodes_reviewed"] == 2
    assert first["run_metrics"]["fact_check"]["prompt_tokens"] > 0
    assert first["run_metrics"]["fact_check"]["qa_path_counts"]["rule-only"] == 1
    assert first["run_metrics"]["fact_check"]["qa_path_counts"]["critic-ran"] == 1
    assert [node["node_title"] for node in first["nodes"]] == [
        "Why DAGs matter",
        "Reading arrows carefully",
    ]

    structure_snapshot = [
        {
            "node_title": node["node_title"],
            "parts": [section["part"] for section in node["sections"]],
            "sections": [section["section"] for section in node["sections"]],
        }
        for node in first["nodes"]
    ]
    assert structure_snapshot == [
        {
            "node_title": "Why DAGs matter",
            "parts": ["hook", "intuition", "checkpoint"],
            "sections": ["The Big Idea", "Intuition", "Checkpoint"],
        },
        {
            "node_title": "Reading arrows carefully",
            "parts": ["hook", "definition", "checkpoint"],
            "sections": ["Start Here", "Definition", "Checkpoint"],
        },
    ]

    cache_dir = (
        tmp_course_dir
        / "data"
        / "user"
        / "learner_50"
        / "passive_courses"
        / "directed-acyclic-graph-dag"
    )
    content_path = cache_dir / "content.json"
    metrics_path = cache_dir / "run_metrics.json"
    assert content_path.exists()
    assert metrics_path.exists()

    cached = json.loads(content_path.read_text())
    metrics = json.loads(metrics_path.read_text())
    assert cached["cache_key"] == "directed-acyclic-graph-dag:CS-BEGINNER"
    assert cached["nodes"] == first["nodes"]
    assert metrics["outline"]["nodes"] == 2
    assert metrics["content"]["nodes"] == 2
    assert metrics["fact_check"]["qa_path_counts"]["critic-ran"] == 1
    assert metrics["image"]["skipped"] is True

    monkeypatch.setattr(
        graph_mod,
        "_get_client",
        lambda: (_ for _ in ()).throw(AssertionError("cache hit should bypass LLM calls")),
    )

    second = compiled.invoke(initial_state)

    assert second["cache_hit"] is True
    assert second["nodes"] == first["nodes"]
    assert second["image_refs"] == []
