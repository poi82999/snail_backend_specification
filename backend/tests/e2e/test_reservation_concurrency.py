from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from app.api import deps
from app.core.config import Settings
from app.main import create_app
from app.models.accounts import Owner, User, UserDeviceToken
from app.models.design import Design, DesignDesigner, DesignImage
from app.models.notification import NotificationDelivery, OwnerNotification
from app.models.reservation import IdempotencyKey, Reservation
from app.models.shop import Designer, DesignerSchedule, DesignerTimeOff, Shop, ShopBusinessHour
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from tests.e2e.conftest import E2EFactory, E2EReservationContext

pytestmark = pytest.mark.e2e


async def _cleanup(
    session: AsyncSession,
    ctx: E2EReservationContext,
    other_user_id: UUID,
) -> None:
    actor_ids = [ctx.user.id, other_user_id, ctx.owner.id]
    await session.execute(delete(IdempotencyKey).where(IdempotencyKey.actor_id.in_(actor_ids)))
    await session.execute(
        delete(NotificationDelivery).where(
            or_(
                NotificationDelivery.recipient_owner_id == ctx.owner.id,
                NotificationDelivery.recipient_user_id.in_([ctx.user.id, other_user_id]),
            )
        )
    )
    await session.execute(
        delete(OwnerNotification).where(OwnerNotification.owner_id == ctx.owner.id)
    )
    await session.execute(delete(Reservation).where(Reservation.shop_id == ctx.shop.id))
    await session.execute(delete(DesignImage).where(DesignImage.design_id == ctx.design.id))
    await session.execute(delete(DesignDesigner).where(DesignDesigner.design_id == ctx.design.id))
    await session.execute(
        delete(DesignerTimeOff).where(DesignerTimeOff.designer_id == ctx.designer.id)
    )
    await session.execute(
        delete(DesignerSchedule).where(DesignerSchedule.designer_id == ctx.designer.id)
    )
    await session.execute(delete(ShopBusinessHour).where(ShopBusinessHour.shop_id == ctx.shop.id))
    await session.execute(delete(Design).where(Design.id == ctx.design.id))
    await session.execute(delete(Designer).where(Designer.id == ctx.designer.id))
    await session.execute(delete(Shop).where(Shop.id == ctx.shop.id))
    await session.execute(
        delete(UserDeviceToken).where(UserDeviceToken.user_id.in_([ctx.user.id, other_user_id]))
    )
    await session.execute(delete(User).where(User.id.in_([ctx.user.id, other_user_id])))
    await session.execute(delete(Owner).where(Owner.id == ctx.owner.id))
    await session.commit()


@pytest.mark.asyncio
async def test_same_slot_concurrent_reservations_only_one_wins(
    settings_override: Settings,
    notification_queue,
) -> None:
    engine = create_async_engine(str(settings_override.DATABASE_URL), pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    ctx: E2EReservationContext | None = None
    other_user_id: UUID | None = None

    try:
        async with session_factory() as session:
            factory = E2EFactory(session)
            ctx = await factory.ready_reservation_context(auto_accept=True)
            other_user, other_user_token = await factory.create_user()
            other_user_id = other_user.id
            await session.commit()

        app = create_app()

        async def override_db_session() -> AsyncIterator[AsyncSession]:
            async with session_factory() as session:
                yield session

        app.dependency_overrides[deps.db_session] = override_db_session
        transport = ASGITransport(app=app)
        assert ctx is not None
        payload = E2EFactory.reservation_payload(ctx)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            responses = await asyncio.gather(
                client.post(
                    "/api/v1/reservations",
                    json=payload,
                    headers=E2EFactory.auth_headers(
                        ctx.user_token,
                        f"reservation-concurrent-{uuid4()}",
                    ),
                ),
                client.post(
                    "/api/v1/reservations",
                    json=payload,
                    headers=E2EFactory.auth_headers(
                        other_user_token,
                        f"reservation-concurrent-{uuid4()}",
                    ),
                ),
            )
        app.dependency_overrides.clear()

        assert sorted(response.status_code for response in responses) == [201, 409]
        failed = next(response for response in responses if response.status_code == 409)
        assert failed.json()["error"]["code"] == "SLOT_TAKEN"

        async with session_factory() as session:
            requested_count = await session.scalar(
                select(func.count())
                .select_from(NotificationDelivery)
                .where(
                    NotificationDelivery.template_code == "RESERVATION_REQUESTED",
                    NotificationDelivery.recipient_owner_id == ctx.owner.id,
                )
            )
            reservation_count = await session.scalar(
                select(func.count())
                .select_from(Reservation)
                .where(Reservation.shop_id == ctx.shop.id)
            )
        assert requested_count == 1
        assert reservation_count == 1
        assert len(notification_queue.calls) == 1
    finally:
        if ctx is not None and other_user_id is not None:
            async with session_factory() as session:
                await _cleanup(session, ctx, other_user_id)
        await engine.dispose()
