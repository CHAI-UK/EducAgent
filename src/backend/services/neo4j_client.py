"""Neo4j driver wrapper and FastAPI dependency."""
from typing import Any

from fastapi import Request
from neo4j import Driver


def get_driver(request: Request) -> Driver:
    """FastAPI dependency — returns the shared Neo4j driver from app.state."""
    return request.app.state.neo4j


def execute_query(driver: Driver, query: str, **params: Any) -> list[dict]:
    """Run a Cypher query and return a list of record dicts."""
    records, _, _ = driver.execute_query(query, **params)
    return [r.data() for r in records]
