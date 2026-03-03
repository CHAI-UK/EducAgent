"""Tests for backend.services.retrieval (T5.2a-c)."""
from unittest.mock import MagicMock

import pytest

from backend.services.retrieval import (
    PassageResult,
    concept_exists,
    get_section_page_ranges,
    retrieve_passages,
)
from backend.settings import Settings


# ── Helpers ───────────────────────────────────────────────────────────────────

def _neo4j_record(**kwargs):
    r = MagicMock()
    r.__getitem__ = lambda self, key: kwargs[key]
    r.get = lambda key, default=None: kwargs.get(key, default)
    # Also support dict-style access via execute_query row iteration
    r.data.return_value = kwargs
    return r


def _qdrant_hit(page_num, chapter, score, section_heading="Sec", content="text"):
    hit = MagicMock()
    hit.score = score
    hit.payload = {
        "page_num": page_num,
        "chapter": chapter,
        "section_heading": section_heading,
        "content": content,
    }
    return hit


def _mock_settings():
    s = MagicMock(spec=Settings)
    s.openrouter_base_url = "https://openrouter.ai/api/v1"
    s.openrouter_api_key = "test-key"
    return s


# ── concept_exists ────────────────────────────────────────────────────────────

def test_concept_exists_true(mock_driver):
    """T5.2a — concept_exists returns True when Neo4j returns rows."""
    mock_driver.execute_query.return_value = (
        [_neo4j_record(concept_id="d_separation")], None, None
    )
    assert concept_exists("d_separation", mock_driver) is True


def test_concept_exists_false(mock_driver):
    """T5.2a — concept_exists returns False for empty result."""
    mock_driver.execute_query.return_value = ([], None, None)
    assert concept_exists("unknown_concept", mock_driver) is False


# ── get_section_page_ranges ───────────────────────────────────────────────────

def test_get_section_page_ranges(mock_driver):
    """T5.2b — page ranges are extracted from Neo4j Section nodes."""
    mock_driver.execute_query.return_value = (
        [_neo4j_record(start_page=81, end_page=88),
         _neo4j_record(start_page=88, end_page=96)],
        None, None,
    )
    ranges = get_section_page_ranges("d_separation", mock_driver)
    assert (81, 88) in ranges
    assert (88, 96) in ranges


def test_get_section_page_ranges_empty(mock_driver):
    """T5.2b — returns empty list when concept has no COVERED_IN edges."""
    mock_driver.execute_query.return_value = ([], None, None)
    ranges = get_section_page_ranges("orphan_concept", mock_driver)
    assert ranges == []


# ── retrieve_passages ─────────────────────────────────────────────────────────

def test_retrieve_passages_filtered(mock_driver, mock_qdrant, monkeypatch):
    """T5.2c — uses Qdrant Range filter when concept has section page ranges."""
    mock_driver.execute_query.return_value = (
        [_neo4j_record(start_page=81, end_page=96)], None, None
    )
    mock_qdrant.query_points.return_value = MagicMock(points=[
        _qdrant_hit(page_num=83, chapter=6, score=0.92)
    ])

    # Patch embed_query to avoid real API call
    monkeypatch.setattr(
        "backend.services.retrieval.embed_query",
        lambda query, settings: [0.0] * 1536,
    )

    results = retrieve_passages(
        "d_separation", "what is d-separation",
        mock_driver, mock_qdrant, _mock_settings(), top_k=3
    )
    assert len(results) == 1
    assert isinstance(results[0], PassageResult)
    assert results[0].page_num == 83
    assert results[0].score == pytest.approx(0.92)

    # Verify filter was passed (not None)
    call_kwargs = mock_qdrant.query_points.call_args
    assert call_kwargs.kwargs.get("query_filter") is not None


def test_retrieve_passages_unfiltered_fallback(mock_driver, mock_qdrant, monkeypatch):
    """T5.2c — falls back to unfiltered search when no COVERED_IN edges exist."""
    mock_driver.execute_query.return_value = ([], None, None)
    mock_qdrant.query_points.return_value = MagicMock(points=[
        _qdrant_hit(page_num=10, chapter=1, score=0.75)
    ])

    monkeypatch.setattr(
        "backend.services.retrieval.embed_query",
        lambda query, settings: [0.0] * 1536,
    )

    results = retrieve_passages(
        "orphan_concept", "some query",
        mock_driver, mock_qdrant, _mock_settings(), top_k=5
    )
    assert len(results) == 1

    # Verify query_filter=None was passed (unfiltered fallback)
    call_kwargs = mock_qdrant.query_points.call_args
    assert call_kwargs.kwargs.get("query_filter") is None


def test_retrieve_passages_returns_passageresult_fields(mock_driver, mock_qdrant, monkeypatch):
    """T5.2c — all PassageResult fields populated from Qdrant payload."""
    mock_driver.execute_query.return_value = (
        [_neo4j_record(start_page=1, end_page=15)], None, None
    )
    mock_qdrant.query_points.return_value = MagicMock(points=[
        _qdrant_hit(
            page_num=5, chapter=1, score=0.88,
            section_heading="1.1 Probability Theory", content="Some content"
        )
    ])
    monkeypatch.setattr(
        "backend.services.retrieval.embed_query",
        lambda q, s: [0.0] * 1536,
    )

    results = retrieve_passages(
        "probability", "define probability",
        mock_driver, mock_qdrant, _mock_settings()
    )
    r = results[0]
    assert r.page_num == 5
    assert r.chapter == 1
    assert r.section_heading == "1.1 Probability Theory"
    assert r.content == "Some content"
    assert r.score == pytest.approx(0.88)
