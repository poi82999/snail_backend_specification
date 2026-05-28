from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import NotificationChannel, NotificationStatus


class OwnerNotification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "owner_notifications"

    owner_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("owners.id"))
    type: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(120))
    body: Mapped[str] = mapped_column(Text)
    resource_type: Mapped[str | None] = mapped_column(String(40))
    resource_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True))
    deeplink: Mapped[str | None] = mapped_column(Text)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSONB)

    deliveries: Mapped[list["NotificationDelivery"]] = relationship(
        back_populates="owner_notification"
    )


class NotificationDelivery(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notification_deliveries"

    owner_notification_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("owner_notifications.id")
    )
    recipient_user_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id")
    )
    recipient_owner_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("owners.id")
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, native_enum=False, length=40), nullable=False
    )
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, native_enum=False, length=30),
        default=NotificationStatus.QUEUED,
        nullable=False,
    )
    template_code: Mapped[str | None] = mapped_column(String(120))
    payload: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    provider_message_id: Mapped[str | None] = mapped_column(String(160))
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_reason: Mapped[str | None] = mapped_column(Text)

    owner_notification: Mapped[OwnerNotification | None] = relationship(back_populates="deliveries")
