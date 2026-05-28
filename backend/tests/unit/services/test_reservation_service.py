from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from http import HTTPStatus
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from app.api.errors import AppError
from app.core.security import hash_password
from app.models.accounts import Owner, User
from app.models.design import Design, DesignDesigner
from app.models.enums import (
    AiAnalysisStatus,
    AssignedBy,
    PaymentMethod,
    ReservationStatus,
    VerificationStatus,
    Visibility,
)
from app.models.reservation import Reservation
from app.models.shop import Designer, DesignerSchedule, Shop, ShopBusinessHour
from app.schemas.reservations import ReservationCreate
from app.services import reservation_service
from sqlalchemy.ext.asyncio import AsyncSession

KST = ZoneInfo("Asia/Seoul")


@dataclass(slots=True)
class ReservationServiceContext:
    user: User
    owner: Owner
    shop: Shop
    designer: Designer
    design: Design
    target_date: date
    start_at: datetime


def _future_date(days: int = 7) -> date:
    return datetime.now(KST).date() + timedelta(days=days)


def _local_at(target_date: date, value: time) -> datetime:
    return datetime.combine(target_date, value).replace(tzinfo=KST).astimezone(UTC)


async def _context(
    session: AsyncSession,
    *,
    auto_accept: bool = False,
    payment_method: PaymentMethod = PaymentMethod.ON_SITE,
) -> ReservationServiceContext:
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
        name="예약 샵",
        address="서울",
        phone_number="02-0000-0000",
        visibility=Visibility.ACTIVE,
        auto_accept=auto_accept,
        payment_method=payment_method,
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

    target_date = _future_date()
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
                is_day_off=False,
            ),
        ]
    )
    await session.flush()
    return ReservationServiceContext(
        user=user,
        owner=owner,
        shop=shop,
        designer=designer,
        design=design,
        target_date=target_date,
        start_at=_local_at(target_date, time(9, 0)),
    )


@pytest.mark.asyncio
async def test_create_reservation_auto_assigns_and_confirms_auto_accept(
    db_session: AsyncSession,
) -> None:
    ctx = await _context(db_session, auto_accept=True)

    reservation = await reservation_service.create_reservation(
        db_session,
        ctx.user.id,
        ReservationCreate(design_id=ctx.design.id, start_at=ctx.start_at),
        f"reservation-{uuid4()}",
    )

    assert reservation.status == ReservationStatus.CONFIRMED
    assert reservation.assigned_by == AssignedBy.AUTO
    assert reservation.designer_id == ctx.designer.id
    assert reservation.end_at == ctx.start_at + timedelta(minutes=ctx.design.duration_minutes)


@pytest.mark.asyncio
async def test_create_reservation_rejects_duplicate_same_shop_day(
    db_session: AsyncSession,
) -> None:
    ctx = await _context(db_session)
    existing_start = _local_at(ctx.target_date, time(10, 0))
    db_session.add(
        Reservation(
            id=uuid4(),
            user_id=ctx.user.id,
            shop_id=ctx.shop.id,
            design_id=ctx.design.id,
            designer_id=ctx.designer.id,
            start_at=existing_start,
            end_at=existing_start + timedelta(hours=1),
            status=ReservationStatus.PENDING,
            total_price=30000,
            payment_method_snapshot=PaymentMethod.ON_SITE,
            idempotency_key=f"reservation-{uuid4()}",
        )
    )
    await db_session.flush()

    with pytest.raises(AppError) as exc_info:
        await reservation_service.create_reservation(
            db_session,
            ctx.user.id,
            ReservationCreate(design_id=ctx.design.id, start_at=ctx.start_at),
            f"reservation-{uuid4()}",
        )

    assert exc_info.value.code == "DUPLICATE_RESERVATION_SAME_DAY"
    assert exc_info.value.status_code == HTTPStatus.CONFLICT


@pytest.mark.asyncio
async def test_mark_no_show_rejects_before_30_minutes(db_session: AsyncSession) -> None:
    ctx = await _context(db_session)
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

    with pytest.raises(AppError) as exc_info:
        await reservation_service.mark_no_show(db_session, ctx.owner.id, reservation.id)

    assert exc_info.value.code == "NO_SHOW_TOO_EARLY"
    assert exc_info.value.status_code == HTTPStatus.CONFLICT
