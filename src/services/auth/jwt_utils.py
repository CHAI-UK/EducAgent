from __future__ import annotations

from jose import JWTError, jwt

from .config import AUTH_ALGORITHM, AUTH_SECRET


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, AUTH_SECRET, algorithms=[AUTH_ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
