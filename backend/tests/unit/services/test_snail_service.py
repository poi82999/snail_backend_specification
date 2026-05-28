from datetime import UTC, datetime, timedelta
from http import HTTPStatus

import pytest
from app.api.errors import AppError
from app.models.community import Snap
from app.models.enums import ActorType, ReservationStatus, UploadTargetType
from app.schemas.snails import SnapCreate, SnapFeedQuery
from app.services import snail_service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.community_factories import (
    create_design,
    create_designer,
    create_owner,
    create_reservation,
    create_shop,
    create_snap,
    create_upload,
    create_user,
)


async def _reservation_context(
    db_session: AsyncSession,
    status: ReservationStatus,
) -> tuple[object, object]:
    user = await create_user(db_session)
    owner = await create_owner(db_session)
    shop = await create_shop(db_session, owner)
    designer = await create_designer(db_session, shop)
    design = await create_design(db_session, shop)
    reservation = await create_reservation(db_session, user, shop, design, designer, status)
    return user, reservation


@pytest.mark.asyncio
async def test_create_snap_marks_completed_own_reservation_verified(
    db_session: AsyncSession,
) -> None:
    user, reservation = await _reservation_context(db_session, ReservationStatus.COMPLETED)

    response = await snail_service.create_snap(
        db_session,
        user.id,
        SnapCreate(tagged_reservation_id=reservation.id),
    )

    assert response.is_reservation_verified is True


@pytest.mark.asyncio
async def test_create_snap_confirmed_reservation_is_not_verified(
    db_session: AsyncSession,
) -> None:
    user, reservation = await _reservation_context(db_session, ReservationStatus.CONFIRMED)

    response = await snail_service.create_snap(
        db_session,
        user.id,
        SnapCreate(tagged_reservation_id=reservation.id),
    )

    assert response.is_reservation_verified is False


@pytest.mark.asyncio
async def test_create_snap_rejects_upload_not_owned_by_user(db_session: AsyncSession) -> None:
    user = await create_user(db_session)
    other_user = await create_user(db_session)
    upload = await create_upload(
        db_session,
        ActorType.USER,
        other_user.id,
        UploadTargetType.SNAP,
    )

    with pytest.raises(AppError) as exc_info:
        await snail_service.create_snap(
            db_session,
            user.id,
            SnapCreate(image_upload_keys=[upload.object_key]),
        )

    assert exc_info.value.code == "INVALID_UPLOAD"
    assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_soft_delete_snap_rejects_other_author(db_session: AsyncSession) -> None:
    author = await create_user(db_session)
    other_user = await create_user(db_session)
    snap = await create_snap(db_session, author)

    with pytest.raises(AppError) as exc_info:
        await snail_service.soft_delete_snap(db_session, other_user.id, snap.id)

    assert exc_info.value.code == "FORBIDDEN"
    assert exc_info.value.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_feed_filters_by_tagged_design_id(db_session: AsyncSession) -> None:
    author = await create_user(db_session)
    owner = await create_owner(db_session)
    shop = await create_shop(db_session, owner)
    design = await create_design(db_session, shop)
    other_design = await create_design(db_session, shop)

    matching = await create_snap(db_session, author, tagged_design_id=design.id)
    await create_snap(db_session, author, tagged_design_id=other_design.id)
    await create_snap(db_session, author)

    items, _ = await snail_service.feed(
        db_session,
        viewer_user_id=None,
        query=SnapFeedQuery(feed_type="latest", tagged_design_id=design.id),
    )

    assert [item.id for item in items] == [matching.id]


@pytest.mark.asyncio
async def test_feed_filters_by_tagged_shop_id(db_session: AsyncSession) -> None:
    author = await create_user(db_session)
    owner = await create_owner(db_session)
    shop_a = await create_shop(db_session, owner)
    owner_b = await create_owner(db_session)
    shop_b = await create_shop(db_session, owner_b)

    matching = await create_snap(db_session, author, tagged_shop_id=shop_a.id)
    await create_snap(db_session, author, tagged_shop_id=shop_b.id)

    items, _ = await snail_service.feed(
        db_session,
        viewer_user_id=None,
        query=SnapFeedQuery(feed_type="latest", tagged_shop_id=shop_a.id),
    )

    assert [item.id for item in items] == [matching.id]


@pytest.mark.asyncio
async def test_ranking_score_decays_old_snaps_below_fresh_ones(db_session: AsyncSession) -> None:
    """같은 like_count에서 더 오래된 스네일의 랭킹 점수가 더 낮은지 (시간 감쇠 검증)."""
    author = await create_user(db_session)
    fresh = await create_snap(db_session, author)
    stale = await create_snap(db_session, author)

    fresh_db = await db_session.get(Snap, fresh.id)
    stale_db = await db_session.get(Snap, stale.id)
    assert fresh_db is not None
    assert stale_db is not None
    fresh_db.like_count = 5
    fresh_db.created_at = datetime.now(UTC) - timedelta(hours=1)
    stale_db.like_count = 5
    stale_db.created_at = datetime.now(UTC) - timedelta(days=30)
    await db_session.flush()

    score = snail_service.ranking_score_expr()
    rows = (
        await db_session.execute(select(Snap.id, score).where(Snap.id.in_([fresh.id, stale.id])))
    ).all()
    scores = {row[0]: row[1] for row in rows}

    assert scores[fresh.id] > scores[stale.id]


@pytest.mark.asyncio
async def test_ranking_score_weights_saves_above_likes(db_session: AsyncSession) -> None:
    """저장(x3)이 좋아요(x1)보다 가중치가 높은지 — 같은 시점/카운트 비교."""
    author = await create_user(db_session)
    liked = await create_snap(db_session, author)
    saved = await create_snap(db_session, author)

    liked_db = await db_session.get(Snap, liked.id)
    saved_db = await db_session.get(Snap, saved.id)
    assert liked_db is not None
    assert saved_db is not None
    now = datetime.now(UTC) - timedelta(hours=1)
    liked_db.like_count = 3
    liked_db.created_at = now
    saved_db.save_count = 3
    saved_db.created_at = now
    await db_session.flush()

    score = snail_service.ranking_score_expr()
    rows = (
        await db_session.execute(select(Snap.id, score).where(Snap.id.in_([liked.id, saved.id])))
    ).all()
    scores = {row[0]: row[1] for row in rows}

    assert scores[saved.id] > scores[liked.id]


@pytest.mark.asyncio
async def test_toggle_snap_save_increments_then_decrements(db_session: AsyncSession) -> None:
    from app.services import like_service

    author = await create_user(db_session)
    saver = await create_user(db_session)
    snap = await create_snap(db_session, author)

    first = await like_service.toggle_snap_save(db_session, snap.id, saver.id)
    assert first.saved is True
    assert first.save_count == 1

    second = await like_service.toggle_snap_save(db_session, snap.id, saver.id)
    assert second.saved is False
    assert second.save_count == 0
