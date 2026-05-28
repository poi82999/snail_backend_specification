from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.users import UserPublic


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    body: str | None = Field(default=None, max_length=2000)
    image_upload_keys: list[str] = Field(default_factory=list)


class ReviewUpdate(BaseModel):
    rating: int = Field(ge=1, le=5)
    body: str | None = Field(default=None, max_length=2000)


class ReviewReplyCreate(BaseModel):
    body: str = Field(min_length=1, max_length=1000)


class ReviewReplyOwnerPublic(BaseModel):
    id: UUID
    representative_name: str


class ReviewReplyPublic(BaseModel):
    id: UUID
    owner: ReviewReplyOwnerPublic
    body: str
    created_at: datetime


class ReviewPublic(BaseModel):
    id: UUID
    reservation_id: UUID
    author: UserPublic
    shop_id: UUID
    design_id: UUID
    rating: int
    body: str | None = None
    images: list[str]
    like_count: int
    reply: ReviewReplyPublic | None = None
    created_at: datetime
