"""POST /api/v1/retrieve — semantic passage retrieval.

Distinct from GET /api/v1/concepts/search (fulltext Neo4j search on concept names).
This endpoint returns textbook passages from Qdrant filtered by concept source sections.
DO NOT merge with concepts.py.
"""
from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

from backend.services.neo4j_client import get_driver
from backend.services.qdrant_client import get_qdrant
from backend.services.retrieval import PassageResult, concept_exists, retrieve_passages
from backend.settings import Settings, get_settings

router = APIRouter(tags=["retrieve"])


class RetrieveRequest(BaseModel):
    concept_id: str
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


class RetrieveResponse(BaseModel):
    passages: list[PassageResult]


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(
    body: RetrieveRequest,
    driver: Driver = Depends(get_driver),
    qdrant: QdrantClient = Depends(get_qdrant),
    s: Settings = Depends(get_settings),
) -> RetrieveResponse:
    if not concept_exists(body.concept_id, driver):
        raise HTTPException(
            status_code=404,
            detail=f"Concept '{body.concept_id}' not found",
        )
    passages = retrieve_passages(
        body.concept_id, body.query, driver, qdrant, s, body.top_k
    )
    return RetrieveResponse(passages=passages)
