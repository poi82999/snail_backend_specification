from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ActorType, ReportAction, ReportStatus, ReportTargetType

if TYPE_CHECKING:
    from app.models.reservation import Reservation


class FavoriteDesign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "favorite_designs"
    __table_args__ = (
        UniqueConstraint("user_id", "design_id", name="uq_favorite_designs_user_design"),
    )

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    design_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("designs.id"))


class UserFollow(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_follows"
    __table_args__ = (UniqueConstraint("follower_id", "following_id", name="uq_user_follows_pair"),)

    follower_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    following_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))


class Snap(UUIDPrimaryKeyMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "snaps"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    tagged_shop_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("shops.id")
    )
    tagged_design_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("designs.id")
    )
    tagged_designer_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("designers.id")
    )
    tagged_reservation_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("reservations.id")
    )
    body: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list)
    is_reservation_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    save_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    images: Mapped[list[SnapImage]] = relationship(back_populates="snap")


class SnapImage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "snap_images"

    snap_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("snaps.id"))
    image_url: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    snap: Mapped[Snap] = relationship(back_populates="images")


class SnapLike(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "snap_likes"
    __table_args__ = (UniqueConstraint("snap_id", "user_id", name="uq_snap_likes_snap_user"),)

    snap_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("snaps.id"))
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))


class SnapSave(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "snap_saves"
    __table_args__ = (UniqueConstraint("snap_id", "user_id", name="uq_snap_saves_snap_user"),)

    snap_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("snaps.id"))
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))


class Comment(UUIDPrimaryKeyMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "comments"

    snap_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("snaps.id"))
    parent_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("comments.id"))
    author_type: Mapped[ActorType] = mapped_column(
        Enum(ActorType, native_enum=False, length=30), nullable=False
    )
    author_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    body: Mapped[str] = mapped_column(Text)
    depth: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class CommentLike(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "comment_likes"
    __table_args__ = (
        UniqueConstraint("comment_id", "user_id", name="uq_comment_likes_comment_user"),
    )

    comment_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("comments.id"))
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))


class Review(UUIDPrimaryKeyMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("reservation_id", name="uq_reviews_reservation"),)

    reservation_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("reservations.id")
    )
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    shop_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("shops.id"))
    design_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("designs.id"))
    rating: Mapped[int] = mapped_column(Integer)
    body: Mapped[str | None] = mapped_column(Text)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    reservation: Mapped[Reservation] = relationship(back_populates="review")
    images: Mapped[list[ReviewImage]] = relationship(back_populates="review")
    reply: Mapped[ReviewReply | None] = relationship(back_populates="review")


class ReviewImage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "review_images"

    review_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("reviews.id"))
    image_url: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    review: Mapped[Review] = relationship(back_populates="images")


class ReviewReply(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "review_replies"
    __table_args__ = (UniqueConstraint("review_id", name="uq_review_replies_review"),)

    review_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("reviews.id"))
    owner_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("owners.id"))
    body: Mapped[str] = mapped_column(Text)

    review: Mapped[Review] = relationship(back_populates="reply")


class Report(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reports"

    reporter_user_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id")
    )
    target_type: Mapped[ReportTargetType] = mapped_column(
        Enum(ReportTargetType, native_enum=False, length=30), nullable=False
    )
    target_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    reason: Mapped[str] = mapped_column(String(80))
    detail: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, native_enum=False, length=30),
        default=ReportStatus.PENDING,
        nullable=False,
    )
    action: Mapped[ReportAction] = mapped_column(
        Enum(ReportAction, native_enum=False, length=30),
        default=ReportAction.NONE,
        nullable=False,
    )
