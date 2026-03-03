"""EducAgent FastAPI backend."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
from qdrant_client import QdrantClient

from backend.routers import chapters, concepts, graph_router, health, query, retrieve
from backend.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.neo4j = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    app.state.neo4j.verify_connectivity()
    app.state.qdrant = QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        api_key=settings.qdrant_api_key,
    )
    yield
    app.state.neo4j.close()
    app.state.qdrant.close()


app = FastAPI(title="EducAgent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(concepts.router, prefix="/api/v1")
app.include_router(chapters.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")
app.include_router(retrieve.router, prefix="/api/v1")
app.include_router(graph_router.router, prefix="/api/v1")
