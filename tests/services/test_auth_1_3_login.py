"""Backend tests for Story 1.3: User Login.

Test strategy:
- Middleware exclusion test: verifies /auth/jwt/login is NOT blocked by our auth guard.
  A 422 (no body sent), 400, or 500 (DB unavailable in CI) is acceptable — only 401 is failure.
- Behavior tests: verify correct credentials → 200 + access_token, bad credentials → 400.
  These require a live PostgreSQL connection; they are skipped gracefully when DB is unavailable.

Implementation notes:
- The middleware test uses raise_server_exceptions=False so server-side exceptions (e.g. when
  the DB is unreachable in CI) are returned as 500 responses rather than raised in the test.
- raise_server_exceptions=False interacts with Starlette's BaseHTTPMiddleware task spawning and
  leaves the asyncpg connection pool in a dirty state after the request. A fixture disposes the
  pool via engine.sync_engine.dispose() so subsequent tests get fresh connections.
- DB availability is checked via a direct TCP socket probe to avoid TestClient/asyncio issues.
"""

from __future__ import annotations

import socket
import uuid

from fastapi.testclient import TestClient
import pytest

from src.api.main import app
from src.services.auth.db import engine


@pytest.fixture(autouse=True)
def reset_engine_pool():
    """Dispose the asyncpg connection pool after each test.

    raise_server_exceptions=False (used by the middleware test) leaves the asyncpg
    pool in a dirty state due to Starlette's BaseHTTPMiddleware task-spawning behaviour.
    Disposing the sync engine resets the pool so the next test gets a clean connection.
    """
    yield
    engine.sync_engine.dispose()


# ── Middleware exclusion — always passes in any environment ──────────────────


def test_login_endpoint_not_blocked_by_auth_middleware() -> None:
    """POST /auth/jwt/login must NOT return 401 from our auth guard middleware.

    The endpoint is mounted at /auth/jwt (outside /api/v1) and must be freely
    accessible without a Bearer token. A 422 (missing form body), 400, or 500
    (DB unreachable in CI) is acceptable — only 401 is a failure.
    """
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/auth/jwt/login",
            data={"username": "anyone@example.com", "password": "anypassword"},
        )
    assert response.status_code != 401


# ── Behavior tests — require live PostgreSQL ─────────────────────────────────


def _is_db_available() -> bool:
    """Return True if the PostgreSQL database port is reachable.

    Uses a plain TCP socket check to avoid async event-loop conflicts that arise
    when probing via TestClient (Starlette's BaseHTTPMiddleware spawns new tasks
    for call_next, which confuses asyncpg's task-bound connection pool).
    """
    try:
        with socket.create_connection(("localhost", 5432), timeout=2):
            return True
    except OSError:
        return False


def test_login_bad_credentials_returns_400() -> None:
    """POST /auth/jwt/login with wrong password must return 400 LOGIN_BAD_CREDENTIALS (AC2).

    Requires DB. Skipped gracefully when DB is unavailable.
    """
    if not _is_db_available():
        pytest.skip("PostgreSQL not available — skipping live-DB login test")

    with TestClient(app) as client:
        # Register a user first so the email is known
        reg = client.post(
            "/auth/register",
            json={
                "email": "logintest_bad@example.com",
                "password": "correctpassword123",
                "username": "logintest_bad",
            },
        )
        assert reg.status_code in (201, 400)  # 400 if already registered from a previous run

        # Now attempt login with the wrong password
        response = client.post(
            "/auth/jwt/login",
            data={"username": "logintest_bad@example.com", "password": "wrongpassword!"},
        )
    assert response.status_code == 400
    assert response.json()["detail"] == "LOGIN_BAD_CREDENTIALS"


def test_login_unknown_email_returns_400() -> None:
    """POST /auth/jwt/login with an unregistered email must return 400 (AC2).

    Requires DB. Skipped gracefully when DB is unavailable.
    """
    if not _is_db_available():
        pytest.skip("PostgreSQL not available — skipping live-DB login test")

    with TestClient(app) as client:
        response = client.post(
            "/auth/jwt/login",
            data={"username": "nobody_registered@example.com", "password": "somepassword123"},
        )
    assert response.status_code == 400


def test_login_success_returns_access_token() -> None:
    """POST /auth/jwt/login with valid credentials returns 200 and an access_token (AC1).

    Requires DB. Skipped gracefully when DB is unavailable.
    """
    if not _is_db_available():
        pytest.skip("PostgreSQL not available — skipping live-DB login test")

    # Register a fresh user
    email = "logintest_ok@example.com"
    password = "correctpassword123"
    with TestClient(app) as client:
        reg = client.post(
            "/auth/register",
            json={"email": email, "password": password, "username": "logintest_ok"},
        )
        assert reg.status_code in (201, 400)  # 400 = already exists from a previous run — fine

        # Login with correct credentials
        response = client.post(
            "/auth/jwt/login",
            data={"username": email, "password": password},
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20  # sanity check it's a real token


def test_login_token_allows_access_to_protected_api() -> None:
    """Register + login should produce a JWT accepted by protected /api/v1 routes.

    Requires DB. Skipped gracefully when DB is unavailable.
    """
    if not _is_db_available():
        pytest.skip("PostgreSQL not available — skipping live-DB login test")

    unique = uuid.uuid4().hex[:8]
    email = f"authflow_{unique}@example.com"
    password = "correctpassword123"
    username = f"authflow_{unique}"

    with TestClient(app) as client:
        reg = client.post(
            "/auth/register",
            json={"email": email, "password": password, "username": username},
        )
        assert reg.status_code == 201

        login = client.post(
            "/auth/jwt/login",
            data={"username": email, "password": password},
        )
        assert login.status_code == 200

        token = login.json()["access_token"]
        protected = client.get(
            "/api/v1/solve/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert protected.status_code == 200
