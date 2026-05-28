from uuid import uuid4

import pytest
from app.models.enums import ReservationStatus
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.community_factories import (
    auth_headers,
    create_design,
    create_designer,
    create_owner,
    create_reservation,
    create_shop,
    create_user,
    owner_token,
    user_token,
)


@pytest.mark.asyncio
async def test_reviews_completed_only_unique_and_owner_reply(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session)
    owner = await create_owner(db_session)
    shop = await create_shop(db_session, owner)
    designer = await create_designer(db_session, shop)
    design = await create_design(db_session, shop)
    completed = await create_reservation(
        db_session,
        user,
        shop,
        design,
        designer,
        ReservationStatus.COMPLETED,
    )
    confirmed = await create_reservation(
        db_session,
        user,
        shop,
        design,
        designer,
        ReservationStatus.CONFIRMED,
    )
    user_auth = user_token(user)

    rejected = await api_client.post(
        f"/api/v1/reservations/{confirmed.id}/reviews",
        json={"rating": 5, "body": "not yet"},
        headers=auth_headers(user_auth, f"review-reject-{uuid4()}"),
    )
    assert rejected.status_code == 400
    assert rejected.json()["error"]["code"] == "RESERVATION_NOT_COMPLETED"

    created = await api_client.post(
        f"/api/v1/reservations/{completed.id}/reviews",
        json={"rating": 5, "body": "great"},
        headers=auth_headers(user_auth, f"review-create-{uuid4()}"),
    )
    assert created.status_code == 201
    review_id = created.json()["id"]

    duplicate = await api_client.post(
        f"/api/v1/reservations/{completed.id}/reviews",
        json={"rating": 4, "body": "again"},
        headers=auth_headers(user_auth, f"review-duplicate-{uuid4()}"),
    )
    assert duplicate.status_code == 409

    reply = await api_client.post(
        f"/api/v1/reviews/{review_id}/replies",
        json={"body": "thanks"},
        headers=auth_headers(owner_token(owner), f"review-reply-{uuid4()}"),
    )
    assert reply.status_code == 201
    assert reply.json()["body"] == "thanks"

    shop_reviews = await api_client.get(f"/api/v1/shops/{shop.id}/reviews")
    assert shop_reviews.status_code == 200
    assert shop_reviews.json()[0]["reply"]["body"] == "thanks"
