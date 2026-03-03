"""Tests for POST /api/v1/retrieve (T6.3a-c)."""
from unittest.mock import patch

import pytest

from backend.services.retrieval import PassageResult
from backend.services.neo4j_client import get_driver
from backend.services.qdrant_client import get_qdrant
from backend.settings import get_settings, Settings


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sample_passage(**overrides):
    base = dict(
        page_num=83,
        chapter=6,
        section_heading="6.3 Interventions",
        content="Some passage text",
        score=0.91,
    )
    base.update(overrides)
    return PassageResult(**base)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_retrieve_happy_path_200(client, mock_driver, mock_qdrant, monkeypatch):
    """T6.3a — POST /retrieve returns 200 with passage list for known concept."""
    from backend.main import app

    # concept_exists returns True
    mock_driver.execute_query.side_effect = [
        ([{"concept_id": "d_separation"}], None, None),  # concept_exists check
        ([{"start_page": 81, "end_page": 96}], None, None),  # page ranges
    ]
    mock_qdrant.search.return_value = []

    monkeypatch.setattr(
        "backend.routers.retrieve.concept_exists", lambda cid, drv: True
    )
    monkeypatch.setattr(
        "backend.routers.retrieve.retrieve_passages",
        lambda *args, **kwargs: [_sample_passage()],
    )

    resp = client.post(
        "/api/v1/retrieve",
        json={"concept_id": "d_separation", "query": "what is d-separation", "top_k": 3},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "passages" in data
    assert len(data["passages"]) == 1
    p = data["passages"][0]
    assert p["page_num"] == 83
    assert p["chapter"] == 6
    assert p["section_heading"] == "6.3 Interventions"


def test_retrieve_unknown_concept_404(client, monkeypatch):
    """T6.3b — returns 404 when concept_id is not in Neo4j."""
    monkeypatch.setattr(
        "backend.routers.retrieve.concept_exists", lambda cid, drv: False
    )

    resp = client.post(
        "/api/v1/retrieve",
        json={"concept_id": "nonexistent_xyz", "query": "anything"},
    )
    assert resp.status_code == 404
    assert "nonexistent_xyz" in resp.json()["detail"]


def test_retrieve_top_k_respected(client, monkeypatch):
    """T6.3c — top_k parameter is forwarded to retrieve_passages."""
    captured = {}

    def fake_retrieve(concept_id, query, driver, qdrant, settings, top_k=5):
        captured["top_k"] = top_k
        return [_sample_passage()] * top_k

    monkeypatch.setattr(
        "backend.routers.retrieve.concept_exists", lambda cid, drv: True
    )
    monkeypatch.setattr("backend.routers.retrieve.retrieve_passages", fake_retrieve)

    resp = client.post(
        "/api/v1/retrieve",
        json={"concept_id": "d_separation", "query": "test", "top_k": 7},
    )
    assert resp.status_code == 200
    assert captured["top_k"] == 7


def test_retrieve_top_k_default_is_5(client, monkeypatch):
    """T6.3c — top_k defaults to 5 when not provided."""
    captured = {}

    def fake_retrieve(concept_id, query, driver, qdrant, settings, top_k=5):
        captured["top_k"] = top_k
        return []

    monkeypatch.setattr(
        "backend.routers.retrieve.concept_exists", lambda cid, drv: True
    )
    monkeypatch.setattr("backend.routers.retrieve.retrieve_passages", fake_retrieve)

    resp = client.post(
        "/api/v1/retrieve",
        json={"concept_id": "d_separation", "query": "test"},
    )
    assert resp.status_code == 200
    assert captured["top_k"] == 5


def test_retrieve_top_k_validation(client):
    """T6.3c — top_k must be between 1 and 20 (Pydantic validation)."""
    resp = client.post(
        "/api/v1/retrieve",
        json={"concept_id": "d_separation", "query": "test", "top_k": 0},
    )
    assert resp.status_code == 422

    resp = client.post(
        "/api/v1/retrieve",
        json={"concept_id": "d_separation", "query": "test", "top_k": 21},
    )
    assert resp.status_code == 422
