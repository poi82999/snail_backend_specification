from datetime import date
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user_id, db_session
from app.api.errors import AppError, request_id_from
from app.api.v1._idempotency import (
    cached_response,
    request_hash_for,
    required_idempotency_key,
    response_body,
)
from app.models.enums import ActorType, ReservationStatus
from app.schemas.common import ListResponse, PageMeta
from app.schemas.reservations import (
    AvailableSlot,
    ReservationActionRequest,
    ReservationCreate,
    ReservationMe,
    ReservationStatsMe,
)
from app.services import availability_service, reservation_service, reservation_stats_service
from app.utils.idempotency import with_idempotency
from app.utils.pagination import CursorParams

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(db_session)]
UserIdDep = Annotated[UUID, Depends(current_user_id)]
IdempotencyKeyDep = Annotated[str, Depends(required_idempotency_key)]


def _required_cancel_reason(payload: ReservationActionRequest) -> str:
    if payload.cancel_reason is None:
        raise AppError(
            "CANCEL_REASON_REQUIRED",
            "취소 사유가 필요합니다.",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    return payload.cancel_reason


@router.get(
    "/designs/{design_id}/availability",
    response_model=list[AvailableSlot],
    summary="디자인 예약 가능 시간 조회",
)
async def get_design_availability(
    design_id: UUID,
    session: SessionDep,
    target_date: Annotated[date, Query(alias="date")],
    option_ids: Annotated[list[UUID] | None, Query()] = None,
) -> list[AvailableSlot]:
    extra_duration = await availability_service.extra_duration_for_options(
        session, design_id, option_ids or []
    )
    return await availability_service.calculate_available_slots(
        session, design_id, target_date, extra_duration
    )


@router.post(
    "/reservations",
    response_model=ReservationMe,
    status_code=HTTPStatus.CREATED,
    summary="예약 생성",
)
async def create_reservation(
    request: Request,
    payload: ReservationCreate,
    user_id: UserIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> ReservationMe | Response:
    request_hash = await request_hash_for(request)
    response: ReservationMe
    async with with_idempotency(
        session,
        ActorType.USER,
        user_id,
        idempotency_key,
        request_hash,
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        reservation = await reservation_service.create_reservation(
            session,
            user_id,
            payload,
            idempotency_key,
        )
        response = await reservation_service.to_me(session, reservation)
        idem.set_response(HTTPStatus.CREATED, response_body(response))
    await session.commit()
    return response


@router.get(
    "/me/reservations",
    response_model=ListResponse[ReservationMe],
    summary="내 예약 목록 조회",
)
async def list_my_reservations(
    request: Request,
    user_id: UserIdDep,
    session: SessionDep,
    params: Annotated[CursorParams, Depends()],
    status: ReservationStatus | None = None,
) -> ListResponse[ReservationMe]:
    reservations, next_cursor = await reservation_service.list_user_reservations(
        session,
        user_id,
        status,
        params,
    )
    return ListResponse[ReservationMe](
        data=[
            await reservation_service.to_me(session, reservation) for reservation in reservations
        ],
        page=PageMeta(next_cursor=next_cursor, has_next=next_cursor is not None),
        request_id=request_id_from(request),
    )


@router.get(
    "/me/reservations/{reservation_id}",
    response_model=ReservationMe,
    summary="내 예약 상세 조회",
)
async def get_my_reservation(
    reservation_id: UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> ReservationMe:
    reservation = await reservation_service.get_user_reservation(
        session,
        user_id,
        reservation_id,
    )
    return await reservation_service.to_me(session, reservation)


@router.post(
    "/me/reservations/{reservation_id}/cancel",
    response_model=ReservationMe,
    summary="내 예약 취소",
)
async def cancel_my_reservation(
    request: Request,
    reservation_id: UUID,
    payload: ReservationActionRequest,
    user_id: UserIdDep,
    idempotency_key: IdempotencyKeyDep,
    session: SessionDep,
) -> ReservationMe | Response:
    request_hash = await request_hash_for(request)
    cancel_reason = _required_cancel_reason(payload)
    response: ReservationMe
    async with with_idempotency(
        session,
        ActorType.USER,
        user_id,
        idempotency_key,
        request_hash,
    ) as idem:
        if idem.cached:
            return cached_response(idem)
        reservation = await reservation_service.user_cancel(
            session,
            user_id,
            reservation_id,
            cancel_reason,
        )
        response = await reservation_service.to_me(session, reservation)
        idem.set_response(HTTPStatus.OK, response_body(response))
    await session.commit()
    return response


@router.get(
    "/me/reservation-stats",
    response_model=ReservationStatsMe,
    summary="내 예약 통계 조회",
)
async def get_my_reservation_stats(
    user_id: UserIdDep,
    session: SessionDep,
) -> ReservationStatsMe:
    return await reservation_stats_service.get_my_stats(session, user_id)
