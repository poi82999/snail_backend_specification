from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.models.notification import OwnerNotification
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.community_factories import auth_headers, create_owner, owner_token


async def _notifications(db_session: AsyncSession) -> tuple[str, list[OwnerNotification]]:
    owner = await create_owner(db_session)
    token = owner_token(owner)
    rows = [
        OwnerNotification(
            id=uuid4(),
            owner_id=owner.id,
            type="RESERVATION_REQUESTED",
            title=f"알림 {index}",
            body="예약 알림",
            resource_type="reservation",
            resource_id=uuid4(),
            deeplink=f"snail://owner/reservations/{uuid4()}",
            metadata_={"index": index},
            read_at=datetime.now(UTC) if index == 2 else None,
        )
        for index in range(3)
    ]
    db_session.add_all(rows)
    await db_session.flush()
    return token, rows


@pytest.mark.asyncio
async def test_owner_notification_list_returns_unread_count(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    token, _ = await _notifications(db_session)

    response = await api_client.get(
        "/api/v1/shops/me/notifications",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 3
    assert body["unread_count"] == 2
    assert body["page"]["has_next"] is False


@pytest.mark.asyncio
async def test_owner_notification_read_decreases_unread_count(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    token, rows = await _notifications(db_session)

    response = await api_client.patch(
        f"/api/v1/shops/me/notifications/{rows[0].id}/read",
        headers=auth_headers(token, f"notification-read-{uuid4()}"),
    )
    assert response.status_code == 200
    assert response.json()["data"]["read_at"] is not None

    list_response = await api_client.get(
        "/api/v1/shops/me/notifications",
        headers=auth_headers(token),
    )
    assert list_response.json()["unread_count"] == 1


@pytest.mark.asyncio
async def test_owner_notification_read_requires_idempotency_key(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    token, rows = await _notifications(db_session)

    response = await api_client.patch(
        f"/api/v1/shops/me/notifications/{rows[0].id}/read",
        headers=auth_headers(token),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"


@pytest.mark.asyncio
async def test_owner_notification_read_all_marks_all_read(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    token, rows = await _notifications(db_session)

    response = await api_client.post(
        "/api/v1/owners/me/notifications/read-all",
        headers=auth_headers(token, f"notification-read-all-{uuid4()}"),
    )
    assert response.status_code == 200
    assert response.json()["data"]["updated_count"] == 2

    refreshed = list(
        (
            await db_session.scalars(
                select(OwnerNotification).where(OwnerNotification.id.in_([row.id for row in rows]))
            )
        ).all()
    )
    assert all(notification.read_at is not None for notification in refreshed)
