from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import AssignedBy, PaymentMethod, ReservationStatus


class AvailabilityQuery(BaseModel):
    design_id: UUID
    date: date
    option_ids: list[UUID] = Field(default_factory=list)


class AvailableSlot(BaseModel):
    start_at: datetime
    end_at: datetime
    available_designer_ids: list[UUID] = Field(default_factory=list)


class ReservationCreate(BaseModel):
    design_id: UUID
    start_at: datetime
    designer_id: UUID | None = None
    selected_option_ids: list[UUID] = Field(default_factory=list)
    user_request: str | None = Field(default=None, max_length=200)

    @field_validator("start_at")
    @classmethod
    def start_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("start_at must be timezone-aware")
        return value


class ReservationShopSummary(BaseModel):
    id: UUID
    name: str
    region: str | None = None
    thumbnail_url: str | None = None


class ReservationDesignerSummary(BaseModel):
    id: UUID
    name: str
    position: str | None = None
    profile_image_url: str | None = None


class ReservationDesignSummary(BaseModel):
    id: UUID
    title: str
    base_price: int
    duration_minutes: int
    thumbnail_url: str | None = None


class ReservationUserSummary(BaseModel):
    id: UUID
    nickname: str
    profile_image_url: str | None = None


class ReservationMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shop_id: UUID
    design_id: UUID
    designer_id: UUID
    assigned_by: AssignedBy
    start_at: datetime
    end_at: datetime
    status: ReservationStatus
    user_request: str | None = None
    selected_option_ids: list[UUID] = Field(default_factory=list)
    total_price: int
    payment_method_snapshot: PaymentMethod
    deposit_amount_snapshot: int | None = None
    bank_snapshot: dict[str, object] | None = None
    reservation_policy_snapshot: str | None = None
    rejected_reason: str | None = None
    cancelled_reason: str | None = None
    user_payment_notified_at: datetime | None = None
    owner_payment_confirmed_at: datetime | None = None
    reminder_sent_at: datetime | None = None
    completed_at: datetime | None = None
    no_show_at: datetime | None = None
    shop: ReservationShopSummary | None = None
    designer: ReservationDesignerSummary | None = None
    design: ReservationDesignSummary | None = None
    created_at: datetime
    updated_at: datetime


class ReservationOwner(ReservationMe):
    user_id: UUID
    user: ReservationUserSummary | None = None


class ReservationActionRequest(BaseModel):
    reject_reason: str | None = Field(default=None, min_length=1, max_length=1000)
    cancel_reason: str | None = Field(default=None, min_length=1, max_length=1000)


class ReservationStatsMe(BaseModel):
    no_show_count: int
    cancelled_by_user_count: int
    completed_count: int
