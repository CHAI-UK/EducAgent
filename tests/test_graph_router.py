"""Tests for GET /api/v1/graph/ego/{concept_id} and POST /api/v1/explain."""
from unittest.mock import AsyncMock, MagicMock, patch


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ego_row(
    center_id="d_separation",
    center_name="D-Separation",
    chapter=6,
    page_refs=None,
    neighbors=None,
    rels=None,
):
    row = MagicMock()
    row.get = lambda key, default=None: {
        "center_id":        center_id,
        "center_name":      center_name,
        "center_chapter":   chapter,
        "center_page_refs": page_refs or [83],
        "neighbors":        neighbors if neighbors is not None else [],
        "rels":             rels if rels is not None else [],
    }.get(key, default)
    row.__getitem__ = lambda self, key: row.get(key)
    row.data = lambda: {
        "center_id":        center_id,
        "center_name":      center_name,
        "center_chapter":   chapter,
        "center_page_refs": page_refs or [83],
        "neighbors":        neighbors if neighbors is not None else [],
        "rels":             rels if rels is not None else [],
    }
    return row


# ── GET /api/v1/graph/ego/{concept_id} ───────────────────────────────────────

def test_ego_graph_200_center_only(client, mock_driver):
    """T_EGO.1 — isolated concept returns center node only."""
    mock_driver.execute_query.return_value = ([_ego_row()], None, None)
    resp = client.get("/api/v1/graph/ego/d_separation")
    assert resp.status_code == 200
    body = resp.json()
    assert body["center"]["id"] == "d_separation"
    assert len(body["nodes"]) == 1
    assert len(body["edges"]) == 0


def test_ego_graph_200_with_neighbors(client, mock_driver):
    """T_EGO.2 — concept with neighbors returns center + neighbors + edges."""
    mock_driver.execute_query.return_value = ([
        _ego_row(
            neighbors=[{
                "id": "conditional_independence",
                "node_type": "Concept",
                "name": "Conditional Independence",
                "chapter": 2,
                "page_refs": [],
            }],
            rels=[{
                "source": "conditional_independence",
                "target": "d_separation",
                "edge_type": "PREREQUISITE_OF",
            }],
        )
    ], None, None)
    resp = client.get("/api/v1/graph/ego/d_separation")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["nodes"]) == 2
    assert len(body["edges"]) == 1
    assert body["edges"][0]["edge_type"] == "PREREQUISITE_OF"


def test_ego_graph_404_unknown_concept(client, mock_driver):
    """T_EGO.3 — unknown concept returns 404."""
    mock_driver.execute_query.return_value = ([], None, None)
    resp = client.get("/api/v1/graph/ego/nonexistent_concept_xyz")
    assert resp.status_code == 404


def test_ego_graph_null_neighbors_filtered(client, mock_driver):
    """T_EGO.4 — null entries from OPTIONAL MATCH are filtered out."""
    mock_driver.execute_query.return_value = ([
        _ego_row(neighbors=[None], rels=[None])
    ], None, None)
    resp = client.get("/api/v1/graph/ego/d_separation")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["nodes"]) == 1   # center only; null filtered
    assert len(body["edges"]) == 0


# ── POST /api/v1/explain ─────────────────────────────────────────────────────

def test_explain_404_unknown_concept(client, monkeypatch):
    """T_EXP.1 — unknown concept returns 404."""
    monkeypatch.setattr(
        "backend.routers.graph_router.concept_exists",
        lambda cid, drv: False,
    )
    resp = client.post("/api/v1/explain", json={"concept_id": "nonexistent_xyz"})
    assert resp.status_code == 404


def test_explain_streams_sse(client, mock_driver, monkeypatch):
    """T_EXP.2 — response is text/event-stream with data: lines and [DONE]."""
    monkeypatch.setattr(
        "backend.routers.graph_router.concept_exists",
        lambda cid, drv: True,
    )
    # Mock concept name lookup
    name_row = MagicMock()
    name_row.get = lambda key, default=None: {"name": "D-Separation"}.get(key, default)
    name_row.__getitem__ = lambda self, key: name_row.get(key)
    name_row.data = lambda: {"name": "D-Separation"}
    mock_driver.execute_query.return_value = ([name_row], None, None)

    # Mock retrieve_passages
    from backend.services.retrieval import PassageResult
    monkeypatch.setattr(
        "backend.routers.graph_router.retrieve_passages",
        lambda *a, **kw: [PassageResult(
            page_num=83, chapter=6,
            section_heading="6.2 SCMs", content="test content", score=0.9,
        )],
    )

    # Mock AsyncOpenAI streaming
    mock_chunk = MagicMock()
    mock_chunk.choices = [MagicMock(delta=MagicMock(content="Hello world"))]

    async def fake_create(**kwargs):
        async def aiter():
            yield mock_chunk
        mock_stream = MagicMock()
        mock_stream.__aiter__ = lambda self: aiter()
        return mock_stream

    mock_aclient = MagicMock()
    mock_aclient.chat.completions.create = fake_create
    monkeypatch.setattr(
        "backend.routers.graph_router.AsyncOpenAI",
        lambda **kw: mock_aclient,
    )

    resp = client.post("/api/v1/explain", json={"concept_id": "d_separation"})
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    body = resp.text
    assert "data: Hello world" in body
    assert "event: sources" in body
    assert "data: [DONE]" in body

    # Validate sources JSON schema: all required fields present and correctly typed
    import json as _json
    sources_marker = "event: sources\ndata: "
    sources_start = body.index(sources_marker) + len(sources_marker)
    sources_end = body.index("\n\n", sources_start)
    sources = _json.loads(body[sources_start:sources_end])
    assert isinstance(sources, list) and len(sources) == 1
    s = sources[0]
    assert s["page_num"] == 83
    assert s["chapter"] == 6
    assert s["section_heading"] == "6.2 SCMs"
    assert isinstance(s["score"], float)
    assert isinstance(s["snippet"], str) and len(s["snippet"]) <= 250
