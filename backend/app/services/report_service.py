from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.models.accounts import User
from app.models.community import Comment, Report, Review, Snap
from app.models.enums import ReportStatus, ReportTargetType
from app.models.shop import Shop
from app.schemas.reports import ReportCreate, ReportPublic

logger = structlog.get_logger()

DUPLICATE_REPORT_WINDOW = timedelta(hours=1)


async def _target_exists(
    session: AsyncSession,
    target_type: ReportTargetType,
    target_id: UUID,
) -> bool:
    if target_type == ReportTargetType.SNAP:
        return (
            await session.scalar(
                select(Snap.id).where(Snap.id == target_id, Snap.deleted_at.is_(None))
            )
            is not None
        )
    if target_type == ReportTargetType.COMMENT:
        return (
            await session.scalar(
                select(Comment.id).where(
                    Comment.id == target_id,
                    Comment.deleted_at.is_(None),
                )
            )
            is not None
        )
    if target_type == ReportTargetType.REVIEW:
        return (
            await session.scalar(
                select(Review.id).where(Review.id == target_id, Review.deleted_at.is_(None))
            )
            is not None
        )
    if target_type == ReportTargetType.USER:
        return (
            await session.scalar(
                select(User.id).where(User.id == target_id, User.is_active.is_(True))
            )
            is not None
        )
    if target_type == ReportTargetType.SHOP:
        return await session.scalar(select(Shop.id).where(Shop.id == target_id)) is not None
    return False


async def create_report(
    session: AsyncSession,
    reporter_user_id: UUID,
    payload: ReportCreate,
) -> ReportPublic:
    if not await _target_exists(session, payload.target_type, payload.target_id):
        raise AppError(
            "REPORT_TARGET_NOT_FOUND", "신고 대상을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND
        )

    duplicate_since = datetime.now(UTC) - DUPLICATE_REPORT_WINDOW
    duplicate = await session.scalar(
        select(Report.id).where(
            Report.reporter_user_id == reporter_user_id,
            Report.target_type == payload.target_type,
            Report.target_id == payload.target_id,
            Report.created_at >= duplicate_since,
        )
    )
    if duplicate is not None:
        raise AppError(
            "DUPLICATE_REPORT",
            "이미 신고하셨습니다.",
            HTTPStatus.CONFLICT,
        )

    report = Report(
        id=uuid4(),
        reporter_user_id=reporter_user_id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        reason=payload.reason,
        detail=payload.detail,
        status=ReportStatus.PENDING,
    )
    session.add(report)
    await session.flush()
    logger.info(
        "report.created",
        reporter_user_id=str(reporter_user_id),
        target_type=payload.target_type.value,
        target_id=str(payload.target_id),
    )
    return ReportPublic(
        id=report.id,
        target_type=report.target_type,
        target_id=report.target_id,
        reason=report.reason,
        status=report.status,
        created_at=report.created_at,
    )
