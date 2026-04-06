from __future__ import annotations

from fastapi import WebSocket, status

from src.services.auth.jwt_utils import decode_access_token


def extract_bearer_token(auth_header: str | None) -> str | None:
    """Extract a bearer token from an Authorization header."""
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1].strip()
    return token or None


def validate_access_token(token: str) -> dict:
    """Decode a JWT and require a subject claim."""
    payload = decode_access_token(token)
    if not payload.get("sub"):
        raise ValueError("Invalid token")
    return payload


def extract_websocket_token(websocket: WebSocket) -> str | None:
    """Read a token from the WS handshake.

    Browsers cannot set custom Authorization headers on native WebSocket
    connections, so we support a query-string fallback used by the frontend.
    """
    return extract_bearer_token(
        websocket.headers.get("Authorization")
    ) or websocket.query_params.get("access_token")


async def require_websocket_auth(websocket: WebSocket) -> dict | None:
    """Validate the WS token before accepting the connection."""
    token = extract_websocket_token(websocket)
    if not token:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Unauthorized",
        )
        return None

    try:
        return validate_access_token(token)
    except ValueError:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Unauthorized",
        )
        return None
