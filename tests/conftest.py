from __future__ import annotations

import asyncio
import os

import pytest
from sqlalchemy import text

# Keep tests explicit and deterministic now that auth startup rejects
# missing or placeholder JWT secrets.
os.environ.setdefault("AUTH_SECRET", "test-auth-secret-0123456789abcdef")
os.environ.setdefault(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://educagent:educagent@localhost:5433/educagent_test",
)
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://educagent:educagent@localhost:5433/educagent_test",
    ),
)


def _ensure_auth_test_schema() -> None:
    """Create the auth schema once in the dedicated test database."""
    try:
        from src.services.auth.db import Base, engine

        async def _setup() -> None:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        asyncio.run(_setup())
        engine.sync_engine.dispose()
    except Exception:
        # Tests that truly require the DB already skip when it is unreachable.
        # Keeping import-time setup best-effort avoids breaking non-DB tests.
        return


def _truncate_auth_tables() -> None:
    """Clear persisted auth rows between pytest runs."""
    try:
        from src.services.auth.db import engine

        async def _truncate() -> None:
            async with engine.begin() as conn:
                await conn.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))

        asyncio.run(_truncate())
        engine.sync_engine.dispose()
    except Exception:
        return


_ensure_auth_test_schema()


@pytest.fixture(scope="session", autouse=True)
def clean_auth_test_database():
    _truncate_auth_tables()
    yield
    _truncate_auth_tables()
