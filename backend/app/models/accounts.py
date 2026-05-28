from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import VerificationStatus

if TYPE_CHECKING:
    from app.models.shop import Shop


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    apple_sub: Mapped[str | None] = mapped_column(String(255), unique=True)
    email: Mapped[str | None] = mapped_column(String(320), unique=True)
    nickname: Mapped[str] = mapped_column(String(40), unique=True)
    profile_image_url: Mapped[str | None] = mapped_column(Text)
    bio: Mapped[str | None] = mapped_column(String(200))
    interest_tags: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    apns_tokens: Mapped[list[UserDeviceToken]] = relationship(back_populates="user")


class UserDeviceToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_device_tokens"
    __table_args__ = (
        UniqueConstraint("user_id", "token", name="uq_user_device_tokens_user_token"),
    )

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(Text)
    platform: Mapped[str] = mapped_column(String(20), default="ios", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="apns_tokens")


class UserOAuthIdentity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_oauth_identities"
    __table_args__ = (
        UniqueConstraint("provider", "provider_sub", name="uq_user_oauth_identities_provider_sub"),
        Index("ix_user_oauth_identities_user_id", "user_id"),
    )

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    provider: Mapped[str] = mapped_column(String(40))
    provider_sub: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320))
    raw_payload: Mapped[dict[str, object] | None] = mapped_column(JSONB)


class Owner(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "owners"

    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    representative_name: Mapped[str] = mapped_column(String(80))
    phone_number: Mapped[str] = mapped_column(String(30))
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, native_enum=False, length=30),
        default=VerificationStatus.PENDING,
        nullable=False,
    )
    verification_rejected_reason: Mapped[str | None] = mapped_column(Text)
    login_failed_count: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    shop: Mapped[Shop | None] = relationship(back_populates="owner")
    verifications: Mapped[list[BusinessVerification]] = relationship(back_populates="owner")


class BusinessVerification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "business_verifications"

    owner_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("owners.id"))
    business_registration_number: Mapped[str] = mapped_column(String(40))
    document_url: Mapped[str] = mapped_column(Text)
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, native_enum=False, length=30),
        default=VerificationStatus.PENDING,
        nullable=False,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_reason: Mapped[str | None] = mapped_column(Text)

    owner: Mapped[Owner] = relationship(back_populates="verifications")


class PasswordResetToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "password_reset_tokens"

    owner_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("owners.id"))
    token_hash: Mapped[str] = mapped_column(Text, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TermsAcceptance(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "terms_acceptances"
    __table_args__ = (
        UniqueConstraint(
            "actor_type",
            "actor_id",
            "policy_type",
            "version",
            name="uq_terms_acceptances_actor_policy_version",
        ),
        Index("ix_terms_acceptances_actor", "actor_type", "actor_id"),
    )

    actor_type: Mapped[str] = mapped_column(String(30))
    actor_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    policy_type: Mapped[str] = mapped_column(String(40))
    version: Mapped[str] = mapped_column(String(20))
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(Text)
