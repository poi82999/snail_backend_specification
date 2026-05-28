from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.users import UserPublic


class SnapCreate(BaseModel):
    body: str | None = Field(default=None, max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    image_upload_keys: list[str] = Field(default_factory=list, max_length=10)
    tagged_shop_id: UUID | None = None
    tagged_design_id: UUID | None = None
    tagged_designer_id: UUID | None = None
    tagged_reservation_id: UUID | None = None


class SnapPublic(BaseModel):
    id: UUID
    author: UserPublic
    body: str | None = None
    tags: list[str]
    images: list[str]
    tagged_shop_id: UUID | None = None
    tagged_design_id: UUID | None = None
    tagged_designer_id: UUID | None = None
    tagged_reservation_id: UUID | None = None
    is_reservation_verified: bool
    like_count: int
    comment_count: int
    save_count: int
    view_count: int
    liked_by_me: bool
    saved_by_me: bool
    created_at: datetime


class SnapFeedQuery(BaseModel):
    feed_type: Literal["latest", "ranking", "following"] = "latest"
    cursor: str | None = None
    limit: int = Field(default=20, ge=1, le=50)
    tagged_design_id: UUID | None = None
    tagged_shop_id: UUID | None = None
    tagged_designer_id: UUID | None = None
