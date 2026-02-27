"""Tests for POST /api/v1/query (text2Cypher endpoint, T4)."""
from unittest.mock import MagicMock, patch


def _rec(**kwargs):
    r = MagicMock()
    r.data.return_value = kwargs
    return r


def test_query_endpoint_200(client, mock_driver):
    cypher = "MATCH (c:Concept {concept_id: 'd_separation'}) RETURN c"
    mock_driver.execute_query.return_value = (
        [_rec(concept_id="d_separation", name="d-separation")], None, None
    )
    with patch("backend.services.text2cypher.generate_cypher", return_value=cypher):
        resp = client.post("/api/v1/query", json={"question": "What is d-separation?"})
    assert resp.status_code == 200
    body = resp.json()
    assert "cypher" in body
    assert "results" in body
    assert "question" in body


def test_query_returns_cypher_and_results(client, mock_driver):
    cypher = "MATCH (c:Concept)-[:PREREQUISITE_OF]->(t:Concept {concept_id:'d_separation'}) RETURN c"
    mock_driver.execute_query.return_value = (
        [_rec(concept_id="conditional_independence", name="conditional independence")],
        None, None,
    )
    with patch("backend.services.text2cypher.generate_cypher", return_value=cypher):
        resp = client.post(
            "/api/v1/query",
            json={"question": "What are the prerequisites of d-separation?"},
        )
    body = resp.json()
    assert body["cypher"] == cypher
    assert len(body["results"]) == 1
    assert body["results"][0]["concept_id"] == "conditional_independence"


def test_query_missing_question_returns_422(client):
    resp = client.post("/api/v1/query", json={})
    assert resp.status_code == 422


def test_query_bad_cypher_returns_422(client, mock_driver):
    mock_driver.execute_query.side_effect = Exception("Cypher syntax error")
    with patch("backend.services.text2cypher.generate_cypher", return_value="INVALID CYPHER"):
        resp = client.post("/api/v1/query", json={"question": "bad question"})
    assert resp.status_code == 422


def test_generate_cypher_builds_prompt():
    """Unit test: generate_cypher sends a message with schema + terminology."""
    from backend.services.text2cypher import TEXT2CYPHER_PROMPT, ECI_SCHEMA, ECI_TERMINOLOGY

    assert "Concept" in ECI_SCHEMA
    assert "PREREQUISITE_OF" in ECI_SCHEMA
    assert "prerequisite" in ECI_TERMINOLOGY.lower()
    assert "{schema}" in TEXT2CYPHER_PROMPT
    assert "{terminology}" in TEXT2CYPHER_PROMPT
    assert "{question}" in TEXT2CYPHER_PROMPT


def test_query_llm_error_returns_503(client, mock_driver):
    """LLM API failure (network/auth) should return 503, not 500."""
    with patch(
        "backend.services.text2cypher.generate_cypher",
        side_effect=Exception("LLM unreachable"),
    ):
        resp = client.post("/api/v1/query", json={"question": "anything"})
    assert resp.status_code == 503
    assert "LLM service error" in resp.json()["detail"]


def test_query_missing_api_key_raises(monkeypatch):
    """generate_cypher raises ValueError when API key is empty."""
    from backend.services import text2cypher
    from backend.settings import Settings

    monkeypatch.setattr(text2cypher, "_client", None)
    monkeypatch.setattr(
        text2cypher, "settings", Settings(openrouter_api_key="")
    )
    try:
        text2cypher.generate_cypher("any question")
        assert False, "Should have raised"
    except ValueError as e:
        assert "OPENROUTER_API_KEY" in str(e)
