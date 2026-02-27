"""Tests for /api/v1/chapters/* endpoints (T3.7)."""
from unittest.mock import MagicMock


def _rec(**kwargs):
    r = MagicMock()
    r.data.return_value = kwargs
    return r


def test_chapter_concepts_200(client, mock_driver):
    mock_driver.execute_query.return_value = (
        [_rec(concept_id="d_separation", name="d-separation", difficulty=0, page_refs=[48]),
         _rec(concept_id="conditional_independence", name="conditional independence",
              difficulty=0, page_refs=[30])],
        None, None,
    )
    resp = client.get("/api/v1/chapters/2/concepts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["concept_id"] == "d_separation"


def test_chapter_concepts_empty(client, mock_driver):
    mock_driver.execute_query.return_value = ([], None, None)
    resp = client.get("/api/v1/chapters/99/concepts")
    assert resp.status_code == 200
    assert resp.json() == []


def test_chapter_1_has_4_concepts(client, mock_driver):
    """Chapter 1 of ECI has exactly 4 concepts per architecture.md."""
    ch1_concepts = [
        "random_variable", "structural_causal_model_scm",
        "conditional_independence", "directed_acyclic_graph_dag",
    ]
    records = [_rec(concept_id=cid, name=cid, difficulty=0, page_refs=[]) for cid in ch1_concepts]
    mock_driver.execute_query.return_value = (records, None, None)
    resp = client.get("/api/v1/chapters/1/concepts")
    assert resp.status_code == 200
    assert len(resp.json()) == 4
