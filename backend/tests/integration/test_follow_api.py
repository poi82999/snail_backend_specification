from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.community_factories import auth_headers, create_user, user_token


@pytest.mark.asyncio
async def test_follow_toggle_and_lists(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    follower = await create_user(db_session, "follower")
    following = await create_user(db_session, "following")
    token = user_token(follower)

    first = await api_client.post(
        f"/api/v1/users/{following.id}/follow",
        headers=auth_headers(token, f"follow-on-{uuid4()}"),
    )
    assert first.status_code == 200
    assert first.json() == {"followed": True, "follower_count": 1}

    followers = await api_client.get(f"/api/v1/users/{following.id}/followers")
    assert followers.status_code == 200
    assert [item["id"] for item in followers.json()["data"]] == [str(follower.id)]

    following_list = await api_client.get(f"/api/v1/users/{follower.id}/following")
    assert following_list.status_code == 200
    assert [item["id"] for item in following_list.json()["data"]] == [str(following.id)]

    second = await api_client.post(
        f"/api/v1/users/{following.id}/follow",
        headers=auth_headers(token, f"follow-off-{uuid4()}"),
    )
    assert second.status_code == 200
    assert second.json() == {"followed": False, "follower_count": 0}


@pytest.mark.asyncio
async def test_followers_cursor_pagination(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    target = await create_user(db_session, "target")
    followers = [await create_user(db_session, f"follower_{index}") for index in range(11)]

    for index, follower in enumerate(followers):
        await api_client.post(
            f"/api/v1/users/{target.id}/follow",
            headers=auth_headers(user_token(follower), f"follow-page-{index}-{uuid4()}"),
        )

    first = await api_client.get(f"/api/v1/users/{target.id}/followers", params={"limit": 5})
    assert first.status_code == 200
    first_body = first.json()
    assert len(first_body["data"]) == 5
    assert first_body["page"]["next_cursor"] is not None

    second = await api_client.get(
        f"/api/v1/users/{target.id}/followers",
        params={"limit": 5, "cursor": first_body["page"]["next_cursor"]},
    )
    assert second.status_code == 200
    second_body = second.json()
    assert len(second_body["data"]) == 5
    assert second_body["page"]["next_cursor"] is not None

    third = await api_client.get(
        f"/api/v1/users/{target.id}/followers",
        params={"limit": 5, "cursor": second_body["page"]["next_cursor"]},
    )
    assert third.status_code == 200
    third_body = third.json()
    assert len(third_body["data"]) == 1
    assert third_body["page"]["next_cursor"] is None
