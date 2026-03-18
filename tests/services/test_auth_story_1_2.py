"""Backend tests for Story 1.2: User Registration.

Test strategy:
- Schema tests: pure Pydantic validation, no DB required — always pass in any environment.
- Endpoint middleware test: verifies /auth/register is exempt from the auth guard middleware.
  A 500 response is acceptable when PostgreSQL is not available in the test environment;
  we only assert the request is not rejected with 401.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.services.auth.schemas import UserCreate


# ── Task 1a: Schema validation — password minimum length ─────────────────────


def test_user_create_rejects_password_shorter_than_8_chars() -> None:
    """UserCreate must reject passwords with fewer than 8 characters (AC3)."""
    with pytest.raises(ValidationError, match="at least 8 characters"):
        UserCreate(email="test@example.com", password="short7!", username="testuser")


def test_user_create_rejects_exactly_7_char_password() -> None:
    """7-character password is one below the minimum and must be rejected."""
    with pytest.raises(ValidationError):
        UserCreate(email="test@example.com", password="1234567", username="testuser")


def test_user_create_accepts_exactly_8_char_password() -> None:
    """Exactly 8 characters is the minimum — must be accepted."""
    user = UserCreate(email="test@example.com", password="12345678", username="testuser")
    assert user.email == "test@example.com"
    assert user.username == "testuser"


def test_user_create_accepts_long_password() -> None:
    """Passwords well above the minimum must be accepted."""
    user = UserCreate(
        email="test@example.com",
        password="a_very_secure_password_123!",
        username="testuser",
    )
    assert user.email == "test@example.com"


# ── Task 1c: Auth middleware exclusion ────────────────────────────────────────


def test_register_endpoint_not_blocked_by_auth_middleware() -> None:
    """POST /auth/register must NOT return 401 from our auth guard middleware.

    The endpoint is mounted outside /api/v1 and must be freely accessible
    without a Bearer token.  A 500 (DB unreachable in CI) or 422 (schema
    validation by FastAPI) is acceptable — only 401 is a failure.
    """
    from fastapi.testclient import TestClient

    from src.api.main import app

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepassword123",
            "username": "newuser",
        },
    )
    assert response.status_code != 401