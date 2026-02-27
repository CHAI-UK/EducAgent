from fastapi import APIRouter, Depends
from neo4j import Driver

from backend.services.neo4j_client import execute_query, get_driver

router = APIRouter()

_COUNT_QUERY = """
MATCH (n)
WITH labels(n)[0] AS label, count(n) AS cnt
RETURN label, cnt
UNION ALL
MATCH ()-[r]->()
WITH type(r) AS label, count(r) AS cnt
RETURN label, cnt
"""


@router.get("/health")
def health(driver: Driver = Depends(get_driver)) -> dict:
    try:
        rows = execute_query(driver, _COUNT_QUERY)
        nodes: dict[str, int] = {}
        edges: dict[str, int] = {}
        node_labels = {"Section", "Concept", "Category"}
        for row in rows:
            label = row.get("label") or ""
            cnt = row.get("cnt", 0)
            if label in node_labels:
                nodes[label] = cnt
            else:
                edges[label] = cnt
        return {
            "status": "ok",
            "neo4j": "connected",
            "graph": {"nodes": nodes, "edges": edges},
        }
    except Exception as exc:
        return {"status": "error", "neo4j": str(exc), "graph": {}}
