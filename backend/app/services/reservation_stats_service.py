from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ReservationStatus
from app.models.reservation import Reservation
from app.schemas.reservations import ReservationStatsMe


async def _count_by_status(
    session: AsyncSession,
    user_id: UUID,
    status: ReservationStatus,
) -> int:
    count = await session.scalar(
        select(func.count())
        .select_from(Reservation)
        .where(Reservation.user_id == user_id, Reservation.status == status)
    )
    return int(count or 0)


async def get_my_stats(session: AsyncSession, user_id: UUID) -> ReservationStatsMe:
    return ReservationStatsMe(
        no_show_count=await _count_by_status(session, user_id, ReservationStatus.NO_SHOW),
        cancelled_by_user_count=await _count_by_status(
            session,
            user_id,
            ReservationStatus.CANCELLED_BY_USER,
        ),
        completed_count=await _count_by_status(session, user_id, ReservationStatus.COMPLETED),
    )
