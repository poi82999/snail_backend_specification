from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import PageMeta


class OwnerNotificationPublic(BaseModel):
    id: UUID
    type: str
    title: str
    body: str
    resource_type: str | None = None
    resource_id: UUID | None = None
    deeplink: str | None = None
    metadata: dict[str, object] | None = None
    read_at: datetime | None = None
    created_at: datetime


class OwnerNotificationListResponse(BaseModel):
    data: list[OwnerNotificationPublic]
    page: PageMeta = Field(default_factory=PageMeta)
    unread_count: int
    request_id: str
