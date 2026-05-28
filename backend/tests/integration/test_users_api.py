from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_me_without_auth_returns_401(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_patch_me_updates_nickname(api_client: AsyncClient, user_token: str) -> None:
    nickname = f"user_{uuid4().hex[:8]}"
    response = await api_client.patch(
        "/api/v1/me",
        json={"nickname": nickname},
        headers={
            "Authorization": f"Bearer {user_token}",
            "Idempotency-Key": f"user-patch-{uuid4()}",
        },
    )

    assert response.status_code == 200
    assert response.json()["nickname"] == nickname
