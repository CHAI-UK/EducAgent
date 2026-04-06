from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi_users.password import PasswordHelper
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.auth import LearnerProfile, User, current_active_user
from src.services.auth.db import get_async_session
from src.services.auth.schemas import (
    LearnerProfileCreate,
    LearnerProfileRead,
    LearnerProfileUpdate,
    ProfilePasswordUpdate,
    ProfileRead,
    ProfileUpdate,
)

router = APIRouter()

MAX_AVATAR_BYTES = 5 * 1024 * 1024
AVATAR_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
PROJECT_ROOT = Path(__file__).resolve().parents[3]
USER_DATA_DIR = PROJECT_ROOT / "data" / "user"
AVATAR_DIR = USER_DATA_DIR / "profile" / "avatars"
password_helper = PasswordHelper()
CurrentUserDep = Annotated[User, Depends(current_active_user)]
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


def _avatar_url(avatar_path: str | None) -> str | None:
    if not avatar_path:
        return None
    return f"/api/outputs/{avatar_path}"


def _serialize_learner_profile(
    learner_profile: LearnerProfile | None,
) -> LearnerProfileRead | None:
    if learner_profile is None:
        return None

    return LearnerProfileRead(
        id=learner_profile.id,
        background=learner_profile.background,
        role=learner_profile.role,
        prior_knowledge=learner_profile.prior_knowledge,
        expertise_level=learner_profile.expertise_level,
        learning_goal=learner_profile.learning_goal,
        is_skipped=learner_profile.is_skipped,
        created_at=learner_profile.created_at,
        updated_at=learner_profile.updated_at,
    )


def _serialize_profile(user: User) -> ProfileRead:
    return ProfileRead(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        institution=user.institution,
        avatar_url=_avatar_url(user.avatar_path),
        learner_profile=_serialize_learner_profile(user.learner_profile),
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _touch_user(user: User) -> None:
    user.updated_at = datetime.now(timezone.utc)


async def _load_current_user_record(session: AsyncSession, user_id: uuid.UUID) -> User:
    result = await session.execute(
        select(User).options(selectinload(User.learner_profile)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def _apply_learner_profile_values(
    learner_profile: LearnerProfile,
    *,
    background: str | None,
    role: str | None,
    prior_knowledge: list[str],
    expertise_level: str | None,
    learning_goal: str | None,
    is_skipped: bool,
) -> None:
    learner_profile.background = background
    learner_profile.role = role
    learner_profile.prior_knowledge = prior_knowledge
    learner_profile.expertise_level = expertise_level
    learner_profile.learning_goal = learning_goal
    learner_profile.is_skipped = is_skipped
    learner_profile.updated_at = datetime.now(timezone.utc)


def _ensure_learner_profile(user: User) -> LearnerProfile:
    if user.learner_profile is None:
        now = datetime.now(timezone.utc)
        user.learner_profile = LearnerProfile(
            id=uuid.uuid4(),
            user_id=user.id,
            prior_knowledge=[],
            is_skipped=False,
            created_at=now,
            updated_at=now,
        )
    return user.learner_profile


def _profile_requires_reload(user: User) -> bool:
    state = inspect(user)
    return state.persistent and "learner_profile" in state.unloaded


@router.get("/profile", response_model=ProfileRead)
async def get_profile(
    current_user: CurrentUserDep,
    session: AsyncSessionDep,
) -> ProfileRead:
    user = current_user
    if _profile_requires_reload(current_user):
        user = await _load_current_user_record(session, current_user.id)
    return _serialize_profile(user)


@router.patch("/profile", response_model=ProfileRead)
async def update_profile(
    payload: ProfileUpdate,
    current_user: CurrentUserDep,
    session: AsyncSessionDep,
) -> ProfileRead:
    user = await _load_current_user_record(session, current_user.id)

    user.username = payload.username
    user.first_name = payload.first_name
    user.last_name = payload.last_name
    user.institution = payload.institution
    _touch_user(user)

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
    user = await _load_current_user_record(session, current_user.id)
    return _serialize_profile(user)


@router.post("/profile/avatar", response_model=ProfileRead)
async def upload_profile_avatar(
    file: Annotated[UploadFile, File(...)],
    current_user: CurrentUserDep,
    session: AsyncSessionDep,
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
    _touch_user(user)
    await session.commit()
    user = await _load_current_user_record(session, current_user.id)
    return _serialize_profile(user)


@router.post("/profile/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_profile_password(
    payload: ProfilePasswordUpdate,
    current_user: CurrentUserDep,
    session: AsyncSessionDep,
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
    _touch_user(user)
    await session.commit()


@router.put("/profile/learner", response_model=ProfileRead)
async def upsert_learner_profile(
    payload: LearnerProfileCreate,
    current_user: CurrentUserDep,
    session: AsyncSessionDep,
) -> ProfileRead:
    user = await _load_current_user_record(session, current_user.id)
    learner_profile = _ensure_learner_profile(user)
    _apply_learner_profile_values(
        learner_profile,
        background=payload.background,
        role=payload.role,
        prior_knowledge=payload.prior_knowledge,
        expertise_level=payload.expertise_level,
        learning_goal=payload.learning_goal,
        is_skipped=False,
    )

    await session.commit()
    user = await _load_current_user_record(session, current_user.id)
    return _serialize_profile(user)


@router.patch("/profile/learner", response_model=ProfileRead)
async def update_learner_profile(
    payload: LearnerProfileUpdate,
    current_user: CurrentUserDep,
    session: AsyncSessionDep,
) -> ProfileRead:
    user = await _load_current_user_record(session, current_user.id)
    learner_profile = _ensure_learner_profile(user)

    if "background" in payload.model_fields_set:
        learner_profile.background = payload.background
    if "role" in payload.model_fields_set:
        learner_profile.role = payload.role
    if "prior_knowledge" in payload.model_fields_set and payload.prior_knowledge is not None:
        learner_profile.prior_knowledge = payload.prior_knowledge
    if "expertise_level" in payload.model_fields_set:
        learner_profile.expertise_level = payload.expertise_level
    if "learning_goal" in payload.model_fields_set:
        learner_profile.learning_goal = payload.learning_goal

    learner_profile.is_skipped = False
    learner_profile.updated_at = datetime.now(timezone.utc)

    await session.commit()
    user = await _load_current_user_record(session, current_user.id)
    return _serialize_profile(user)


@router.post("/profile/learner/skip", response_model=ProfileRead)
async def skip_learner_profile(
    current_user: CurrentUserDep,
    session: AsyncSessionDep,
) -> ProfileRead:
    user = await _load_current_user_record(session, current_user.id)
    learner_profile = _ensure_learner_profile(user)
    _apply_learner_profile_values(
        learner_profile,
        background=None,
        role=None,
        prior_knowledge=[],
        expertise_level=None,
        learning_goal=None,
        is_skipped=True,
    )

    await session.commit()
    user = await _load_current_user_record(session, current_user.id)
    return _serialize_profile(user)
