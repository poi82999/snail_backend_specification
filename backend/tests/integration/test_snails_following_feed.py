from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.community_factories import auth_headers, create_user, user_token


@pytest.mark.asyncio
async def test_following_feed_shows_followed_user_only(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    viewer = await create_user(db_session, "viewer")
    followed = await create_user(db_session, "followed")
    not_followed = await create_user(db_session, "not_followed")
    viewer_token = user_token(viewer)
    followed_token = user_token(followed)
    not_followed_token = user_token(not_followed)

    follow_response = await api_client.post(
        f"/api/v1/users/{followed.id}/follow",
        headers=auth_headers(viewer_token, f"follow-{uuid4()}"),
    )
    assert follow_response.status_code == 200
    assert follow_response.json()["followed"] is True

    followed_snap = await api_client.post(
        "/api/v1/snails",
        json={"body": "followed snap"},
        headers=auth_headers(followed_token, f"followed-snap-{uuid4()}"),
    )
    assert followed_snap.status_code == 201
    other_snap = await api_client.post(
        "/api/v1/snails",
        json={"body": "other snap"},
        headers=auth_headers(not_followed_token, f"other-snap-{uuid4()}"),
    )
    assert other_snap.status_code == 201

    feed_response = await api_client.get(
        "/api/v1/snails?feed_type=following&limit=10",
        headers=auth_headers(viewer_token),
    )

    assert feed_response.status_code == 200
    ids = {item["id"] for item in feed_response.json()["items"]}
    assert ids == {followed_snap.json()["id"]}
