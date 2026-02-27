"""Tests for /api/v1/concepts/* template retriever endpoints (T3)."""
from unittest.mock import MagicMock


def _rec(**kwargs):
    """Make a mock Neo4j record whose .data() returns kwargs."""
    r = MagicMock()
    r.data.return_value = kwargs
    return r


# ── prerequisites ────────────────────────────────────────────────────────────

def test_prerequisites_200(client, mock_driver):
    mock_driver.execute_query.return_value = (
        [_rec(concept_id="conditional_independence", name="conditional independence",
              chapter=2, difficulty=0)],
        None, None,
    )
    resp = client.get("/api/v1/concepts/d_separation/prerequisites")
    assert resp.status_code == 200


def test_prerequisites_returns_list(client, mock_driver):
    mock_driver.execute_query.return_value = (
        [_rec(concept_id="conditional_independence", name="conditional independence",
              chapter=2, difficulty=0),
         _rec(concept_id="directed_acyclic_graph_dag", name="DAG",
              chapter=1, difficulty=0)],
        None, None,
    )
    data = client.get("/api/v1/concepts/d_separation/prerequisites").json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["concept_id"] == "conditional_independence"


def test_prerequisites_unknown_concept_returns_empty(client, mock_driver):
    mock_driver.execute_query.return_value = ([], None, None)
    resp = client.get("/api/v1/concepts/nonexistent_xyz/prerequisites")
    assert resp.status_code == 200
    assert resp.json() == []


# ── next-concepts ────────────────────────────────────────────────────────────

def test_next_concepts_200(client, mock_driver):
    mock_driver.execute_query.return_value = (
        [_rec(concept_id="pc_algorithm", name="PC Algorithm", chapter=7, difficulty=0)],
        None, None,
    )
    resp = client.get("/api/v1/concepts/causal_learning/next-concepts")
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["concept_id"] == "pc_algorithm"


# ── related ──────────────────────────────────────────────────────────────────

def test_related_200(client, mock_driver):
    mock_driver.execute_query.return_value = (
        [_rec(concept_id="potential_outcomes", name="Potential Outcomes",
              relation_type="COMMONLY_CONFUSED")],
        None, None,
    )
    resp = client.get("/api/v1/concepts/counterfactuals/related")
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["relation_type"] == "COMMONLY_CONFUSED"


# ── sections ─────────────────────────────────────────────────────────────────

def test_sections_200(client, mock_driver):
    mock_driver.execute_query.return_value = (
        [_rec(section_id="6.1", label="§6.1 Structural Causal Models",
              chapter=6, start_page=100, end_page=115)],
        None, None,
    )
    resp = client.get("/api/v1/concepts/structural_causal_model_scm/sections")
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["section_id"] == "6.1"


# ── search ───────────────────────────────────────────────────────────────────

def test_search_200(client, mock_driver):
    mock_driver.execute_query.return_value = (
        [_rec(concept_id="causal_learning", name="causal learning", chapter=7, score=0.9)],
        None, None,
    )
    resp = client.get("/api/v1/concepts/search?q=causal")
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["concept_id"] == "causal_learning"


def test_search_requires_q_param(client):
    resp = client.get("/api/v1/concepts/search")
    assert resp.status_code == 422  # missing required query param


def test_search_default_limit(client, mock_driver):
    mock_driver.execute_query.return_value = ([], None, None)
    resp = client.get("/api/v1/concepts/search?q=test")
    assert resp.status_code == 200


# ── single concept ───────────────────────────────────────────────────────────

def test_get_concept_200(client, mock_driver):
    mock_driver.execute_query.return_value = (
        [_rec(concept_id="d_separation", name="d-separation",
              chapter=2, difficulty=0, page_refs=[48], misconceptions=[])],
        None, None,
    )
    resp = client.get("/api/v1/concepts/d_separation")
    assert resp.status_code == 200
    data = resp.json()
    assert data["concept_id"] == "d_separation"


def test_get_concept_not_found(client, mock_driver):
    mock_driver.execute_query.return_value = ([], None, None)
    resp = client.get("/api/v1/concepts/does_not_exist")
    assert resp.status_code == 404
