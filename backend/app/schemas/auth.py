from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.schemas.users import UserMe


class AppleSignInRequest(BaseModel):
    id_token: str
    accepted_terms_version: str = Field(min_length=1, max_length=20)
    accepted_privacy_version: str = Field(min_length=1, max_length=20)
    nonce: str | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"] = "Bearer"
    access_expires_at: datetime
    refresh_expires_at: datetime


class AppleSignInResponse(BaseModel):
    tokens: TokenPair
    user: UserMe


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class OwnerSignupRequest(BaseModel):
    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=8, max_length=128)
    representative_name: str = Field(min_length=1, max_length=80)
    phone_number: str = Field(min_length=1, max_length=30)
    accepted_terms_version: str = Field(min_length=1, max_length=20)
    accepted_privacy_version: str = Field(min_length=1, max_length=20)


class OwnerLoginRequest(BaseModel):
    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=1, max_length=128)


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(max_length=320)


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=16)
    new_password: str = Field(min_length=8, max_length=128)
