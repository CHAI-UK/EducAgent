"""Shared test fixtures for EducAgent backend tests."""
from unittest.mock import MagicMock, patch

import pytest
from starlette.testclient import TestClient


@pytest.fixture
def mock_driver():
    """A mock Neo4j driver whose execute_query returns empty results by default."""
    driver = MagicMock()
    driver.execute_query.return_value = ([], None, None)
    driver.verify_connectivity.return_value = None
    return driver


@pytest.fixture
def mock_qdrant():
    """A mock QdrantClient that returns empty query_points results by default."""
    qdrant = MagicMock()
    qdrant.query_points.return_value = MagicMock(points=[])
    return qdrant


@pytest.fixture
def client(mock_driver, mock_qdrant):
    """FastAPI TestClient with Neo4j and Qdrant mocked out (no real DBs needed)."""
    from backend.main import app

    with patch("backend.main.GraphDatabase.driver", return_value=mock_driver):
        with patch("backend.main.QdrantClient", return_value=mock_qdrant):
            with TestClient(app) as c:
                yield c
