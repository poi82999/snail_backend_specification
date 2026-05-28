from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import ReportStatus, ReportTargetType


class ReportCreate(BaseModel):
    target_type: ReportTargetType
    target_id: UUID
    reason: str = Field(min_length=1, max_length=80)
    detail: str | None = None


class ReportPublic(BaseModel):
    id: UUID
    target_type: ReportTargetType
    target_id: UUID
    reason: str
    status: ReportStatus
    created_at: datetime
