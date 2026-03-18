from __future__ import annotations

import uuid

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin

from .config import AUTH_SECRET
from .db import User, get_user_db


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = AUTH_SECRET
    verification_token_secret = AUTH_SECRET

    async def on_after_register(self, user: User, request: Request | None = None) -> None:
        # Hook for auditing/metrics later.
        return None


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
