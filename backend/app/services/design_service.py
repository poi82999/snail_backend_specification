from __future__ import annotations

import importlib
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any, cast
from uuid import UUID, uuid4

import structlog
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.core.redis import get_arq_pool
from app.models.accounts import Owner
from app.models.community import FavoriteDesign, Review
from app.models.design import Design, DesignDesigner, DesignImage, LlmJob
from app.models.enums import (
    ActorType,
    AiAnalysisStatus,
    UploadTargetType,
    VerificationStatus,
    Visibility,
)
from app.models.ops import UploadObject
from app.models.shop import Designer, Shop
from app.schemas.designs import (
    DesignCreate,
    DesignDesignerPublic,
    DesignImagePublic,
    DesignMe,
    DesignPublic,
    DesignShopSummary,
    DesignUpdate,
    LlmJobSummary,
)
from app.services import shop_service
from app.utils.pagination import CursorParams, paginate_query
from app.utils.storage import upload_public_url

logger = structlog.get_logger()


async def _enqueue_analysis_job(design_id: UUID) -> None:
    try:
        importlib.import_module("app.workers.llm_pipeline")
    except ImportError:
        logger.info(
            "design.analyze.skipped",
            design_id=str(design_id),
            reason="llm_worker_not_ready",
        )
        return

    try:
        await get_arq_pool().enqueue_job("analyze_design", str(design_id))
    except Exception as exc:
        logger.info(
            "design.analyze.skipped",
            design_id=str(design_id),
            reason="enqueue_failed",
            error=str(exc),
        )


def _ensure_unique(values: list[UUID] | list[str], error_code: str, message: str) -> None:
    if len(set(values)) != len(values):
        raise AppError(error_code, message, HTTPStatus.BAD_REQUEST)


async def _validate_designers(
    session: AsyncSession,
    shop_id: UUID,
    designer_ids: list[UUID],
) -> list[Designer]:
    _ensure_unique(
        designer_ids,
        "INVALID_DESIGNER",
        "디자이너는 중복 지정할 수 없습니다.",
    )
    designers = list(
        (
            await session.scalars(
                select(Designer).where(
                    Designer.id.in_(designer_ids),
                    Designer.shop_id == shop_id,
                    Designer.is_active.is_(True),
                )
            )
        ).all()
    )
    designers_by_id = {designer.id: designer for designer in designers}
    if set(designers_by_id) != set(designer_ids):
        raise AppError(
            "INVALID_DESIGNER",
            "본인 샵의 활성 디자이너만 지정할 수 있습니다.",
            HTTPStatus.BAD_REQUEST,
        )
    return [designers_by_id[designer_id] for designer_id in designer_ids]


async def _validate_uploads(
    session: AsyncSession,
    owner_id: UUID,
    image_upload_keys: list[str],
) -> list[UploadObject]:
    _ensure_unique(
        image_upload_keys,
        "INVALID_UPLOAD",
        "디자인 이미지는 중복 지정할 수 없습니다.",
    )
    uploads = list(
        (
            await session.scalars(
                select(UploadObject).where(
                    UploadObject.object_key.in_(image_upload_keys),
                    UploadObject.owner_actor_type == ActorType.OWNER.value,
                    UploadObject.owner_actor_id == owner_id,
                    UploadObject.target_type == UploadTargetType.DESIGN,
                )
            )
        ).all()
    )
    uploads_by_key = {upload.object_key: upload for upload in uploads}
    if set(uploads_by_key) != set(image_upload_keys):
        raise AppError(
            "INVALID_UPLOAD",
            "본인이 업로드한 디자인 이미지만 사용할 수 있습니다.",
            HTTPStatus.BAD_REQUEST,
        )
    return [uploads_by_key[object_key] for object_key in image_upload_keys]


async def _replace_designers(
    session: AsyncSession,
    design_id: UUID,
    designers: list[Designer],
) -> None:
    await session.execute(delete(DesignDesigner).where(DesignDesigner.design_id == design_id))
    for designer in designers:
        session.add(DesignDesigner(design_id=design_id, designer_id=designer.id))


async def _replace_images(
    session: AsyncSession,
    design: Design,
    uploads: list[UploadObject],
) -> None:
    await session.execute(delete(DesignImage).where(DesignImage.design_id == design.id))
    design.thumbnail_url = upload_public_url(uploads[0])
    for index, upload in enumerate(uploads):
        image_url = upload_public_url(upload)
        session.add(
            DesignImage(
                id=uuid4(),
                design_id=design.id,
                original_url=image_url,
                processed_url=upload.processed_url,
                sort_order=index,
                is_thumbnail=index == 0,
            )
        )


async def _get_owner_design(session: AsyncSession, owner_id: UUID, design_id: UUID) -> Design:
    design = await session.scalar(
        select(Design)
        .join(Shop, Shop.id == Design.shop_id)
        .where(
            Design.id == design_id,
            Shop.owner_id == owner_id,
            Design.deleted_at.is_(None),
        )
    )
    if design is None:
        raise AppError("DESIGN_NOT_FOUND", "디자인을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return design


async def _design_images(
    session: AsyncSession, design_ids: list[UUID]
) -> dict[UUID, list[DesignImage]]:
    if not design_ids:
        return {}
    images = list(
        (
            await session.scalars(
                select(DesignImage)
                .where(DesignImage.design_id.in_(design_ids))
                .order_by(DesignImage.sort_order, DesignImage.id)
            )
        ).all()
    )
    by_design: dict[UUID, list[DesignImage]] = {design_id: [] for design_id in design_ids}
    for image in images:
        by_design.setdefault(image.design_id, []).append(image)
    return by_design


async def _design_designers(
    session: AsyncSession,
    design_ids: list[UUID],
) -> dict[UUID, list[Designer]]:
    if not design_ids:
        return {}
    rows = (
        await session.execute(
            select(DesignDesigner.design_id, Designer)
            .join(Designer, Designer.id == DesignDesigner.designer_id)
            .where(DesignDesigner.design_id.in_(design_ids))
            .order_by(Designer.created_at, Designer.id)
        )
    ).all()
    by_design: dict[UUID, list[Designer]] = {design_id: [] for design_id in design_ids}
    for design_id, designer in rows:
        by_design.setdefault(cast(UUID, design_id), []).append(cast(Designer, designer))
    return by_design


async def _latest_llm_jobs(session: AsyncSession, design_ids: list[UUID]) -> dict[UUID, LlmJob]:
    if not design_ids:
        return {}
    rows = (
        await session.execute(
            select(LlmJob)
            .where(LlmJob.design_id.in_(design_ids))
            .order_by(LlmJob.design_id, LlmJob.created_at.desc(), LlmJob.id.desc())
        )
    ).scalars()
    latest: dict[UUID, LlmJob] = {}
    for job in rows:
        latest.setdefault(job.design_id, job)
    return latest


def _image_public(image: DesignImage) -> DesignImagePublic:
    return DesignImagePublic(
        id=image.id,
        original_url=image.original_url,
        processed_url=image.processed_url,
        sort_order=image.sort_order,
        is_thumbnail=image.is_thumbnail,
    )


def _designer_public(designer: Designer) -> DesignDesignerPublic:
    return DesignDesignerPublic(
        id=designer.id,
        shop_id=designer.shop_id,
        name=designer.name,
        position=designer.position,
        profile_image_url=designer.profile_image_url,
        specialty_tags=designer.specialty_tags,
    )


def _llm_job_summary(job: LlmJob) -> LlmJobSummary:
    return LlmJobSummary(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        attempts=job.attempts,
        error_code=job.error_code,
        error_message=job.error_message,
        created_at=job.created_at,
        finished_at=job.finished_at,
    )


async def _to_design_me(session: AsyncSession, designs: list[Design]) -> list[DesignMe]:
    design_ids = [design.id for design in designs]
    images_by_design = await _design_images(session, design_ids)
    designers_by_design = await _design_designers(session, design_ids)
    latest_jobs = await _latest_llm_jobs(session, design_ids)

    result: list[DesignMe] = []
    for design in designs:
        latest_job = latest_jobs.get(design.id)
        result.append(
            DesignMe(
                id=design.id,
                shop_id=design.shop_id,
                title=design.title,
                description=design.description,
                base_price=design.base_price,
                duration_minutes=design.duration_minutes,
                thumbnail_url=design.thumbnail_url,
                visibility=design.visibility,
                ai_analysis_status=design.ai_analysis_status,
                owner_tags=design.owner_tags,
                ai_tags=design.ai_tags,
                color_palette=design.color_palette,
                style_category=design.style_category,
                nail_shape=design.nail_shape,
                ai_confidence=design.ai_confidence,
                ai_error_code=design.ai_error_code,
                ai_error_message=design.ai_error_message,
                ai_model_version=design.ai_model_version,
                search_indexed_at=design.search_indexed_at,
                images=[_image_public(image) for image in images_by_design.get(design.id, [])],
                designers=[
                    _designer_public(designer)
                    for designer in designers_by_design.get(design.id, [])
                ],
                llm_jobs=[_llm_job_summary(latest_job)] if latest_job is not None else [],
                deleted_at=design.deleted_at,
                created_at=design.created_at,
                updated_at=design.updated_at,
            )
        )
    return result


async def public_design_rows(
    session: AsyncSession,
    viewer_user_id: UUID | None,
    design_ids: list[UUID],
    scores: dict[UUID, float | None] | None = None,
) -> list[DesignPublic]:
    if not design_ids:
        return []
    favorite_counts = (
        select(FavoriteDesign.design_id, func.count(FavoriteDesign.id).label("favorite_count"))
        .where(FavoriteDesign.design_id.in_(design_ids))
        .group_by(FavoriteDesign.design_id)
        .subquery()
    )
    ratings = (
        select(Review.design_id, func.avg(Review.rating).label("average_rating"))
        .where(Review.design_id.in_(design_ids), Review.deleted_at.is_(None))
        .group_by(Review.design_id)
        .subquery()
    )
    favorited = (
        select(FavoriteDesign.design_id.label("design_id"))
        .where(
            FavoriteDesign.design_id.in_(design_ids),
            FavoriteDesign.user_id == viewer_user_id,
        )
        .subquery()
        if viewer_user_id is not None
        else None
    )

    columns: list[Any] = [
        Design,
        Shop,
        func.coalesce(favorite_counts.c.favorite_count, 0).label("favorite_count"),
        func.coalesce(ratings.c.average_rating, 0).label("average_rating"),
    ]
    if favorited is not None:
        columns.append((favorited.c.design_id.is_not(None)).label("favorited_by_me"))

    statement = (
        select(*columns)
        .join(Shop, Shop.id == Design.shop_id)
        .join(Owner, Owner.id == Shop.owner_id)
        .outerjoin(favorite_counts, favorite_counts.c.design_id == Design.id)
        .outerjoin(ratings, ratings.c.design_id == Design.id)
        .where(
            Design.id.in_(design_ids),
            Design.deleted_at.is_(None),
            Design.visibility == Visibility.ACTIVE,
            Design.ai_analysis_status == AiAnalysisStatus.DONE,
            Shop.visibility == Visibility.ACTIVE,
            Owner.verification_status == VerificationStatus.APPROVED,
            Owner.is_active.is_(True),
        )
    )
    if favorited is not None:
        statement = statement.outerjoin(favorited, favorited.c.design_id == Design.id)

    rows = (await session.execute(statement)).all()
    designs_by_id: dict[UUID, tuple[Design, Shop, int, float, bool]] = {}
    for row in rows:
        design = cast(Design, row[0])
        shop = cast(Shop, row[1])
        favorite_count = int(cast(int | None, row[2]) or 0)
        average_rating = float(cast(float | None, row[3]) or 0)
        favorited_by_me = bool(row[4]) if viewer_user_id is not None else False
        designs_by_id[design.id] = (design, shop, favorite_count, average_rating, favorited_by_me)

    ordered_designs = [
        designs_by_id[design_id][0] for design_id in design_ids if design_id in designs_by_id
    ]
    images_by_design = await _design_images(session, [design.id for design in ordered_designs])
    designers_by_design = await _design_designers(
        session, [design.id for design in ordered_designs]
    )

    result: list[DesignPublic] = []
    for design in ordered_designs:
        _, shop, favorite_count, average_rating, favorited_by_me = designs_by_id[design.id]
        result.append(
            DesignPublic(
                id=design.id,
                title=design.title,
                description=design.description,
                base_price=design.base_price,
                duration_minutes=design.duration_minutes,
                thumbnail_url=design.thumbnail_url,
                images=[_image_public(image) for image in images_by_design.get(design.id, [])],
                ai_tags=design.ai_tags,
                color_palette=design.color_palette,
                style_category=design.style_category,
                nail_shape=design.nail_shape,
                shop=DesignShopSummary(
                    id=shop.id,
                    name=shop.name,
                    region=shop.region,
                    thumbnail_url=shop.thumbnail_url,
                ),
                designers=[
                    _designer_public(designer)
                    for designer in designers_by_design.get(design.id, [])
                ],
                average_rating=average_rating,
                favorite_count=favorite_count,
                favorited_by_me=favorited_by_me,
                score=scores.get(design.id) if scores is not None else None,
                created_at=design.created_at,
            )
        )
    return result


async def create_design(
    session: AsyncSession,
    owner_id: UUID,
    payload: DesignCreate,
) -> DesignMe:
    shop = await shop_service.get_my_shop(session, owner_id)
    if shop is None:
        raise AppError("SHOP_NOT_FOUND", "샵을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)

    uploads = await _validate_uploads(session, owner_id, payload.image_upload_keys)
    designers = await _validate_designers(session, shop.id, payload.designer_ids)
    design = Design(
        id=uuid4(),
        shop_id=shop.id,
        title=payload.title,
        description=payload.description,
        base_price=payload.base_price,
        duration_minutes=payload.duration_minutes,
        visibility=Visibility.DRAFT,
        ai_analysis_status=AiAnalysisStatus.PENDING,
        owner_tags=payload.owner_tags,
        thumbnail_url=upload_public_url(uploads[0]),
    )
    session.add(design)
    await session.flush()
    await _replace_images(session, design, uploads)
    await _replace_designers(session, design.id, designers)
    await session.flush()
    await session.refresh(design)
    await _enqueue_analysis_job(design.id)
    logger.info("design.created", owner_id=str(owner_id), design_id=str(design.id))
    return (await _to_design_me(session, [design]))[0]


async def update_design(
    session: AsyncSession,
    owner_id: UUID,
    design_id: UUID,
    payload: DesignUpdate,
) -> DesignMe:
    design = await _get_owner_design(session, owner_id, design_id)
    shop = await session.get(Shop, design.shop_id)
    if shop is None:
        raise AppError("SHOP_NOT_FOUND", "샵을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)

    if "title" in payload.model_fields_set and payload.title is not None:
        design.title = payload.title
    if "description" in payload.model_fields_set:
        design.description = payload.description
    if "base_price" in payload.model_fields_set and payload.base_price is not None:
        design.base_price = payload.base_price
    if "duration_minutes" in payload.model_fields_set and payload.duration_minutes is not None:
        design.duration_minutes = payload.duration_minutes
    if payload.owner_tags is not None:
        design.owner_tags = payload.owner_tags
    if payload.image_upload_keys is not None:
        uploads = await _validate_uploads(session, owner_id, payload.image_upload_keys)
        await _replace_images(session, design, uploads)
    if payload.designer_ids is not None:
        designers = await _validate_designers(session, shop.id, payload.designer_ids)
        await _replace_designers(session, design.id, designers)

    await session.flush()
    await session.refresh(design)
    logger.info("design.updated", owner_id=str(owner_id), design_id=str(design.id))
    return (await _to_design_me(session, [design]))[0]


async def request_reanalyze(session: AsyncSession, owner_id: UUID, design_id: UUID) -> DesignMe:
    design = await session.scalar(
        select(Design).where(
            Design.id == design_id,
            Design.deleted_at.is_(None),
        )
    )
    if design is None:
        raise AppError("DESIGN_NOT_FOUND", "디자인을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)

    shop = await session.get(Shop, design.shop_id)
    if shop is None:
        raise AppError(
            "SHOP_NOT_FOUND",
            "샵을 찾을 수 없습니다.",
            HTTPStatus.NOT_FOUND,
        )
    if shop.owner_id != owner_id:
        raise AppError("FORBIDDEN", "권한이 없습니다.", HTTPStatus.FORBIDDEN)

    design.ai_analysis_status = AiAnalysisStatus.PENDING
    design.ai_error_code = None
    design.ai_error_message = None
    await session.flush()
    await session.refresh(design)
    await _enqueue_analysis_job(design.id)
    logger.info("design.reanalyze_requested", owner_id=str(owner_id), design_id=str(design.id))
    return (await _to_design_me(session, [design]))[0]


async def soft_delete_design(session: AsyncSession, owner_id: UUID, design_id: UUID) -> None:
    design = await _get_owner_design(session, owner_id, design_id)
    design.deleted_at = datetime.now(UTC)
    await session.flush()
    logger.info("design.deleted", owner_id=str(owner_id), design_id=str(design.id))


async def toggle_hide(
    session: AsyncSession,
    owner_id: UUID,
    design_id: UUID,
    visibility: Visibility,
) -> DesignMe:
    design = await _get_owner_design(session, owner_id, design_id)
    design.visibility = visibility
    await session.flush()
    await session.refresh(design)
    logger.info(
        "design.visibility_changed",
        owner_id=str(owner_id),
        design_id=str(design.id),
        visibility=visibility.value,
    )
    return (await _to_design_me(session, [design]))[0]


async def get_my_design(session: AsyncSession, owner_id: UUID, design_id: UUID) -> DesignMe:
    design = await _get_owner_design(session, owner_id, design_id)
    return (await _to_design_me(session, [design]))[0]


async def list_my_designs(
    session: AsyncSession,
    owner_id: UUID,
    cursor: CursorParams,
) -> list[DesignMe]:
    shop = await shop_service.get_my_shop(session, owner_id)
    if shop is None:
        raise AppError("SHOP_NOT_FOUND", "샵을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    statement = select(Design).where(Design.shop_id == shop.id, Design.deleted_at.is_(None))
    designs, _ = await paginate_query(session, statement, Design, cursor)
    return await _to_design_me(session, designs)


async def get_public_design(
    session: AsyncSession,
    viewer_user_id: UUID | None,
    design_id: UUID,
) -> DesignPublic:
    designs = await public_design_rows(session, viewer_user_id, [design_id])
    if not designs:
        raise AppError("DESIGN_NOT_FOUND", "디자인을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return designs[0]
