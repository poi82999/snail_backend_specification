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
from app.schemas.reports import ReportCreate, ReportPublic
from app.services import report_service
from app.utils.idempotency import with_idempotency

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(db_session)]
UserIdDep = Annotated[UUID, Depends(current_user_id)]
IdempotencyKeyDep = Annotated[str, Depends(required_idempotency_key)]


@router.post(
    "/reports",
    response_model=ReportPublic,
    status_code=HTTPStatus.CREATED,
    summary="신고 생성",
)
async def create_report(
    request: Request,
    payload: ReportCreate,
    user_id: UserIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> ReportPublic | Response:
    request_hash = await request_hash_for(request)
    response: ReportPublic
    async with with_idempotency(
        session, ActorType.USER, user_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        response = await report_service.create_report(session, user_id, payload)
        idem.set_response(HTTPStatus.CREATED, response_body(response))
    await session.commit()
    return response
