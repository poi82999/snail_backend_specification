from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_owner_id, current_user_id, db_session
from app.api.v1._idempotency import (
    cached_response,
    request_hash_for,
    required_idempotency_key,
    response_body,
)
from app.models.enums import ActorType
from app.schemas.reviews import (
    ReviewCreate,
    ReviewPublic,
    ReviewReplyCreate,
    ReviewReplyPublic,
    ReviewUpdate,
)
from app.services import review_service
from app.utils.idempotency import with_idempotency
from app.utils.pagination import CursorParams

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(db_session)]
UserIdDep = Annotated[UUID, Depends(current_user_id)]
OwnerIdDep = Annotated[UUID, Depends(current_owner_id)]
IdempotencyKeyDep = Annotated[str, Depends(required_idempotency_key)]


@router.post(
    "/reservations/{reservation_id}/reviews",
    response_model=ReviewPublic,
    status_code=HTTPStatus.CREATED,
)
async def create_review(
    request: Request,
    reservation_id: UUID,
    payload: ReviewCreate,
    user_id: UserIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> ReviewPublic | Response:
    request_hash = await request_hash_for(request)
    response: ReviewPublic
    async with with_idempotency(
        session, ActorType.USER, user_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        response = await review_service.create_review(session, user_id, reservation_id, payload)
        idem.set_response(HTTPStatus.CREATED, response_body(response))
    await session.commit()
    return response


@router.get("/shops/{shop_id}/reviews", response_model=list[ReviewPublic])
async def list_reviews_for_shop(
    shop_id: UUID,
    params: Annotated[CursorParams, Depends()],
    session: SessionDep,
) -> list[ReviewPublic]:
    return await review_service.list_reviews_for_shop(session, shop_id, params)


@router.get("/designs/{design_id}/reviews", response_model=list[ReviewPublic])
async def list_reviews_for_design(
    design_id: UUID,
    params: Annotated[CursorParams, Depends()],
    session: SessionDep,
) -> list[ReviewPublic]:
    return await review_service.list_reviews_for_design(session, design_id, params)


@router.patch("/reviews/{review_id}", response_model=ReviewPublic)
async def update_review(
    request: Request,
    review_id: UUID,
    payload: ReviewUpdate,
    user_id: UserIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> ReviewPublic | Response:
    request_hash = await request_hash_for(request)
    response: ReviewPublic
    async with with_idempotency(
        session, ActorType.USER, user_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        response = await review_service.update_review(session, user_id, review_id, payload)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.delete("/reviews/{review_id}", status_code=HTTPStatus.NO_CONTENT)
async def delete_review(
    request: Request,
    review_id: UUID,
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
        await review_service.soft_delete_review(session, user_id, review_id)
        idem.set_response(HTTPStatus.NO_CONTENT, None)
    await session.commit()
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post(
    "/reviews/{review_id}/replies",
    response_model=ReviewReplyPublic,
    status_code=HTTPStatus.CREATED,
)
async def create_review_reply(
    request: Request,
    review_id: UUID,
    payload: ReviewReplyCreate,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> ReviewReplyPublic | Response:
    request_hash = await request_hash_for(request)
    response: ReviewReplyPublic
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        response = await review_service.create_review_reply(session, owner_id, review_id, payload)
        idem.set_response(HTTPStatus.CREATED, response_body(response))
    await session.commit()
    return response
