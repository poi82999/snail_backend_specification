from datetime import date
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_owner_id, db_session
from app.api.errors import AppError, request_id_from
from app.api.v1._idempotency import (
    cached_response,
    request_hash_for,
    required_idempotency_key,
    response_body,
)
from app.models.enums import ActorType, ReservationStatus
from app.schemas.common import ListResponse, PageMeta
from app.schemas.reservations import ReservationActionRequest, ReservationOwner
from app.services import reservation_service
from app.utils.idempotency import with_idempotency
from app.utils.pagination import CursorParams

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(db_session)]
OwnerIdDep = Annotated[UUID, Depends(current_owner_id)]
IdempotencyKeyDep = Annotated[str, Depends(required_idempotency_key)]


def _required_reject_reason(payload: ReservationActionRequest) -> str:
    if payload.reject_reason is None:
        raise AppError(
            "REJECT_REASON_REQUIRED",
            "거절 사유가 필요합니다.",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    return payload.reject_reason


def _required_cancel_reason(payload: ReservationActionRequest) -> str:
    if payload.cancel_reason is None:
        raise AppError(
            "CANCEL_REASON_REQUIRED",
            "취소 사유가 필요합니다.",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    return payload.cancel_reason


@router.get("/shops/me/reservations", response_model=ListResponse[ReservationOwner])
async def list_shop_reservations(
    request: Request,
    owner_id: OwnerIdDep,
    session: SessionDep,
    params: Annotated[CursorParams, Depends()],
    status: ReservationStatus | None = None,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
) -> ListResponse[ReservationOwner]:
    reservations, next_cursor = await reservation_service.list_owner_reservations(
        session,
        owner_id,
        status,
        from_date,
        to_date,
        params,
    )
    return ListResponse[ReservationOwner](
        data=[
            await reservation_service.to_owner(session, reservation) for reservation in reservations
        ],
        page=PageMeta(next_cursor=next_cursor, has_next=next_cursor is not None),
        request_id=request_id_from(request),
    )


@router.get("/shops/me/reservations/{reservation_id}", response_model=ReservationOwner)
async def get_shop_reservation(
    reservation_id: UUID,
    owner_id: OwnerIdDep,
    session: SessionDep,
) -> ReservationOwner:
    reservation = await reservation_service.get_owner_reservation(
        session,
        owner_id,
        reservation_id,
    )
    return await reservation_service.to_owner(session, reservation)


@router.post("/shops/me/reservations/{reservation_id}/accept", response_model=ReservationOwner)
async def accept_reservation(
    request: Request,
    reservation_id: UUID,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> ReservationOwner | Response:
    request_hash = await request_hash_for(request)
    response: ReservationOwner
    async with with_idempotency(
        session,
        ActorType.OWNER,
        owner_id,
        idempotency_key,
        request_hash,
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        reservation = await reservation_service.owner_accept(session, owner_id, reservation_id)
        response = await reservation_service.to_owner(session, reservation)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.post(
    "/shops/me/reservations/{reservation_id}/confirm-payment",
    response_model=ReservationOwner,
)
async def confirm_reservation_payment(
    request: Request,
    reservation_id: UUID,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> ReservationOwner | Response:
    request_hash = await request_hash_for(request)
    response: ReservationOwner
    async with with_idempotency(
        session,
        ActorType.OWNER,
        owner_id,
        idempotency_key,
        request_hash,
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        reservation = await reservation_service.owner_confirm_payment(
            session,
            owner_id,
            reservation_id,
        )
        response = await reservation_service.to_owner(session, reservation)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.post("/shops/me/reservations/{reservation_id}/reject", response_model=ReservationOwner)
async def reject_reservation(
    request: Request,
    reservation_id: UUID,
    payload: ReservationActionRequest,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> ReservationOwner | Response:
    request_hash = await request_hash_for(request)
    reject_reason = _required_reject_reason(payload)
    response: ReservationOwner
    async with with_idempotency(
        session,
        ActorType.OWNER,
        owner_id,
        idempotency_key,
        request_hash,
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        reservation = await reservation_service.owner_reject(
            session,
            owner_id,
            reservation_id,
            reject_reason,
        )
        response = await reservation_service.to_owner(session, reservation)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.post("/shops/me/reservations/{reservation_id}/cancel", response_model=ReservationOwner)
async def cancel_reservation_by_shop(
    request: Request,
    reservation_id: UUID,
    payload: ReservationActionRequest,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> ReservationOwner | Response:
    request_hash = await request_hash_for(request)
    cancel_reason = _required_cancel_reason(payload)
    response: ReservationOwner
    async with with_idempotency(
        session,
        ActorType.OWNER,
        owner_id,
        idempotency_key,
        request_hash,
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        reservation = await reservation_service.shop_cancel(
            session,
            owner_id,
            reservation_id,
            cancel_reason,
        )
        response = await reservation_service.to_owner(session, reservation)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.post("/shops/me/reservations/{reservation_id}/no-show", response_model=ReservationOwner)
async def mark_no_show(
    request: Request,
    reservation_id: UUID,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> ReservationOwner | Response:
    request_hash = await request_hash_for(request)
    response: ReservationOwner
    async with with_idempotency(
        session,
        ActorType.OWNER,
        owner_id,
        idempotency_key,
        request_hash,
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        reservation = await reservation_service.mark_no_show(session, owner_id, reservation_id)
        response = await reservation_service.to_owner(session, reservation)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.post("/shops/me/reservations/{reservation_id}/complete", response_model=ReservationOwner)
async def complete_reservation(
    request: Request,
    reservation_id: UUID,
    owner_id: OwnerIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> ReservationOwner | Response:
    request_hash = await request_hash_for(request)
    response: ReservationOwner
    async with with_idempotency(
        session,
        ActorType.OWNER,
        owner_id,
        idempotency_key,
        request_hash,
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        reservation = await reservation_service.mark_completed(session, owner_id, reservation_id)
        response = await reservation_service.to_owner(session, reservation)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response
