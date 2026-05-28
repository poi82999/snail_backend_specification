from uuid import uuid4

import pytest
from app.services.notifications import owner_inbox
from app.services.notifications.templates import NotificationTemplateKey
from app.utils.pagination import CursorParams
from sqlalchemy.ext.asyncio import AsyncSession
from tests.community_factories import create_owner


@pytest.mark.asyncio
async def test_create_owner_notification_and_mark_read(db_session: AsyncSession) -> None:
    owner = await create_owner(db_session)
    notification = await owner_inbox.create_owner_notification(
        db_session,
        owner_id=owner.id,
        template_key=NotificationTemplateKey.RESERVATION_REQUESTED,
        payload={
            "reservation_id": str(uuid4()),
            "shop_name": "스네일 네일",
            "user_name": "민지",
            "date": "06/01",
            "time": "14:00",
        },
        delivery_id=uuid4(),
    )

    assert notification.read_at is None
    assert notification.type == NotificationTemplateKey.RESERVATION_REQUESTED.value

    updated = await owner_inbox.mark_read(db_session, owner.id, notification.id)

    assert updated is not None
    assert updated.read_at is not None


@pytest.mark.asyncio
async def test_list_inbox_filters_unread(db_session: AsyncSession) -> None:
    owner = await create_owner(db_session)
    first = await owner_inbox.create_owner_notification(
        db_session,
        owner_id=owner.id,
        template_key=NotificationTemplateKey.RESERVATION_REQUESTED,
        payload={"reservation_id": str(uuid4()), "shop_name": "샵"},
    )
    await owner_inbox.create_owner_notification(
        db_session,
        owner_id=owner.id,
        template_key=NotificationTemplateKey.RESERVATION_CANCELLED_BY_USER,
        payload={"reservation_id": str(uuid4()), "shop_name": "샵"},
    )
    await owner_inbox.mark_read(db_session, owner.id, first.id)

    rows, next_cursor = await owner_inbox.list_inbox(
        db_session,
        owner.id,
        CursorParams(limit=10),
        unread_only=True,
    )

    assert len(rows) == 1
    assert rows[0].read_at is None
    assert next_cursor is None
