from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.models.accounts import User, UserDeviceToken
from app.schemas.users import UserUpdate


async def get_me(session: AsyncSession, user_id: UUID) -> User:
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise AppError("USER_NOT_FOUND", "사용자를 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return user


async def update_me(session: AsyncSession, user_id: UUID, payload: UserUpdate) -> User:
    user = await get_me(session, user_id)

    if payload.nickname is not None and payload.nickname != user.nickname:
        existing = await session.scalar(
            select(User.id).where(User.nickname == payload.nickname, User.id != user_id)
        )
        if existing is not None:
            raise AppError(
                "NICKNAME_TAKEN",
                "이미 사용 중인 닉네임입니다.",
                HTTPStatus.CONFLICT,
            )
        user.nickname = payload.nickname

    if "bio" in payload.model_fields_set:
        user.bio = payload.bio
    if "profile_image_url" in payload.model_fields_set:
        user.profile_image_url = payload.profile_image_url
    if payload.interest_tags is not None:
        user.interest_tags = payload.interest_tags

    await session.flush()
    return user


async def register_device_token(
    session: AsyncSession, user_id: UUID, token: str, platform: str
) -> None:
    await get_me(session, user_id)
    existing = await session.scalar(
        select(UserDeviceToken).where(
            UserDeviceToken.user_id == user_id,
            UserDeviceToken.token == token,
        )
    )
    now = datetime.now(UTC)
    if existing is not None:
        existing.platform = platform
        existing.is_active = True
        existing.last_seen_at = now
    else:
        session.add(
            UserDeviceToken(
                id=uuid4(),
                user_id=user_id,
                token=token,
                platform=platform,
                is_active=True,
                last_seen_at=now,
            )
        )
    await session.flush()


async def unregister_device_token(session: AsyncSession, user_id: UUID, token: str) -> None:
    await get_me(session, user_id)
    existing = await session.scalar(
        select(UserDeviceToken).where(
            UserDeviceToken.user_id == user_id,
            UserDeviceToken.token == token,
        )
    )
    if existing is not None:
        existing.is_active = False
        existing.last_seen_at = datetime.now(UTC)
        await session.flush()
