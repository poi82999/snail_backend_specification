from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, cast
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_arq_pool
from app.models.accounts import Owner, User, UserDeviceToken
from app.models.design import Design
from app.models.enums import NotificationChannel, NotificationStatus
from app.models.notification import NotificationDelivery
from app.models.reservation import Reservation
from app.models.shop import Designer, Shop
from app.services.notification_dispatcher import ReservationEvent
from app.services.notifications import owner_inbox
from app.services.notifications.templates import (
    NotificationTemplateKey,
    ReservationNotificationPayload,
    payload_from_models,
    render_apns,
    render_kakao,
)

logger = structlog.get_logger()


@dataclass(frozen=True, slots=True)
class NotificationTarget:
    channel: NotificationChannel
    recipient: Literal["user", "owner"]
    template_code: str


EVENT_ROUTING: dict[ReservationEvent, list[NotificationTarget]] = {
    ReservationEvent.REQUESTED: [
        NotificationTarget(
            NotificationChannel.KAKAO_ALIMTALK,
            "owner",
            NotificationTemplateKey.RESERVATION_REQUESTED.value,
        ),
        NotificationTarget(
            NotificationChannel.OWNER_INBOX,
            "owner",
            NotificationTemplateKey.RESERVATION_REQUESTED.value,
        ),
    ],
    ReservationEvent.CONFIRMED: [
        NotificationTarget(
            NotificationChannel.APNS,
            "user",
            NotificationTemplateKey.RESERVATION_CONFIRMED.value,
        )
    ],
    ReservationEvent.PAYMENT_REQUIRED: [
        NotificationTarget(
            NotificationChannel.APNS,
            "user",
            NotificationTemplateKey.RESERVATION_PAYMENT_REQUIRED.value,
        )
    ],
    ReservationEvent.REJECTED: [
        NotificationTarget(
            NotificationChannel.APNS,
            "user",
            NotificationTemplateKey.RESERVATION_REJECTED.value,
        )
    ],
    ReservationEvent.CANCELLED_BY_SHOP: [
        NotificationTarget(
            NotificationChannel.APNS,
            "user",
            NotificationTemplateKey.RESERVATION_CANCELLED_BY_SHOP.value,
        )
    ],
    ReservationEvent.CANCELLED_BY_USER: [
        NotificationTarget(
            NotificationChannel.KAKAO_ALIMTALK,
            "owner",
            NotificationTemplateKey.RESERVATION_CANCELLED_BY_USER.value,
        ),
        NotificationTarget(
            NotificationChannel.OWNER_INBOX,
            "owner",
            NotificationTemplateKey.RESERVATION_CANCELLED_BY_USER.value,
        ),
    ],
    ReservationEvent.COMPLETED: [
        NotificationTarget(
            NotificationChannel.APNS,
            "user",
            NotificationTemplateKey.RESERVATION_COMPLETED.value,
        )
    ],
    ReservationEvent.NO_SHOW: [
        NotificationTarget(
            NotificationChannel.APNS,
            "user",
            NotificationTemplateKey.RESERVATION_NO_SHOW.value,
        )
    ],
}


async def _enqueue_delivery(redis: Any | None, delivery_id: UUID) -> None:
    try:
        pool = redis if redis is not None else get_arq_pool()
        await pool.enqueue_job("send_notification", str(delivery_id))
    except Exception as exc:
        logger.info(
            "notification.enqueue.skipped",
            delivery_id=str(delivery_id),
            reason="enqueue_failed",
            error=exc.__class__.__name__,
        )


async def build_reservation_notification_payload(
    session: AsyncSession,
    reservation: Reservation,
) -> ReservationNotificationPayload | None:
    statement = (
        select(Reservation, Shop, User, Designer, Design)
        .join(Shop, Shop.id == Reservation.shop_id)
        .join(User, User.id == Reservation.user_id)
        .join(Designer, Designer.id == Reservation.designer_id)
        .join(Design, Design.id == Reservation.design_id)
        .where(Reservation.id == reservation.id)
    )
    row = (await session.execute(statement)).one_or_none()
    if row is None:
        logger.info(
            "notification.payload.skipped",
            reservation_id=str(reservation.id),
            reason="reservation_context_not_found",
        )
        return None
    loaded_reservation = cast(Reservation, row[0])
    shop = cast(Shop, row[1])
    user = cast(User, row[2])
    designer = cast(Designer, row[3])
    design = cast(Design, row[4])
    return payload_from_models(loaded_reservation, shop, user, designer, design)


async def send_to_user(
    session: AsyncSession,
    redis: Any | None,
    user_id: UUID,
    template_key: NotificationTemplateKey | str,
    payload: ReservationNotificationPayload,
) -> NotificationDelivery | None:
    tokens = list(
        (
            await session.scalars(
                select(UserDeviceToken).where(
                    UserDeviceToken.user_id == user_id,
                    UserDeviceToken.is_active.is_(True),
                )
            )
        ).all()
    )
    if not tokens:
        logger.info(
            "notification.user.skipped",
            user_id=str(user_id),
            template_key=NotificationTemplateKey(template_key).value,
            reason="no_active_device_token",
        )
        return None

    rendered = render_apns(template_key, payload)
    delivery = NotificationDelivery(
        id=uuid4(),
        recipient_user_id=user_id,
        channel=NotificationChannel.APNS,
        status=NotificationStatus.QUEUED,
        template_code=NotificationTemplateKey(template_key).value,
        payload={
            "title": rendered["title"],
            "body": rendered["body"],
            "data": rendered["data"],
        },
    )
    session.add(delivery)
    await session.flush()
    await _enqueue_delivery(redis, delivery.id)
    return delivery


async def send_to_owner(
    session: AsyncSession,
    redis: Any | None,
    owner_id: UUID,
    template_key: NotificationTemplateKey | str,
    payload: ReservationNotificationPayload,
) -> NotificationDelivery | None:
    owner = await session.get(Owner, owner_id)
    if owner is None:
        logger.info(
            "notification.owner.skipped",
            owner_id=str(owner_id),
            template_key=NotificationTemplateKey(template_key).value,
            reason="owner_not_found",
        )
        return None

    rendered = render_kakao(template_key, payload)
    delivery: NotificationDelivery | None = None
    if owner.phone_number:
        delivery = NotificationDelivery(
            id=uuid4(),
            recipient_owner_id=owner_id,
            channel=NotificationChannel.KAKAO_ALIMTALK,
            status=NotificationStatus.QUEUED,
            template_code=NotificationTemplateKey(template_key).value,
            payload={
                "provider_template_code": rendered["template_code"],
                "variables": rendered["variables"],
                "content": rendered["content"],
            },
        )
        session.add(delivery)
        await session.flush()
    else:
        logger.info(
            "notification.owner.external_skipped",
            owner_id=str(owner_id),
            template_key=NotificationTemplateKey(template_key).value,
            reason="recipient_phone_missing",
        )

    notification = await owner_inbox.create_owner_notification(
        session,
        owner_id=owner_id,
        template_key=template_key,
        payload=payload,
        delivery_id=delivery.id if delivery is not None else None,
    )
    if delivery is not None:
        delivery.owner_notification_id = notification.id
        await session.flush()
        await _enqueue_delivery(redis, delivery.id)
    return delivery
