"""Chapter template retriever endpoints."""
from fastapi import APIRouter, Depends
from neo4j import Driver

from backend.services.neo4j_client import execute_query, get_driver

router = APIRouter(tags=["chapters"])

_CHAPTER_CONCEPTS_Q = """
MATCH (c:Concept {chapter: $chapter})
RETURN c.concept_id AS concept_id, c.name AS name,
       c.difficulty AS difficulty, c.page_refs AS page_refs
ORDER BY c.concept_id
"""


@router.get("/chapters/{chapter}/concepts")
def get_chapter_concepts(chapter: int, driver: Driver = Depends(get_driver)) -> list[dict]:
    return execute_query(driver, _CHAPTER_CONCEPTS_Q, chapter=chapter)
