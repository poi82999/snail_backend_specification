from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_owner_id, db_session
from app.api.v1._idempotency import (
    cached_response,
    request_hash_for,
    required_idempotency_key,
    response_body,
)
from app.models.enums import ActorType
from app.schemas.owners import (
    BusinessVerificationMe,
    BusinessVerificationSubmit,
    OwnerMe,
    OwnerUpdate,
)
from app.services import owner_service
from app.utils.idempotency import with_idempotency

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(db_session)]
OwnerIdDep = Annotated[UUID, Depends(current_owner_id)]
IdempotencyKeyDep = Annotated[str, Depends(required_idempotency_key)]


@router.get("/owners/me", response_model=OwnerMe)
async def get_me(owner_id: OwnerIdDep, session: SessionDep) -> OwnerMe:
    owner = await owner_service.get_me(session, owner_id)
    return OwnerMe.model_validate(owner)


@router.patch("/owners/me", response_model=OwnerMe)
async def update_me(
    request: Request,
    payload: OwnerUpdate,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> OwnerMe | Response:
    request_hash = await request_hash_for(request)
    response: OwnerMe
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        owner = await owner_service.update_me(session, owner_id, payload)
        response = OwnerMe.model_validate(owner)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.post(
    "/owners/me/business-verification",
    response_model=BusinessVerificationMe,
    status_code=HTTPStatus.CREATED,
)
async def submit_business_verification(
    request: Request,
    payload: BusinessVerificationSubmit,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> BusinessVerificationMe | Response:
    request_hash = await request_hash_for(request)
    response: BusinessVerificationMe
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        verification = await owner_service.submit_business_verification(session, owner_id, payload)
        response = BusinessVerificationMe.model_validate(verification)
        idem.set_response(HTTPStatus.CREATED, response_body(response))
    await session.commit()
    return response


@router.get("/owners/me/business-verification", response_model=BusinessVerificationMe)
async def get_latest_business_verification(
    owner_id: OwnerIdDep, session: SessionDep
) -> BusinessVerificationMe:
    verification = await owner_service.get_latest_business_verification(session, owner_id)
    return BusinessVerificationMe.model_validate(verification)
