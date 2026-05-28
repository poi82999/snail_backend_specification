from http import HTTPStatus
from typing import cast
from uuid import UUID, uuid4

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.models.accounts import User
from app.models.community import UserFollow
from app.schemas.follows import FollowToggleResponse
from app.schemas.users import UserPublic
from app.services import user_service
from app.utils.pagination import CursorParams, paginate_query

logger = structlog.get_logger()


async def _follower_count(session: AsyncSession, user_id: UUID) -> int:
    count = await session.scalar(
        select(func.count()).select_from(UserFollow).where(UserFollow.following_id == user_id)
    )
    return int(count or 0)


async def toggle_follow(
    session: AsyncSession,
    follower_id: UUID,
    following_id: UUID,
) -> FollowToggleResponse:
    if follower_id == following_id:
        raise AppError(
            "CANNOT_FOLLOW_SELF",
            "자신을 팔로우할 수 없습니다.",
            HTTPStatus.BAD_REQUEST,
        )

    await user_service.get_me(session, follower_id)
    await user_service.get_me(session, following_id)

    existing = await session.scalar(
        select(UserFollow).where(
            UserFollow.follower_id == follower_id,
            UserFollow.following_id == following_id,
        )
    )
    if existing is None:
        session.add(UserFollow(id=uuid4(), follower_id=follower_id, following_id=following_id))
        followed = True
    else:
        await session.delete(existing)
        followed = False

    await session.flush()
    follower_count = await _follower_count(session, following_id)
    logger.info(
        "follow.toggled",
        follower_id=str(follower_id),
        following_id=str(following_id),
        followed=followed,
    )
    return FollowToggleResponse(followed=followed, follower_count=follower_count)


async def _follow_users(
    session: AsyncSession,
    follows: list[UserFollow],
    user_id_attr: str,
) -> list[UserPublic]:
    user_ids = [cast(UUID, getattr(follow, user_id_attr)) for follow in follows]
    if not user_ids:
        return []
    users = await session.scalars(
        select(User).where(User.id.in_(user_ids), User.is_active.is_(True))
    )
    users_by_id = {user.id: user for user in users}
    return [
        UserPublic.model_validate(users_by_id[user_id])
        for user_id in user_ids
        if user_id in users_by_id
    ]


async def list_followers(
    session: AsyncSession,
    user_id: UUID,
    cursor: CursorParams,
) -> tuple[list[UserPublic], str | None]:
    await user_service.get_me(session, user_id)
    statement = (
        select(UserFollow)
        .join(User, UserFollow.follower_id == User.id)
        .where(UserFollow.following_id == user_id, User.is_active.is_(True))
    )
    follows, next_cursor = await paginate_query(session, statement, UserFollow, cursor)
    return await _follow_users(session, follows, "follower_id"), next_cursor


async def list_following(
    session: AsyncSession,
    user_id: UUID,
    cursor: CursorParams,
) -> tuple[list[UserPublic], str | None]:
    await user_service.get_me(session, user_id)
    statement = (
        select(UserFollow)
        .join(User, UserFollow.following_id == User.id)
        .where(UserFollow.follower_id == user_id, User.is_active.is_(True))
    )
    follows, next_cursor = await paginate_query(session, statement, UserFollow, cursor)
    return await _follow_users(session, follows, "following_id"), next_cursor
