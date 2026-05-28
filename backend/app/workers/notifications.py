from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import database
from app.core.config import get_settings
from app.models.accounts import Owner, UserDeviceToken
from app.models.enums import NotificationChannel, NotificationStatus
from app.models.notification import NotificationDelivery
from app.models.reservation import Reservation
from app.services.notification_dispatcher import ReservationEvent
from app.services.notifications import apns, kakao_alimtalk
from app.services.notifications.router import (
    build_reservation_notification_payload,
    send_to_owner,
    send_to_user,
)
from app.services.notifications.templates import NotificationTemplateKey
from app.services.notifications.types import SendResult
from app.workers.registry import register_job

logger = structlog.get_logger()
MAX_DELIVERY_ATTEMPTS = 2
RETRY_DELAY = timedelta(minutes=5)


def _now() -> datetime:
    return datetime.now(UTC)


def _sessionmaker() -> async_sessionmaker[AsyncSession]:
    if database._sessionmaker is None:
        raise RuntimeError("DB engine not initialized - call init_engine() before workers")
    return database._sessionmaker


def _payload(delivery: NotificationDelivery) -> dict[str, object]:
    return dict(delivery.payload or {})


def _string_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): cast(object, item) for key, item in value.items()}


async def _active_tokens(session: AsyncSession, user_id: UUID) -> list[str]:
    return list(
        (
            await session.scalars(
                select(UserDeviceToken.token).where(
                    UserDeviceToken.user_id == user_id,
                    UserDeviceToken.is_active.is_(True),
                )
            )
        ).all()
    )


async def _send_apns(session: AsyncSession, delivery: NotificationDelivery) -> SendResult:
    if delivery.recipient_user_id is None:
        return SendResult(status="failed", reason="recipient_user_missing", retryable=False)
    payload = _payload(delivery)
    return await apns.send_push(
        session=session,
        device_tokens=await _active_tokens(session, delivery.recipient_user_id),
        title=str(payload.get("title") or "예약 알림"),
        body=str(payload.get("body") or ""),
        data=_string_mapping(payload.get("data")),
    )


async def _send_kakao(session: AsyncSession, delivery: NotificationDelivery) -> SendResult:
    if delivery.recipient_owner_id is None:
        return SendResult(status="failed", reason="recipient_owner_missing", retryable=False)
    owner = await session.get(Owner, delivery.recipient_owner_id)
    if owner is None:
        return SendResult(status="failed", reason="recipient_owner_missing", retryable=False)
    payload = _payload(delivery)
    settings = get_settings()
    return await kakao_alimtalk.send_alimtalk(
        sender_key=settings.KAKAO_SENDER_KEY,
        template_code=str(payload.get("provider_template_code") or ""),
        phone_number=owner.phone_number,
        variables=_string_mapping(payload.get("variables")),
        payload={"content": str(payload.get("content") or "")},
    )


def _apply_result(
    delivery: NotificationDelivery,
    result: SendResult,
    *,
    retry_requested: bool,
) -> None:
    delivery.attempts += 1
    delivery.provider_message_id = result.provider_message_id
    if result.status == "sent":
        delivery.status = NotificationStatus.SENT
        delivery.sent_at = _now()
        delivery.next_retry_at = None
        delivery.failed_reason = None
        return

    delivery.failed_reason = result.reason or result.status
    if retry_requested:
        delivery.status = NotificationStatus.RETRYING
        delivery.next_retry_at = _now() + RETRY_DELAY
        return

    delivery.status = NotificationStatus.FAILED
    delivery.next_retry_at = None


async def _defer_retry(ctx: dict[str, Any], delivery_id: UUID) -> None:
    redis = ctx.get("redis")
    if redis is None:
        logger.info(
            "notification.delivery.retry_skipped",
            delivery_id=str(delivery_id),
            reason="redis_missing",
        )
        return
    await redis.enqueue_job("send_notification", str(delivery_id), _defer_by=RETRY_DELAY)


@register_job
async def send_notification(ctx: dict[str, Any], delivery_id: str) -> None:
    try:
        parsed_delivery_id = UUID(delivery_id)
    except ValueError:
        logger.info("notification.delivery.skipped", delivery_id=delivery_id, reason="invalid_id")
        return

    session_factory = _sessionmaker()
    async with session_factory() as session:
        delivery = await session.get(NotificationDelivery, parsed_delivery_id)
        if delivery is None:
            logger.info(
                "notification.delivery.skipped",
                delivery_id=str(parsed_delivery_id),
                reason="not_found",
            )
            return
        if delivery.status == NotificationStatus.SENT:
            return

        if delivery.channel == NotificationChannel.APNS:
            result = await _send_apns(session, delivery)
        elif delivery.channel == NotificationChannel.KAKAO_ALIMTALK:
            result = await _send_kakao(session, delivery)
        else:
            result = SendResult(
                status="sent", provider_message_id=str(delivery.owner_notification_id)
            )

        retry_requested = result.status == "failed" and result.retryable and delivery.attempts == 0
        _apply_result(delivery, result, retry_requested=retry_requested)
        await session.commit()

    if retry_requested:
        await _defer_retry(ctx, parsed_delivery_id)


@register_job
async def dispatch_notification(
    ctx: dict[str, Any],
    event: str,
    reservation_id: str,
    meta: dict[str, object] | None = None,
) -> None:
    del meta
    try:
        reservation_event = ReservationEvent(event)
        parsed_reservation_id = UUID(reservation_id)
    except ValueError:
        logger.info(
            "notification.dispatch.skipped",
            reservation_event=event,
            reservation_id=reservation_id,
            reason="invalid_payload",
        )
        return

    session_factory = _sessionmaker()
    async with session_factory() as session:
        reservation = await session.get(Reservation, parsed_reservation_id)
        if reservation is None:
            logger.info(
                "notification.dispatch.skipped",
                reservation_event=reservation_event.value,
                reservation_id=str(parsed_reservation_id),
                reason="reservation_not_found",
            )
            return
        payload = await build_reservation_notification_payload(session, reservation)
        if payload is None:
            return
        redis = ctx.get("redis")
        if reservation_event == ReservationEvent.REQUESTED:
            await send_to_owner(
                session,
                redis,
                UUID(str(payload["owner_id"])),
                NotificationTemplateKey.RESERVATION_REQUESTED,
                payload,
            )
        elif reservation_event == ReservationEvent.CONFIRMED:
            await send_to_user(
                session,
                redis,
                reservation.user_id,
                NotificationTemplateKey.RESERVATION_CONFIRMED,
                payload,
            )
        elif reservation_event == ReservationEvent.PAYMENT_REQUIRED:
            await send_to_user(
                session,
                redis,
                reservation.user_id,
                NotificationTemplateKey.RESERVATION_PAYMENT_REQUIRED,
                payload,
            )
        elif reservation_event == ReservationEvent.REJECTED:
            await send_to_user(
                session,
                redis,
                reservation.user_id,
                NotificationTemplateKey.RESERVATION_REJECTED,
                payload,
            )
        elif reservation_event == ReservationEvent.CANCELLED_BY_SHOP:
            await send_to_user(
                session,
                redis,
                reservation.user_id,
                NotificationTemplateKey.RESERVATION_CANCELLED_BY_SHOP,
                payload,
            )
        elif reservation_event == ReservationEvent.CANCELLED_BY_USER:
            await send_to_owner(
                session,
                redis,
                UUID(str(payload["owner_id"])),
                NotificationTemplateKey.RESERVATION_CANCELLED_BY_USER,
                payload,
            )
        elif reservation_event == ReservationEvent.COMPLETED:
            await send_to_user(
                session,
                redis,
                reservation.user_id,
                NotificationTemplateKey.RESERVATION_COMPLETED,
                payload,
            )
        elif reservation_event == ReservationEvent.NO_SHOW:
            await send_to_user(
                session,
                redis,
                reservation.user_id,
                NotificationTemplateKey.RESERVATION_NO_SHOW,
                payload,
            )
        await session.commit()
