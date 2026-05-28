from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from app.core import database
from app.core.security import hash_password
from app.models.accounts import Owner
from app.models.design import Design, DesignImage, LlmJob
from app.models.enums import AiAnalysisStatus, JobStatus, LlmJobType, VerificationStatus, Visibility
from app.models.shop import Shop
from app.workers.llm_pipeline import analyze_design
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


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


@pytest.mark.asyncio
async def test_analyze_design_populates_design_ai_fields(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    mock_openai: type[object],
) -> None:
    monkeypatch.setattr(database, "_sessionmaker", _SessionFactory(db_session))
    owner = Owner(
        id=uuid4(),
        email=f"{uuid4().hex}@example.com",
        password_hash=hash_password("Strong123"),
        representative_name="대표",
        phone_number="010-0000-0000",
        verification_status=VerificationStatus.APPROVED,
    )
    shop = Shop(
        id=uuid4(),
        owner_id=owner.id,
        name="테스트 샵",
        address="서울",
        phone_number="02-0000-0000",
        visibility=Visibility.ACTIVE,
    )
    design = Design(
        id=uuid4(),
        shop_id=shop.id,
        title="분석 대상 네일",
        base_price=30000,
        duration_minutes=60,
        visibility=Visibility.ACTIVE,
        ai_analysis_status=AiAnalysisStatus.PENDING,
    )
    image = DesignImage(
        id=uuid4(),
        design_id=design.id,
        original_url="https://cdn.test/not-thumb.jpg",
        sort_order=2,
        is_thumbnail=False,
    )
    thumbnail = DesignImage(
        id=uuid4(),
        design_id=design.id,
        original_url="https://cdn.test/thumb.jpg",
        sort_order=9,
        is_thumbnail=True,
    )
    db_session.add_all([owner, shop, design, image, thumbnail])
    await db_session.flush()

    await analyze_design({"job_try": 1, "redis": None}, str(design.id))

    await db_session.refresh(design)
    jobs = list(
        (
            await db_session.scalars(
                select(LlmJob).where(LlmJob.design_id == design.id).order_by(LlmJob.started_at)
            )
        ).all()
    )
    assert design.ai_analysis_status == AiAnalysisStatus.DONE
    assert design.ai_tags == ["clean", "pink"]
    assert design.color_palette == ["pink"]
    assert design.style_category == "simple"
    assert design.nail_shape == "round"
    assert design.ai_confidence is not None
    assert design.embedding is not None
    assert len(design.embedding) == 1536
    assert design.search_indexed_at is not None
    assert len(jobs) == 3
    assert [job.job_type for job in jobs] == [
        LlmJobType.TRANSFORM,
        LlmJobType.CLASSIFY,
        LlmJobType.EMBED,
    ]
    assert {job.status for job in jobs} == {JobStatus.SUCCEEDED}
    assert jobs[0].design_image_id == thumbnail.id
