from uuid import uuid4

import pytest
from app.models.enums import ActorType, UploadTargetType
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.community_factories import auth_headers, create_upload, create_user, user_token


@pytest.mark.asyncio
async def test_snails_create_feed_like_comment_delete_flow(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session)
    token = user_token(user)
    upload = await create_upload(db_session, ActorType.USER, user.id, UploadTargetType.SNAP)

    create_response = await api_client.post(
        "/api/v1/snails",
        json={
            "body": "new snap",
            "tags": ["simple"],
            "image_upload_keys": [upload.object_key],
        },
        headers=auth_headers(token, f"snap-create-{uuid4()}"),
    )
    assert create_response.status_code == 201
    snap_body = create_response.json()
    snap_id = snap_body["id"]
    assert snap_body["images"] == [upload.original_url]

    feed_response = await api_client.get("/api/v1/snails?feed_type=latest&limit=10")
    assert feed_response.status_code == 200
    assert any(item["id"] == snap_id for item in feed_response.json()["items"])

    like_response = await api_client.post(
        f"/api/v1/snails/{snap_id}/like",
        headers=auth_headers(token, f"snap-like-{uuid4()}"),
    )
    assert like_response.status_code == 200
    assert like_response.json() == {"liked": True, "like_count": 1}

    comment_response = await api_client.post(
        f"/api/v1/snails/{snap_id}/comments",
        json={"body": "nice"},
        headers=auth_headers(token, f"snap-comment-{uuid4()}"),
    )
    assert comment_response.status_code == 201
    assert comment_response.json()["body"] == "nice"

    save_response = await api_client.post(
        f"/api/v1/snails/{snap_id}/save",
        headers=auth_headers(token, f"snap-save-{uuid4()}"),
    )
    assert save_response.status_code == 200
    assert save_response.json() == {"saved": True, "save_count": 1}

    detail = await api_client.get(
        f"/api/v1/snails/{snap_id}",
        headers=auth_headers(token),
    )
    assert detail.status_code == 200
    assert detail.json()["save_count"] == 1
    assert detail.json()["saved_by_me"] is True

    unsave_response = await api_client.post(
        f"/api/v1/snails/{snap_id}/save",
        headers=auth_headers(token, f"snap-unsave-{uuid4()}"),
    )
    assert unsave_response.status_code == 200
    assert unsave_response.json() == {"saved": False, "save_count": 0}

    delete_response = await api_client.delete(
        f"/api/v1/snails/{snap_id}",
        headers=auth_headers(token, f"snap-delete-{uuid4()}"),
    )
    assert delete_response.status_code == 204

    deleted_detail = await api_client.get(f"/api/v1/snails/{snap_id}")
    assert deleted_detail.status_code == 404
