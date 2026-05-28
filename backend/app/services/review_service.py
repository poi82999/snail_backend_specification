from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from uuid import UUID, uuid4

import structlog
from sqlalchemy import case, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.errors import AppError
from app.models.accounts import Owner, User
from app.models.community import Review, ReviewImage, ReviewReply
from app.models.enums import ActorType, ReservationStatus, UploadTargetType
from app.models.ops import UploadObject
from app.models.reservation import Reservation
from app.models.shop import Shop
from app.schemas.reviews import (
    ReviewCreate,
    ReviewPublic,
    ReviewReplyCreate,
    ReviewReplyOwnerPublic,
    ReviewReplyPublic,
    ReviewUpdate,
)
from app.schemas.users import UserPublic
from app.services import shop_service
from app.utils.pagination import CursorParams, paginate_query
from app.utils.storage import upload_public_url

logger = structlog.get_logger()

MAX_REVIEW_IMAGES = 5
REVIEW_EDIT_WINDOW = timedelta(days=7)


def _ensure_edit_window(review: Review) -> None:
    created = review.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    if datetime.now(UTC) - created > REVIEW_EDIT_WINDOW:
        raise AppError(
            "REVIEW_EDIT_WINDOW_CLOSED",
            "리뷰는 작성 후 7일 이내에만 수정/삭제할 수 있습니다.",
            HTTPStatus.FORBIDDEN,
        )


async def _get_user_upload(session: AsyncSession, user_id: UUID, object_key: str) -> UploadObject:
    upload = await session.scalar(
        select(UploadObject).where(
            UploadObject.object_key == object_key,
            UploadObject.owner_actor_type == ActorType.USER.value,
            UploadObject.owner_actor_id == user_id,
            UploadObject.target_type == UploadTargetType.REVIEW,
        )
    )
    if upload is None:
        raise AppError(
            "INVALID_UPLOAD",
            "올바른 업로드가 아닙니다.",
            HTTPStatus.BAD_REQUEST,
        )
    return upload


async def _review_with_details(session: AsyncSession, review_id: UUID) -> Review:
    review = await session.scalar(
        select(Review)
        .where(Review.id == review_id, Review.deleted_at.is_(None))
        .options(selectinload(Review.images), selectinload(Review.reply))
    )
    if review is None:
        raise AppError("REVIEW_NOT_FOUND", "리뷰를 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return review


async def _users_by_id(session: AsyncSession, user_ids: set[UUID]) -> dict[UUID, User]:
    if not user_ids:
        return {}
    users = await session.scalars(select(User).where(User.id.in_(user_ids)))
    return {user.id: user for user in users}


async def _owners_by_id(session: AsyncSession, owner_ids: set[UUID]) -> dict[UUID, Owner]:
    if not owner_ids:
        return {}
    owners = await session.scalars(select(Owner).where(Owner.id.in_(owner_ids)))
    return {owner.id: owner for owner in owners}


def _reply_public(reply: ReviewReply, owner: Owner) -> ReviewReplyPublic:
    return ReviewReplyPublic(
        id=reply.id,
        owner=ReviewReplyOwnerPublic(
            id=owner.id,
            representative_name=owner.representative_name,
        ),
        body=reply.body,
        created_at=reply.created_at,
    )


async def _to_public_reviews(session: AsyncSession, reviews: list[Review]) -> list[ReviewPublic]:
    users = await _users_by_id(session, {review.user_id for review in reviews})
    owner_ids = {review.reply.owner_id for review in reviews if review.reply is not None}
    owners = await _owners_by_id(session, owner_ids)

    public_reviews: list[ReviewPublic] = []
    for review in reviews:
        author = users.get(review.user_id)
        if author is None:
            raise AppError("REVIEW_NOT_FOUND", "리뷰를 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)

        reply = None
        if review.reply is not None:
            owner = owners.get(review.reply.owner_id)
            if owner is None:
                raise AppError("REVIEW_NOT_FOUND", "리뷰를 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
            reply = _reply_public(review.reply, owner)

        images = sorted(review.images, key=lambda image: (image.sort_order, image.id))
        public_reviews.append(
            ReviewPublic(
                id=review.id,
                reservation_id=review.reservation_id,
                author=UserPublic.model_validate(author),
                shop_id=review.shop_id,
                design_id=review.design_id,
                rating=review.rating,
                body=review.body,
                images=[image.image_url for image in images],
                like_count=review.like_count,
                reply=reply,
                created_at=review.created_at,
            )
        )
    return public_reviews


async def get_review_public(session: AsyncSession, review_id: UUID) -> ReviewPublic:
    review = await _review_with_details(session, review_id)
    return (await _to_public_reviews(session, [review]))[0]


async def get_public_reviews(session: AsyncSession, review_ids: list[UUID]) -> list[ReviewPublic]:
    if not review_ids:
        return []
    reviews = list(
        (
            await session.scalars(
                select(Review)
                .where(Review.id.in_(review_ids), Review.deleted_at.is_(None))
                .options(selectinload(Review.images), selectinload(Review.reply))
            )
        ).all()
    )
    reviews_by_id = {review.id: review for review in reviews}
    ordered_reviews = [
        reviews_by_id[review_id] for review_id in review_ids if review_id in reviews_by_id
    ]
    return await _to_public_reviews(session, ordered_reviews)


async def create_review(
    session: AsyncSession,
    user_id: UUID,
    reservation_id: UUID,
    payload: ReviewCreate,
) -> ReviewPublic:
    if len(payload.image_upload_keys) > MAX_REVIEW_IMAGES:
        raise AppError(
            "TOO_MANY_REVIEW_IMAGES",
            "리뷰 이미지는 최대 5장까지 등록할 수 있습니다.",
            HTTPStatus.BAD_REQUEST,
        )

    reservation = await session.get(Reservation, reservation_id)
    if (
        reservation is None
        or reservation.user_id != user_id
        or reservation.status != ReservationStatus.COMPLETED
    ):
        raise AppError(
            "RESERVATION_NOT_COMPLETED",
            "완료된 예약만 리뷰 작성 가능합니다.",
            HTTPStatus.BAD_REQUEST,
        )

    existing_review = await session.scalar(
        select(Review.id).where(Review.reservation_id == reservation_id)
    )
    if existing_review is not None:
        raise AppError(
            "REVIEW_ALREADY_EXISTS",
            "이미 작성한 리뷰가 있습니다.",
            HTTPStatus.CONFLICT,
        )

    uploads = [
        await _get_user_upload(session, user_id, object_key)
        for object_key in payload.image_upload_keys
    ]
    review = Review(
        id=uuid4(),
        reservation_id=reservation_id,
        user_id=user_id,
        shop_id=reservation.shop_id,
        design_id=reservation.design_id,
        rating=payload.rating,
        body=payload.body,
    )
    session.add(review)
    await session.flush()

    for index, upload in enumerate(uploads):
        session.add(
            ReviewImage(
                id=uuid4(),
                review_id=review.id,
                image_url=upload_public_url(upload),
                sort_order=index,
            )
        )

    await session.execute(
        update(Shop)
        .where(Shop.id == reservation.shop_id)
        .values(
            review_count=Shop.review_count + 1,
            average_rating=((Shop.average_rating * Shop.review_count) + payload.rating)
            / (Shop.review_count + 1),
        )
    )
    try:
        await session.flush()
    except IntegrityError as exc:
        raise AppError(
            "REVIEW_ALREADY_EXISTS",
            "이미 작성한 리뷰가 있습니다.",
            HTTPStatus.CONFLICT,
        ) from exc

    logger.info("review.created", user_id=str(user_id), review_id=str(review.id))
    return await get_review_public(session, review.id)


async def list_reviews_for_shop(
    session: AsyncSession,
    shop_id: UUID,
    cursor: CursorParams,
) -> list[ReviewPublic]:
    statement = (
        select(Review)
        .where(Review.shop_id == shop_id, Review.deleted_at.is_(None))
        .options(selectinload(Review.images), selectinload(Review.reply))
    )
    reviews, _ = await paginate_query(session, statement, Review, cursor)
    return await _to_public_reviews(session, reviews)


async def list_reviews_for_design(
    session: AsyncSession,
    design_id: UUID,
    cursor: CursorParams,
) -> list[ReviewPublic]:
    statement = (
        select(Review)
        .where(Review.design_id == design_id, Review.deleted_at.is_(None))
        .options(selectinload(Review.images), selectinload(Review.reply))
    )
    reviews, _ = await paginate_query(session, statement, Review, cursor)
    return await _to_public_reviews(session, reviews)


async def create_review_reply(
    session: AsyncSession,
    owner_id: UUID,
    review_id: UUID,
    payload: ReviewReplyCreate,
) -> ReviewReplyPublic:
    review = await _review_with_details(session, review_id)
    shop = await shop_service.get_my_shop(session, owner_id)
    if shop is None or review.shop_id != shop.id:
        raise AppError(
            "FORBIDDEN",
            "본인 샵 리뷰에만 답변할 수 있습니다.",
            HTTPStatus.FORBIDDEN,
        )

    existing_reply = await session.scalar(
        select(ReviewReply.id).where(ReviewReply.review_id == review_id)
    )
    if existing_reply is not None:
        raise AppError(
            "REVIEW_REPLY_ALREADY_EXISTS",
            "이미 답변한 리뷰입니다.",
            HTTPStatus.CONFLICT,
        )

    reply = ReviewReply(
        id=uuid4(),
        review_id=review_id,
        owner_id=owner_id,
        body=payload.body,
    )
    session.add(reply)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise AppError(
            "REVIEW_REPLY_ALREADY_EXISTS",
            "이미 답변한 리뷰입니다.",
            HTTPStatus.CONFLICT,
        ) from exc

    owner = await session.get(Owner, owner_id)
    if owner is None:
        raise AppError("OWNER_NOT_FOUND", "사장님 계정을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    logger.info("review.reply_created", owner_id=str(owner_id), review_id=str(review_id))
    return _reply_public(reply, owner)


async def update_review(
    session: AsyncSession,
    user_id: UUID,
    review_id: UUID,
    payload: ReviewUpdate,
) -> ReviewPublic:
    review = await _review_with_details(session, review_id)
    if review.user_id != user_id:
        raise AppError("FORBIDDEN", "본인 리뷰만 수정할 수 있습니다.", HTTPStatus.FORBIDDEN)
    _ensure_edit_window(review)

    old_rating = review.rating
    review.rating = payload.rating
    review.body = payload.body

    if payload.rating != old_rating:
        await session.execute(
            update(Shop)
            .where(Shop.id == review.shop_id, Shop.review_count > 0)
            .values(
                average_rating=(
                    (Shop.average_rating * Shop.review_count) - old_rating + payload.rating
                )
                / Shop.review_count
            )
        )

    await session.flush()
    logger.info("review.updated", user_id=str(user_id), review_id=str(review_id))
    return await get_review_public(session, review_id)


async def soft_delete_review(session: AsyncSession, user_id: UUID, review_id: UUID) -> None:
    review = await _review_with_details(session, review_id)
    if review.user_id != user_id:
        raise AppError("FORBIDDEN", "본인 리뷰만 삭제할 수 있습니다.", HTTPStatus.FORBIDDEN)
    _ensure_edit_window(review)

    rating = review.rating
    review.deleted_at = datetime.now(UTC)

    await session.execute(
        update(Shop)
        .where(Shop.id == review.shop_id, Shop.review_count > 0)
        .values(
            review_count=Shop.review_count - 1,
            average_rating=case(
                (
                    Shop.review_count > 1,
                    ((Shop.average_rating * Shop.review_count) - rating) / (Shop.review_count - 1),
                ),
                else_=0,
            ),
        )
    )

    await session.flush()
    logger.info("review.deleted", user_id=str(user_id), review_id=str(review_id))
