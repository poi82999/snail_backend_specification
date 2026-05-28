from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from http import HTTPStatus
from uuid import UUID, uuid4

import structlog
from sqlalchemy import ColumnElement, Float, cast, desc, func, literal, select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.errors import AppError
from app.core.redis import get_redis
from app.models.accounts import User
from app.models.community import Snap, SnapImage, SnapLike, SnapSave, UserFollow
from app.models.enums import ActorType, ReservationStatus, UploadTargetType
from app.models.ops import UploadObject
from app.models.reservation import Reservation
from app.schemas.snails import SnapCreate, SnapFeedQuery, SnapPublic
from app.schemas.users import UserPublic
from app.utils.pagination import CursorParams, decode_cursor, encode_cursor, paginate_query
from app.utils.storage import upload_public_url

logger = structlog.get_logger()

VIEW_DEDUP_TTL_SECONDS = 24 * 60 * 60


def ranking_score_expr() -> ColumnElement[float | Decimal]:
    """추천/랭킹 점수 = (좋아요·1 + 댓글·2 + 저장·3) / (경과시간h + 2)^1.5. 시간 감쇠로 신선도 반영."""
    age_hours = func.extract("epoch", func.now() - Snap.created_at) / 3600.0
    return (Snap.like_count * 1 + Snap.comment_count * 2 + Snap.save_count * 3) / func.power(
        cast(age_hours + 2.0, Float), 1.5
    )


async def _get_user_upload(session: AsyncSession, user_id: UUID, object_key: str) -> UploadObject:
    upload = await session.scalar(
        select(UploadObject).where(
            UploadObject.object_key == object_key,
            UploadObject.owner_actor_type == ActorType.USER.value,
            UploadObject.owner_actor_id == user_id,
            UploadObject.target_type == UploadTargetType.SNAP,
        )
    )
    if upload is None:
        raise AppError(
            "INVALID_UPLOAD",
            "올바른 업로드가 아닙니다.",
            HTTPStatus.BAD_REQUEST,
        )
    return upload


async def _reservation_verification(
    session: AsyncSession,
    user_id: UUID,
    reservation_id: UUID | None,
) -> tuple[UUID | None, bool]:
    if reservation_id is None:
        return None, False

    reservation = await session.get(Reservation, reservation_id)
    if reservation is None:
        return None, False
    verified = reservation.user_id == user_id and reservation.status == ReservationStatus.COMPLETED
    return reservation.id, verified


async def _users_by_id(session: AsyncSession, user_ids: set[UUID]) -> dict[UUID, User]:
    if not user_ids:
        return {}
    users = await session.scalars(select(User).where(User.id.in_(user_ids)))
    return {user.id: user for user in users}


async def _liked_snap_ids(
    session: AsyncSession,
    viewer_user_id: UUID | None,
    snap_ids: list[UUID],
) -> set[UUID]:
    if viewer_user_id is None or not snap_ids:
        return set()
    liked = await session.scalars(
        select(SnapLike.snap_id).where(
            SnapLike.user_id == viewer_user_id,
            SnapLike.snap_id.in_(snap_ids),
        )
    )
    return set(liked.all())


async def _saved_snap_ids(
    session: AsyncSession,
    viewer_user_id: UUID | None,
    snap_ids: list[UUID],
) -> set[UUID]:
    if viewer_user_id is None or not snap_ids:
        return set()
    saved = await session.scalars(
        select(SnapSave.snap_id).where(
            SnapSave.user_id == viewer_user_id,
            SnapSave.snap_id.in_(snap_ids),
        )
    )
    return set(saved.all())


async def _to_public_snaps(
    session: AsyncSession,
    snaps: list[Snap],
    viewer_user_id: UUID | None,
) -> list[SnapPublic]:
    users = await _users_by_id(session, {snap.user_id for snap in snaps})
    snap_ids = [snap.id for snap in snaps]
    liked_ids = await _liked_snap_ids(session, viewer_user_id, snap_ids)
    saved_ids = await _saved_snap_ids(session, viewer_user_id, snap_ids)

    public_snaps: list[SnapPublic] = []
    for snap in snaps:
        author = users.get(snap.user_id)
        if author is None:
            raise AppError("SNAP_NOT_FOUND", "스네일을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
        images = sorted(snap.images, key=lambda image: (image.sort_order, image.id))
        public_snaps.append(
            SnapPublic(
                id=snap.id,
                author=UserPublic.model_validate(author),
                body=snap.body,
                tags=snap.tags,
                images=[image.image_url for image in images],
                tagged_shop_id=snap.tagged_shop_id,
                tagged_design_id=snap.tagged_design_id,
                tagged_designer_id=snap.tagged_designer_id,
                tagged_reservation_id=snap.tagged_reservation_id,
                is_reservation_verified=snap.is_reservation_verified,
                like_count=snap.like_count,
                comment_count=snap.comment_count,
                save_count=snap.save_count,
                view_count=snap.view_count,
                liked_by_me=snap.id in liked_ids,
                saved_by_me=snap.id in saved_ids,
                created_at=snap.created_at,
            )
        )
    return public_snaps


async def create_snap(session: AsyncSession, user_id: UUID, payload: SnapCreate) -> SnapPublic:
    uploads = [
        await _get_user_upload(session, user_id, object_key)
        for object_key in payload.image_upload_keys
    ]
    tagged_reservation_id, is_reservation_verified = await _reservation_verification(
        session,
        user_id,
        payload.tagged_reservation_id,
    )

    snap = Snap(
        id=uuid4(),
        user_id=user_id,
        tagged_shop_id=payload.tagged_shop_id,
        tagged_design_id=payload.tagged_design_id,
        tagged_designer_id=payload.tagged_designer_id,
        tagged_reservation_id=tagged_reservation_id,
        body=payload.body,
        tags=payload.tags,
        is_reservation_verified=is_reservation_verified,
    )
    session.add(snap)
    await session.flush()

    for index, upload in enumerate(uploads):
        session.add(
            SnapImage(
                id=uuid4(),
                snap_id=snap.id,
                image_url=upload_public_url(upload),
                sort_order=index,
            )
        )

    await session.flush()
    logger.info("snap.created", user_id=str(user_id), snap_id=str(snap.id))
    return await get_snap_detail(session, user_id, snap.id)


async def feed(
    session: AsyncSession,
    viewer_user_id: UUID | None,
    query: SnapFeedQuery,
) -> tuple[list[SnapPublic], str | None]:
    statement = select(Snap).where(Snap.deleted_at.is_(None)).options(selectinload(Snap.images))

    if query.feed_type == "following":
        if viewer_user_id is None:
            raise AppError("UNAUTHORIZED", "로그인이 필요합니다.", HTTPStatus.UNAUTHORIZED)
        statement = statement.join(UserFollow, UserFollow.following_id == Snap.user_id).where(
            UserFollow.follower_id == viewer_user_id
        )

    if query.tagged_design_id is not None:
        statement = statement.where(Snap.tagged_design_id == query.tagged_design_id)
    if query.tagged_shop_id is not None:
        statement = statement.where(Snap.tagged_shop_id == query.tagged_shop_id)
    if query.tagged_designer_id is not None:
        statement = statement.where(Snap.tagged_designer_id == query.tagged_designer_id)

    params = CursorParams(cursor=query.cursor, limit=query.limit)
    if query.feed_type != "ranking":
        snaps, next_cursor = await paginate_query(session, statement, Snap, params)
        return await _to_public_snaps(session, snaps, viewer_user_id), next_cursor

    if query.cursor:
        cursor_created_at, cursor_id = decode_cursor(query.cursor)
        statement = statement.where(
            tuple_(Snap.created_at, Snap.id)
            < tuple_(literal(cursor_created_at), literal(cursor_id))
        )

    score = ranking_score_expr()
    statement = statement.order_by(desc(score), desc(Snap.created_at), desc(Snap.id)).limit(
        query.limit + 1
    )
    snaps = list((await session.scalars(statement)).all())
    items = snaps[: query.limit]
    next_cursor = (
        encode_cursor(items[-1].created_at, items[-1].id) if len(snaps) > query.limit else None
    )
    return await _to_public_snaps(session, items, viewer_user_id), next_cursor


async def get_snap_detail(
    session: AsyncSession,
    viewer_user_id: UUID | None,
    snap_id: UUID,
) -> SnapPublic:
    snap = await session.scalar(
        select(Snap)
        .where(Snap.id == snap_id, Snap.deleted_at.is_(None))
        .options(selectinload(Snap.images))
    )
    if snap is None:
        raise AppError("SNAP_NOT_FOUND", "스네일을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return (await _to_public_snaps(session, [snap], viewer_user_id))[0]


async def soft_delete_snap(session: AsyncSession, user_id: UUID, snap_id: UUID) -> None:
    snap = await session.scalar(select(Snap).where(Snap.id == snap_id, Snap.deleted_at.is_(None)))
    if snap is None:
        raise AppError("SNAP_NOT_FOUND", "스네일을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    if snap.user_id != user_id:
        raise AppError("FORBIDDEN", "본인 글만 삭제할 수 있습니다.", HTTPStatus.FORBIDDEN)
    snap.deleted_at = datetime.now(UTC)
    await session.flush()
    logger.info("snap.deleted", user_id=str(user_id), snap_id=str(snap_id))


def view_identity(
    viewer_user_id: UUID | None,
    client_host: str | None,
    user_agent: str | None,
) -> str:
    if viewer_user_id is not None:
        return f"user:{viewer_user_id}"
    digest = sha256(f"{client_host or 'unknown'}|{user_agent or ''}".encode()).hexdigest()
    return f"anon:{digest}"


async def _should_increment_view(snap_id: UUID, viewer_key: str) -> bool:
    try:
        redis = get_redis()
    except RuntimeError:
        return True

    redis_key = f"snap:view:{snap_id}"
    added = await redis.sadd(redis_key, viewer_key)
    if int(added) == 1:
        await redis.expire(redis_key, VIEW_DEDUP_TTL_SECONDS)
        return True
    return False


async def increment_view_count(session: AsyncSession, snap_id: UUID, viewer_key: str) -> None:
    if not await _should_increment_view(snap_id, viewer_key):
        return
    await session.execute(
        update(Snap)
        .where(Snap.id == snap_id, Snap.deleted_at.is_(None))
        .values(view_count=Snap.view_count + 1)
    )
    await session.flush()
