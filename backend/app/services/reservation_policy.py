from datetime import UTC, datetime
from http import HTTPStatus
from typing import Literal

from app.api.errors import AppError
from app.models.enums import PaymentMethod, ReservationStatus

ACTIVE_USER_RESERVATION_STATUSES = {
    ReservationStatus.PENDING,
    ReservationStatus.PAYMENT_PENDING,
    ReservationStatus.CONFIRMED,
}

MAX_ACTIVE_USER_RESERVATIONS = 3

SLOT_LOCK_STATUSES = {
    ReservationStatus.PAYMENT_PENDING,
    ReservationStatus.CONFIRMED,
}

_ALLOWED_TRANSITIONS: dict[
    Literal["user", "owner"],
    dict[ReservationStatus, set[ReservationStatus]],
] = {
    "owner": {
        ReservationStatus.PENDING: {
            ReservationStatus.CONFIRMED,
            ReservationStatus.PAYMENT_PENDING,
            ReservationStatus.REJECTED,
        },
        ReservationStatus.PAYMENT_PENDING: {
            ReservationStatus.CONFIRMED,
            ReservationStatus.REJECTED,
            ReservationStatus.CANCELLED_BY_SHOP,
        },
        ReservationStatus.CONFIRMED: {
            ReservationStatus.CANCELLED_BY_SHOP,
            ReservationStatus.NO_SHOW,
            ReservationStatus.COMPLETED,
        },
    },
    "user": {
        ReservationStatus.PENDING: {ReservationStatus.CANCELLED_BY_USER},
        ReservationStatus.PAYMENT_PENDING: {ReservationStatus.CANCELLED_BY_USER},
        ReservationStatus.CONFIRMED: {ReservationStatus.CANCELLED_BY_USER},
    },
}


def next_status_after_owner_accept(payment_method: PaymentMethod) -> ReservationStatus:
    if payment_method == PaymentMethod.BANK_TRANSFER_GUIDE:
        return ReservationStatus.PAYMENT_PENDING
    return ReservationStatus.CONFIRMED


def normalize_utc(value: datetime) -> datetime:
    aware = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return aware.astimezone(UTC)


def ensure_slot_not_in_past(start_at: datetime) -> None:
    if normalize_utc(start_at) <= datetime.now(UTC):
        raise AppError(
            "SLOT_IN_PAST",
            "이미 지난 시간은 예약할 수 없습니다.",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        )


def can_transition(
    from_status: ReservationStatus,
    to_status: ReservationStatus,
    actor: Literal["user", "owner"],
) -> bool:
    return to_status in _ALLOWED_TRANSITIONS.get(actor, {}).get(from_status, set())


def can_mark_no_show(status: ReservationStatus, start_at: datetime) -> bool:
    if status != ReservationStatus.CONFIRMED:
        return False
    normalized_start = normalize_utc(start_at)
    return (datetime.now(UTC) - normalized_start).total_seconds() >= 30 * 60


def validate_shop_payment_policy(auto_accept: bool, payment_method: PaymentMethod) -> None:
    if auto_accept and payment_method == PaymentMethod.BANK_TRANSFER_GUIDE:
        raise AppError(
            "INVALID_PAYMENT_POLICY",
            "자동 수락은 현장 결제(on_site)에서만 가능합니다.",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        )
