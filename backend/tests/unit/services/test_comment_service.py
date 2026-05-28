from http import HTTPStatus

import pytest
from app.api.errors import AppError
from app.models.enums import ActorType
from app.schemas.comments import CommentCreate
from app.services import comment_service
from sqlalchemy.ext.asyncio import AsyncSession
from tests.community_factories import (
    create_owner,
    create_shop,
    create_snap,
    create_user,
)


@pytest.mark.asyncio
async def test_owner_comment_rejected_when_snap_does_not_tag_own_shop(
    db_session: AsyncSession,
) -> None:
    owner = await create_owner(db_session)
    other_owner = await create_owner(db_session)
    await create_shop(db_session, owner)
    other_shop = await create_shop(db_session, other_owner)
    user = await create_user(db_session)
    snap = await create_snap(db_session, user, tagged_shop_id=other_shop.id)

    with pytest.raises(AppError) as exc_info:
        await comment_service.create_comment(
            db_session,
            ActorType.OWNER,
            owner.id,
            snap.id,
            CommentCreate(body="owner comment"),
        )

    assert exc_info.value.code == "FORBIDDEN"
    assert exc_info.value.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_create_comment_rejects_depth_three(db_session: AsyncSession) -> None:
    user = await create_user(db_session)
    snap = await create_snap(db_session, user)
    root = await comment_service.create_comment(
        db_session,
        ActorType.USER,
        user.id,
        snap.id,
        CommentCreate(body="root"),
    )
    reply = await comment_service.create_comment(
        db_session,
        ActorType.USER,
        user.id,
        snap.id,
        CommentCreate(body="reply", parent_id=root.id),
    )

    with pytest.raises(AppError) as exc_info:
        await comment_service.create_comment(
            db_session,
            ActorType.USER,
            user.id,
            snap.id,
            CommentCreate(body="depth three", parent_id=reply.id),
        )

    assert exc_info.value.code == "COMMENT_DEPTH_EXCEEDED"
    assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
