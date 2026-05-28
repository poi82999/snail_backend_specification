from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import UploadTargetType


class UploadObject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "upload_objects"

    owner_actor_type: Mapped[str] = mapped_column(String(30))
    owner_actor_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    target_type: Mapped[UploadTargetType] = mapped_column(
        Enum(UploadTargetType, native_enum=False, length=40), nullable=False
    )
    object_key: Mapped[str] = mapped_column(Text, unique=True)
    content_type: Mapped[str] = mapped_column(String(120))
    byte_size: Mapped[int] = mapped_column(Integer)
    original_url: Mapped[str | None] = mapped_column(Text)
    processed_url: Mapped[str | None] = mapped_column(Text)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
