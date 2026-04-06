from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

from fastapi import status
from fastapi.testclient import TestClient
from jose import jwt
import pytest
from starlette.websockets import WebSocketDisconnect

from src.api.main import app
from src.services.auth.config import AUTH_ALGORITHM, AUTH_SECRET
from src.services.auth.jwt_utils import decode_access_token


def test_protected_endpoint_requires_bearer_token() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/solve/sessions")

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_protected_websocket_requires_token() -> None:
    client = TestClient(app)

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/api/v1/knowledge/test-kb/progress/ws"):
            pass

    assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION


def test_protected_websocket_accepts_query_token() -> None:
    user_id = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    token = jwt.encode(payload, AUTH_SECRET, algorithm=AUTH_ALGORITHM)

    with TestClient(app) as client:
        with client.websocket_connect(
            f"/api/v1/knowledge/test-kb/progress/ws?access_token={token}"
        ):
            pass


def test_decode_access_token_returns_subject_for_valid_token() -> None:
    user_id = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    token = jwt.encode(payload, AUTH_SECRET, algorithm=AUTH_ALGORITHM)

    decoded = decode_access_token(token)

    assert decoded["sub"] == user_id


def test_decode_access_token_raises_on_expired_token() -> None:
    payload = {
        "sub": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    token = jwt.encode(payload, AUTH_SECRET, algorithm=AUTH_ALGORITHM)

    with pytest.raises(ValueError):
        decode_access_token(token)
