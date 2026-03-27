from __future__ import annotations

from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi_users.password import PasswordHelper
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.auth import User, current_active_user
from src.services.auth.db import get_async_session
from src.services.auth.schemas import ProfilePasswordUpdate, ProfileRead, ProfileUpdate

router = APIRouter()

MAX_AVATAR_BYTES = 5 * 1024 * 1024
AVATAR_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
PROJECT_ROOT = Path(__file__).resolve().parents[3]
USER_DATA_DIR = PROJECT_ROOT / "data" / "user"
AVATAR_DIR = USER_DATA_DIR / "profile" / "avatars"
password_helper = PasswordHelper()


def _avatar_url(avatar_path: str | None) -> str | None:
    if not avatar_path:
        return None
    return f"/api/outputs/{avatar_path}"


def _serialize_profile(user: User) -> ProfileRead:
    return ProfileRead(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        institution=user.institution,
        avatar_url=_avatar_url(user.avatar_path),
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
    )


async def _load_current_user_record(session: AsyncSession, user_id: uuid.UUID) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/profile", response_model=ProfileRead)
async def get_profile(current_user: User = Depends(current_active_user)) -> ProfileRead:
    return _serialize_profile(current_user)


@router.patch("/profile", response_model=ProfileRead)
async def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> ProfileRead:
    user = await _load_current_user_record(session, current_user.id)

    user.username = payload.username
    user.first_name = payload.first_name
    user.last_name = payload.last_name
    user.institution = payload.institution

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        if "username" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username is already taken",
            ) from exc
        raise

    await session.refresh(user)
    return _serialize_profile(user)


@router.post("/profile/avatar", response_model=ProfileRead)
async def upload_profile_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> ProfileRead:
    if file.content_type not in AVATAR_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar must be a JPEG, PNG, WebP, or GIF image",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar file is empty",
        )
    if len(contents) > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar must be 5 MB or smaller",
        )

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        suffix = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
        }[file.content_type]

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)

    user = await _load_current_user_record(session, current_user.id)
    if user.avatar_path:
        existing_avatar = USER_DATA_DIR / user.avatar_path
        if existing_avatar.exists():
            existing_avatar.unlink()

    filename = f"{user.id}_{uuid.uuid4().hex}{suffix}"
    destination = AVATAR_DIR / filename
    destination.write_bytes(contents)

    user.avatar_path = f"profile/avatars/{filename}"
    await session.commit()
    await session.refresh(user)
    return _serialize_profile(user)


@router.post("/profile/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_profile_password(
    payload: ProfilePasswordUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    user = await _load_current_user_record(session, current_user.id)
    password_valid, _ = password_helper.verify_and_update(
        payload.current_password,
        user.hashed_password,
    )
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    user.hashed_password = password_helper.hash(payload.new_password)
    await session.commit()
