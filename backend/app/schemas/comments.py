from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=1000)
    parent_id: UUID | None = None


class AuthorRef(BaseModel):
    actor_type: Literal["user", "owner"]
    id: UUID
    display_name: str
    profile_image_url: str | None = None


class CommentPublic(BaseModel):
    id: UUID
    snap_id: UUID
    parent_id: UUID | None = None
    author: AuthorRef
    body: str
    depth: int
    like_count: int
    liked_by_me: bool
    created_at: datetime
