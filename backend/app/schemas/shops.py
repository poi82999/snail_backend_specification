from datetime import datetime, time
from decimal import Decimal
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PaymentMethod, VerificationStatus, Visibility
from app.models.shop import Shop


class ShopCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    address: str = Field(min_length=1)
    address_detail: str | None = None
    region: str | None = Field(default=None, max_length=80)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    phone_number: str = Field(min_length=1, max_length=30)
    introduction: str | None = None
    payment_method: PaymentMethod = PaymentMethod.ON_SITE
    deposit_amount: int | None = Field(default=None, ge=0)
    bank_name: str | None = Field(default=None, max_length=80)
    bank_account_number: str | None = Field(default=None, max_length=80)
    bank_account_holder: str | None = Field(default=None, max_length=80)
    auto_accept: bool = False
    reservation_policy: str | None = None


class ShopUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    address: str | None = Field(default=None, min_length=1)
    address_detail: str | None = None
    region: str | None = Field(default=None, max_length=80)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    phone_number: str | None = Field(default=None, min_length=1, max_length=30)
    introduction: str | None = None
    payment_method: PaymentMethod | None = None
    deposit_amount: int | None = Field(default=None, ge=0)
    bank_name: str | None = Field(default=None, max_length=80)
    bank_account_number: str | None = Field(default=None, max_length=80)
    bank_account_holder: str | None = Field(default=None, max_length=80)
    auto_accept: bool | None = None
    reservation_policy: str | None = None


class ShopImageCreate(BaseModel):
    upload_object_key: str = Field(min_length=1)
    sort_order: int = 0
    is_thumbnail: bool = False


class ShopImagePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    image_url: str
    sort_order: int
    is_thumbnail: bool


class BusinessHourEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    weekday: int = Field(ge=0, le=6)
    open_time: time | None = None
    close_time: time | None = None
    is_closed: bool = False


class BusinessHoursSet(BaseModel):
    entries: list[BusinessHourEntry] = Field(default_factory=list, max_length=7)


class ShopMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    name: str
    address: str
    address_detail: str | None = None
    region: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    phone_number: str
    introduction: str | None = None
    thumbnail_url: str | None = None
    visibility: Visibility
    auto_accept: bool
    reservation_policy: str | None = None
    payment_method: PaymentMethod
    deposit_amount: int | None = None
    bank_name: str | None = None
    bank_account_number: str | None = None
    bank_account_holder: str | None = None
    average_rating: Decimal
    review_count: int
    favorite_count: int
    verification_status: VerificationStatus
    images: list[ShopImagePublic] = Field(default_factory=list)
    business_hours: list[BusinessHourEntry] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_shop(cls, shop: Shop, verification_status: VerificationStatus) -> Self:
        images = sorted(shop.images, key=lambda image: (image.sort_order, image.id))
        business_hours = sorted(shop.business_hours, key=lambda hour: hour.weekday)
        return cls(
            id=shop.id,
            owner_id=shop.owner_id,
            name=shop.name,
            address=shop.address,
            address_detail=shop.address_detail,
            region=shop.region,
            latitude=shop.latitude,
            longitude=shop.longitude,
            phone_number=shop.phone_number,
            introduction=shop.introduction,
            thumbnail_url=shop.thumbnail_url,
            visibility=shop.visibility,
            auto_accept=shop.auto_accept,
            reservation_policy=shop.reservation_policy,
            payment_method=shop.payment_method,
            deposit_amount=shop.deposit_amount,
            bank_name=shop.bank_name,
            bank_account_number=shop.bank_account_number,
            bank_account_holder=shop.bank_account_holder,
            average_rating=shop.average_rating,
            review_count=shop.review_count,
            favorite_count=shop.favorite_count,
            verification_status=verification_status,
            images=[ShopImagePublic.model_validate(image) for image in images],
            business_hours=[BusinessHourEntry.model_validate(hour) for hour in business_hours],
            created_at=shop.created_at,
            updated_at=shop.updated_at,
        )


class ShopPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    address: str
    address_detail: str | None = None
    region: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    phone_number: str
    introduction: str | None = None
    thumbnail_url: str | None = None
    auto_accept: bool
    reservation_policy: str | None = None
    payment_method: PaymentMethod
    deposit_amount: int | None = None
    average_rating: Decimal
    review_count: int
    favorite_count: int
    images: list[ShopImagePublic] = Field(default_factory=list)
    business_hours: list[BusinessHourEntry] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_shop(cls, shop: Shop) -> Self:
        images = sorted(shop.images, key=lambda image: (image.sort_order, image.id))
        business_hours = sorted(shop.business_hours, key=lambda hour: hour.weekday)
        return cls(
            id=shop.id,
            name=shop.name,
            address=shop.address,
            address_detail=shop.address_detail,
            region=shop.region,
            latitude=shop.latitude,
            longitude=shop.longitude,
            phone_number=shop.phone_number,
            introduction=shop.introduction,
            thumbnail_url=shop.thumbnail_url,
            auto_accept=shop.auto_accept,
            reservation_policy=shop.reservation_policy,
            payment_method=shop.payment_method,
            deposit_amount=shop.deposit_amount,
            average_rating=shop.average_rating,
            review_count=shop.review_count,
            favorite_count=shop.favorite_count,
            images=[ShopImagePublic.model_validate(image) for image in images],
            business_hours=[BusinessHourEntry.model_validate(hour) for hour in business_hours],
            created_at=shop.created_at,
            updated_at=shop.updated_at,
        )
