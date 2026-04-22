"""Tests for run_metrics persistence (Story 5.3 AC-11, AC-12)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.agents.passive import graph as graph_mod


@pytest.fixture
def tmp_course_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr("src.agents.passive.mock_data.PROJECT_ROOT", tmp_path)
    return tmp_path


def test_cache_writer_persists_run_metrics_sidecar(tmp_course_dir: Path) -> None:
    """cache_writer should drop run_metrics.json next to content.json."""
    state = {
        "user_id": "learner_test",
        "concept_id": "dag",
        "profile_sig": "CS-STATS-ADV",
        "concept_ctx": {"concept_id": "dag"},
        "outline": [],
        "nodes": [],
        "image_refs": [],
        "fact_check_issues": [],
        "run_metrics": {
            "outline": {"duration_s": 1.23},
            "content": {"duration_s": 4.56, "nodes": 3},
            "fact_check": {"duration_s": 0.78},
        },
    }
    graph_mod.cache_writer(state)

    metrics_path = (
        tmp_course_dir
        / "data"
        / "user"
        / "learner_test"
        / "passive_courses"
        / "dag"
        / "run_metrics.json"
    )
    assert metrics_path.exists(), "run_metrics.json must be written alongside content.json"
    data = json.loads(metrics_path.read_text())
    assert data["outline"]["duration_s"] == 1.23
    assert data["content"]["nodes"] == 3
    assert data["fact_check"]["duration_s"] == 0.78


def test_cache_writer_skips_metrics_on_cache_hit(tmp_course_dir: Path) -> None:
    """On cache_hit, no metrics sidecar is written (nothing new happened)."""
    state = {
        "user_id": "learner_test",
        "concept_id": "dag",
        "profile_sig": "CS-STATS-ADV",
        "concept_ctx": {"concept_id": "dag"},
        "cache_hit": True,
        "run_metrics": {"outline": {"duration_s": 1.0}},
    }
    graph_mod.cache_writer(state)

    metrics_path = (
        tmp_course_dir
        / "data"
        / "user"
        / "learner_test"
        / "passive_courses"
        / "dag"
        / "run_metrics.json"
    )
    assert not metrics_path.exists()


def test_merge_run_metrics_preserves_prior_phases() -> None:
    """Adding a new phase must not clobber earlier phase entries."""
    state = {"run_metrics": {"outline": {"duration_s": 1.0}}}
    merged = graph_mod._merge_run_metrics(state, "content", {"duration_s": 5.0, "nodes": 4})
    assert merged["outline"]["duration_s"] == 1.0
    assert merged["content"]["duration_s"] == 5.0
    assert merged["content"]["nodes"] == 4


def test_merge_run_metrics_handles_missing_initial_state() -> None:
    """Merging into state with no run_metrics should yield a fresh dict."""
    merged = graph_mod._merge_run_metrics({}, "outline", {"duration_s": 1.0})
    assert merged == {"outline": {"duration_s": 1.0}}
