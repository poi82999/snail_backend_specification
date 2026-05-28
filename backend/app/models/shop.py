from __future__ import annotations

from datetime import date, time
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import PaymentMethod, Visibility

if TYPE_CHECKING:
    from app.models.accounts import Owner
    from app.models.design import Design


class Shop(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "shops"

    owner_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("owners.id"), unique=True
    )
    name: Mapped[str] = mapped_column(String(120))
    address: Mapped[str] = mapped_column(Text)
    address_detail: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(String(80))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    phone_number: Mapped[str] = mapped_column(String(30))
    introduction: Mapped[str | None] = mapped_column(Text)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    visibility: Mapped[Visibility] = mapped_column(
        Enum(Visibility, native_enum=False, length=30),
        default=Visibility.DRAFT,
        nullable=False,
    )
    auto_accept: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reservation_policy: Mapped[str | None] = mapped_column(Text)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, native_enum=False, length=40),
        default=PaymentMethod.ON_SITE,
        nullable=False,
    )
    deposit_amount: Mapped[int | None] = mapped_column(Integer)
    bank_name: Mapped[str | None] = mapped_column(String(80))
    bank_account_number: Mapped[str | None] = mapped_column(String(80))
    bank_account_holder: Mapped[str | None] = mapped_column(String(80))
    average_rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0, nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    favorite_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    owner: Mapped[Owner] = relationship(back_populates="shop")
    images: Mapped[list[ShopImage]] = relationship(back_populates="shop")
    business_hours: Mapped[list[ShopBusinessHour]] = relationship(back_populates="shop")
    designers: Mapped[list[Designer]] = relationship(back_populates="shop")
    designs: Mapped[list[Design]] = relationship(back_populates="shop")


class ShopImage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "shop_images"

    shop_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("shops.id"))
    image_url: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_thumbnail: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    shop: Mapped[Shop] = relationship(back_populates="images")


class ShopBusinessHour(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "shop_business_hours"
    __table_args__ = (UniqueConstraint("shop_id", "weekday", name="uq_shop_business_hours_day"),)

    shop_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("shops.id"))
    weekday: Mapped[int] = mapped_column(Integer)
    open_time: Mapped[time | None] = mapped_column(Time(timezone=False))
    close_time: Mapped[time | None] = mapped_column(Time(timezone=False))
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    shop: Mapped[Shop] = relationship(back_populates="business_hours")


class Designer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "designers"

    shop_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("shops.id"))
    name: Mapped[str] = mapped_column(String(80))
    position: Mapped[str | None] = mapped_column(String(80))
    career_years: Mapped[int | None] = mapped_column(Integer)
    profile_image_url: Mapped[str | None] = mapped_column(Text)
    specialty_tags: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    shop: Mapped[Shop] = relationship(back_populates="designers")
    schedules: Mapped[list[DesignerSchedule]] = relationship(back_populates="designer")
    time_offs: Mapped[list[DesignerTimeOff]] = relationship(back_populates="designer")


class DesignerSchedule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "designer_schedules"
    __table_args__ = (UniqueConstraint("designer_id", "weekday", name="uq_designer_schedules_day"),)

    designer_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("designers.id"))
    weekday: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[time | None] = mapped_column(Time(timezone=False))
    end_time: Mapped[time | None] = mapped_column(Time(timezone=False))
    break_start_time: Mapped[time | None] = mapped_column(Time(timezone=False))
    break_end_time: Mapped[time | None] = mapped_column(Time(timezone=False))
    is_day_off: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    designer: Mapped[Designer] = relationship(back_populates="schedules")


class DesignerTimeOff(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "designer_time_offs"

    designer_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("designers.id"))
    off_date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time | None] = mapped_column(Time(timezone=False))
    end_time: Mapped[time | None] = mapped_column(Time(timezone=False))
    reason: Mapped[str | None] = mapped_column(Text)

    designer: Mapped[Designer] = relationship(back_populates="time_offs")
