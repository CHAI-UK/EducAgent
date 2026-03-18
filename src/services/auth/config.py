from __future__ import annotations

import os

AUTH_SECRET = os.getenv("AUTH_SECRET", "change-me-in-production")
AUTH_ALGORITHM = os.getenv("AUTH_ALGORITHM", "HS256")
AUTH_TOKEN_LIFETIME_SECONDS = int(os.getenv("AUTH_TOKEN_LIFETIME_SECONDS", "3600"))
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://educagent:educagent@localhost:5432/educagent",
)
