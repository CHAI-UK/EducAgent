"""Graph endpoints — ego-graph view and streaming concept explanation.

Routes (registered with prefix /api/v1):
  GET  /graph/ego/{concept_id}   — 1-hop ego-graph for a concept
  POST /explain                  — SSE stream: AI explanation sourced from Qdrant passages
"""
import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from neo4j import Driver
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

from backend.services.neo4j_client import execute_query, get_driver
from backend.services.qdrant_client import get_qdrant
from backend.services.retrieval import concept_exists, retrieve_passages
from backend.settings import Settings, get_settings

router = APIRouter(tags=["graph"])


# ── Pydantic models ───────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    node_type: str          # "Concept" | "Section" | "Category"
    name: str
    chapter: int | None = None
    page_refs: list[int] = []


class GraphEdge(BaseModel):
    source: str
    target: str
    edge_type: str


class EgoGraphResponse(BaseModel):
    center: GraphNode
    nodes: list[GraphNode]   # all nodes including center
    edges: list[GraphEdge]


class ExplainRequest(BaseModel):
    concept_id: str
    top_k: int = Field(default=5, ge=1, le=10)


# ── Cypher ────────────────────────────────────────────────────────────────────

_EGO_Q = """
MATCH (c:Concept {concept_id: $concept_id})
OPTIONAL MATCH (c)-[r]-(n)
WHERE n:Concept OR n:Section OR n:Category
WITH c, r, n,
     CASE labels(n)[0]
       WHEN 'Concept' THEN n.concept_id
       WHEN 'Section' THEN n.node_id
       ELSE n.name
     END AS n_id
RETURN
  c.concept_id AS center_id,
  c.name       AS center_name,
  c.chapter    AS center_chapter,
  c.page_refs  AS center_page_refs,
  collect(DISTINCT {
    id:        n_id,
    node_type: labels(n)[0],
    name:      COALESCE(n.name, n.label),
    chapter:   n.chapter,
    page_refs: n.page_refs
  }) AS neighbors,
  collect(DISTINCT {
    source:    CASE WHEN startNode(r) = c THEN c.concept_id ELSE n_id END,
    target:    CASE WHEN endNode(r)   = c THEN c.concept_id ELSE n_id END,
    edge_type: type(r)
  }) AS rels
"""

_CONCEPT_NAME_Q = "MATCH (c:Concept {concept_id: $concept_id}) RETURN c.name AS name"


# ── Ego-graph endpoint ────────────────────────────────────────────────────────

@router.get("/graph/ego/{concept_id}", response_model=EgoGraphResponse)
def get_ego_graph(
    concept_id: str,
    driver: Driver = Depends(get_driver),
) -> EgoGraphResponse:
    rows = execute_query(driver, _EGO_Q, concept_id=concept_id)
    if not rows or rows[0].get("center_id") is None:
        raise HTTPException(status_code=404, detail=f"Concept '{concept_id}' not found")

    row = rows[0]
    center = GraphNode(
        id=row["center_id"],
        node_type="Concept",
        name=row["center_name"],
        chapter=row["center_chapter"],
        page_refs=row.get("center_page_refs") or [],
    )
    # OPTIONAL MATCH with no results gives collect([null]) — filter those out
    neighbors = [
        GraphNode(
            id=n["id"],
            node_type=n["node_type"],
            name=n["name"],
            chapter=n.get("chapter"),
            page_refs=n.get("page_refs") or [],
        )
        for n in (row.get("neighbors") or [])
        if n and n.get("id")
    ]
    edges = [
        GraphEdge(source=e["source"], target=e["target"], edge_type=e["edge_type"])
        for e in (row.get("rels") or [])
        if e and e.get("source") and e.get("target")
    ]
    return EgoGraphResponse(center=center, nodes=[center] + neighbors, edges=edges)


# ── Explain endpoint (SSE) ────────────────────────────────────────────────────

_EXPLAIN_PROMPT = """\
You are an expert teacher of causal inference, explaining concepts from
"Elements of Causal Inference" by Peters, Janzing and Schölkopf (2017).

Based only on the following textbook passages, explain the concept "{concept_name}":
- What it is (1–2 sentences)
- Why it matters in causal reasoning (1–2 sentences)
- Any common pitfalls or confusion worth noting

TEXTBOOK PASSAGES:
{passages}

Write in clear prose. Do not use bullet points for the main explanation.
Cite page numbers as (p.N) where relevant. Keep the response under 250 words."""


@router.post("/explain")
async def explain_concept(
    body: ExplainRequest,
    driver: Driver = Depends(get_driver),
    qdrant: QdrantClient = Depends(get_qdrant),
    s: Settings = Depends(get_settings),
) -> StreamingResponse:
    # Use asyncio.to_thread for sync Neo4j/Qdrant calls to avoid blocking
    # the event loop in this async endpoint.
    exists = await asyncio.to_thread(concept_exists, body.concept_id, driver)
    if not exists:
        raise HTTPException(status_code=404, detail=f"Concept '{body.concept_id}' not found")

    name_rows = await asyncio.to_thread(
        execute_query, driver, _CONCEPT_NAME_Q, concept_id=body.concept_id
    )
    concept_name = name_rows[0]["name"] if name_rows else body.concept_id

    passages = await asyncio.to_thread(
        retrieve_passages,
        body.concept_id,
        f"explain {concept_name}",
        driver, qdrant, s,
        top_k=body.top_k,
    )

    passages_text = "\n\n---\n\n".join(
        f"[p.{p.page_num}, {p.section_heading}]\n{p.content[:600]}"
        for p in passages
    )
    prompt = _EXPLAIN_PROMPT.format(concept_name=concept_name, passages=passages_text)

    async def event_stream():
        try:
            aclient = AsyncOpenAI(
                base_url=s.openrouter_base_url,
                api_key=s.openrouter_api_key,
            )
            stream = await aclient.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    yield f"data: {delta}\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"
            return

        # Send source metadata as a named event
        sources_payload = json.dumps([
            {
                "page_num": p.page_num,
                "chapter": p.chapter,
                "section_heading": p.section_heading,
                "score": p.score,
                "snippet": p.content[:250].strip(),
            }
            for p in passages
        ])
        yield f"event: sources\ndata: {sources_payload}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
