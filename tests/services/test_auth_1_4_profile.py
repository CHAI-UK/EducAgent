from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import BytesIO
import uuid

from fastapi.testclient import TestClient
from fastapi_users.password import PasswordHelper
from jose import jwt
import pytest
from sqlalchemy.exc import IntegrityError

from src.api.main import app
from src.api.routers import profile as profile_router
from src.services.auth import current_active_user
from src.services.auth.config import AUTH_ALGORITHM, AUTH_SECRET
from src.services.auth.db import User, get_async_session


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode(
        {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
            "aud": "fastapi-users:auth",
        },
        AUTH_SECRET,
        algorithm=AUTH_ALGORITHM,
    )
    return {"Authorization": f"Bearer {token}"}


class FakeAsyncSession:
    def __init__(
        self,
        user: User,
        *,
        fail_on_commit: Exception | None = None,
    ) -> None:
        self.user = user
        self.fail_on_commit = fail_on_commit
        self.commits = 0
        self.rollbacks = 0

    async def get(self, model, user_id):
        if str(user_id) == str(self.user.id):
            return self.user
        return None

    async def commit(self) -> None:
        if self.fail_on_commit is not None:
            raise self.fail_on_commit
        self.commits += 1

    async def refresh(self, user: User) -> None:
        return None

    async def rollback(self) -> None:
        self.rollbacks += 1


@pytest.fixture
def sample_user() -> User:
    helper = PasswordHelper()
    user = User(
        id=uuid.uuid4(),
        email="profile@example.com",
        username="profile-user",
        hashed_password=helper.hash("current-pass-123"),
        is_active=True,
        is_verified=True,
        is_superuser=False,
        first_name="Ada",
        last_name="Lovelace",
        institution="EducAgent University",
        avatar_path=None,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    return user


@pytest.fixture
def clear_profile_overrides():
    original_avatar_dir = profile_router.AVATAR_DIR
    original_user_data_dir = profile_router.USER_DATA_DIR
    yield
    app.dependency_overrides.pop(current_active_user, None)
    app.dependency_overrides.pop(get_async_session, None)
    profile_router.AVATAR_DIR = original_avatar_dir
    profile_router.USER_DATA_DIR = original_user_data_dir


def test_profile_fetch_returns_expected_fields(
    sample_user: User,
    clear_profile_overrides,
) -> None:
    app.dependency_overrides[current_active_user] = lambda: sample_user

    with TestClient(app) as client:
        response = client.get("/api/v1/profile", headers=_auth_headers(sample_user.id))

    assert response.status_code == 200
    assert response.json()["username"] == "profile-user"
    assert response.json()["first_name"] == "Ada"
    assert response.json()["institution"] == "EducAgent University"
    assert response.json()["avatar_url"] is None


def test_profile_patch_updates_allowed_fields(
    sample_user: User,
    clear_profile_overrides,
) -> None:
    session = FakeAsyncSession(sample_user)
    app.dependency_overrides[current_active_user] = lambda: sample_user
    app.dependency_overrides[get_async_session] = lambda: session

    with TestClient(app) as client:
        response = client.patch(
            "/api/v1/profile",
            headers=_auth_headers(sample_user.id),
            json={
                "username": "new-handle",
                "first_name": "Grace",
                "last_name": "Hopper",
                "institution": "Naval Academy",
            },
        )

    assert response.status_code == 200
    assert sample_user.username == "new-handle"
    assert sample_user.first_name == "Grace"
    assert sample_user.last_name == "Hopper"
    assert sample_user.institution == "Naval Academy"
    assert session.commits == 1


def test_profile_patch_rejects_duplicate_username(
    sample_user: User,
    clear_profile_overrides,
) -> None:
    duplicate_error = IntegrityError("UPDATE users", None, Exception("username unique violation"))
    session = FakeAsyncSession(sample_user, fail_on_commit=duplicate_error)
    app.dependency_overrides[current_active_user] = lambda: sample_user
    app.dependency_overrides[get_async_session] = lambda: session

    with TestClient(app) as client:
        response = client.patch(
            "/api/v1/profile",
            headers=_auth_headers(sample_user.id),
            json={
                "username": "taken-name",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "institution": "EducAgent University",
            },
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "Username is already taken"
    assert session.rollbacks == 1


def test_avatar_upload_accepts_valid_image(
    sample_user: User,
    clear_profile_overrides,
    tmp_path,
) -> None:
    profile_router.USER_DATA_DIR = tmp_path / "user"
    profile_router.AVATAR_DIR = profile_router.USER_DATA_DIR / "profile" / "avatars"
    session = FakeAsyncSession(sample_user)
    app.dependency_overrides[current_active_user] = lambda: sample_user
    app.dependency_overrides[get_async_session] = lambda: session

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/profile/avatar",
            headers=_auth_headers(sample_user.id),
            files={"file": ("avatar.png", BytesIO(b"\x89PNG\r\n\x1a\nprofile"), "image/png")},
        )

    assert response.status_code == 200
    assert sample_user.avatar_path is not None
    assert response.json()["avatar_url"].startswith("/api/outputs/profile/avatars/")
    saved_avatar = profile_router.USER_DATA_DIR / sample_user.avatar_path
    assert saved_avatar.exists()


def test_avatar_upload_rejects_invalid_type(
    sample_user: User,
    clear_profile_overrides,
) -> None:
    session = FakeAsyncSession(sample_user)
    app.dependency_overrides[current_active_user] = lambda: sample_user
    app.dependency_overrides[get_async_session] = lambda: session

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/profile/avatar",
            headers=_auth_headers(sample_user.id),
            files={"file": ("avatar.txt", BytesIO(b"not-an-image"), "text/plain")},
        )

    assert response.status_code == 400
    assert "Avatar must be" in response.json()["detail"]


def test_password_change_rejects_wrong_current_password(
    sample_user: User,
    clear_profile_overrides,
) -> None:
    session = FakeAsyncSession(sample_user)
    app.dependency_overrides[current_active_user] = lambda: sample_user
    app.dependency_overrides[get_async_session] = lambda: session

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/profile/password",
            headers=_auth_headers(sample_user.id),
            json={"current_password": "wrong-pass", "new_password": "next-pass-123"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Current password is incorrect"


def test_password_change_accepts_valid_current_password(
    sample_user: User,
    clear_profile_overrides,
) -> None:
    helper = PasswordHelper()
    session = FakeAsyncSession(sample_user)
    app.dependency_overrides[current_active_user] = lambda: sample_user
    app.dependency_overrides[get_async_session] = lambda: session

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/profile/password",
            headers=_auth_headers(sample_user.id),
            json={
                "current_password": "current-pass-123",
                "new_password": "next-pass-123",
            },
        )

    assert response.status_code == 204
    assert helper.verify_and_update("next-pass-123", sample_user.hashed_password)[0] is True
    assert session.commits == 1
