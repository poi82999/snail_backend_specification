from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nickname: str
    email: str | None = None
    profile_image_url: str | None = None
    bio: str | None = None
    interest_tags: list[str]
    created_at: datetime


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nickname: str
    profile_image_url: str | None = None
    bio: str | None = None


class UserUpdate(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=40)
    bio: str | None = Field(default=None, max_length=200)
    profile_image_url: str | None = None
    interest_tags: list[str] | None = None


class DeviceTokenRegister(BaseModel):
    token: str = Field(min_length=1)
    platform: str = Field(default="ios", min_length=1, max_length=20)
