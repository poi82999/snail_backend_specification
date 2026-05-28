from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from app.api import deps
from app.core.config import Settings
from app.core.security import hash_password, issue_access_token
from app.main import create_app
from app.models.accounts import Owner, User
from app.models.design import Design, DesignDesigner
from app.models.enums import (
    ActorType,
    AiAnalysisStatus,
    PaymentMethod,
    ReservationStatus,
    VerificationStatus,
    Visibility,
)
from app.models.notification import NotificationDelivery, OwnerNotification
from app.models.reservation import IdempotencyKey, Reservation
from app.models.shop import Designer, DesignerSchedule, Shop, ShopBusinessHour
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

KST = ZoneInfo("Asia/Seoul")


@dataclass(slots=True)
class ReservationContext:
    user: User
    user_token: str
    owner: Owner
    owner_token: str
    shop: Shop
    designer: Designer
    design: Design
    target_date: date
    start_at: datetime


def _auth_headers(token: str, idempotency_key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    return headers


def _future_date(days: int = 7) -> date:
    return datetime.now(KST).date() + timedelta(days=days)


def _local_at(target_date: date, value: time) -> datetime:
    return datetime.combine(target_date, value).replace(tzinfo=KST).astimezone(UTC)


async def _create_user(session: AsyncSession) -> tuple[User, str]:
    user = User(
        id=uuid4(),
        apple_sub=f"apple-{uuid4().hex}",
        email=f"{uuid4().hex}@example.com",
        nickname=f"user_{uuid4().hex[:10]}",
    )
    session.add(user)
    await session.flush()
    return user, issue_access_token(ActorType.USER, user.id)


async def _reservation_context(
    session: AsyncSession,
    *,
    payment_method: PaymentMethod = PaymentMethod.ON_SITE,
    auto_accept: bool = False,
    break_time: bool = False,
    days: int = 7,
) -> ReservationContext:
    user, user_token = await _create_user(session)
    owner = Owner(
        id=uuid4(),
        email=f"{uuid4().hex}@example.com",
        password_hash=hash_password("Strong123"),
        representative_name="대표",
        phone_number="010-0000-0000",
        verification_status=VerificationStatus.APPROVED,
    )
    session.add(owner)
    await session.flush()
    shop = Shop(
        id=uuid4(),
        owner_id=owner.id,
        name="예약 샵",
        address="서울",
        phone_number="02-0000-0000",
        visibility=Visibility.ACTIVE,
        payment_method=payment_method,
        auto_accept=auto_accept,
        deposit_amount=10000 if payment_method == PaymentMethod.BANK_TRANSFER_GUIDE else None,
        bank_name="테스트은행" if payment_method == PaymentMethod.BANK_TRANSFER_GUIDE else None,
        bank_account_number="123-456"
        if payment_method == PaymentMethod.BANK_TRANSFER_GUIDE
        else None,
        bank_account_holder="대표" if payment_method == PaymentMethod.BANK_TRANSFER_GUIDE else None,
        reservation_policy="예약 변경은 샵에 문의해주세요.",
    )
    session.add(shop)
    await session.flush()

    designer = Designer(
        id=uuid4(),
        shop_id=shop.id,
        name="디자이너",
        specialty_tags=[],
    )
    design = Design(
        id=uuid4(),
        shop_id=shop.id,
        title="기본 네일",
        base_price=30000,
        duration_minutes=60,
        visibility=Visibility.ACTIVE,
        ai_analysis_status=AiAnalysisStatus.DONE,
    )
    session.add_all([designer, design])
    await session.flush()
    session.add(DesignDesigner(design_id=design.id, designer_id=designer.id))

    target_date = _future_date(days)
    weekday = target_date.weekday()
    session.add_all(
        [
            ShopBusinessHour(
                id=uuid4(),
                shop_id=shop.id,
                weekday=weekday,
                open_time=time(9, 0),
                close_time=time(18, 0),
                is_closed=False,
            ),
            DesignerSchedule(
                id=uuid4(),
                designer_id=designer.id,
                weekday=weekday,
                start_time=time(9, 0),
                end_time=time(18, 0),
                break_start_time=time(12, 0) if break_time else None,
                break_end_time=time(13, 0) if break_time else None,
                is_day_off=False,
            ),
        ]
    )
    await session.flush()
    return ReservationContext(
        user=user,
        user_token=user_token,
        owner=owner,
        owner_token=issue_access_token(ActorType.OWNER, owner.id),
        shop=shop,
        designer=designer,
        design=design,
        target_date=target_date,
        start_at=_local_at(target_date, time(9, 0)),
    )


def _reservation_payload(
    ctx: ReservationContext,
    *,
    designer_id: bool = True,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "design_id": str(ctx.design.id),
        "start_at": ctx.start_at.isoformat(),
    }
    if designer_id:
        payload["designer_id"] = str(ctx.designer.id)
    return payload


async def _create_reservation(
    api_client: AsyncClient,
    ctx: ReservationContext,
    user_token: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, object]:
    response = await api_client.post(
        "/api/v1/reservations",
        json=_reservation_payload(ctx),
        headers=_auth_headers(
            user_token or ctx.user_token,
            idempotency_key or f"reservation-create-{uuid4()}",
        ),
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_on_site_auto_accept_confirms_then_completes(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    ctx = await _reservation_context(db_session, auto_accept=True)
    created = await _create_reservation(api_client, ctx)

    assert created["status"] == "confirmed"

    complete_response = await api_client.post(
        f"/api/v1/shops/me/reservations/{created['id']}/complete",
        headers=_auth_headers(ctx.owner_token, f"reservation-complete-{uuid4()}"),
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_bank_transfer_accept_confirm_payment_then_complete(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    ctx = await _reservation_context(
        db_session,
        payment_method=PaymentMethod.BANK_TRANSFER_GUIDE,
    )
    created = await _create_reservation(api_client, ctx)
    assert created["status"] == "pending"

    accept_response = await api_client.post(
        f"/api/v1/shops/me/reservations/{created['id']}/accept",
        headers=_auth_headers(ctx.owner_token, f"reservation-accept-{uuid4()}"),
    )
    assert accept_response.status_code == 200
    accepted = accept_response.json()
    assert accepted["status"] == "payment_pending"
    assert accepted["deposit_amount_snapshot"] == 10000
    assert accepted["bank_snapshot"]["bank_name"] == "테스트은행"
    assert accepted["user_payment_notified_at"] is not None

    confirm_response = await api_client.post(
        f"/api/v1/shops/me/reservations/{created['id']}/confirm-payment",
        headers=_auth_headers(ctx.owner_token, f"reservation-confirm-payment-{uuid4()}"),
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["status"] == "confirmed"
    assert confirm_response.json()["owner_payment_confirmed_at"] is not None

    complete_response = await api_client.post(
        f"/api/v1/shops/me/reservations/{created['id']}/complete",
        headers=_auth_headers(ctx.owner_token, f"reservation-complete-{uuid4()}"),
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_create_reservation_idempotency_key_replay_returns_same_response(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    ctx = await _reservation_context(db_session, auto_accept=True)
    key = f"reservation-create-{uuid4()}"

    first = await api_client.post(
        "/api/v1/reservations",
        json=_reservation_payload(ctx),
        headers=_auth_headers(ctx.user_token, key),
    )
    second = await api_client.post(
        "/api/v1/reservations",
        json=_reservation_payload(ctx),
        headers=_auth_headers(ctx.user_token, key),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert first.json() == second.json()


@pytest.mark.asyncio
async def test_concurrent_create_same_slot_only_one_succeeds(
    settings_override: Settings,
) -> None:
    engine = create_async_engine(str(settings_override.DATABASE_URL), pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with session_factory() as session:
        ctx = await _reservation_context(session, auto_accept=True)
        other_user, other_user_token = await _create_user(session)
        await session.commit()

    app = create_app()

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[deps.db_session] = override_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        responses = await asyncio.gather(
            client.post(
                "/api/v1/reservations",
                json=_reservation_payload(ctx),
                headers=_auth_headers(ctx.user_token, f"reservation-create-{uuid4()}"),
            ),
            client.post(
                "/api/v1/reservations",
                json=_reservation_payload(ctx),
                headers=_auth_headers(other_user_token, f"reservation-create-{uuid4()}"),
            ),
        )
    app.dependency_overrides.clear()

    assert sorted(response.status_code for response in responses) == [201, 409]
    failed = next(response for response in responses if response.status_code == 409)
    assert failed.json()["error"]["code"] == "SLOT_TAKEN"

    async with session_factory() as session:
        await session.execute(
            delete(IdempotencyKey).where(
                IdempotencyKey.actor_id.in_([ctx.user.id, other_user.id, ctx.owner.id])
            )
        )
        await session.execute(
            delete(NotificationDelivery).where(
                NotificationDelivery.recipient_owner_id == ctx.owner.id
            )
        )
        await session.execute(
            delete(OwnerNotification).where(OwnerNotification.owner_id == ctx.owner.id)
        )
        await session.execute(delete(Reservation).where(Reservation.shop_id == ctx.shop.id))
        await session.execute(
            delete(DesignDesigner).where(DesignDesigner.design_id == ctx.design.id)
        )
        await session.execute(
            delete(DesignerSchedule).where(DesignerSchedule.designer_id == ctx.designer.id)
        )
        await session.execute(
            delete(ShopBusinessHour).where(ShopBusinessHour.shop_id == ctx.shop.id)
        )
        await session.execute(delete(Design).where(Design.id == ctx.design.id))
        await session.execute(delete(Designer).where(Designer.id == ctx.designer.id))
        await session.execute(delete(Shop).where(Shop.id == ctx.shop.id))
        await session.execute(delete(User).where(User.id.in_([ctx.user.id, other_user.id])))
        await session.execute(delete(Owner).where(Owner.id == ctx.owner.id))
        await session.commit()
    await engine.dispose()


@pytest.mark.asyncio
async def test_no_show_requires_start_plus_30_minutes(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    ctx = await _reservation_context(db_session)
    start_at = datetime.now(UTC) - timedelta(minutes=29)
    reservation = Reservation(
        id=uuid4(),
        user_id=ctx.user.id,
        shop_id=ctx.shop.id,
        design_id=ctx.design.id,
        designer_id=ctx.designer.id,
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
        status=ReservationStatus.CONFIRMED,
        total_price=30000,
        payment_method_snapshot=PaymentMethod.ON_SITE,
        idempotency_key=f"reservation-{uuid4()}",
    )
    db_session.add(reservation)
    await db_session.flush()

    early = await api_client.post(
        f"/api/v1/shops/me/reservations/{reservation.id}/no-show",
        headers=_auth_headers(ctx.owner_token, f"reservation-no-show-{uuid4()}"),
    )
    assert early.status_code == 409
    assert early.json()["error"]["code"] == "NO_SHOW_TOO_EARLY"

    reservation.start_at = datetime.now(UTC) - timedelta(minutes=31)
    reservation.end_at = reservation.start_at + timedelta(hours=1)
    await db_session.flush()
    allowed = await api_client.post(
        f"/api/v1/shops/me/reservations/{reservation.id}/no-show",
        headers=_auth_headers(ctx.owner_token, f"reservation-no-show-{uuid4()}"),
    )
    assert allowed.status_code == 200
    assert allowed.json()["status"] == "no_show"


@pytest.mark.asyncio
async def test_design_availability_groups_designer_ids_and_excludes_locked_slot(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    ctx = await _reservation_context(db_session, break_time=True)
    start_at = _local_at(ctx.target_date, time(14, 0))
    db_session.add(
        Reservation(
            id=uuid4(),
            user_id=ctx.user.id,
            shop_id=ctx.shop.id,
            design_id=ctx.design.id,
            designer_id=ctx.designer.id,
            start_at=start_at,
            end_at=start_at + timedelta(hours=1),
            status=ReservationStatus.CONFIRMED,
            total_price=30000,
            payment_method_snapshot=PaymentMethod.ON_SITE,
            idempotency_key=f"reservation-{uuid4()}",
        )
    )
    await db_session.flush()

    response = await api_client.get(
        f"/api/v1/designs/{ctx.design.id}/availability",
        params={"date": ctx.target_date.isoformat()},
    )

    assert response.status_code == 200, response.text
    starts = [
        datetime.fromisoformat(slot["start_at"]).astimezone(KST).strftime("%H:%M")
        for slot in response.json()
    ]
    assert starts == ["09:00", "10:00", "11:00", "13:00", "15:00", "16:00", "17:00"]
    assert response.json()[0]["available_designer_ids"] == [str(ctx.designer.id)]


@pytest.mark.asyncio
async def test_reservation_stats_endpoint_counts_user_history(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    ctx = await _reservation_context(db_session)
    for index, status in enumerate(
        [
            ReservationStatus.NO_SHOW,
            ReservationStatus.CANCELLED_BY_USER,
            ReservationStatus.COMPLETED,
        ]
    ):
        start_at = datetime.now(UTC) + timedelta(days=10, hours=index)
        db_session.add(
            Reservation(
                id=uuid4(),
                user_id=ctx.user.id,
                shop_id=ctx.shop.id,
                design_id=ctx.design.id,
                designer_id=ctx.designer.id,
                start_at=start_at,
                end_at=start_at + timedelta(hours=1),
                status=status,
                total_price=30000,
                payment_method_snapshot=PaymentMethod.ON_SITE,
                idempotency_key=f"reservation-{uuid4()}",
            )
        )
    await db_session.flush()

    response = await api_client.get(
        "/api/v1/me/reservation-stats",
        headers=_auth_headers(ctx.user_token),
    )

    assert response.status_code == 200
    assert response.json() == {
        "no_show_count": 1,
        "cancelled_by_user_count": 1,
        "completed_count": 1,
    }
