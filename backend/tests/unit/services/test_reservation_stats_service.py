from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.core.security import hash_password
from app.models.accounts import Owner, User
from app.models.design import Design
from app.models.enums import (
    AiAnalysisStatus,
    PaymentMethod,
    ReservationStatus,
    VerificationStatus,
    Visibility,
)
from app.models.reservation import Reservation
from app.models.shop import Designer, Shop
from app.services import reservation_stats_service
from sqlalchemy.ext.asyncio import AsyncSession


async def _stats_context(db_session: AsyncSession) -> tuple[User, Shop, Design, Designer]:
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
    db_session.add_all([user, owner])
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
        visibility=Visibility.ACTIVE,
        ai_analysis_status=AiAnalysisStatus.DONE,
    )
    db_session.add_all([designer, design])
    await db_session.flush()
    return user, shop, design, designer


async def _add_reservation(
    db_session: AsyncSession,
    user: User,
    shop: Shop,
    design: Design,
    designer: Designer,
    status: ReservationStatus,
) -> None:
    start_at = datetime.now(UTC) + timedelta(days=1, minutes=len(status.value))
    db_session.add(
        Reservation(
            id=uuid4(),
            user_id=user.id,
            shop_id=shop.id,
            design_id=design.id,
            designer_id=designer.id,
            start_at=start_at,
            end_at=start_at + timedelta(hours=1),
            status=status,
            total_price=30000,
            payment_method_snapshot=PaymentMethod.ON_SITE,
            idempotency_key=f"reservation-{uuid4()}",
        )
    )
    await db_session.flush()


@pytest.mark.asyncio
async def test_get_my_stats_counts_target_statuses(db_session: AsyncSession) -> None:
    user, shop, design, designer = await _stats_context(db_session)
    await _add_reservation(db_session, user, shop, design, designer, ReservationStatus.NO_SHOW)
    await _add_reservation(
        db_session,
        user,
        shop,
        design,
        designer,
        ReservationStatus.CANCELLED_BY_USER,
    )
    await _add_reservation(db_session, user, shop, design, designer, ReservationStatus.COMPLETED)
    await _add_reservation(db_session, user, shop, design, designer, ReservationStatus.CONFIRMED)

    stats = await reservation_stats_service.get_my_stats(db_session, user.id)

    assert stats.no_show_count == 1
    assert stats.cancelled_by_user_count == 1
    assert stats.completed_count == 1


@pytest.mark.asyncio
async def test_get_my_stats_ignores_other_users(db_session: AsyncSession) -> None:
    user, shop, design, designer = await _stats_context(db_session)
    other_user = User(
        id=uuid4(),
        apple_sub=f"apple-{uuid4().hex}",
        email=f"{uuid4().hex}@example.com",
        nickname=f"user_{uuid4().hex[:10]}",
    )
    db_session.add(other_user)
    await db_session.flush()
    await _add_reservation(
        db_session,
        other_user,
        shop,
        design,
        designer,
        ReservationStatus.NO_SHOW,
    )

    stats = await reservation_stats_service.get_my_stats(db_session, user.id)

    assert stats.no_show_count == 0
    assert stats.cancelled_by_user_count == 0
    assert stats.completed_count == 0
