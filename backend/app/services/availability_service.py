from datetime import UTC, date, datetime, time, timedelta
from http import HTTPStatus
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.models.design import Design, DesignDesigner
from app.models.reservation import Reservation
from app.models.shop import Designer, DesignerSchedule, DesignerTimeOff, ShopBusinessHour
from app.schemas.reservations import AvailableSlot
from app.services.reservation_policy import SLOT_LOCK_STATUSES, normalize_utc

KST = ZoneInfo("Asia/Seoul")
Interval = tuple[datetime, datetime]


def _local_datetime(target_date: date, value: time) -> datetime:
    return datetime.combine(target_date, value).replace(tzinfo=KST)


def _day_bounds_utc(target_date: date) -> Interval:
    start = datetime.combine(target_date, time.min).replace(tzinfo=KST)
    end = start + timedelta(days=1)
    return start.astimezone(UTC), end.astimezone(UTC)


def _intersection(first: Interval, second: Interval) -> Interval | None:
    start = max(first[0], second[0])
    end = min(first[1], second[1])
    if start >= end:
        return None
    return start, end


def _subtract_interval(interval: Interval, blocked: Interval) -> list[Interval]:
    overlap = _intersection(interval, blocked)
    if overlap is None:
        return [interval]

    result: list[Interval] = []
    if interval[0] < overlap[0]:
        result.append((interval[0], overlap[0]))
    if overlap[1] < interval[1]:
        result.append((overlap[1], interval[1]))
    return result


def _subtract_many(intervals: list[Interval], blocked_intervals: list[Interval]) -> list[Interval]:
    available = intervals
    for blocked in blocked_intervals:
        next_available: list[Interval] = []
        for interval in available:
            next_available.extend(_subtract_interval(interval, blocked))
        available = next_available
    return available


def _time_range(target_date: date, start_time: time | None, end_time: time | None) -> Interval:
    if not _valid_time_range(start_time, end_time):
        raise ValueError("invalid time range")
    assert start_time is not None
    assert end_time is not None
    return (
        _local_datetime(target_date, start_time).astimezone(UTC),
        _local_datetime(target_date, end_time).astimezone(UTC),
    )


def _valid_time_range(start_time: time | None, end_time: time | None) -> bool:
    return start_time is not None and end_time is not None and start_time < end_time


async def _load_design(session: AsyncSession, design_id: UUID) -> Design:
    design = await session.scalar(
        select(Design).where(Design.id == design_id, Design.deleted_at.is_(None))
    )
    if design is None:
        raise AppError("DESIGN_NOT_FOUND", "디자인을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return design


async def _active_design_designers(
    session: AsyncSession,
    design: Design,
) -> list[Designer]:
    designers = await session.scalars(
        select(Designer)
        .join(DesignDesigner, DesignDesigner.designer_id == Designer.id)
        .where(
            DesignDesigner.design_id == design.id,
            Designer.shop_id == design.shop_id,
            Designer.is_active.is_(True),
        )
        .order_by(Designer.id)
    )
    return list(designers.all())


async def _designer_available_slots(
    session: AsyncSession,
    designer: Designer,
    target_date: date,
    duration_minutes: int,
) -> list[AvailableSlot]:
    weekday = target_date.weekday()
    schedule = await session.scalar(
        select(DesignerSchedule).where(
            DesignerSchedule.designer_id == designer.id,
            DesignerSchedule.weekday == weekday,
        )
    )
    if (
        schedule is None
        or schedule.is_day_off
        or not _valid_time_range(schedule.start_time, schedule.end_time)
    ):
        return []

    shop_hour = await session.scalar(
        select(ShopBusinessHour).where(
            ShopBusinessHour.shop_id == designer.shop_id,
            ShopBusinessHour.weekday == weekday,
        )
    )
    if (
        shop_hour is None
        or shop_hour.is_closed
        or not _valid_time_range(shop_hour.open_time, shop_hour.close_time)
    ):
        return []

    schedule_interval = _time_range(target_date, schedule.start_time, schedule.end_time)
    shop_interval = _time_range(target_date, shop_hour.open_time, shop_hour.close_time)
    base_interval = _intersection(schedule_interval, shop_interval)
    if base_interval is None:
        return []

    available = [base_interval]
    if _valid_time_range(schedule.break_start_time, schedule.break_end_time):
        available = _subtract_many(
            available,
            [_time_range(target_date, schedule.break_start_time, schedule.break_end_time)],
        )

    day_start_utc, day_end_utc = _day_bounds_utc(target_date)
    time_offs = await session.scalars(
        select(DesignerTimeOff).where(
            DesignerTimeOff.designer_id == designer.id,
            DesignerTimeOff.off_date == target_date,
        )
    )
    blocked_by_time_off: list[Interval] = []
    for time_off in time_offs.all():
        if not _valid_time_range(time_off.start_time, time_off.end_time):
            blocked_by_time_off.append((day_start_utc, day_end_utc))
        else:
            blocked_by_time_off.append(
                _time_range(target_date, time_off.start_time, time_off.end_time)
            )
    available = _subtract_many(available, blocked_by_time_off)

    reservations = await session.scalars(
        select(Reservation).where(
            Reservation.designer_id == designer.id,
            Reservation.status.in_(SLOT_LOCK_STATUSES),
            Reservation.start_at < day_end_utc,
            Reservation.end_at > day_start_utc,
        )
    )
    blocked_by_reservations = [
        (normalize_utc(reservation.start_at), normalize_utc(reservation.end_at))
        for reservation in reservations.all()
    ]
    available = _subtract_many(available, blocked_by_reservations)

    duration = timedelta(minutes=duration_minutes)
    now = datetime.now(UTC)
    slots: list[AvailableSlot] = []
    for interval_start, interval_end in sorted(available):
        slot_start = interval_start
        while slot_start + duration <= interval_end:
            slot_end = slot_start + duration
            if slot_start > now:
                slots.append(
                    AvailableSlot(
                        start_at=slot_start,
                        end_at=slot_end,
                        available_designer_ids=[designer.id],
                    )
                )
            slot_start += duration
    return slots


async def calculate_available_slots(
    session: AsyncSession,
    design_id: UUID,
    target_date: date,
) -> list[AvailableSlot]:
    design = await _load_design(session, design_id)
    designers = await _active_design_designers(session, design)
    grouped: dict[tuple[datetime, datetime], set[UUID]] = {}

    for designer in designers:
        slots = await _designer_available_slots(
            session,
            designer,
            target_date,
            design.duration_minutes,
        )
        for slot in slots:
            grouped.setdefault((slot.start_at, slot.end_at), set()).add(designer.id)

    return [
        AvailableSlot(
            start_at=start_at,
            end_at=end_at,
            available_designer_ids=sorted(designer_ids),
        )
        for (start_at, end_at), designer_ids in sorted(grouped.items())
        if designer_ids
    ]


async def get_designer_available_slots(
    session: AsyncSession,
    designer_id: UUID,
    target_date: date,
    slot_minutes: int = 60,
) -> list[AvailableSlot]:
    designer = await session.scalar(
        select(Designer).where(Designer.id == designer_id, Designer.is_active.is_(True))
    )
    if designer is None:
        raise AppError(
            "DESIGNER_NOT_FOUND",
            "디자이너를 찾을 수 없습니다.",
            HTTPStatus.NOT_FOUND,
        )
    return await _designer_available_slots(session, designer, target_date, slot_minutes)
