from collections.abc import AsyncIterator
from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from app.api.errors import AppError
from app.core import database
from app.models.design import Design, LlmJob
from app.models.enums import ActorType, AiAnalysisStatus, JobStatus, LlmJobType, UploadTargetType
from app.services.llm import openai_client
from app.workers.llm_pipeline import analyze_design
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.community_factories import (
    auth_headers,
    create_designer,
    create_owner,
    create_shop,
    create_upload,
    owner_token,
)


class _SessionContext:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *args: object) -> bool:
        return False


class _SessionFactory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def __call__(self) -> AsyncIterator[AsyncSession]:
        return _SessionContext(self._session)


@pytest.fixture
def worker_sessionmaker(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(database, "_sessionmaker", _SessionFactory(db_session))


async def _create_design_via_api(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> tuple[UUID, str]:
    owner = await create_owner(db_session)
    token = owner_token(owner)
    shop = await create_shop(db_session, owner)
    designer = await create_designer(db_session, shop)
    upload = await create_upload(
        db_session,
        ActorType.OWNER,
        owner.id,
        UploadTargetType.DESIGN,
    )

    response = await api_client.post(
        "/api/v1/shops/me/designs",
        json={
            "title": "러블리 핑크",
            "description": "봄 네일",
            "base_price": 40000,
            "duration_minutes": 90,
            "designer_ids": [str(designer.id)],
            "image_upload_keys": [upload.object_key],
            "owner_tags": ["봄"],
        },
        headers=auth_headers(token, f"design-analysis-create-{uuid4()}"),
    )
    assert response.status_code == 201, response.text
    return UUID(response.json()["id"]), token


async def _jobs(db_session: AsyncSession, design_id: UUID) -> list[LlmJob]:
    return list(
        (
            await db_session.scalars(
                select(LlmJob).where(LlmJob.design_id == design_id).order_by(LlmJob.started_at)
            )
        ).all()
    )


@pytest.mark.asyncio
async def test_created_design_can_be_analyzed_in_process(
    api_client: AsyncClient,
    db_session: AsyncSession,
    worker_sessionmaker: None,
    mock_openai: type[object],
) -> None:
    design_id, _ = await _create_design_via_api(api_client, db_session)

    await analyze_design({"job_try": 1, "redis": None}, str(design_id))

    design = await db_session.get(Design, design_id)
    assert design is not None
    assert design.ai_analysis_status == AiAnalysisStatus.DONE
    assert design.ai_tags
    assert design.embedding is not None
    jobs = await _jobs(db_session, design_id)
    assert len(jobs) == 3
    assert [job.job_type for job in jobs] == [
        LlmJobType.TRANSFORM,
        LlmJobType.CLASSIFY,
        LlmJobType.EMBED,
    ]
    assert {job.status for job in jobs} == {JobStatus.SUCCEEDED}


@pytest.mark.asyncio
async def test_reanalyze_runs_second_llm_job_set(
    api_client: AsyncClient,
    db_session: AsyncSession,
    worker_sessionmaker: None,
    mock_openai: type[object],
) -> None:
    design_id, token = await _create_design_via_api(api_client, db_session)
    await analyze_design({"job_try": 1, "redis": None}, str(design_id))

    response = await api_client.post(
        f"/api/v1/shops/me/designs/{design_id}/reanalyze",
        headers=auth_headers(token, f"design-analysis-reanalyze-{uuid4()}"),
    )
    assert response.status_code == 202, response.text
    assert response.json()["design_id"] == str(design_id)

    await analyze_design({"job_try": 1, "redis": None}, str(design_id))

    design = await db_session.get(Design, design_id)
    assert design is not None
    assert design.ai_analysis_status == AiAnalysisStatus.DONE
    jobs = await _jobs(db_session, design_id)
    assert len(jobs) == 6
    assert [job.job_type for job in jobs[-3:]] == [
        LlmJobType.TRANSFORM,
        LlmJobType.CLASSIFY,
        LlmJobType.EMBED,
    ]


@pytest.mark.asyncio
async def test_last_attempt_vision_failure_marks_design_failed(
    api_client: AsyncClient,
    db_session: AsyncSession,
    worker_sessionmaker: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design_id, _ = await _create_design_via_api(api_client, db_session)

    async def fail_vision(image_url: str, *, prompt: str) -> openai_client.VisionResult:
        raise AppError("VISION_FAILED", "비전 분석에 실패했습니다.", HTTPStatus.BAD_GATEWAY)

    monkeypatch.setattr(openai_client, "vision_describe", fail_vision)

    with pytest.raises(AppError):
        await analyze_design({"job_try": 3, "max_tries": 3, "redis": None}, str(design_id))

    design = await db_session.get(Design, design_id)
    assert design is not None
    assert design.ai_analysis_status == AiAnalysisStatus.FAILED
    assert design.ai_error_code == "VISION_FAILED"
    jobs = await _jobs(db_session, design_id)
    assert len(jobs) == 1
    assert jobs[0].job_type == LlmJobType.TRANSFORM
    assert jobs[0].status == JobStatus.FAILED
    assert jobs[0].error_code == "VISION_FAILED"
