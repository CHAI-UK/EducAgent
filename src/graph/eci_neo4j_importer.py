"""
ECI Knowledge Graph → Neo4j importer.

Reads src/graph/output/eci_graph.json and writes all nodes + edges into Neo4j
using MERGE statements (idempotent — safe to re-run).

Usage:
    python src/graph/eci_neo4j_importer.py

Environment variables (or .env):
    NEO4J_URI      bolt://localhost:7687
    NEO4J_USER     neo4j
    NEO4J_PASSWORD educagent
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from neo4j import GraphDatabase

# ── Constraints & indexes ────────────────────────────────────────────────────

_CONSTRAINTS = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Section)  REQUIRE s.node_id  IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Concept)  REQUIRE c.concept_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (cat:Category) REQUIRE cat.name IS UNIQUE",
]

_INDEXES = [
    # Fulltext index for concept name/id search
    (
        "CREATE FULLTEXT INDEX concept_fulltext IF NOT EXISTS "
        "FOR (c:Concept) ON EACH [c.name, c.concept_id]"
    ),
    # Vector index stub (1536-dim cosine) – no embeddings yet, activated in Epic 2
    (
        "CREATE VECTOR INDEX concept_embedding IF NOT EXISTS "
        "FOR (c:Concept) ON (c.embedding) "
        "OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}"
    ),
]

# ── Node import Cypher ───────────────────────────────────────────────────────

_SECTION_MERGE = """
MERGE (s:Section {node_id: $node_id})
SET s.section_id   = $section_id,
    s.label        = $label,
    s.short_label  = $short_label,
    s.chapter      = $chapter,
    s.depth        = $depth,
    s.start_page   = $start_page,
    s.end_page     = $end_page
"""

_CONCEPT_MERGE = """
MERGE (c:Concept {concept_id: $concept_id})
SET c.name       = $name,
    c.node_id    = $concept_id,
    c.chapter    = $chapter,
    c.page_refs  = $page_refs,
    c.difficulty = $difficulty,
    c.misconceptions = $misconceptions
"""

_CATEGORY_MERGE = """
MERGE (cat:Category {name: $name})
SET cat.label   = $label,
    cat.node_id = $name
"""

# ── Edge import Cypher (one per relationship type) ───────────────────────────

_EDGE_CYPHER: dict[str, str] = {
    "NEXT_IN_SEQUENCE": (
        "MATCH (a:Section {node_id:$s}),(b:Section {node_id:$t}) "
        "MERGE (a)-[:NEXT_IN_SEQUENCE]->(b)"
    ),
    "COVERED_IN": (
        "MATCH (a:Concept {concept_id:$s}),(b:Section {node_id:$t}) "
        "MERGE (a)-[:COVERED_IN]->(b)"
    ),
    "SUBTOPIC_OF": (
        "MATCH (a:Concept {concept_id:$s}),(b:Category {name:$t}) "
        "MERGE (a)-[:SUBTOPIC_OF]->(b)"
    ),
    "RELATED_TO_SEE_ALSO": (
        "MATCH (a:Concept {concept_id:$s}),(b:Concept {concept_id:$t}) "
        "MERGE (a)-[:RELATED_TO_SEE_ALSO]->(b)"
    ),
    "PREREQUISITE_OF": (
        "MATCH (a:Concept {concept_id:$s}),(b:Concept {concept_id:$t}) "
        "MERGE (a)-[:PREREQUISITE_OF]->(b)"
    ),
    "COMMONLY_CONFUSED": (
        "MATCH (a:Concept {concept_id:$s}),(b:Concept {concept_id:$t}) "
        "MERGE (a)-[:COMMONLY_CONFUSED]-(b)"
    ),
    "RELATED_TO_ALIAS": (
        "MATCH (a:Concept {concept_id:$s}),(b:Concept {concept_id:$t}) "
        "MERGE (a)-[:RELATED_TO_ALIAS]->(b)"
    ),
}


# ── Public API ───────────────────────────────────────────────────────────────

def create_schema(driver: Any) -> None:
    """Create uniqueness constraints and indexes (idempotent)."""
    for stmt in _CONSTRAINTS:
        driver.execute_query(stmt)
    for stmt in _INDEXES:
        try:
            driver.execute_query(stmt)
        except Exception:
            # Vector index creation syntax varies across Neo4j versions; non-fatal
            pass


def import_nodes(driver: Any, nodes: list[dict]) -> None:
    """Merge all nodes from the graph JSON node list into Neo4j."""
    for node in nodes:
        node_type = node["type"]
        if node_type == "section":
            driver.execute_query(
                _SECTION_MERGE,
                node_id=node["id"],
                section_id=node.get("section_id", node["id"]),
                label=node.get("label", ""),
                short_label=node.get("short_label", ""),
                chapter=node.get("chapter", 0),
                depth=node.get("depth", 0),
                start_page=node.get("start_page", 0),
                end_page=node.get("end_page", 0),
            )
        elif node_type == "concept":
            driver.execute_query(
                _CONCEPT_MERGE,
                concept_id=node["id"],
                name=node.get("label", node["id"]),
                chapter=node.get("chapter", 0),
                page_refs=node.get("page_refs", []),
                difficulty=node.get("difficulty", 0),
                misconceptions=node.get("misconceptions", []),
            )
        elif node_type == "category":
            driver.execute_query(
                _CATEGORY_MERGE,
                name=node["id"],
                label=node.get("label", node["id"]),
            )


def import_edges(driver: Any, edges: list[dict]) -> None:
    """Merge all edges from the graph JSON edge list into Neo4j."""
    for edge in edges:
        edge_type = edge["edge_type"]
        cypher = _EDGE_CYPHER.get(edge_type)
        if cypher is None:
            print(f"  [WARN] Unknown edge type: {edge_type} — skipped", file=sys.stderr)
            continue
        driver.execute_query(cypher, s=edge["source"], t=edge["target"])


_DEFAULT_JSON = Path(__file__).parent / "output" / "eci_graph.json"


def run_import(driver: Any, json_path: Path = _DEFAULT_JSON) -> None:
    """Full import pipeline: schema → nodes → edges."""
    print(f"Loading {json_path}...")
    with open(json_path) as f:
        data = json.load(f)

    node_count = len(data["nodes"])
    edge_count = len(data["edges"])
    print(f"  {node_count} nodes, {edge_count} edges found.")

    print("Creating schema (constraints + indexes)...")
    create_schema(driver)

    print("Importing nodes...")
    import_nodes(driver, data["nodes"])
    print(f"  {node_count} nodes merged.")

    print("Importing edges...")
    import_edges(driver, data["edges"])
    print(f"  {edge_count} edges merged.")

    print("Done. Import complete (idempotent — safe to re-run).")


# ── CLI entrypoint ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Load .env so credentials work without manual export
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv not installed; rely on shell env vars

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "educagent")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
        print(f"Connected to Neo4j at {uri}")
        run_import(driver)
    finally:
        driver.close()
