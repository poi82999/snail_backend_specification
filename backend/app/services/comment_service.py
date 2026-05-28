from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID, uuid4

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.errors import AppError
from app.models.accounts import Owner, User
from app.models.community import Comment, CommentLike, Snap
from app.models.enums import ActorType
from app.schemas.comments import AuthorRef, CommentCreate, CommentPublic
from app.schemas.likes import LikeToggleResponse
from app.services import shop_service
from app.utils.pagination import CursorParams, paginate_query

logger = structlog.get_logger()


async def _get_snap(session: AsyncSession, snap_id: UUID) -> Snap:
    snap = await session.scalar(
        select(Snap)
        .where(Snap.id == snap_id, Snap.deleted_at.is_(None))
        .options(selectinload(Snap.images))
    )
    if snap is None:
        raise AppError("SNAP_NOT_FOUND", "스네일을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return snap


async def _author_refs(
    session: AsyncSession,
    comments: list[Comment],
) -> dict[tuple[ActorType, UUID], AuthorRef]:
    user_ids = {comment.author_id for comment in comments if comment.author_type == ActorType.USER}
    owner_ids = {
        comment.author_id for comment in comments if comment.author_type == ActorType.OWNER
    }

    refs: dict[tuple[ActorType, UUID], AuthorRef] = {}
    if user_ids:
        users = await session.scalars(select(User).where(User.id.in_(user_ids)))
        for user in users:
            refs[(ActorType.USER, user.id)] = AuthorRef(
                actor_type="user",
                id=user.id,
                display_name=user.nickname,
                profile_image_url=user.profile_image_url,
            )
    if owner_ids:
        owners = await session.scalars(select(Owner).where(Owner.id.in_(owner_ids)))
        for owner in owners:
            refs[(ActorType.OWNER, owner.id)] = AuthorRef(
                actor_type="owner",
                id=owner.id,
                display_name=owner.representative_name,
                profile_image_url=None,
            )
    return refs


async def _liked_comment_ids(
    session: AsyncSession,
    viewer_user_id: UUID | None,
    comment_ids: list[UUID],
) -> set[UUID]:
    if viewer_user_id is None or not comment_ids:
        return set()
    liked = await session.scalars(
        select(CommentLike.comment_id).where(
            CommentLike.user_id == viewer_user_id,
            CommentLike.comment_id.in_(comment_ids),
        )
    )
    return set(liked.all())


async def _to_public_comments(
    session: AsyncSession,
    comments: list[Comment],
    viewer_user_id: UUID | None,
) -> list[CommentPublic]:
    refs = await _author_refs(session, comments)
    liked_ids = await _liked_comment_ids(
        session, viewer_user_id, [comment.id for comment in comments]
    )
    public_comments: list[CommentPublic] = []
    for comment in comments:
        author = refs.get((comment.author_type, comment.author_id))
        if author is None:
            raise AppError("COMMENT_NOT_FOUND", "댓글을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
        public_comments.append(
            CommentPublic(
                id=comment.id,
                snap_id=comment.snap_id,
                parent_id=comment.parent_id,
                author=author,
                body=comment.body,
                depth=comment.depth,
                like_count=comment.like_count,
                liked_by_me=comment.id in liked_ids,
                created_at=comment.created_at,
            )
        )
    return public_comments


async def create_comment(
    session: AsyncSession,
    actor_type: ActorType,
    actor_id: UUID,
    snap_id: UUID,
    payload: CommentCreate,
) -> CommentPublic:
    snap = await _get_snap(session, snap_id)

    if actor_type == ActorType.OWNER:
        shop = await shop_service.get_my_shop(session, actor_id)
        if shop is None or snap.tagged_shop_id != shop.id:
            raise AppError(
                "FORBIDDEN",
                "본인 샵이 태그된 스네일에만 댓글 가능합니다.",
                HTTPStatus.FORBIDDEN,
            )
    elif actor_type != ActorType.USER:
        raise AppError("FORBIDDEN", "권한이 없습니다.", HTTPStatus.FORBIDDEN)

    parent_id = payload.parent_id
    depth = 1
    if parent_id is not None:
        parent = await session.scalar(
            select(Comment).where(
                Comment.id == parent_id,
                Comment.snap_id == snap_id,
                Comment.deleted_at.is_(None),
            )
        )
        if parent is None:
            raise AppError("COMMENT_NOT_FOUND", "댓글을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
        if parent.parent_id is not None:
            raise AppError(
                "COMMENT_DEPTH_EXCEEDED",
                "대댓글은 2단계까지만 작성할 수 있습니다.",
                HTTPStatus.BAD_REQUEST,
            )
        depth = 2

    comment = Comment(
        id=uuid4(),
        snap_id=snap_id,
        parent_id=parent_id,
        author_type=actor_type,
        author_id=actor_id,
        body=payload.body,
        depth=depth,
    )
    session.add(comment)
    snap.comment_count += 1
    await session.flush()
    logger.info(
        "comment.created",
        actor_type=actor_type.value,
        actor_id=str(actor_id),
        snap_id=str(snap_id),
        comment_id=str(comment.id),
    )
    return (
        await _to_public_comments(
            session, [comment], actor_id if actor_type == ActorType.USER else None
        )
    )[0]


async def list_comments(
    session: AsyncSession,
    snap_id: UUID,
    viewer_user_id: UUID | None,
    cursor: CursorParams,
) -> list[CommentPublic]:
    await _get_snap(session, snap_id)
    statement = select(Comment).where(
        Comment.snap_id == snap_id,
        Comment.deleted_at.is_(None),
    )
    comments, _ = await paginate_query(
        session,
        statement,
        Comment,
        cursor,
        order_by_created_desc=False,
    )
    return await _to_public_comments(session, comments, viewer_user_id)


async def soft_delete_comment(
    session: AsyncSession,
    actor_type: ActorType,
    actor_id: UUID,
    comment_id: UUID,
) -> None:
    comment = await session.scalar(
        select(Comment).where(Comment.id == comment_id, Comment.deleted_at.is_(None))
    )
    if comment is None:
        raise AppError("COMMENT_NOT_FOUND", "댓글을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    if comment.author_type != actor_type or comment.author_id != actor_id:
        raise AppError("FORBIDDEN", "본인 댓글만 삭제할 수 있습니다.", HTTPStatus.FORBIDDEN)

    comment.deleted_at = datetime.now(UTC)
    await session.execute(
        update(Snap)
        .where(Snap.id == comment.snap_id, Snap.comment_count > 0)
        .values(comment_count=Snap.comment_count - 1)
    )
    await session.flush()
    logger.info(
        "comment.deleted",
        actor_type=actor_type.value,
        actor_id=str(actor_id),
        comment_id=str(comment_id),
    )


async def toggle_like(
    session: AsyncSession,
    comment_id: UUID,
    user_id: UUID,
) -> LikeToggleResponse:
    comment = await session.scalar(
        select(Comment).where(Comment.id == comment_id, Comment.deleted_at.is_(None))
    )
    if comment is None:
        raise AppError("COMMENT_NOT_FOUND", "댓글을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)

    existing = await session.scalar(
        select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user_id,
        )
    )
    if existing is None:
        session.add(CommentLike(id=uuid4(), comment_id=comment_id, user_id=user_id))
        comment.like_count += 1
        liked = True
    else:
        await session.delete(existing)
        comment.like_count = max(comment.like_count - 1, 0)
        liked = False

    await session.flush()
    count = await session.scalar(
        select(func.count()).select_from(CommentLike).where(CommentLike.comment_id == comment_id)
    )
    return LikeToggleResponse(liked=liked, like_count=int(count or 0))
