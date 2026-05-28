from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.models.enums import PaymentMethod
from app.services import reservation_policy
from httpx import AsyncClient

pytestmark = pytest.mark.e2e


async def _create_pending_reservation(
    api_client: AsyncClient,
    e2e_factory,
    ctx,
) -> str:
    response = await api_client.post(
        "/api/v1/reservations",
        json=e2e_factory.reservation_payload(ctx),
        headers=e2e_factory.auth_headers(ctx.user_token, f"reservation-create-{uuid4()}"),
    )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "pending"
    return str(response.json()["id"])


@pytest.mark.asyncio
async def test_pending_to_rejected_path(api_client: AsyncClient, e2e_factory) -> None:
    ctx = await e2e_factory.ready_reservation_context()
    reservation_id = await _create_pending_reservation(api_client, e2e_factory, ctx)

    response = await api_client.post(
        f"/api/v1/shops/me/reservations/{reservation_id}/reject",
        json={"reject_reason": "해당 시간 시술이 어렵습니다."},
        headers=e2e_factory.auth_headers(ctx.owner_token, f"reservation-reject-{uuid4()}"),
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "rejected"
    assert response.json()["rejected_reason"] == "해당 시간 시술이 어렵습니다."


@pytest.mark.asyncio
async def test_pending_to_cancelled_by_user_path(api_client: AsyncClient, e2e_factory) -> None:
    ctx = await e2e_factory.ready_reservation_context()
    reservation_id = await _create_pending_reservation(api_client, e2e_factory, ctx)

    response = await api_client.post(
        f"/api/v1/me/reservations/{reservation_id}/cancel",
        json={"cancel_reason": "일정 변경"},
        headers=e2e_factory.auth_headers(ctx.user_token, f"reservation-user-cancel-{uuid4()}"),
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "cancelled_by_user"
    assert response.json()["cancelled_reason"] == "일정 변경"


@pytest.mark.asyncio
async def test_on_site_confirmed_to_cancelled_by_shop_path(
    api_client: AsyncClient,
    e2e_factory,
) -> None:
    ctx = await e2e_factory.ready_reservation_context()
    reservation_id = await _create_pending_reservation(api_client, e2e_factory, ctx)

    accepted = await api_client.post(
        f"/api/v1/shops/me/reservations/{reservation_id}/accept",
        headers=e2e_factory.auth_headers(ctx.owner_token, f"reservation-accept-{uuid4()}"),
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "confirmed"

    cancelled = await api_client.post(
        f"/api/v1/shops/me/reservations/{reservation_id}/cancel",
        json={"cancel_reason": "샵 사정으로 취소합니다."},
        headers=e2e_factory.auth_headers(ctx.owner_token, f"reservation-shop-cancel-{uuid4()}"),
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "cancelled_by_shop"


@pytest.mark.asyncio
async def test_on_site_confirmed_to_completed_to_review_path(
    api_client: AsyncClient,
    e2e_factory,
) -> None:
    ctx = await e2e_factory.ready_reservation_context()
    reservation_id = await _create_pending_reservation(api_client, e2e_factory, ctx)

    accepted = await api_client.post(
        f"/api/v1/shops/me/reservations/{reservation_id}/accept",
        headers=e2e_factory.auth_headers(ctx.owner_token, f"reservation-accept-{uuid4()}"),
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "confirmed"

    completed = await api_client.post(
        f"/api/v1/shops/me/reservations/{reservation_id}/complete",
        headers=e2e_factory.auth_headers(ctx.owner_token, f"reservation-complete-{uuid4()}"),
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"

    review = await api_client.post(
        f"/api/v1/reservations/{reservation_id}/reviews",
        json={"rating": 5, "body": "상태 전이 후 작성한 리뷰"},
        headers=e2e_factory.auth_headers(ctx.user_token, f"reservation-review-{uuid4()}"),
    )
    assert review.status_code == 201, review.text
    assert review.json()["reservation_id"] == reservation_id


@pytest.mark.asyncio
async def test_bank_transfer_pending_to_payment_pending_confirmed_completed_path(
    api_client: AsyncClient,
    e2e_factory,
) -> None:
    ctx = await e2e_factory.ready_reservation_context(
        payment_method=PaymentMethod.BANK_TRANSFER_GUIDE,
    )
    reservation_id = await _create_pending_reservation(api_client, e2e_factory, ctx)

    accepted = await api_client.post(
        f"/api/v1/shops/me/reservations/{reservation_id}/accept",
        headers=e2e_factory.auth_headers(ctx.owner_token, f"reservation-bank-accept-{uuid4()}"),
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "payment_pending"
    assert accepted.json()["deposit_amount_snapshot"] == 10000
    assert accepted.json()["bank_snapshot"]["bank_name"] == "테스트은행"

    confirmed = await api_client.post(
        f"/api/v1/shops/me/reservations/{reservation_id}/confirm-payment",
        headers=e2e_factory.auth_headers(ctx.owner_token, f"reservation-bank-confirm-{uuid4()}"),
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "confirmed"
    assert confirmed.json()["owner_payment_confirmed_at"] is not None

    completed = await api_client.post(
        f"/api/v1/shops/me/reservations/{reservation_id}/complete",
        headers=e2e_factory.auth_headers(ctx.owner_token, f"reservation-bank-complete-{uuid4()}"),
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_confirmed_to_no_show_path_after_start_plus_30_minutes(
    api_client: AsyncClient,
    e2e_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = await e2e_factory.ready_reservation_context()
    reservation_id = await _create_pending_reservation(api_client, e2e_factory, ctx)
    accepted = await api_client.post(
        f"/api/v1/shops/me/reservations/{reservation_id}/accept",
        headers=e2e_factory.auth_headers(ctx.owner_token, f"reservation-accept-{uuid4()}"),
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "confirmed"

    fake_now = ctx.start_at + timedelta(minutes=31)

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz: object = None) -> datetime:
            if tz is None:
                return fake_now.replace(tzinfo=None)
            if tz == UTC:
                return fake_now
            return fake_now.astimezone(tz)  # type: ignore[arg-type]

    monkeypatch.setattr(reservation_policy, "datetime", FrozenDateTime)

    no_show = await api_client.post(
        f"/api/v1/shops/me/reservations/{reservation_id}/no-show",
        headers=e2e_factory.auth_headers(ctx.owner_token, f"reservation-no-show-{uuid4()}"),
    )
    assert no_show.status_code == 200, no_show.text
    assert no_show.json()["status"] == "no_show"
    assert no_show.json()["no_show_at"] is not None
