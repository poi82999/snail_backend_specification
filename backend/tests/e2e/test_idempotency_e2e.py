from __future__ import annotations

from uuid import uuid4

import pytest
from app.models.notification import NotificationDelivery
from app.models.reservation import Reservation
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_reservation_create_and_cancel_idempotency_are_single_effect(
    api_client: AsyncClient,
    db_session: AsyncSession,
    e2e_factory,
    notification_queue,
) -> None:
    ctx = await e2e_factory.ready_reservation_context()
    create_key = f"reservation-idempotent-create-{uuid4()}"

    first = await api_client.post(
        "/api/v1/reservations",
        json=e2e_factory.reservation_payload(ctx),
        headers=e2e_factory.auth_headers(ctx.user_token, create_key),
    )
    second = await api_client.post(
        "/api/v1/reservations",
        json=e2e_factory.reservation_payload(ctx),
        headers=e2e_factory.auth_headers(ctx.user_token, create_key),
    )

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert second.json() == first.json()
    reservation_id = first.json()["id"]

    created_count = await db_session.scalar(
        select(func.count())
        .select_from(Reservation)
        .where(Reservation.idempotency_key == create_key)
    )
    requested_count = await db_session.scalar(
        select(func.count())
        .select_from(NotificationDelivery)
        .where(
            NotificationDelivery.recipient_owner_id == ctx.owner.id,
            NotificationDelivery.template_code == "RESERVATION_REQUESTED",
        )
    )
    assert created_count == 1
    assert requested_count == 1

    cancel_key = f"reservation-idempotent-cancel-{uuid4()}"
    cancel_payload = {"cancel_reason": "일정이 변경되었습니다."}
    first_cancel = await api_client.post(
        f"/api/v1/me/reservations/{reservation_id}/cancel",
        json=cancel_payload,
        headers=e2e_factory.auth_headers(ctx.user_token, cancel_key),
    )
    second_cancel = await api_client.post(
        f"/api/v1/me/reservations/{reservation_id}/cancel",
        json=cancel_payload,
        headers=e2e_factory.auth_headers(ctx.user_token, cancel_key),
    )

    assert first_cancel.status_code == 200, first_cancel.text
    assert second_cancel.status_code == 200, second_cancel.text
    assert second_cancel.json() == first_cancel.json()
    assert first_cancel.json()["status"] == "cancelled_by_user"

    cancelled_owner_notification_count = await db_session.scalar(
        select(func.count())
        .select_from(NotificationDelivery)
        .where(
            NotificationDelivery.recipient_owner_id == ctx.owner.id,
            NotificationDelivery.template_code == "RESERVATION_CANCELLED_BY_USER",
        )
    )
    assert cancelled_owner_notification_count == 1
    assert len(notification_queue.calls) == 2


@pytest.mark.asyncio
async def test_signup_requires_idempotency_key_but_login_is_exempt(
    api_client: AsyncClient,
) -> None:
    email = f"owner-{uuid4().hex}@example.com"
    payload = {
        "email": email,
        "password": "Strong123",
        "representative_name": "대표",
        "phone_number": "010-0000-0000",
        "accepted_terms_version": "1.0",
        "accepted_privacy_version": "1.0",
    }

    missing_key = await api_client.post("/api/v1/auth/owner/signup", json=payload)
    assert missing_key.status_code == 400
    assert missing_key.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"

    signup = await api_client.post(
        "/api/v1/auth/owner/signup",
        json=payload,
        headers={"Idempotency-Key": f"owner-signup-{uuid4()}"},
    )
    assert signup.status_code == 201, signup.text

    login = await api_client.post(
        "/api/v1/auth/owner/login",
        json={"email": email, "password": "Strong123"},
    )
    assert login.status_code == 200, login.text
    assert login.json()["access_token"]


def test_demo_reset_refuses_prod(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import demo_reset

    monkeypatch.setenv("ENV", "prod")
    with pytest.raises(SystemExit) as exc_info:
        demo_reset.ensure_not_prod()

    assert exc_info.value.code == 1
