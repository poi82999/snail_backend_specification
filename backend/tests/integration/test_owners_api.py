from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_owner_me_without_auth_returns_401(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/owners/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_patch_owner_me_updates_profile(api_client: AsyncClient, owner_token: str) -> None:
    response = await api_client.patch(
        "/api/v1/owners/me",
        json={"representative_name": "변경 대표"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "Idempotency-Key": f"owner-patch-{uuid4()}",
        },
    )

    assert response.status_code == 200
    assert response.json()["representative_name"] == "변경 대표"
