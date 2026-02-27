"""Text2Cypher endpoint for ad-hoc agent queries."""
from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver
from pydantic import BaseModel

from backend.services import text2cypher
from backend.services.neo4j_client import execute_query, get_driver

router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    cypher: str
    results: list[dict]


@router.post("/query", response_model=QueryResponse)
def text2cypher_query(
    req: QueryRequest,
    driver: Driver = Depends(get_driver),
) -> QueryResponse:
    try:
        cypher = text2cypher.generate_cypher(req.question)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"LLM service error: {exc}",
        )
    try:
        results = execute_query(driver, cypher)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Generated Cypher failed to execute: {exc}",
        )
    return QueryResponse(question=req.question, cypher=cypher, results=results)
