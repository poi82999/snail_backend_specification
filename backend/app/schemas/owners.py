from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import VerificationStatus


class OwnerMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    representative_name: str
    phone_number: str
    verification_status: VerificationStatus
    verification_rejected_reason: str | None = None
    created_at: datetime


class OwnerUpdate(BaseModel):
    representative_name: str | None = Field(default=None, min_length=1, max_length=80)
    phone_number: str | None = Field(default=None, min_length=1, max_length=30)


class BusinessVerificationSubmit(BaseModel):
    business_registration_number: str = Field(min_length=1, max_length=40)
    document_object_key: str = Field(min_length=1)


class BusinessVerificationMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: VerificationStatus
    rejected_reason: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
