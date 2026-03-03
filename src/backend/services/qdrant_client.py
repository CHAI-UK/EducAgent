"""Qdrant client FastAPI dependency — mirrors neo4j_client.py pattern."""
from fastapi import Request
from qdrant_client import QdrantClient


def get_qdrant(request: Request) -> QdrantClient:
    """FastAPI dependency — returns the shared QdrantClient from app.state."""
    return request.app.state.qdrant
