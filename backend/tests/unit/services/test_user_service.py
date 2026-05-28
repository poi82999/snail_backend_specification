from uuid import uuid4

import pytest
from app.api.errors import AppError
from app.models.accounts import User
from app.schemas.users import UserUpdate
from app.services import user_service
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_update_me_rejects_duplicate_nickname(db_session: AsyncSession) -> None:
    existing = User(
        id=uuid4(),
        apple_sub="apple-existing",
        email="existing@example.com",
        nickname="taken",
    )
    user = User(
        id=uuid4(),
        apple_sub="apple-user",
        email="user@example.com",
        nickname="user",
    )
    db_session.add_all([existing, user])
    await db_session.flush()

    with pytest.raises(AppError) as exc_info:
        await user_service.update_me(db_session, user.id, UserUpdate(nickname="taken"))

    assert exc_info.value.code == "NICKNAME_TAKEN"
    assert exc_info.value.status_code == 409
