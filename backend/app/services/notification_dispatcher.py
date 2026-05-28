from enum import StrEnum
from uuid import UUID

import structlog

from app.core.redis import get_arq_pool

logger = structlog.get_logger()


class ReservationEvent(StrEnum):
    REQUESTED = "REQUESTED"
    CONFIRMED = "CONFIRMED"
    PAYMENT_REQUIRED = "PAYMENT_REQUIRED"
    REJECTED = "REJECTED"
    CANCELLED_BY_SHOP = "CANCELLED_BY_SHOP"
    CANCELLED_BY_USER = "CANCELLED_BY_USER"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"


async def enqueue_reservation_event(
    event: ReservationEvent,
    reservation_id: UUID,
    **meta: object,
) -> None:
    try:
        await get_arq_pool().enqueue_job(
            "dispatch_notification",
            event.value,
            str(reservation_id),
            dict(meta),
        )
    except Exception as exc:
        logger.info(
            "notification.enqueue.skipped",
            reservation_event=event.value,
            reservation_id=str(reservation_id),
            reason="enqueue_failed",
            error=str(exc),
        )
