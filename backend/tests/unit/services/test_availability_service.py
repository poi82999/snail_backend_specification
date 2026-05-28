from datetime import UTC, date, datetime, time, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from app.core.security import hash_password
from app.models.accounts import Owner, User
from app.models.design import Design, DesignDesigner
from app.models.enums import (
    PaymentMethod,
    ReservationStatus,
    VerificationStatus,
    Visibility,
)
from app.models.reservation import Reservation
from app.models.shop import (
    Designer,
    DesignerSchedule,
    DesignerTimeOff,
    Shop,
    ShopBusinessHour,
)
from app.schemas.reservations import AvailableSlot
from app.services.availability_service import (
    calculate_available_slots,
    get_designer_available_slots,
)
from sqlalchemy.ext.asyncio import AsyncSession

KST = ZoneInfo("Asia/Seoul")


def _future_date() -> date:
    return datetime.now(KST).date() + timedelta(days=7)


def _local_at(target_date: date, value: time) -> datetime:
    return datetime.combine(target_date, value).replace(tzinfo=KST).astimezone(UTC)


def _slot_starts(slots: list[AvailableSlot]) -> list[str]:
    return [slot.start_at.astimezone(KST).strftime("%H:%M") for slot in slots]


async def _availability_context(
    db_session: AsyncSession,
    target_date: date,
    *,
    with_schedule: bool = True,
) -> tuple[User, Shop, Designer, Design]:
    owner = Owner(
        id=uuid4(),
        email=f"{uuid4().hex}@example.com",
        password_hash=hash_password("Strong123"),
        representative_name="대표",
        phone_number="010-0000-0000",
        verification_status=VerificationStatus.APPROVED,
    )
    user = User(
        id=uuid4(),
        apple_sub=f"apple-{uuid4().hex}",
        email=f"{uuid4().hex}@example.com",
        nickname=f"user_{uuid4().hex[:10]}",
    )
    db_session.add_all([owner, user])
    await db_session.flush()

    shop = Shop(
        id=uuid4(),
        owner_id=owner.id,
        name="예약 샵",
        address="서울",
        phone_number="02-0000-0000",
        visibility=Visibility.ACTIVE,
    )
    db_session.add(shop)
    await db_session.flush()

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
    )
    db_session.add_all([designer, design])
    await db_session.flush()
    db_session.add(DesignDesigner(design_id=design.id, designer_id=designer.id))
    await db_session.flush()

    weekday = target_date.weekday()
    db_session.add(
        ShopBusinessHour(
            id=uuid4(),
            shop_id=shop.id,
            weekday=weekday,
            open_time=time(9, 0),
            close_time=time(18, 0),
            is_closed=False,
        )
    )
    if with_schedule:
        db_session.add(
            DesignerSchedule(
                id=uuid4(),
                designer_id=designer.id,
                weekday=weekday,
                start_time=time(9, 0),
                end_time=time(18, 0),
                break_start_time=time(12, 0),
                break_end_time=time(13, 0),
                is_day_off=False,
            )
        )
    await db_session.flush()
    return user, shop, designer, design


@pytest.mark.asyncio
async def test_availability_slices_business_hours_and_break(
    db_session: AsyncSession,
) -> None:
    target_date = _future_date()
    _, _, designer, _ = await _availability_context(db_session, target_date)

    slots = await get_designer_available_slots(db_session, designer.id, target_date, 60)

    assert _slot_starts(slots) == [
        "09:00",
        "10:00",
        "11:00",
        "13:00",
        "14:00",
        "15:00",
        "16:00",
        "17:00",
    ]


@pytest.mark.asyncio
async def test_availability_excludes_designer_time_off(db_session: AsyncSession) -> None:
    target_date = _future_date()
    _, _, designer, _ = await _availability_context(db_session, target_date)
    db_session.add(
        DesignerTimeOff(
            id=uuid4(),
            designer_id=designer.id,
            off_date=target_date,
            start_time=time(15, 0),
            end_time=time(16, 0),
        )
    )
    await db_session.flush()

    slots = await get_designer_available_slots(db_session, designer.id, target_date, 60)

    assert "15:00" not in _slot_starts(slots)


@pytest.mark.asyncio
async def test_availability_excludes_locked_reservations(db_session: AsyncSession) -> None:
    target_date = _future_date()
    user, shop, designer, design = await _availability_context(db_session, target_date)
    start_at = _local_at(target_date, time(14, 0))
    db_session.add(
        Reservation(
            id=uuid4(),
            user_id=user.id,
            shop_id=shop.id,
            design_id=design.id,
            designer_id=designer.id,
            start_at=start_at,
            end_at=start_at + timedelta(hours=1),
            status=ReservationStatus.CONFIRMED,
            total_price=30000,
            payment_method_snapshot=PaymentMethod.ON_SITE,
            idempotency_key=f"reservation-{uuid4()}",
        )
    )
    await db_session.flush()

    slots = await get_designer_available_slots(db_session, designer.id, target_date, 60)

    assert "14:00" not in _slot_starts(slots)


@pytest.mark.asyncio
async def test_availability_returns_empty_without_designer_schedule(
    db_session: AsyncSession,
) -> None:
    target_date = _future_date()
    _, _, designer, _ = await _availability_context(
        db_session,
        target_date,
        with_schedule=False,
    )

    slots = await get_designer_available_slots(db_session, designer.id, target_date, 60)

    assert slots == []


@pytest.mark.asyncio
async def test_calculate_available_slots_groups_designers_by_slot(
    db_session: AsyncSession,
) -> None:
    target_date = _future_date()
    _, shop, _, design = await _availability_context(db_session, target_date)
    designer = Designer(
        id=uuid4(),
        shop_id=shop.id,
        name="두번째 디자이너",
        specialty_tags=[],
    )
    db_session.add(designer)
    await db_session.flush()
    weekday = target_date.weekday()
    db_session.add_all(
        [
            DesignDesigner(design_id=design.id, designer_id=designer.id),
            DesignerSchedule(
                id=uuid4(),
                designer_id=designer.id,
                weekday=weekday,
                start_time=time(9, 0),
                end_time=time(11, 0),
                is_day_off=False,
            ),
        ]
    )
    await db_session.flush()

    slots = await calculate_available_slots(db_session, design.id, target_date)

    first_slot = slots[0]
    assert first_slot.start_at.astimezone(KST).strftime("%H:%M") == "09:00"
    assert len(first_slot.available_designer_ids) == 2


@pytest.mark.asyncio
async def test_calculate_available_slots_does_not_exclude_pending_reservations(
    db_session: AsyncSession,
) -> None:
    target_date = _future_date()
    user, shop, designer, design = await _availability_context(db_session, target_date)
    start_at = _local_at(target_date, time(14, 0))
    db_session.add(
        Reservation(
            id=uuid4(),
            user_id=user.id,
            shop_id=shop.id,
            design_id=design.id,
            designer_id=designer.id,
            start_at=start_at,
            end_at=start_at + timedelta(hours=1),
            status=ReservationStatus.PENDING,
            total_price=30000,
            payment_method_snapshot=PaymentMethod.ON_SITE,
            idempotency_key=f"reservation-{uuid4()}",
        )
    )
    await db_session.flush()

    slots = await calculate_available_slots(db_session, design.id, target_date)

    assert "14:00" in _slot_starts(slots)
