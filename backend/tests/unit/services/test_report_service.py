from http import HTTPStatus

import pytest
from app.api.errors import AppError
from app.models.enums import ReportTargetType
from app.schemas.reports import ReportCreate
from app.services import report_service
from sqlalchemy.ext.asyncio import AsyncSession
from tests.community_factories import (
    create_comment,
    create_design,
    create_designer,
    create_owner,
    create_reservation,
    create_review,
    create_shop,
    create_snap,
    create_user,
)


@pytest.mark.asyncio
async def test_create_report_rejects_duplicate_within_one_hour(
    db_session: AsyncSession,
) -> None:
    reporter = await create_user(db_session)
    author = await create_user(db_session)
    snap = await create_snap(db_session, author)
    payload = ReportCreate(
        target_type=ReportTargetType.SNAP,
        target_id=snap.id,
        reason="spam",
    )
    await report_service.create_report(db_session, reporter.id, payload)

    with pytest.raises(AppError) as exc_info:
        await report_service.create_report(db_session, reporter.id, payload)

    assert exc_info.value.code == "DUPLICATE_REPORT"
    assert exc_info.value.status_code == HTTPStatus.CONFLICT


@pytest.mark.asyncio
async def test_create_report_supports_all_target_types(db_session: AsyncSession) -> None:
    reporter = await create_user(db_session, "reporter")
    target_user = await create_user(db_session, "target_user")
    owner = await create_owner(db_session)
    shop = await create_shop(db_session, owner)
    designer = await create_designer(db_session, shop)
    design = await create_design(db_session, shop)
    reservation = await create_reservation(db_session, target_user, shop, design, designer)
    snap = await create_snap(db_session, target_user)
    comment = await create_comment(db_session, snap, target_user)
    review = await create_review(db_session, reservation)

    targets = [
        (ReportTargetType.SNAP, snap.id),
        (ReportTargetType.COMMENT, comment.id),
        (ReportTargetType.REVIEW, review.id),
        (ReportTargetType.USER, target_user.id),
        (ReportTargetType.SHOP, shop.id),
    ]

    for target_type, target_id in targets:
        report = await report_service.create_report(
            db_session,
            reporter.id,
            ReportCreate(target_type=target_type, target_id=target_id, reason=target_type.value),
        )
        assert report.target_type == target_type
        assert report.target_id == target_id
