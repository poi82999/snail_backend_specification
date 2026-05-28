from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_actor, current_user_id, db_session, optional_user_id
from app.api.errors import AppError
from app.api.v1._idempotency import (
    cached_response,
    request_hash_for,
    required_idempotency_key,
    response_body,
)
from app.models.enums import ActorType
from app.schemas.comments import CommentCreate, CommentPublic
from app.schemas.likes import LikeToggleResponse, SaveToggleResponse
from app.schemas.snails import SnapCreate, SnapFeedQuery, SnapPublic
from app.services import comment_service, like_service, snail_service
from app.utils.idempotency import with_idempotency
from app.utils.pagination import CursorParams, PageResult

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(db_session)]
UserIdDep = Annotated[UUID, Depends(current_user_id)]
ActorDep = Annotated[dict[str, object], Depends(current_actor)]
IdempotencyKeyDep = Annotated[str, Depends(required_idempotency_key)]


OptionalUserIdDep = Annotated[UUID | None, Depends(optional_user_id)]


def _comment_actor(actor: dict[str, object]) -> tuple[ActorType, UUID]:
    try:
        actor_type = ActorType(str(actor["actor_type"]))
        actor_id = UUID(str(actor["sub"]))
    except Exception as exc:
        raise AppError("FORBIDDEN", "권한이 없습니다.", HTTPStatus.FORBIDDEN) from exc
    if actor_type not in {ActorType.USER, ActorType.OWNER}:
        raise AppError("FORBIDDEN", "권한이 없습니다.", HTTPStatus.FORBIDDEN)
    return actor_type, actor_id


@router.post(
    "/snails",
    response_model=SnapPublic,
    status_code=HTTPStatus.CREATED,
    summary="스네일 게시글 생성",
)
async def create_snap(
    request: Request,
    payload: SnapCreate,
    user_id: UserIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> SnapPublic | Response:
    request_hash = await request_hash_for(request)
    response: SnapPublic
    async with with_idempotency(
        session, ActorType.USER, user_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        response = await snail_service.create_snap(session, user_id, payload)
        idem.set_response(HTTPStatus.CREATED, response_body(response))
    await session.commit()
    return response


@router.get(
    "/snails",
    response_model=PageResult[SnapPublic],
    summary="스네일 피드 조회",
)
async def list_snails(
    query: Annotated[SnapFeedQuery, Depends()],
    viewer_user_id: OptionalUserIdDep,
    session: SessionDep,
) -> PageResult[SnapPublic]:
    items, next_cursor = await snail_service.feed(session, viewer_user_id, query)
    return PageResult[SnapPublic](items=items, next_cursor=next_cursor)


@router.get(
    "/snails/{snap_id}",
    response_model=SnapPublic,
    summary="스네일 게시글 상세 조회",
)
async def get_snap(
    request: Request,
    snap_id: UUID,
    viewer_user_id: OptionalUserIdDep,
    session: SessionDep,
) -> SnapPublic:
    viewer_key = snail_service.view_identity(
        viewer_user_id,
        request.client.host if request.client is not None else None,
        request.headers.get("User-Agent"),
    )
    await snail_service.increment_view_count(session, snap_id, viewer_key)
    await session.commit()
    return await snail_service.get_snap_detail(session, viewer_user_id, snap_id)


@router.delete(
    "/snails/{snap_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="스네일 게시글 삭제",
)
async def delete_snap(
    request: Request,
    snap_id: UUID,
    user_id: UserIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> Response:
    request_hash = await request_hash_for(request)
    async with with_idempotency(
        session, ActorType.USER, user_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        await snail_service.soft_delete_snap(session, user_id, snap_id)
        idem.set_response(HTTPStatus.NO_CONTENT, None)
    await session.commit()
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post(
    "/snails/{snap_id}/like",
    response_model=LikeToggleResponse,
    summary="스네일 좋아요 토글",
)
async def toggle_snap_like(
    request: Request,
    snap_id: UUID,
    user_id: UserIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> LikeToggleResponse | Response:
    request_hash = await request_hash_for(request)
    response: LikeToggleResponse
    async with with_idempotency(
        session, ActorType.USER, user_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        response = await like_service.toggle_snap_like(session, snap_id, user_id)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.post(
    "/snails/{snap_id}/save",
    response_model=SaveToggleResponse,
    summary="스네일 저장 토글",
)
async def toggle_snap_save(
    request: Request,
    snap_id: UUID,
    user_id: UserIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> SaveToggleResponse | Response:
    request_hash = await request_hash_for(request)
    response: SaveToggleResponse
    async with with_idempotency(
        session, ActorType.USER, user_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        response = await like_service.toggle_snap_save(session, snap_id, user_id)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.get(
    "/snails/{snap_id}/comments",
    response_model=list[CommentPublic],
    summary="스네일 댓글 목록 조회",
)
async def list_comments(
    snap_id: UUID,
    viewer_user_id: OptionalUserIdDep,
    params: Annotated[CursorParams, Depends()],
    session: SessionDep,
) -> list[CommentPublic]:
    return await comment_service.list_comments(session, snap_id, viewer_user_id, params)


@router.post(
    "/snails/{snap_id}/comments",
    response_model=CommentPublic,
    status_code=HTTPStatus.CREATED,
    summary="스네일 댓글 생성",
)
async def create_comment(
    request: Request,
    snap_id: UUID,
    payload: CommentCreate,
    actor: ActorDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> CommentPublic | Response:
    actor_type, actor_id = _comment_actor(actor)
    request_hash = await request_hash_for(request)
    response: CommentPublic
    async with with_idempotency(
        session, actor_type, actor_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        response = await comment_service.create_comment(
            session,
            actor_type,
            actor_id,
            snap_id,
            payload,
        )
        idem.set_response(HTTPStatus.CREATED, response_body(response))
    await session.commit()
    return response


@router.delete(
    "/comments/{comment_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="댓글 삭제",
)
async def delete_comment(
    request: Request,
    comment_id: UUID,
    actor: ActorDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> Response:
    actor_type, actor_id = _comment_actor(actor)
    request_hash = await request_hash_for(request)
    async with with_idempotency(
        session, actor_type, actor_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        await comment_service.soft_delete_comment(session, actor_type, actor_id, comment_id)
        idem.set_response(HTTPStatus.NO_CONTENT, None)
    await session.commit()
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post(
    "/comments/{comment_id}/like",
    response_model=LikeToggleResponse,
    summary="댓글 좋아요 토글",
)
async def toggle_comment_like(
    request: Request,
    comment_id: UUID,
    user_id: UserIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> LikeToggleResponse | Response:
    request_hash = await request_hash_for(request)
    response: LikeToggleResponse
    async with with_idempotency(
        session, ActorType.USER, user_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        response = await comment_service.toggle_like(session, comment_id, user_id)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response
