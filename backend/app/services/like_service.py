from http import HTTPStatus
from uuid import UUID, uuid4

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.models.accounts import Owner
from app.models.community import FavoriteDesign, Snap, SnapLike, SnapSave
from app.models.design import Design
from app.models.enums import AiAnalysisStatus, VerificationStatus, Visibility
from app.models.shop import Shop
from app.schemas.likes import LikeToggleResponse, SaveToggleResponse
from app.services import user_service

logger = structlog.get_logger()


async def toggle_snap_like(
    session: AsyncSession,
    snap_id: UUID,
    user_id: UUID,
) -> LikeToggleResponse:
    await user_service.get_me(session, user_id)
    snap = await session.scalar(select(Snap).where(Snap.id == snap_id, Snap.deleted_at.is_(None)))
    if snap is None:
        raise AppError("SNAP_NOT_FOUND", "스네일을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)

    existing = await session.scalar(
        select(SnapLike).where(SnapLike.snap_id == snap_id, SnapLike.user_id == user_id)
    )
    if existing is None:
        session.add(SnapLike(id=uuid4(), snap_id=snap_id, user_id=user_id))
        snap.like_count += 1
        liked = True
    else:
        await session.delete(existing)
        snap.like_count = max(snap.like_count - 1, 0)
        liked = False

    await session.flush()
    logger.info("snap.like_toggled", user_id=str(user_id), snap_id=str(snap_id), liked=liked)
    return LikeToggleResponse(liked=liked, like_count=snap.like_count)


async def toggle_snap_save(
    session: AsyncSession,
    snap_id: UUID,
    user_id: UUID,
) -> SaveToggleResponse:
    await user_service.get_me(session, user_id)
    snap = await session.scalar(select(Snap).where(Snap.id == snap_id, Snap.deleted_at.is_(None)))
    if snap is None:
        raise AppError("SNAP_NOT_FOUND", "스네일을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)

    existing = await session.scalar(
        select(SnapSave).where(SnapSave.snap_id == snap_id, SnapSave.user_id == user_id)
    )
    if existing is None:
        session.add(SnapSave(id=uuid4(), snap_id=snap_id, user_id=user_id))
        snap.save_count += 1
        saved = True
    else:
        await session.delete(existing)
        snap.save_count = max(snap.save_count - 1, 0)
        saved = False

    await session.flush()
    logger.info("snap.save_toggled", user_id=str(user_id), snap_id=str(snap_id), saved=saved)
    return SaveToggleResponse(saved=saved, save_count=snap.save_count)


async def _get_public_design(session: AsyncSession, design_id: UUID) -> Design:
    design = await session.scalar(
        select(Design)
        .join(Shop, Shop.id == Design.shop_id)
        .join(Owner, Owner.id == Shop.owner_id)
        .where(
            Design.id == design_id,
            Design.deleted_at.is_(None),
            Design.visibility == Visibility.ACTIVE,
            Design.ai_analysis_status == AiAnalysisStatus.DONE,
            Shop.visibility == Visibility.ACTIVE,
            Owner.verification_status == VerificationStatus.APPROVED,
            Owner.is_active.is_(True),
        )
    )
    if design is None:
        raise AppError("DESIGN_NOT_FOUND", "디자인을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return design


async def toggle_design_favorite(
    session: AsyncSession,
    design_id: UUID,
    user_id: UUID,
) -> LikeToggleResponse:
    await user_service.get_me(session, user_id)
    await _get_public_design(session, design_id)

    existing = await session.scalar(
        select(FavoriteDesign).where(
            FavoriteDesign.design_id == design_id,
            FavoriteDesign.user_id == user_id,
        )
    )
    if existing is None:
        session.add(FavoriteDesign(id=uuid4(), design_id=design_id, user_id=user_id))
        liked = True
    else:
        await session.delete(existing)
        liked = False

    await session.flush()
    count = await session.scalar(
        select(func.count())
        .select_from(FavoriteDesign)
        .where(FavoriteDesign.design_id == design_id)
    )
    favorite_count = int(count or 0)
    logger.info(
        "design.favorite_toggled",
        user_id=str(user_id),
        design_id=str(design_id),
        liked=liked,
    )
    return LikeToggleResponse(liked=liked, like_count=favorite_count)
