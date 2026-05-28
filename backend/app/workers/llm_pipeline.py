from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from http import HTTPStatus
from typing import Any, cast
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.errors import AppError
from app.core import database
from app.core.config import get_settings
from app.models.design import Design, DesignImage, LlmJob
from app.models.enums import AiAnalysisStatus, JobStatus, LlmJobType
from app.services.llm import cache as llm_cache
from app.services.llm import openai_client, usage_counter
from app.workers.registry import register_job

logger = structlog.get_logger()

ANALYZE_MAX_TRIES = 3
# TODO: 차후 prompts/transform.md 로딩으로 대체 예정 — LLM 작업자 합의 후.
VISION_PROMPT = (
    "네일 디자인 이미지를 검색과 추천에 쓸 수 있게 한국어로 간결히 묘사하세요. "
    "색상, 질감, 패턴, 분위기, 네일 쉐입이 보이면 포함하세요."
)


@dataclass(frozen=True, slots=True)
class TargetImage:
    image_url: str
    design_image_id: UUID | None


def _now() -> datetime:
    return datetime.now(UTC)


def _sessionmaker() -> async_sessionmaker[AsyncSession]:
    if database._sessionmaker is None:
        raise RuntimeError("DB engine not initialized - call init_engine() before workers")
    return database._sessionmaker


def _mask_message(message: str) -> str:
    api_key = get_settings().OPENAI_API_KEY
    if api_key:
        message = message.replace(api_key, "***")
    return message[:500]


def _error_details(exc: Exception) -> tuple[str, str]:
    if isinstance(exc, AppError):
        return exc.code, exc.message
    message = _mask_message(str(exc)) or "디자인 AI 분석 중 오류가 발생했습니다."
    return exc.__class__.__name__[:80], message


def _decimal_confidence(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.001"))


def _model_version(models: list[str]) -> str:
    unique: list[str] = []
    for model in models:
        if model and model not in unique:
            unique.append(model)
    return ", ".join(unique)[:120]


def _vision_from_cached(payload: dict[str, object]) -> openai_client.VisionResult | None:
    description = payload.get("description")
    model = payload.get("model")
    if not isinstance(description, str) or not isinstance(model, str):
        return None
    return {"description": description, "model": model}


async def _cached_vision(
    redis: object | None,
    key: str,
) -> openai_client.VisionResult | None:
    if redis is None:
        return None
    try:
        payload = await llm_cache.get_cached_vision(cast(llm_cache.VisionCacheRedis, redis), key)
    except Exception as exc:
        logger.info("llm.vision_cache.skipped", reason=exc.__class__.__name__)
        return None
    if payload is None:
        return None
    return _vision_from_cached(payload)


async def _store_vision_cache(
    redis: object | None,
    key: str,
    vision: openai_client.VisionResult,
) -> None:
    if redis is None:
        return
    try:
        await llm_cache.set_cached_vision(
            cast(llm_cache.VisionCacheRedis, redis),
            key,
            {"description": vision["description"], "model": vision["model"]},
        )
    except Exception as exc:
        logger.info("llm.vision_cache.write_skipped", reason=exc.__class__.__name__)


async def _vision_describe_with_cache(
    redis: object | None,
    image_url: str,
    *,
    model: str,
    prompt: str,
) -> tuple[openai_client.VisionResult, bool]:
    cache_key = llm_cache.image_hash_cache_key(image_url, model, prompt)
    cached = await _cached_vision(redis, cache_key)
    if cached is not None:
        return cached, True

    vision = await openai_client.vision_describe(image_url, prompt=prompt)
    await _store_vision_cache(redis, cache_key, vision)
    return vision, False


async def _record_usage(redis: object | None, model: str) -> None:
    if redis is None:
        return
    try:
        await usage_counter.incr_usage(
            cast(usage_counter.UsageRedis, redis),
            model,
            tokens=0,
            cost_estimate=Decimal("0"),
        )
    except Exception as exc:
        logger.info("llm.usage_counter.skipped", reason=exc.__class__.__name__)


async def _target_image(session: AsyncSession, design: Design) -> TargetImage:
    if design.thumbnail_url:
        return TargetImage(image_url=design.thumbnail_url, design_image_id=None)

    image = await session.scalar(
        select(DesignImage)
        .where(DesignImage.design_id == design.id)
        .order_by(DesignImage.is_thumbnail.desc(), DesignImage.sort_order, DesignImage.id)
        .limit(1)
    )
    if image is None:
        raise AppError("NO_IMAGE", "분석할 디자인 이미지가 없습니다.", HTTPStatus.BAD_REQUEST)

    image_url = image.processed_url or image.original_url
    if not image_url:
        raise AppError("NO_IMAGE", "분석할 디자인 이미지가 없습니다.", HTTPStatus.BAD_REQUEST)
    return TargetImage(image_url=image_url, design_image_id=image.id)


async def _start_job(
    session: AsyncSession,
    *,
    design_id: UUID,
    design_image_id: UUID | None,
    job_type: LlmJobType,
    attempts: int,
    request_payload: dict[str, object],
) -> LlmJob:
    job = LlmJob(
        id=uuid4(),
        design_id=design_id,
        design_image_id=design_image_id,
        job_type=job_type,
        status=JobStatus.RUNNING,
        attempts=attempts,
        request_payload=request_payload,
        started_at=_now(),
    )
    session.add(job)
    await session.commit()
    return job


async def _succeed_job(
    session: AsyncSession,
    job: LlmJob,
    response_payload: dict[str, object],
) -> None:
    job.status = JobStatus.SUCCEEDED
    job.response_payload = response_payload
    job.error_code = None
    job.error_message = None
    job.finished_at = _now()
    await session.commit()


async def _fail_job(
    session: AsyncSession,
    job_id: UUID,
    *,
    error_code: str,
    error_message: str,
) -> None:
    job = await session.get(LlmJob, job_id)
    if job is None:
        return
    job.status = JobStatus.FAILED
    job.error_code = error_code[:80]
    job.error_message = error_message
    job.finished_at = _now()


async def _mark_design_failed(
    session: AsyncSession,
    design_id: UUID,
    *,
    error_code: str,
    error_message: str,
) -> None:
    design = await session.get(Design, design_id)
    if design is None:
        return
    design.ai_analysis_status = AiAnalysisStatus.FAILED
    design.ai_error_code = error_code[:80]
    design.ai_error_message = error_message


@register_job
async def analyze_design(ctx: dict[str, Any], design_id: str) -> None:
    try:
        parsed_design_id = UUID(design_id)
    except ValueError:
        logger.info("design.analyze.skipped", design_id=design_id, reason="invalid_design_id")
        return

    job_try = int(ctx.get("job_try", 1) or 1)
    max_tries = int(ctx.get("max_tries", ANALYZE_MAX_TRIES) or ANALYZE_MAX_TRIES)
    current_job_id: UUID | None = None
    models_used: list[str] = []
    redis = ctx.get("redis")

    session_factory = _sessionmaker()
    async with session_factory() as session:
        design = await session.get(Design, parsed_design_id)
        if design is None or design.deleted_at is not None:
            logger.info(
                "design.analyze.skipped",
                design_id=str(parsed_design_id),
                reason="not_found_or_deleted",
            )
            return

        design.ai_analysis_status = AiAnalysisStatus.IN_PROGRESS
        design.ai_error_code = None
        design.ai_error_message = None
        await session.commit()

        try:
            transform_job = await _start_job(
                session,
                design_id=parsed_design_id,
                design_image_id=None,
                job_type=LlmJobType.TRANSFORM,
                attempts=job_try,
                request_payload={"prompt": VISION_PROMPT},
            )
            current_job_id = transform_job.id
            target = await _target_image(session, design)
            transform_job.design_image_id = target.design_image_id
            transform_job.request_payload = {
                "image_url": target.image_url,
                "prompt": VISION_PROMPT,
            }
            await session.commit()

            vision, vision_cache_hit = await _vision_describe_with_cache(
                redis,
                target.image_url,
                model=get_settings().OPENAI_VISION_MODEL,
                prompt=VISION_PROMPT,
            )
            description = vision["description"]
            models_used.append(vision["model"])
            if not vision_cache_hit:
                await _record_usage(redis, vision["model"])
            await _succeed_job(
                session,
                transform_job,
                {"description": description, "model": vision["model"]},
            )
            # TODO: LLM 작업자 영역 — masking 결과 bytes를 받아서 upload_and_attach_processed_image() 호출

            classify_job = await _start_job(
                session,
                design_id=parsed_design_id,
                design_image_id=target.design_image_id,
                job_type=LlmJobType.CLASSIFY,
                attempts=job_try,
                request_payload={"description": description},
            )
            current_job_id = classify_job.id
            classified = await openai_client.classify_from_description(description)
            models_used.append(classified["model"])
            await _record_usage(redis, classified["model"])
            design.ai_tags = classified["ai_tags"]
            design.color_palette = classified["color_palette"]
            design.style_category = classified["style_category"]
            design.nail_shape = classified["nail_shape"]
            design.ai_confidence = _decimal_confidence(classified["confidence"])
            await _succeed_job(
                session,
                classify_job,
                {
                    "ai_tags": classified["ai_tags"],
                    "color_palette": classified["color_palette"],
                    "style_category": classified["style_category"],
                    "nail_shape": classified["nail_shape"],
                    "confidence": classified["confidence"],
                    "model": classified["model"],
                },
            )

            embed_input = f"{description} {' '.join(classified['ai_tags'])}".strip()
            embed_job = await _start_job(
                session,
                design_id=parsed_design_id,
                design_image_id=target.design_image_id,
                job_type=LlmJobType.EMBED,
                attempts=job_try,
                request_payload={"text": embed_input},
            )
            current_job_id = embed_job.id
            embedding = await openai_client.embed_text(embed_input)
            embed_model = get_settings().OPENAI_EMBED_MODEL
            models_used.append(embed_model)
            await _record_usage(redis, embed_model)
            design.embedding = embedding
            await _succeed_job(
                session,
                embed_job,
                {"dimensions": len(embedding), "model": embed_model},
            )

            design.ai_analysis_status = AiAnalysisStatus.DONE
            design.ai_model_version = _model_version(models_used)
            design.ai_error_code = None
            design.ai_error_message = None
            design.search_indexed_at = _now()
            await session.commit()
            logger.info("design.analyze.done", design_id=str(parsed_design_id))
        except Exception as exc:
            await session.rollback()
            error_code, error_message = _error_details(exc)
            if current_job_id is not None:
                await _fail_job(
                    session,
                    current_job_id,
                    error_code=error_code,
                    error_message=error_message,
                )
            if job_try >= max_tries:
                await _mark_design_failed(
                    session,
                    parsed_design_id,
                    error_code=error_code,
                    error_message=error_message,
                )
            await session.commit()
            logger.warning(
                "design.analyze.failed",
                design_id=str(parsed_design_id),
                job_try=job_try,
                max_tries=max_tries,
                error_code=error_code,
            )
            raise
