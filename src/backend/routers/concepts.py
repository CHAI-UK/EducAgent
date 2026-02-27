"""Concept template retriever endpoints.

All queries use hardcoded Cypher — fastest and most reliable per GraphRAG
best practice (vs. text2Cypher for ad-hoc queries).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from neo4j import Driver

from backend.services.neo4j_client import execute_query, get_driver

router = APIRouter(tags=["concepts"])

# ── Cypher templates ─────────────────────────────────────────────────────────

_PREREQUISITES_Q = """
MATCH (prereq:Concept)-[:PREREQUISITE_OF]->(c:Concept {concept_id: $concept_id})
RETURN prereq.concept_id AS concept_id, prereq.name AS name,
       prereq.chapter AS chapter, prereq.difficulty AS difficulty
ORDER BY prereq.chapter
"""

_NEXT_CONCEPTS_Q = """
MATCH (c:Concept {concept_id: $concept_id})-[:PREREQUISITE_OF]->(next:Concept)
RETURN next.concept_id AS concept_id, next.name AS name,
       next.chapter AS chapter, next.difficulty AS difficulty
ORDER BY next.chapter
"""

_RELATED_Q = """
MATCH (c:Concept {concept_id: $concept_id})-[r:RELATED_TO_SEE_ALSO|COMMONLY_CONFUSED]-(rel:Concept)
RETURN rel.concept_id AS concept_id, rel.name AS name, type(r) AS relation_type
"""

_SECTIONS_Q = """
MATCH (c:Concept {concept_id: $concept_id})-[:COVERED_IN]->(s:Section)
RETURN s.section_id AS section_id, s.label AS label,
       s.chapter AS chapter, s.start_page AS start_page, s.end_page AS end_page
ORDER BY s.chapter, s.depth
"""

_SEARCH_Q = """
CALL db.index.fulltext.queryNodes('concept_fulltext', $search_term, {limit: $limit})
YIELD node, score
RETURN node.concept_id AS concept_id, node.name AS name,
       node.chapter AS chapter, score
ORDER BY score DESC
"""

_GET_CONCEPT_Q = """
MATCH (c:Concept {concept_id: $concept_id})
RETURN c.concept_id AS concept_id, c.name AS name,
       c.chapter AS chapter, c.difficulty AS difficulty,
       c.page_refs AS page_refs, c.misconceptions AS misconceptions
"""


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/concepts/search")
def search_concepts(
    q: str = Query(..., description="Search query for concept name or id"),
    limit: int = Query(10, ge=1, le=50),
    driver: Driver = Depends(get_driver),
) -> list[dict]:
    return execute_query(driver, _SEARCH_Q, search_term=q, limit=limit)


@router.get("/concepts/{concept_id}/prerequisites")
def get_prerequisites(concept_id: str, driver: Driver = Depends(get_driver)) -> list[dict]:
    return execute_query(driver, _PREREQUISITES_Q, concept_id=concept_id)


@router.get("/concepts/{concept_id}/next-concepts")
def get_next_concepts(concept_id: str, driver: Driver = Depends(get_driver)) -> list[dict]:
    return execute_query(driver, _NEXT_CONCEPTS_Q, concept_id=concept_id)


@router.get("/concepts/{concept_id}/related")
def get_related(concept_id: str, driver: Driver = Depends(get_driver)) -> list[dict]:
    return execute_query(driver, _RELATED_Q, concept_id=concept_id)


@router.get("/concepts/{concept_id}/sections")
def get_sections(concept_id: str, driver: Driver = Depends(get_driver)) -> list[dict]:
    return execute_query(driver, _SECTIONS_Q, concept_id=concept_id)


@router.get("/concepts/{concept_id}")
def get_concept(concept_id: str, driver: Driver = Depends(get_driver)) -> dict:
    rows = execute_query(driver, _GET_CONCEPT_Q, concept_id=concept_id)
    if not rows:
        raise HTTPException(status_code=404, detail=f"Concept '{concept_id}' not found")
    return rows[0]
