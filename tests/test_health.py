"""Tests for GET /health (covers T2 app scaffold + T5 health endpoint)."""
from unittest.mock import MagicMock


def _node_count_record(label, count):
    rec = MagicMock()
    rec.data.return_value = {"label": label, "cnt": count}  # matches health.py: row.get("cnt")
    return rec


def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_status_ok(client):
    resp = client.get("/health")
    body = resp.json()
    assert body["status"] == "ok"
    assert body["neo4j"] == "connected"


def test_health_has_graph_key(client):
    resp = client.get("/health")
    body = resp.json()
    assert "graph" in body


def test_cors_header_present(client):
    resp = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert resp.headers.get("access-control-allow-origin") is not None


def test_settings_have_required_fields():
    from backend.settings import Settings

    s = Settings(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="test",
    )
    assert s.neo4j_uri == "bolt://localhost:7687"
    assert s.neo4j_user == "neo4j"
    assert s.neo4j_password == "test"
