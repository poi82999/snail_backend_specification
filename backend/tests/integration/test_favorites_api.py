from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.community_factories import (
    auth_headers,
    create_design,
    create_owner,
    create_shop,
    create_user,
    user_token,
)


@pytest.mark.asyncio
async def test_design_favorite_toggle_with_public_guard(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user(db_session)
    owner = await create_owner(db_session, approved=True)
    shop = await create_shop(db_session, owner)
    design = await create_design(db_session, shop)
    token = user_token(user)

    first = await api_client.post(
        f"/api/v1/designs/{design.id}/favorite",
        headers=auth_headers(token, f"favorite-on-{uuid4()}"),
    )
    assert first.status_code == 200
    assert first.json() == {"liked": True, "like_count": 1}

    second = await api_client.post(
        f"/api/v1/designs/{design.id}/favorite",
        headers=auth_headers(token, f"favorite-off-{uuid4()}"),
    )
    assert second.status_code == 200
    assert second.json() == {"liked": False, "like_count": 0}
