"""Graph-anchored passage retrieval service.

Retrieval flow:
  1. Verify concept exists in Neo4j
  2. Query Neo4j COVERED_IN edges → Section start_page / end_page ranges
  3. Embed user query via OpenRouter (text-embedding-3-small)
  4. Qdrant search filtered to those page ranges
     Fallback: unfiltered global search if concept has no COVERED_IN edges
"""
from neo4j import Driver
from openai import OpenAI
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, Range

from backend.services.neo4j_client import execute_query
from backend.settings import Settings

COLLECTION = "eci_passages"

_CONCEPT_EXISTS_Q = """
MATCH (c:Concept {concept_id: $concept_id})
RETURN c.concept_id AS concept_id
"""

# Uses existing start_page / end_page on Section nodes (loaded by eci_neo4j_importer.py)
_PAGE_RANGES_Q = """
MATCH (c:Concept {concept_id: $concept_id})-[:COVERED_IN]->(s:Section)
RETURN s.start_page AS start_page, s.end_page AS end_page
"""


# ── Response model ────────────────────────────────────────────────────────────

class PassageResult(BaseModel):
    page_num: int
    chapter: int
    section_heading: str
    content: str   # full markdown with absolute image paths; ready for frontend
    score: float


# ── Service functions ─────────────────────────────────────────────────────────

def concept_exists(concept_id: str, driver: Driver) -> bool:
    rows = execute_query(driver, _CONCEPT_EXISTS_Q, concept_id=concept_id)
    return bool(rows)


def get_section_page_ranges(
    concept_id: str, driver: Driver
) -> list[tuple[int, int]]:
    """Return [(start_page, end_page), ...] for all sections covering concept."""
    rows = execute_query(driver, _PAGE_RANGES_Q, concept_id=concept_id)
    return [(r["start_page"], r["end_page"]) for r in rows]


def embed_query(query: str, settings: Settings) -> list[float]:
    """Embed a single query string via OpenRouter."""
    client = OpenAI(
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
    )
    resp = client.embeddings.create(
        model="openai/text-embedding-3-small",
        input=[query],
    )
    return resp.data[0].embedding


def retrieve_passages(
    concept_id: str,
    query: str,
    driver: Driver,
    qdrant: QdrantClient,
    settings: Settings,
    top_k: int = 5,
) -> list[PassageResult]:
    """Return top_k passages from Qdrant filtered to concept's source sections.

    Falls back to unfiltered global search when concept has no COVERED_IN edges.

    TODO: follow one RELATED_TO_ALIAS hop to broaden coverage for alias concepts
    (14 such edges exist in the graph).
    """
    page_ranges = get_section_page_ranges(concept_id, driver)
    query_vec = embed_query(query, settings)

    if page_ranges:
        qdrant_filter = Filter(
            should=[
                FieldCondition(key="page_num", range=Range(gte=start, lte=end))
                for start, end in page_ranges
            ]
        )
    else:
        qdrant_filter = None   # unfiltered fallback

    response = qdrant.query_points(
        collection_name=COLLECTION,
        query=query_vec,
        query_filter=qdrant_filter,
        limit=top_k,
    )
    return [
        PassageResult(
            page_num=r.payload["page_num"],
            chapter=r.payload["chapter"],
            section_heading=r.payload.get("section_heading", ""),
            content=r.payload["content"],
            score=r.score,
        )
        for r in response.points
    ]
