from collections.abc import AsyncIterator
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.core.database import get_session
from app.core.security import decode_token


async def db_session() -> AsyncIterator[AsyncSession]:
    async for session in get_session():
        yield session


async def current_actor(authorization: str | None = Header(default=None)) -> dict[str, object]:
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError("UNAUTHORIZED", "로그인이 필요합니다.", HTTPStatus.UNAUTHORIZED)

    try:
        actor = decode_token(authorization.removeprefix("Bearer ").strip())
    except Exception as exc:
        raise AppError("UNAUTHORIZED", "로그인이 필요합니다.", HTTPStatus.UNAUTHORIZED) from exc
    if actor.get("type") != "access":
        raise AppError(
            "INVALID_TOKEN_TYPE",
            "access 토큰이 필요합니다",
            HTTPStatus.UNAUTHORIZED,
        )
    return actor


CurrentActor = Annotated[dict[str, object], Depends(current_actor)]


async def optional_user_id(authorization: str | None = Header(default=None)) -> UUID | None:
    if authorization is None:
        return None
    actor = await current_actor(authorization)
    if actor.get("actor_type") != "user":
        return None
    return UUID(str(actor["sub"]))


async def current_user_id(actor: CurrentActor) -> UUID:
    if actor.get("actor_type") != "user":
        raise AppError("FORBIDDEN", "권한이 없습니다.", HTTPStatus.FORBIDDEN)
    return UUID(str(actor["sub"]))


async def current_owner_id(actor: CurrentActor) -> UUID:
    if actor.get("actor_type") != "owner":
        raise AppError("FORBIDDEN", "권한이 없습니다.", HTTPStatus.FORBIDDEN)
    return UUID(str(actor["sub"]))
