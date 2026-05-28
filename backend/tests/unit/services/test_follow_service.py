from http import HTTPStatus

import pytest
from app.api.errors import AppError
from app.services import follow_service
from sqlalchemy.ext.asyncio import AsyncSession
from tests.community_factories import create_user


@pytest.mark.asyncio
async def test_toggle_follow_rejects_self_follow(db_session: AsyncSession) -> None:
    user = await create_user(db_session)

    with pytest.raises(AppError) as exc_info:
        await follow_service.toggle_follow(db_session, user.id, user.id)

    assert exc_info.value.code == "CANNOT_FOLLOW_SELF"
    assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_toggle_follow_adds_then_removes_pair(db_session: AsyncSession) -> None:
    follower = await create_user(db_session)
    following = await create_user(db_session)

    first = await follow_service.toggle_follow(db_session, follower.id, following.id)
    second = await follow_service.toggle_follow(db_session, follower.id, following.id)

    assert first.followed is True
    assert first.follower_count == 1
    assert second.followed is False
    assert second.follower_count == 0
