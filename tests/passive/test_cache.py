"""Tests for cache_reader / cache_writer roundtrip (Story 5.3 AC-4, AC-5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.agents.passive import graph as graph_mod


@pytest.fixture
def tmp_course_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the passive_courses storage root to a tmp dir for isolation."""
    fake_root = tmp_path
    monkeypatch.setattr(
        "src.agents.passive.mock_data.PROJECT_ROOT", fake_root
    )
    return fake_root


def _base_state() -> dict:
    return {
        "user_id": "learner_test",
        "concept_id": "dag",
        "profile_sig": "CS-STATS-ADV",
        "concept_ctx": {"concept_id": "dag"},
    }


def test_cache_reader_miss_when_file_absent(tmp_course_dir: Path) -> None:
    state = _base_state()
    out = graph_mod.cache_reader(state)
    assert out["cache_hit"] is False
    assert out["cache_key"] == "dag:CS-STATS-ADV"


def test_cache_reader_hit_populates_state(tmp_course_dir: Path) -> None:
    """Pre-seed the cache file and verify reader loads content + flips cache_hit."""
    course_dir = tmp_course_dir / "data" / "user" / "learner_test" / "passive_courses" / "dag"
    course_dir.mkdir(parents=True)
    content = {
        "cache_key": "dag:CS-STATS-ADV",
        "concept_id": "dag",
        "profile_sig": "CS-STATS-ADV",
        "outline": [{"title": "N1", "summary": "", "rag_focus": ""}],
        "nodes": [
            {
                "node_title": "N1",
                "sections": [
                    {"section": "Hook", "content": "Hi.", "markers": [], "part": "hook"}
                ],
            }
        ],
        "image_refs": [],
    }
    (course_dir / "content.json").write_text(json.dumps(content))

    out = graph_mod.cache_reader(_base_state())
    assert out["cache_hit"] is True
    assert out["cache_key"] == "dag:CS-STATS-ADV"
    assert out["outline"] == content["outline"]
    assert out["nodes"] == content["nodes"]
    assert out["image_refs"] == content["image_refs"]


def test_cache_reader_miss_on_stale_profile_sig(tmp_course_dir: Path) -> None:
    """A cache file for a DIFFERENT profile_sig should NOT be returned."""
    course_dir = tmp_course_dir / "data" / "user" / "learner_test" / "passive_courses" / "dag"
    course_dir.mkdir(parents=True)
    content = {
        "cache_key": "dag:OTHER-PROFILE",  # stale — different from request
        "concept_id": "dag",
        "profile_sig": "OTHER-PROFILE",
        "outline": [],
        "nodes": [],
        "image_refs": [],
    }
    (course_dir / "content.json").write_text(json.dumps(content))

    out = graph_mod.cache_reader(_base_state())
    assert out["cache_hit"] is False


def test_cache_reader_miss_on_corrupt_json(tmp_course_dir: Path) -> None:
    course_dir = tmp_course_dir / "data" / "user" / "learner_test" / "passive_courses" / "dag"
    course_dir.mkdir(parents=True)
    (course_dir / "content.json").write_text("{not valid json")

    out = graph_mod.cache_reader(_base_state())
    assert out["cache_hit"] is False


def test_cache_writer_persists_full_blob(tmp_course_dir: Path) -> None:
    """cache_writer should write a JSON file that cache_reader can roundtrip."""
    state = _base_state()
    state["outline"] = [{"title": "N1", "summary": "", "rag_focus": ""}]
    state["nodes"] = [
        {
            "node_title": "N1",
            "sections": [
                {"section": "Hook", "content": "Hi.", "markers": [], "part": "hook"}
            ],
        }
    ]
    state["image_refs"] = []
    state["fact_check_issues"] = []

    graph_mod.cache_writer(state)

    cache_path = (
        tmp_course_dir / "data" / "user" / "learner_test" / "passive_courses" / "dag" / "content.json"
    )
    assert cache_path.exists()
    data = json.loads(cache_path.read_text())
    assert data["cache_key"] == "dag:CS-STATS-ADV"
    assert data["nodes"] == state["nodes"]


def test_cache_writer_does_not_rewrite_on_hit(tmp_course_dir: Path) -> None:
    """When cache_hit is True, cache_writer should NOT overwrite the existing file."""
    course_dir = (
        tmp_course_dir / "data" / "user" / "learner_test" / "passive_courses" / "dag"
    )
    course_dir.mkdir(parents=True)
    existing = {"cache_key": "dag:CS-STATS-ADV", "nodes": [{"marker": "original"}]}
    cache_path = course_dir / "content.json"
    cache_path.write_text(json.dumps(existing))

    state = _base_state()
    state["cache_hit"] = True
    state["nodes"] = [{"marker": "would-overwrite"}]

    graph_mod.cache_writer(state)

    # File should be unchanged
    assert json.loads(cache_path.read_text()) == existing
