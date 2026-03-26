from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(PROJECT_ROOT / ".env.local", override=True)

MIN_AUTH_SECRET_LENGTH = 32
PLACEHOLDER_AUTH_SECRET = "change-me-in-production"

AUTH_SECRET = os.getenv("AUTH_SECRET", "")
AUTH_ALGORITHM = os.getenv("AUTH_ALGORITHM", "HS256")
AUTH_TOKEN_LIFETIME_SECONDS = int(os.getenv("AUTH_TOKEN_LIFETIME_SECONDS", "3600"))
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://educagent:educagent@localhost:5432/educagent",
)


def validate_auth_settings() -> None:
    """Reject unsafe JWT signing configuration."""
    if not AUTH_SECRET:
        raise ValueError(
            "AUTH_SECRET is required. Set a strong JWT signing secret in .env or the environment."
        )

    if AUTH_SECRET == PLACEHOLDER_AUTH_SECRET:
        raise ValueError(
            "AUTH_SECRET is using the placeholder value. Set a unique JWT signing secret before starting the app."
        )

    if len(AUTH_SECRET) < MIN_AUTH_SECRET_LENGTH:
        raise ValueError(
            f"AUTH_SECRET must be at least {MIN_AUTH_SECRET_LENGTH} characters long."
        )
