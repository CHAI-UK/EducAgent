"""Tests for graph/eci_neo4j_importer.py — run with mock Neo4j driver."""
import json
import types
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

GRAPH_JSON = Path("src/graph/output/eci_graph.json")


@pytest.fixture
def graph_data():
    with open(GRAPH_JSON) as f:
        return json.load(f)


@pytest.fixture
def mock_driver():
    driver = MagicMock()
    driver.execute_query = MagicMock(return_value=([], None, None))
    return driver


def test_graph_json_exists():
    assert GRAPH_JSON.exists(), "eci_graph.json must exist before import"


def test_graph_json_node_count(graph_data):
    assert len(graph_data["nodes"]) == 189


def test_graph_json_edge_count(graph_data):
    assert len(graph_data["edges"]) == 332


def test_graph_json_node_types(graph_data):
    types_count = {}
    for n in graph_data["nodes"]:
        t = n["type"]
        types_count[t] = types_count.get(t, 0) + 1
    assert types_count["concept"] == 101
    assert types_count["section"] == 79
    assert types_count["category"] == 9


def test_importer_creates_constraints(mock_driver):
    from graph.eci_neo4j_importer import create_schema

    create_schema(mock_driver)
    calls = [str(c) for c in mock_driver.execute_query.call_args_list]
    combined = " ".join(calls)
    assert "Section" in combined
    assert "Concept" in combined
    assert "Category" in combined
    assert "UNIQUE" in combined or "CONSTRAINT" in combined


def test_importer_imports_nodes(mock_driver, graph_data):
    from graph.eci_neo4j_importer import import_nodes

    import_nodes(mock_driver, graph_data["nodes"])
    assert mock_driver.execute_query.call_count >= 189


def test_importer_imports_edges(mock_driver, graph_data):
    from graph.eci_neo4j_importer import import_edges

    import_edges(mock_driver, graph_data["edges"])
    assert mock_driver.execute_query.call_count >= 332


def test_importer_idempotent_uses_merge(mock_driver, graph_data):
    """All import queries must use MERGE (not CREATE) so re-runs are safe."""
    from graph.eci_neo4j_importer import import_nodes

    import_nodes(mock_driver, graph_data["nodes"])
    for c in mock_driver.execute_query.call_args_list:
        query = c.args[0] if c.args else list(c.kwargs.values())[0]
        assert "MERGE" in query, f"Expected MERGE in query: {query}"
        assert "CREATE" not in query.replace("CREATE CONSTRAINT", "").replace(
            "CREATE VECTOR", ""
        ).replace("CREATE FULLTEXT", ""), f"Unexpected CREATE in node import: {query}"
