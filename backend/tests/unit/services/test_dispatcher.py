from uuid import uuid4

import pytest
from app.models.accounts import UserDeviceToken
from app.models.enums import NotificationChannel, NotificationStatus
from app.models.notification import OwnerNotification
from app.services.notifications import router as notification_service
from app.services.notifications.templates import NotificationTemplateKey
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.community_factories import create_owner, create_user


class _FakeRedis:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def enqueue_job(self, name: str, delivery_id: str) -> None:
        self.calls.append((name, delivery_id))


@pytest.mark.asyncio
async def test_send_to_user_skips_without_active_device_tokens(
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session)
    fake_redis = _FakeRedis()

    delivery = await notification_service.send_to_user(
        db_session,
        fake_redis,
        user.id,
        NotificationTemplateKey.RESERVATION_CONFIRMED,
        {"reservation_id": str(uuid4()), "shop_name": "샵"},
    )

    assert delivery is None
    assert fake_redis.calls == []


@pytest.mark.asyncio
async def test_send_to_user_inserts_apns_delivery_and_enqueues(
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session)
    db_session.add(UserDeviceToken(id=uuid4(), user_id=user.id, token="token-1"))
    await db_session.flush()
    fake_redis = _FakeRedis()

    delivery = await notification_service.send_to_user(
        db_session,
        fake_redis,
        user.id,
        NotificationTemplateKey.RESERVATION_CONFIRMED,
        {"reservation_id": str(uuid4()), "shop_name": "샵"},
    )

    assert delivery is not None
    assert delivery.channel == NotificationChannel.APNS
    assert delivery.status == NotificationStatus.QUEUED
    assert fake_redis.calls == [("send_notification", str(delivery.id))]


@pytest.mark.asyncio
async def test_send_to_owner_creates_kakao_delivery_and_inbox(
    db_session: AsyncSession,
) -> None:
    owner = await create_owner(db_session)
    fake_redis = _FakeRedis()

    delivery = await notification_service.send_to_owner(
        db_session,
        fake_redis,
        owner.id,
        NotificationTemplateKey.RESERVATION_REQUESTED,
        {
            "reservation_id": str(uuid4()),
            "owner_id": str(owner.id),
            "shop_name": "샵",
            "user_name": "민지",
        },
    )

    notifications = list((await db_session.scalars(select(OwnerNotification))).all())
    assert delivery is not None
    assert delivery.channel == NotificationChannel.KAKAO_ALIMTALK
    assert delivery.status == NotificationStatus.QUEUED
    assert len(notifications) == 1
    assert delivery.owner_notification_id == notifications[0].id
    assert fake_redis.calls == [("send_notification", str(delivery.id))]
