from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import OwnerNotification
from app.services.notifications.templates import (
    InboxContent,
    NotificationTemplateKey,
    ReservationNotificationPayload,
    render_inbox,
)
from app.utils.pagination import CursorParams, paginate_query


def _now() -> datetime:
    return datetime.now(UTC)


async def create_owner_notification(
    session: AsyncSession,
    *,
    owner_id: UUID,
    template_key: NotificationTemplateKey | str,
    payload: ReservationNotificationPayload,
    delivery_id: UUID | None = None,
) -> OwnerNotification:
    content = render_inbox(template_key, payload)
    metadata = dict(content.metadata)
    if delivery_id is not None:
        metadata["delivery_id"] = str(delivery_id)
    notification = OwnerNotification(
        id=uuid4(),
        owner_id=owner_id,
        type=NotificationTemplateKey(template_key).value,
        title=content.title,
        body=content.body,
        resource_type=content.resource_type,
        resource_id=content.resource_id,
        deeplink=content.deeplink,
        metadata_=metadata,
    )
    session.add(notification)
    await session.flush()
    return notification


async def create_from_content(
    session: AsyncSession,
    *,
    owner_id: UUID,
    notification_type: str,
    content: InboxContent,
) -> OwnerNotification:
    notification = OwnerNotification(
        id=uuid4(),
        owner_id=owner_id,
        type=notification_type,
        title=content.title,
        body=content.body,
        resource_type=content.resource_type,
        resource_id=content.resource_id,
        deeplink=content.deeplink,
        metadata_=content.metadata,
    )
    session.add(notification)
    await session.flush()
    return notification


async def list_inbox(
    session: AsyncSession,
    owner_id: UUID,
    params: CursorParams,
    *,
    unread_only: bool = False,
) -> tuple[list[OwnerNotification], str | None]:
    statement = select(OwnerNotification).where(OwnerNotification.owner_id == owner_id)
    if unread_only:
        statement = statement.where(OwnerNotification.read_at.is_(None))
    return await paginate_query(session, statement, OwnerNotification, params)


async def list_owner_notifications(
    session: AsyncSession,
    owner_id: UUID,
    *,
    unread_only: bool,
    params: CursorParams,
) -> tuple[list[OwnerNotification], str | None]:
    return await list_inbox(session, owner_id, params, unread_only=unread_only)


async def unread_count(session: AsyncSession, owner_id: UUID) -> int:
    return int(
        await session.scalar(
            select(func.count(OwnerNotification.id)).where(
                OwnerNotification.owner_id == owner_id,
                OwnerNotification.read_at.is_(None),
            )
        )
        or 0
    )


async def mark_read(
    session: AsyncSession,
    owner_id: UUID,
    notification_id: UUID,
) -> OwnerNotification | None:
    notification = await session.scalar(
        select(OwnerNotification).where(
            OwnerNotification.id == notification_id,
            OwnerNotification.owner_id == owner_id,
        )
    )
    if notification is None:
        return None
    if notification.read_at is None:
        notification.read_at = _now()
        await session.flush()
    return notification


async def mark_all_read(session: AsyncSession, owner_id: UUID) -> int:
    result = await session.execute(
        update(OwnerNotification)
        .where(
            OwnerNotification.owner_id == owner_id,
            OwnerNotification.read_at.is_(None),
        )
        .values(read_at=_now())
    )
    await session.flush()
    return int(result.rowcount or 0)
