from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from app.core.security import hash_password, issue_access_token
from app.models.accounts import Owner, User, UserDeviceToken
from app.models.design import Design, DesignDesigner
from app.models.enums import (
    ActorType,
    AiAnalysisStatus,
    PaymentMethod,
    VerificationStatus,
    Visibility,
)
from app.models.notification import NotificationDelivery, OwnerNotification
from app.models.shop import Designer, DesignerSchedule, Shop, ShopBusinessHour
from app.services.notifications import router as notification_service
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.community_factories import auth_headers

KST = ZoneInfo("Asia/Seoul")


@dataclass(slots=True)
class _Context:
    user: User
    user_token: str
    owner: Owner
    owner_token: str
    shop: Shop
    designer: Designer
    design: Design
    start_at: datetime


class _FakeRedis:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def enqueue_job(self, name: str, delivery_id: str) -> None:
        self.calls.append((name, delivery_id))


def _future_date() -> date:
    return datetime.now(KST).date() + timedelta(days=7)


def _local_at(target_date: date, value: time) -> datetime:
    return datetime.combine(target_date, value).replace(tzinfo=KST).astimezone(UTC)


async def _context(session: AsyncSession) -> _Context:
    user = User(
        id=uuid4(),
        apple_sub=f"apple-{uuid4().hex}",
        email=f"{uuid4().hex}@example.com",
        nickname=f"user_{uuid4().hex[:10]}",
    )
    owner = Owner(
        id=uuid4(),
        email=f"{uuid4().hex}@example.com",
        password_hash=hash_password("Strong123"),
        representative_name="대표",
        phone_number="010-0000-0000",
        verification_status=VerificationStatus.APPROVED,
    )
    session.add_all([user, owner])
    await session.flush()
    shop = Shop(
        id=uuid4(),
        owner_id=owner.id,
        name="알림 샵",
        address="서울",
        phone_number="02-0000-0000",
        visibility=Visibility.ACTIVE,
        payment_method=PaymentMethod.ON_SITE,
    )
    designer = Designer(id=uuid4(), shop_id=shop.id, name="디자이너", specialty_tags=[])
    design = Design(
        id=uuid4(),
        shop_id=shop.id,
        title="기본 네일",
        base_price=30000,
        duration_minutes=60,
        visibility=Visibility.ACTIVE,
        ai_analysis_status=AiAnalysisStatus.DONE,
    )
    session.add_all([shop, designer, design])
    await session.flush()
    session.add(DesignDesigner(design_id=design.id, designer_id=designer.id))
    target_date = _future_date()
    session.add_all(
        [
            ShopBusinessHour(
                id=uuid4(),
                shop_id=shop.id,
                weekday=target_date.weekday(),
                open_time=time(9, 0),
                close_time=time(18, 0),
                is_closed=False,
            ),
            DesignerSchedule(
                id=uuid4(),
                designer_id=designer.id,
                weekday=target_date.weekday(),
                start_time=time(9, 0),
                end_time=time(18, 0),
                is_day_off=False,
            ),
            UserDeviceToken(id=uuid4(), user_id=user.id, token="token-1"),
        ]
    )
    await session.flush()
    return _Context(
        user=user,
        user_token=issue_access_token(ActorType.USER, user.id),
        owner=owner,
        owner_token=issue_access_token(ActorType.OWNER, owner.id),
        shop=shop,
        designer=designer,
        design=design,
        start_at=_local_at(target_date, time(9, 0)),
    )


@pytest.mark.asyncio
async def test_reservation_create_and_accept_enqueue_notifications(
    api_client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_redis = _FakeRedis()
    monkeypatch.setattr(notification_service, "get_arq_pool", lambda: fake_redis)
    ctx = await _context(db_session)

    create_response = await api_client.post(
        "/api/v1/reservations",
        json={
            "design_id": str(ctx.design.id),
            "designer_id": str(ctx.designer.id),
            "start_at": ctx.start_at.isoformat(),
        },
        headers=auth_headers(ctx.user_token, f"reservation-create-{uuid4()}"),
    )
    assert create_response.status_code == 201, create_response.text

    reservation_id = create_response.json()["id"]
    accept_response = await api_client.post(
        f"/api/v1/shops/me/reservations/{reservation_id}/accept",
        headers=auth_headers(ctx.owner_token, f"reservation-accept-{uuid4()}"),
    )
    assert accept_response.status_code == 200, accept_response.text

    deliveries = list(
        (
            await db_session.scalars(
                select(NotificationDelivery).order_by(NotificationDelivery.created_at)
            )
        ).all()
    )
    inbox = list((await db_session.scalars(select(OwnerNotification))).all())
    assert len(inbox) == 1
    assert [delivery.template_code for delivery in deliveries] == [
        "RESERVATION_REQUESTED",
        "RESERVATION_CONFIRMED",
    ]
    assert fake_redis.calls == [
        ("send_notification", str(deliveries[0].id)),
        ("send_notification", str(deliveries[1].id)),
    ]
