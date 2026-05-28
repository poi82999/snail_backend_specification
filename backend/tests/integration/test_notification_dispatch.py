from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from app.core import database
from app.models.accounts import UserDeviceToken
from app.models.enums import NotificationChannel, NotificationStatus, ReservationStatus
from app.models.notification import NotificationDelivery, OwnerNotification
from app.services.notifications.types import SendResult
from app.workers import notifications as notification_worker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.community_factories import (
    create_design,
    create_designer,
    create_owner,
    create_reservation,
    create_shop,
    create_user,
)


class _SessionContext:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *args: object) -> bool:
        return False


class _SessionFactory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def __call__(self) -> AsyncIterator[AsyncSession]:
        return _SessionContext(self._session)


class _FakeRedis:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, object]] = []

    async def enqueue_job(self, name: str, delivery_id: str, **kwargs: object) -> None:
        self.calls.append((name, delivery_id, kwargs.get("_defer_by")))


@pytest.fixture
def worker_sessionmaker(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(database, "_sessionmaker", _SessionFactory(db_session))


async def _owner_delivery(db_session: AsyncSession) -> NotificationDelivery:
    owner = await create_owner(db_session)
    delivery = NotificationDelivery(
        id=uuid4(),
        recipient_owner_id=owner.id,
        channel=NotificationChannel.KAKAO_ALIMTALK,
        status=NotificationStatus.QUEUED,
        template_code="RESERVATION_REQUESTED",
        payload={
            "provider_template_code": "SNAIL_RESV_REQUESTED_V1",
            "variables": {"#{shop_name}": "샵"},
            "content": "새 예약",
        },
    )
    db_session.add(delivery)
    await db_session.flush()
    return delivery


@pytest.mark.asyncio
async def test_send_notification_transitions_queued_to_sent(
    db_session: AsyncSession,
    worker_sessionmaker: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delivery = await _owner_delivery(db_session)

    async def fake_send_alimtalk(**_: object) -> SendResult:
        return SendResult(status="sent", provider_message_id="kakao-1")

    monkeypatch.setattr(notification_worker.kakao_alimtalk, "send_alimtalk", fake_send_alimtalk)

    await notification_worker.send_notification({"redis": _FakeRedis()}, str(delivery.id))

    assert delivery.status == NotificationStatus.SENT
    assert delivery.provider_message_id == "kakao-1"
    assert delivery.attempts == 1


@pytest.mark.asyncio
async def test_send_notification_transitions_retryable_failure_to_retrying_then_failed(
    db_session: AsyncSession,
    worker_sessionmaker: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delivery = await _owner_delivery(db_session)
    fake_redis = _FakeRedis()

    async def fake_send_alimtalk(**_: object) -> SendResult:
        return SendResult(status="failed", reason="http_500", retryable=True)

    monkeypatch.setattr(notification_worker.kakao_alimtalk, "send_alimtalk", fake_send_alimtalk)

    await notification_worker.send_notification({"redis": fake_redis}, str(delivery.id))

    assert delivery.status == NotificationStatus.RETRYING
    assert delivery.attempts == 1
    assert delivery.next_retry_at is not None
    assert fake_redis.calls[0][0] == "send_notification"

    await notification_worker.send_notification({"redis": fake_redis}, str(delivery.id))

    assert delivery.status == NotificationStatus.FAILED
    assert delivery.attempts == 2
    assert delivery.failed_reason == "http_500"


@pytest.mark.asyncio
async def test_dispatch_notification_creates_inbox_and_queued_delivery(
    db_session: AsyncSession,
    worker_sessionmaker: None,
) -> None:
    owner = await create_owner(db_session)
    user = await create_user(db_session)
    shop = await create_shop(db_session, owner)
    designer = await create_designer(db_session, shop)
    design = await create_design(db_session, shop)
    reservation = await create_reservation(
        db_session,
        user,
        shop,
        design,
        designer,
        status=ReservationStatus.PENDING,
    )

    await notification_worker.dispatch_notification(
        {"redis": _FakeRedis()},
        "REQUESTED",
        str(reservation.id),
    )

    deliveries = list((await db_session.scalars(select(NotificationDelivery))).all())
    notifications = list((await db_session.scalars(select(OwnerNotification))).all())
    assert len(deliveries) == 1
    assert deliveries[0].status == NotificationStatus.QUEUED
    assert deliveries[0].channel == NotificationChannel.KAKAO_ALIMTALK
    assert len(notifications) == 1


@pytest.mark.asyncio
async def test_dispatch_notification_user_event_requires_active_token(
    db_session: AsyncSession,
    worker_sessionmaker: None,
) -> None:
    owner = await create_owner(db_session)
    user = await create_user(db_session)
    shop = await create_shop(db_session, owner)
    designer = await create_designer(db_session, shop)
    design = await create_design(db_session, shop)
    reservation = await create_reservation(
        db_session,
        user,
        shop,
        design,
        designer,
        status=ReservationStatus.CONFIRMED,
    )
    db_session.add(UserDeviceToken(id=uuid4(), user_id=user.id, token="token-1"))
    await db_session.flush()

    await notification_worker.dispatch_notification(
        {"redis": _FakeRedis()},
        "CONFIRMED",
        str(reservation.id),
    )

    delivery = await db_session.scalar(select(NotificationDelivery))
    assert delivery is not None
    assert delivery.channel == NotificationChannel.APNS
    assert delivery.status == NotificationStatus.QUEUED
