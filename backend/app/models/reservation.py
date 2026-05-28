from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AssignedBy, PaymentMethod, ReservationStatus

if TYPE_CHECKING:
    from app.models.community import Review


class Reservation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reservations"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_reservations_idempotency_key"),)

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    shop_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("shops.id"))
    design_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("designs.id"))
    designer_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("designers.id"))
    assigned_by: Mapped[AssignedBy] = mapped_column(
        Enum(AssignedBy, native_enum=False, length=30), default=AssignedBy.AUTO, nullable=False
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, native_enum=False, length=40),
        default=ReservationStatus.PENDING,
        nullable=False,
    )
    user_request: Mapped[str | None] = mapped_column(Text)
    total_price: Mapped[int] = mapped_column(Integer)
    payment_method_snapshot: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, native_enum=False, length=40), nullable=False
    )
    deposit_amount_snapshot: Mapped[int | None] = mapped_column(Integer)
    bank_snapshot: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    reservation_policy_snapshot: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(120))
    rejected_reason: Mapped[str | None] = mapped_column(Text)
    cancelled_reason: Mapped[str | None] = mapped_column(Text)
    user_payment_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    owner_payment_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    no_show_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    review: Mapped[Review | None] = relationship(back_populates="reservation")


class IdempotencyKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint("actor_type", "actor_id", "key", name="uq_idempotency_actor_key"),
    )

    actor_type: Mapped[str] = mapped_column(String(30))
    actor_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    key: Mapped[str] = mapped_column(String(120))
    request_hash: Mapped[str] = mapped_column(String(128))
    response_status: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
