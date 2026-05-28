from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user_id, db_session
from app.api.errors import request_id_from
from app.api.v1._idempotency import (
    cached_response,
    request_hash_for,
    required_idempotency_key,
    response_body,
)
from app.models.enums import ActorType
from app.schemas.common import ListResponse, PageMeta
from app.schemas.follows import FollowToggleResponse
from app.schemas.users import UserPublic
from app.services import follow_service
from app.utils.idempotency import with_idempotency
from app.utils.pagination import CursorParams

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(db_session)]
UserIdDep = Annotated[UUID, Depends(current_user_id)]
IdempotencyKeyDep = Annotated[str, Depends(required_idempotency_key)]


@router.post(
    "/users/{user_id}/follow",
    response_model=FollowToggleResponse,
    summary="사용자 팔로우 토글",
)
async def toggle_follow(
    request: Request,
    user_id: UUID,
    follower_id: UserIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> FollowToggleResponse | Response:
    request_hash = await request_hash_for(request)
    response: FollowToggleResponse
    async with with_idempotency(
        session, ActorType.USER, follower_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        response = await follow_service.toggle_follow(session, follower_id, user_id)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.get(
    "/users/{user_id}/followers",
    response_model=ListResponse[UserPublic],
    summary="팔로워 목록 조회",
)
async def list_followers(
    request: Request,
    user_id: UUID,
    session: SessionDep,
    params: Annotated[CursorParams, Depends()],
) -> ListResponse[UserPublic]:
    items, next_cursor = await follow_service.list_followers(session, user_id, params)
    return ListResponse[UserPublic](
        data=items,
        page=PageMeta(next_cursor=next_cursor, has_next=next_cursor is not None),
        request_id=request_id_from(request),
    )


@router.get(
    "/users/{user_id}/following",
    response_model=ListResponse[UserPublic],
    summary="팔로잉 목록 조회",
)
async def list_following(
    request: Request,
    user_id: UUID,
    session: SessionDep,
    params: Annotated[CursorParams, Depends()],
) -> ListResponse[UserPublic]:
    items, next_cursor = await follow_service.list_following(session, user_id, params)
    return ListResponse[UserPublic](
        data=items,
        page=PageMeta(next_cursor=next_cursor, has_next=next_cursor is not None),
        request_id=request_id_from(request),
    )
