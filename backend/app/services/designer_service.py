from datetime import time
from http import HTTPStatus
from uuid import UUID, uuid4

import structlog
from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.models.accounts import Owner
from app.models.design import DesignDesigner
from app.models.enums import ActorType, UploadTargetType, VerificationStatus, Visibility
from app.models.ops import UploadObject
from app.models.shop import Designer, DesignerSchedule, DesignerTimeOff, Shop
from app.schemas.designers import (
    DesignerCreate,
    DesignerScheduleSet,
    DesignerUpdate,
    ScheduleEntry,
    TimeOffCreate,
)
from app.services.owner_service import get_me
from app.services.shop_service import get_public_shop
from app.utils.storage import upload_public_url

logger = structlog.get_logger()


async def _get_my_shop(session: AsyncSession, owner_id: UUID) -> Shop:
    await get_me(session, owner_id)
    shop = await session.scalar(select(Shop).where(Shop.owner_id == owner_id))
    if shop is None:
        raise AppError("SHOP_NOT_FOUND", "샵을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return shop


async def _get_designer_for_owner(
    session: AsyncSession,
    owner_id: UUID,
    designer_id: UUID,
) -> Designer:
    designer = await session.scalar(
        select(Designer)
        .join(Shop, Shop.id == Designer.shop_id)
        .where(Designer.id == designer_id, Shop.owner_id == owner_id)
    )
    if designer is None:
        raise AppError(
            "DESIGNER_NOT_FOUND",
            "디자이너를 찾을 수 없습니다.",
            HTTPStatus.NOT_FOUND,
        )
    return designer


async def _get_profile_upload(
    session: AsyncSession,
    owner_id: UUID,
    object_key: str,
) -> UploadObject:
    upload = await session.scalar(
        select(UploadObject).where(
            UploadObject.object_key == object_key,
            UploadObject.owner_actor_type == ActorType.OWNER.value,
            UploadObject.owner_actor_id == owner_id,
            UploadObject.target_type == UploadTargetType.PROFILE,
        )
    )
    if upload is None:
        raise AppError("UPLOAD_NOT_FOUND", "업로드 파일을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return upload


async def create_designer(
    session: AsyncSession,
    owner_id: UUID,
    payload: DesignerCreate,
) -> Designer:
    shop = await _get_my_shop(session, owner_id)
    profile_image_url = None
    if payload.profile_image_object_key is not None:
        upload = await _get_profile_upload(session, owner_id, payload.profile_image_object_key)
        profile_image_url = upload_public_url(upload)

    designer = Designer(
        id=uuid4(),
        shop_id=shop.id,
        name=payload.name,
        position=payload.position,
        career_years=payload.career_years,
        profile_image_url=profile_image_url,
        specialty_tags=payload.specialty_tags,
        is_active=True,
    )
    session.add(designer)
    await session.flush()
    await session.refresh(designer)
    logger.info("designer.created", owner_id=str(owner_id), designer_id=str(designer.id))
    return designer


async def update_designer(
    session: AsyncSession,
    owner_id: UUID,
    designer_id: UUID,
    payload: DesignerUpdate,
) -> Designer:
    designer = await _get_designer_for_owner(session, owner_id, designer_id)

    if "name" in payload.model_fields_set and payload.name is not None:
        designer.name = payload.name
    if "position" in payload.model_fields_set:
        designer.position = payload.position
    if "career_years" in payload.model_fields_set:
        designer.career_years = payload.career_years
    if "profile_image_object_key" in payload.model_fields_set:
        if payload.profile_image_object_key is None:
            designer.profile_image_url = None
        else:
            upload = await _get_profile_upload(session, owner_id, payload.profile_image_object_key)
            designer.profile_image_url = upload_public_url(upload)
    if payload.specialty_tags is not None:
        designer.specialty_tags = payload.specialty_tags

    await session.flush()
    await session.refresh(designer)
    logger.info("designer.updated", owner_id=str(owner_id), designer_id=str(designer.id))
    return designer


async def soft_disable_designer(
    session: AsyncSession,
    owner_id: UUID,
    designer_id: UUID,
) -> None:
    designer = await _get_designer_for_owner(session, owner_id, designer_id)
    has_linked_design = await session.scalar(
        select(exists().where(DesignDesigner.designer_id == designer.id))
    )
    if has_linked_design:
        designer.is_active = False
    else:
        await session.execute(
            delete(DesignerTimeOff).where(DesignerTimeOff.designer_id == designer.id)
        )
        await session.execute(
            delete(DesignerSchedule).where(DesignerSchedule.designer_id == designer.id)
        )
        await session.delete(designer)
    await session.flush()
    logger.info(
        "designer.deleted",
        owner_id=str(owner_id),
        designer_id=str(designer_id),
        soft=bool(has_linked_design),
    )


def _validate_schedule_entries(entries: list[ScheduleEntry]) -> dict[int, ScheduleEntry]:
    if len(entries) != 7:
        raise AppError(
            "INVALID_DESIGNER_SCHEDULE",
            "디자이너 스케줄은 요일별 7건이 필요합니다.",
            HTTPStatus.BAD_REQUEST,
        )
    by_weekday: dict[int, ScheduleEntry] = {}
    for entry in entries:
        if entry.weekday in by_weekday:
            raise AppError(
                "INVALID_DESIGNER_SCHEDULE",
                "요일별 스케줄은 중복될 수 없습니다.",
                HTTPStatus.BAD_REQUEST,
            )
        by_weekday[entry.weekday] = entry
    if set(by_weekday) != set(range(7)):
        raise AppError(
            "INVALID_DESIGNER_SCHEDULE",
            "디자이너 스케줄은 월요일부터 일요일까지 모두 필요합니다.",
            HTTPStatus.BAD_REQUEST,
        )
    return by_weekday


def _validate_break_time(
    start_time: time,
    end_time: time,
    break_start_time: time | None,
    break_end_time: time | None,
) -> None:
    if break_start_time is None and break_end_time is None:
        return
    if break_start_time is None or break_end_time is None:
        raise AppError(
            "INVALID_DESIGNER_SCHEDULE",
            "휴게 시간은 시작과 종료를 함께 입력해야 합니다.",
            HTTPStatus.BAD_REQUEST,
        )
    if break_start_time >= break_end_time:
        raise AppError(
            "INVALID_DESIGNER_SCHEDULE",
            "휴게 시작 시간은 종료 시간보다 빨라야 합니다.",
            HTTPStatus.BAD_REQUEST,
        )
    if break_start_time < start_time or break_end_time > end_time:
        raise AppError(
            "INVALID_DESIGNER_SCHEDULE",
            "휴게 시간은 근무 시간 안에 있어야 합니다.",
            HTTPStatus.BAD_REQUEST,
        )


def _normalized_schedule(
    entry: ScheduleEntry,
) -> tuple[time | None, time | None, time | None, time | None, bool]:
    if entry.is_day_off:
        return None, None, None, None, True
    if entry.start_time is None or entry.end_time is None:
        raise AppError(
            "INVALID_DESIGNER_SCHEDULE",
            "근무일에는 시작 시간과 종료 시간이 필요합니다.",
            HTTPStatus.BAD_REQUEST,
        )
    if entry.start_time >= entry.end_time:
        raise AppError(
            "INVALID_DESIGNER_SCHEDULE",
            "근무 시작 시간은 종료 시간보다 빨라야 합니다.",
            HTTPStatus.BAD_REQUEST,
        )
    _validate_break_time(
        entry.start_time,
        entry.end_time,
        entry.break_start_time,
        entry.break_end_time,
    )
    return (
        entry.start_time,
        entry.end_time,
        entry.break_start_time,
        entry.break_end_time,
        False,
    )


async def set_designer_schedule(
    session: AsyncSession,
    owner_id: UUID,
    designer_id: UUID,
    payload: DesignerScheduleSet,
) -> None:
    designer = await _get_designer_for_owner(session, owner_id, designer_id)
    by_weekday = _validate_schedule_entries(payload.entries)

    existing_schedules = (
        await session.scalars(
            select(DesignerSchedule).where(DesignerSchedule.designer_id == designer.id)
        )
    ).all()
    existing_by_weekday = {schedule.weekday: schedule for schedule in existing_schedules}

    for weekday in range(7):
        entry = by_weekday[weekday]
        start_time, end_time, break_start_time, break_end_time, is_day_off = _normalized_schedule(
            entry
        )
        existing = existing_by_weekday.get(weekday)
        if existing is None:
            session.add(
                DesignerSchedule(
                    id=uuid4(),
                    designer_id=designer.id,
                    weekday=weekday,
                    start_time=start_time,
                    end_time=end_time,
                    break_start_time=break_start_time,
                    break_end_time=break_end_time,
                    is_day_off=is_day_off,
                )
            )
        else:
            existing.start_time = start_time
            existing.end_time = end_time
            existing.break_start_time = break_start_time
            existing.break_end_time = break_end_time
            existing.is_day_off = is_day_off

    await session.flush()
    logger.info("designer.schedule_set", owner_id=str(owner_id), designer_id=str(designer.id))


def _validate_time_off(payload: TimeOffCreate) -> None:
    if payload.start_time is None and payload.end_time is None:
        return
    if payload.start_time is None or payload.end_time is None:
        raise AppError(
            "INVALID_TIME_OFF",
            "부분 휴무는 시작 시간과 종료 시간을 함께 입력해야 합니다.",
            HTTPStatus.BAD_REQUEST,
        )
    if payload.start_time >= payload.end_time:
        raise AppError(
            "INVALID_TIME_OFF",
            "휴무 시작 시간은 종료 시간보다 빨라야 합니다.",
            HTTPStatus.BAD_REQUEST,
        )


async def add_time_off(
    session: AsyncSession,
    owner_id: UUID,
    designer_id: UUID,
    payload: TimeOffCreate,
) -> DesignerTimeOff:
    designer = await _get_designer_for_owner(session, owner_id, designer_id)
    _validate_time_off(payload)
    time_off = DesignerTimeOff(
        id=uuid4(),
        designer_id=designer.id,
        off_date=payload.off_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        reason=payload.reason,
    )
    session.add(time_off)
    await session.flush()
    await session.refresh(time_off)
    logger.info("designer.time_off_added", owner_id=str(owner_id), designer_id=str(designer.id))
    return time_off


async def delete_time_off(
    session: AsyncSession,
    owner_id: UUID,
    designer_id: UUID,
    time_off_id: UUID,
) -> None:
    designer = await _get_designer_for_owner(session, owner_id, designer_id)
    time_off = await session.scalar(
        select(DesignerTimeOff).where(
            DesignerTimeOff.id == time_off_id,
            DesignerTimeOff.designer_id == designer.id,
        )
    )
    if time_off is None:
        raise AppError("TIME_OFF_NOT_FOUND", "휴무 일정을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    await session.delete(time_off)
    await session.flush()
    logger.info(
        "designer.time_off_deleted",
        owner_id=str(owner_id),
        designer_id=str(designer.id),
        time_off_id=str(time_off_id),
    )


async def list_designers_for_my_shop(session: AsyncSession, owner_id: UUID) -> list[Designer]:
    shop = await _get_my_shop(session, owner_id)
    designers = await session.scalars(
        select(Designer)
        .where(Designer.shop_id == shop.id)
        .order_by(Designer.created_at, Designer.id)
    )
    return list(designers.all())


async def list_public_designers_for_shop(session: AsyncSession, shop_id: UUID) -> list[Designer]:
    await get_public_shop(session, shop_id)
    designers = await session.scalars(
        select(Designer)
        .where(Designer.shop_id == shop_id, Designer.is_active.is_(True))
        .order_by(Designer.created_at, Designer.id)
    )
    return list(designers.all())


async def get_public_designer(session: AsyncSession, designer_id: UUID) -> Designer:
    designer = await session.scalar(
        select(Designer)
        .join(Shop, Shop.id == Designer.shop_id)
        .join(Owner, Owner.id == Shop.owner_id)
        .where(
            Designer.id == designer_id,
            Designer.is_active.is_(True),
            Shop.visibility == Visibility.ACTIVE,
            Owner.verification_status == VerificationStatus.APPROVED,
            Owner.is_active.is_(True),
        )
    )
    if designer is None:
        raise AppError(
            "DESIGNER_NOT_FOUND",
            "디자이너를 찾을 수 없습니다.",
            HTTPStatus.NOT_FOUND,
        )
    return designer
