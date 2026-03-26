from __future__ import annotations

from datetime import datetime
import uuid

from fastapi_users import schemas
from pydantic import field_validator


class UserRead(schemas.BaseUser[uuid.UUID]):
    username: str
    created_at: datetime | None = None


class UserCreate(schemas.BaseUserCreate):
    username: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("username")
    @classmethod
    def username_required(cls, value: str) -> str:
        if not value:
            raise ValueError("Username is required")
        return value

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdate(schemas.BaseUserUpdate):
    username: str | None = None
