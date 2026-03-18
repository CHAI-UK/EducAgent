from __future__ import annotations

import uuid

from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy

from .config import AUTH_SECRET, AUTH_TOKEN_LIFETIME_SECONDS
from .db import User
from .manager import get_user_manager
from .schemas import UserCreate, UserRead, UserUpdate

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=AUTH_SECRET, lifetime_seconds=AUTH_TOKEN_LIFETIME_SECONDS)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)


def get_auth_routers():
    return [
        fastapi_users.get_auth_router(auth_backend),
        fastapi_users.get_register_router(UserRead, UserCreate),
        fastapi_users.get_users_router(UserRead, UserUpdate),
    ]
