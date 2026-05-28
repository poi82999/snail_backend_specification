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
from app.schemas.designers import (
    DesignerCreate,
    DesignerPublic,
    DesignerScheduleSet,
    DesignerUpdate,
    TimeOffCreate,
    TimeOffPublic,
)
from app.services import designer_service
from app.utils.idempotency import with_idempotency

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(db_session)]
OwnerIdDep = Annotated[UUID, Depends(current_owner_id)]
IdempotencyKeyDep = Annotated[str, Depends(required_idempotency_key)]


@router.post(
    "/shops/me/designers",
    response_model=DesignerPublic,
    status_code=HTTPStatus.CREATED,
    summary="디자이너 생성",
)
async def create_designer(
    request: Request,
    payload: DesignerCreate,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> DesignerPublic | Response:
    request_hash = await request_hash_for(request)
    response: DesignerPublic
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        designer = await designer_service.create_designer(session, owner_id, payload)
        response = DesignerPublic.model_validate(designer)
        idem.set_response(HTTPStatus.CREATED, response_body(response))
    await session.commit()
    return response


@router.get(
    "/shops/me/designers",
    response_model=list[DesignerPublic],
    summary="내 샵 디자이너 목록 조회",
)
async def list_my_designers(owner_id: OwnerIdDep, session: SessionDep) -> list[DesignerPublic]:
    designers = await designer_service.list_designers_for_my_shop(session, owner_id)
    return [DesignerPublic.model_validate(designer) for designer in designers]


@router.patch(
    "/shops/me/designers/{designer_id}",
    response_model=DesignerPublic,
    summary="디자이너 수정",
)
async def update_designer(
    request: Request,
    designer_id: UUID,
    payload: DesignerUpdate,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> DesignerPublic | Response:
    request_hash = await request_hash_for(request)
    response: DesignerPublic
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        designer = await designer_service.update_designer(session, owner_id, designer_id, payload)
        response = DesignerPublic.model_validate(designer)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.delete(
    "/shops/me/designers/{designer_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="디자이너 삭제",
)
async def delete_designer(
    request: Request,
    designer_id: UUID,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> Response:
    request_hash = await request_hash_for(request)
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        await designer_service.soft_disable_designer(session, owner_id, designer_id)
        idem.set_response(HTTPStatus.NO_CONTENT, None)
    await session.commit()
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.put(
    "/shops/me/designers/{designer_id}/schedule",
    status_code=HTTPStatus.NO_CONTENT,
    summary="디자이너 일정 설정",
)
async def set_designer_schedule(
    request: Request,
    designer_id: UUID,
    payload: DesignerScheduleSet,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> Response:
    request_hash = await request_hash_for(request)
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        await designer_service.set_designer_schedule(session, owner_id, designer_id, payload)
        idem.set_response(HTTPStatus.NO_CONTENT, None)
    await session.commit()
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post(
    "/shops/me/designers/{designer_id}/time-off",
    response_model=TimeOffPublic,
    status_code=HTTPStatus.CREATED,
    summary="디자이너 휴무 추가",
)
async def add_designer_time_off(
    request: Request,
    designer_id: UUID,
    payload: TimeOffCreate,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> TimeOffPublic | Response:
    request_hash = await request_hash_for(request)
    response: TimeOffPublic
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        time_off = await designer_service.add_time_off(session, owner_id, designer_id, payload)
        response = TimeOffPublic.model_validate(time_off)
        idem.set_response(HTTPStatus.CREATED, response_body(response))
    await session.commit()
    return response


@router.delete(
    "/shops/me/designers/{designer_id}/time-off/{time_off_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="디자이너 휴무 삭제",
)
async def delete_designer_time_off(
    request: Request,
    designer_id: UUID,
    time_off_id: UUID,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> Response:
    request_hash = await request_hash_for(request)
    async with with_idempotency(
        session, ActorType.OWNER, owner_id, idempotency_key, request_hash
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        await designer_service.delete_time_off(session, owner_id, designer_id, time_off_id)
        idem.set_response(HTTPStatus.NO_CONTENT, None)
    await session.commit()
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get(
    "/shops/{shop_id}/designers",
    response_model=list[DesignerPublic],
    summary="공개 디자이너 목록 조회",
)
async def list_public_designers(shop_id: UUID, session: SessionDep) -> list[DesignerPublic]:
    designers = await designer_service.list_public_designers_for_shop(session, shop_id)
    return [DesignerPublic.model_validate(designer) for designer in designers]
