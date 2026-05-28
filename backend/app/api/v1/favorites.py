from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user_id, db_session
from app.api.v1._idempotency import (
    cached_response,
    request_hash_for,
    required_idempotency_key,
    response_body,
)
from app.models.enums import ActorType
from app.schemas.likes import LikeToggleResponse
from app.services import like_service
from app.utils.idempotency import with_idempotency

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(db_session)]
UserIdDep = Annotated[UUID, Depends(current_user_id)]
IdempotencyKeyDep = Annotated[str, Depends(required_idempotency_key)]


@router.post("/designs/{design_id}/favorite", response_model=LikeToggleResponse)
async def toggle_design_favorite(
    request: Request,
    design_id: UUID,
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
        response = await like_service.toggle_design_favorite(session, design_id, user_id)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response
