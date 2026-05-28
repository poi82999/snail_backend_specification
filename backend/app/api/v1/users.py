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
from app.schemas.users import DeviceTokenRegister, UserMe, UserUpdate
from app.services import user_service
from app.utils.idempotency import with_idempotency

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(db_session)]
UserIdDep = Annotated[UUID, Depends(current_user_id)]
IdempotencyKeyDep = Annotated[str, Depends(required_idempotency_key)]


@router.get("/me", response_model=UserMe)
async def get_me(user_id: UserIdDep, session: SessionDep) -> UserMe:
    user = await user_service.get_me(session, user_id)
    return UserMe.model_validate(user)


@router.patch("/me", response_model=UserMe)
async def update_me(
    request: Request,
    payload: UserUpdate,
    user_id: UserIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> UserMe | Response:
    request_hash = await request_hash_for(request)
    response: UserMe
    async with with_idempotency(
        session, ActorType.USER, user_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        user = await user_service.update_me(session, user_id, payload)
        response = UserMe.model_validate(user)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.post("/me/device-tokens", status_code=HTTPStatus.NO_CONTENT)
async def register_device_token(
    request: Request,
    payload: DeviceTokenRegister,
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
        await user_service.register_device_token(session, user_id, payload.token, payload.platform)
        idem.set_response(HTTPStatus.NO_CONTENT, None)
    await session.commit()
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.delete("/me/device-tokens/{token}", status_code=HTTPStatus.NO_CONTENT)
async def unregister_device_token(
    request: Request,
    token: str,
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
        await user_service.unregister_device_token(session, user_id, token)
        idem.set_response(HTTPStatus.NO_CONTENT, None)
    await session.commit()
    return Response(status_code=HTTPStatus.NO_CONTENT)
