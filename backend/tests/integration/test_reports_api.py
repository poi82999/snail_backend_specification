from uuid import uuid4

import pytest
from app.models.enums import ReportTargetType
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.community_factories import (
    auth_headers,
    create_comment,
    create_design,
    create_designer,
    create_owner,
    create_reservation,
    create_review,
    create_shop,
    create_snap,
    create_user,
    user_token,
)


@pytest.mark.asyncio
async def test_reports_api_supports_all_target_types(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    reporter = await create_user(db_session, "api_reporter")
    target_user = await create_user(db_session, "api_target_user")
    owner = await create_owner(db_session)
    shop = await create_shop(db_session, owner)
    designer = await create_designer(db_session, shop)
    design = await create_design(db_session, shop)
    reservation = await create_reservation(db_session, target_user, shop, design, designer)
    snap = await create_snap(db_session, target_user)
    comment = await create_comment(db_session, snap, target_user)
    review = await create_review(db_session, reservation)
    token = user_token(reporter)

    targets = [
        (ReportTargetType.SNAP, snap.id),
        (ReportTargetType.COMMENT, comment.id),
        (ReportTargetType.REVIEW, review.id),
        (ReportTargetType.USER, target_user.id),
        (ReportTargetType.SHOP, shop.id),
    ]

    for target_type, target_id in targets:
        response = await api_client.post(
            "/api/v1/reports",
            json={
                "target_type": target_type.value,
                "target_id": str(target_id),
                "reason": f"reason-{target_type.value}",
            },
            headers=auth_headers(token, f"report-{target_type.value}-{uuid4()}"),
        )
        assert response.status_code == 201
        assert response.json()["target_type"] == target_type.value
        assert response.json()["target_id"] == str(target_id)
