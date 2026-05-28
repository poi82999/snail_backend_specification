from datetime import UTC, datetime, timedelta
from decimal import Decimal
from http import HTTPStatus

import pytest
from app.api.errors import AppError
from app.models.community import Review
from app.models.enums import ActorType, ReservationStatus, UploadTargetType
from app.schemas.reviews import ReviewCreate, ReviewUpdate
from app.services import review_service
from sqlalchemy.ext.asyncio import AsyncSession
from tests.community_factories import (
    create_design,
    create_designer,
    create_owner,
    create_reservation,
    create_shop,
    create_upload,
    create_user,
)


async def _review_context(
    db_session: AsyncSession,
    status: ReservationStatus = ReservationStatus.COMPLETED,
    average_rating: Decimal | None = None,
    review_count: int = 0,
) -> tuple[object, object, object]:
    user = await create_user(db_session)
    owner = await create_owner(db_session)
    shop = await create_shop(
        db_session,
        owner,
        average_rating=average_rating,
        review_count=review_count,
    )
    designer = await create_designer(db_session, shop)
    design = await create_design(db_session, shop)
    reservation = await create_reservation(db_session, user, shop, design, designer, status)
    return user, shop, reservation


@pytest.mark.asyncio
async def test_create_review_rejects_non_completed_reservation(
    db_session: AsyncSession,
) -> None:
    user, _, reservation = await _review_context(db_session, ReservationStatus.CONFIRMED)

    with pytest.raises(AppError) as exc_info:
        await review_service.create_review(
            db_session,
            user.id,
            reservation.id,
            ReviewCreate(rating=5, body="good"),
        )

    assert exc_info.value.code == "RESERVATION_NOT_COMPLETED"
    assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_create_review_rejects_duplicate_reservation_review(
    db_session: AsyncSession,
) -> None:
    user, _, reservation = await _review_context(db_session)
    await review_service.create_review(
        db_session,
        user.id,
        reservation.id,
        ReviewCreate(rating=5, body="first"),
    )

    with pytest.raises(AppError) as exc_info:
        await review_service.create_review(
            db_session,
            user.id,
            reservation.id,
            ReviewCreate(rating=4, body="second"),
        )

    assert exc_info.value.code == "REVIEW_ALREADY_EXISTS"
    assert exc_info.value.status_code == HTTPStatus.CONFLICT


@pytest.mark.asyncio
async def test_create_review_rejects_six_images(db_session: AsyncSession) -> None:
    user, _, reservation = await _review_context(db_session)
    uploads = [
        await create_upload(db_session, ActorType.USER, user.id, UploadTargetType.REVIEW)
        for _ in range(6)
    ]

    with pytest.raises(AppError) as exc_info:
        await review_service.create_review(
            db_session,
            user.id,
            reservation.id,
            ReviewCreate(rating=5, image_upload_keys=[upload.object_key for upload in uploads]),
        )

    assert exc_info.value.code == "TOO_MANY_REVIEW_IMAGES"
    assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_create_review_updates_shop_average_rating(db_session: AsyncSession) -> None:
    user, shop, reservation = await _review_context(
        db_session,
        average_rating=Decimal("4.00"),
        review_count=1,
    )

    await review_service.create_review(
        db_session,
        user.id,
        reservation.id,
        ReviewCreate(rating=2, body="average"),
    )
    await db_session.refresh(shop)

    assert shop.review_count == 2
    assert shop.average_rating == Decimal("3.00")


@pytest.mark.asyncio
async def test_update_review_within_window_recomputes_average(
    db_session: AsyncSession,
) -> None:
    user, shop, reservation = await _review_context(db_session)
    created = await review_service.create_review(
        db_session,
        user.id,
        reservation.id,
        ReviewCreate(rating=5, body="great"),
    )

    updated = await review_service.update_review(
        db_session,
        user.id,
        created.id,
        ReviewUpdate(rating=3, body="meh"),
    )
    await db_session.refresh(shop)

    assert updated.rating == 3
    assert updated.body == "meh"
    assert shop.review_count == 1
    assert shop.average_rating == Decimal("3.00")


@pytest.mark.asyncio
async def test_update_review_after_seven_days_is_rejected(db_session: AsyncSession) -> None:
    user, _, reservation = await _review_context(db_session)
    created = await review_service.create_review(
        db_session,
        user.id,
        reservation.id,
        ReviewCreate(rating=5, body="great"),
    )

    review = await db_session.get(Review, created.id)
    assert review is not None
    review.created_at = datetime.now(UTC) - timedelta(days=8)
    await db_session.flush()

    with pytest.raises(AppError) as exc_info:
        await review_service.update_review(
            db_session,
            user.id,
            created.id,
            ReviewUpdate(rating=3, body="too late"),
        )

    assert exc_info.value.code == "REVIEW_EDIT_WINDOW_CLOSED"
    assert exc_info.value.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_delete_review_within_window_decrements_shop_stats(
    db_session: AsyncSession,
) -> None:
    user, shop, reservation = await _review_context(db_session)
    created = await review_service.create_review(
        db_session,
        user.id,
        reservation.id,
        ReviewCreate(rating=4, body="good"),
    )

    await review_service.soft_delete_review(db_session, user.id, created.id)
    await db_session.refresh(shop)

    assert shop.review_count == 0
    assert shop.average_rating == Decimal("0.00")


@pytest.mark.asyncio
async def test_delete_review_after_seven_days_is_rejected(db_session: AsyncSession) -> None:
    user, _, reservation = await _review_context(db_session)
    created = await review_service.create_review(
        db_session,
        user.id,
        reservation.id,
        ReviewCreate(rating=4, body="good"),
    )

    review = await db_session.get(Review, created.id)
    assert review is not None
    review.created_at = datetime.now(UTC) - timedelta(days=8)
    await db_session.flush()

    with pytest.raises(AppError) as exc_info:
        await review_service.soft_delete_review(db_session, user.id, created.id)

    assert exc_info.value.code == "REVIEW_EDIT_WINDOW_CLOSED"
    assert exc_info.value.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_update_review_by_other_user_is_forbidden(db_session: AsyncSession) -> None:
    user, _, reservation = await _review_context(db_session)
    created = await review_service.create_review(
        db_session,
        user.id,
        reservation.id,
        ReviewCreate(rating=5, body="great"),
    )
    intruder = await create_user(db_session)

    with pytest.raises(AppError) as exc_info:
        await review_service.update_review(
            db_session,
            intruder.id,
            created.id,
            ReviewUpdate(rating=1, body="hack"),
        )

    assert exc_info.value.code == "FORBIDDEN"
    assert exc_info.value.status_code == HTTPStatus.FORBIDDEN
