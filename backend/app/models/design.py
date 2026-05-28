from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    AiAnalysisStatus,
    DesignOptionKind,
    JobStatus,
    LlmJobType,
    Visibility,
)

if TYPE_CHECKING:
    from app.models.shop import Shop


class DesignDesigner(Base):
    __tablename__ = "design_designers"
    __table_args__ = (UniqueConstraint("design_id", "designer_id", name="uq_design_designers"),)

    design_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("designs.id"), primary_key=True
    )
    designer_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("designers.id"), primary_key=True
    )


class Design(UUIDPrimaryKeyMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "designs"

    shop_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("shops.id"))
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    base_price: Mapped[int] = mapped_column(Integer)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    visibility: Mapped[Visibility] = mapped_column(
        Enum(Visibility, native_enum=False, length=30),
        default=Visibility.DRAFT,
        nullable=False,
    )
    ai_analysis_status: Mapped[AiAnalysisStatus] = mapped_column(
        Enum(AiAnalysisStatus, native_enum=False, length=30),
        default=AiAnalysisStatus.PENDING,
        nullable=False,
    )
    owner_tags: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list)
    ai_tags: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list)
    color_palette: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list)
    style_category: Mapped[str | None] = mapped_column(String(40))
    nail_shape: Mapped[str | None] = mapped_column(String(40))
    ai_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    ai_error_code: Mapped[str | None] = mapped_column(String(80))
    ai_error_message: Mapped[str | None] = mapped_column(Text)
    ai_model_version: Mapped[str | None] = mapped_column(String(120))
    search_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

    shop: Mapped[Shop] = relationship(back_populates="designs")
    images: Mapped[list[DesignImage]] = relationship(back_populates="design")
    llm_jobs: Mapped[list[LlmJob]] = relationship(back_populates="design")
    options: Mapped[list[DesignOption]] = relationship(back_populates="design")


class DesignOption(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "design_options"

    design_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("designs.id"))
    kind: Mapped[DesignOptionKind] = mapped_column(
        Enum(DesignOptionKind, native_enum=False, length=20), nullable=False
    )
    name: Mapped[str] = mapped_column(String(80))
    price_delta: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_delta_min: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    design: Mapped[Design] = relationship(back_populates="options")


class DesignImage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "design_images"

    design_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("designs.id"))
    original_url: Mapped[str] = mapped_column(Text)
    processed_url: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_thumbnail: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    content_hash: Mapped[str | None] = mapped_column(String(128))

    design: Mapped[Design] = relationship(back_populates="images")


class LlmJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "llm_jobs"

    design_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("designs.id"))
    design_image_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("design_images.id")
    )
    job_type: Mapped[LlmJobType] = mapped_column(
        Enum(LlmJobType, native_enum=False, length=30), nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False, length=30), default=JobStatus.QUEUED, nullable=False
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    request_payload: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    response_payload: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    design: Mapped[Design] = relationship(back_populates="llm_jobs")
