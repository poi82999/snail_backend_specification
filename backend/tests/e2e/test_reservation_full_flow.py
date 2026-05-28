from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest
from app.models.notification import NotificationDelivery, OwnerNotification
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_search_to_reservation_accept_complete_review_flow(
    api_client: AsyncClient,
    db_session: AsyncSession,
    e2e_factory,
    notification_queue,
) -> None:
    ctx = await e2e_factory.ready_reservation_context(with_device_token=True)

    search = await api_client.get(
        "/api/v1/search",
        params={"q": "여리여리한 핑크 네일", "scope": "designs"},
    )
    assert search.status_code == 200, search.text
    assert str(ctx.design.id) in [item["id"] for item in search.json()["items"]]

    detail = await api_client.get(f"/api/v1/designs/{ctx.design.id}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["shop"]["id"] == str(ctx.shop.id)

    availability = await api_client.get(
        f"/api/v1/designs/{ctx.design.id}/availability",
        params={"date": ctx.target_date.isoformat()},
    )
    assert availability.status_code == 200, availability.text
    slot_start = datetime.fromisoformat(availability.json()[0]["start_at"].replace("Z", "+00:00"))
    assert slot_start == ctx.start_at

    created = await api_client.post(
        "/api/v1/reservations",
        json=e2e_factory.reservation_payload(ctx),
        headers=e2e_factory.auth_headers(ctx.user_token, f"reservation-create-{uuid4()}"),
    )
    assert created.status_code == 201, created.text
    reservation_id = created.json()["id"]
    assert created.json()["status"] == "pending"

    deliveries = list(
        (
            await db_session.scalars(
                select(NotificationDelivery).order_by(NotificationDelivery.created_at)
            )
        ).all()
    )
    inbox = list((await db_session.scalars(select(OwnerNotification))).all())
    assert [delivery.template_code for delivery in deliveries] == ["RESERVATION_REQUESTED"]
    assert len(inbox) == 1
    assert inbox[0].type == "RESERVATION_REQUESTED"
    assert notification_queue.calls == [("send_notification", str(deliveries[0].id))]

    inbox_response = await api_client.get(
        "/api/v1/shops/me/notifications",
        headers=e2e_factory.auth_headers(ctx.owner_token),
    )
    assert inbox_response.status_code == 200, inbox_response.text
    assert inbox_response.json()["data"][0]["type"] == "RESERVATION_REQUESTED"

    accepted = await api_client.post(
        f"/api/v1/shops/me/reservations/{reservation_id}/accept",
        headers=e2e_factory.auth_headers(ctx.owner_token, f"reservation-accept-{uuid4()}"),
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "confirmed"

    deliveries = list(
        (
            await db_session.scalars(
                select(NotificationDelivery).order_by(NotificationDelivery.created_at)
            )
        ).all()
    )
    assert [delivery.template_code for delivery in deliveries] == [
        "RESERVATION_REQUESTED",
        "RESERVATION_CONFIRMED",
    ]
    assert notification_queue.calls[-1] == ("send_notification", str(deliveries[-1].id))

    completed = await api_client.post(
        f"/api/v1/shops/me/reservations/{reservation_id}/complete",
        headers=e2e_factory.auth_headers(ctx.owner_token, f"reservation-complete-{uuid4()}"),
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"

    review = await api_client.post(
        f"/api/v1/reservations/{reservation_id}/reviews",
        json={"rating": 5, "body": "검색부터 예약까지 자연스럽게 진행되었습니다."},
        headers=e2e_factory.auth_headers(ctx.user_token, f"review-create-{uuid4()}"),
    )
    assert review.status_code == 201, review.text
    assert review.json()["reservation_id"] == reservation_id
    assert review.json()["design_id"] == str(ctx.design.id)
