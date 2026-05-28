from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from app.api.errors import AppError
from app.core.security import hash_password
from app.models.accounts import Owner
from app.models.design import Design
from app.models.enums import (
    ActorType,
    AiAnalysisStatus,
    UploadTargetType,
    VerificationStatus,
    Visibility,
)
from app.models.ops import UploadObject
from app.models.shop import Designer, Shop
from app.schemas.designs import DesignCreate
from app.services import design_service
from sqlalchemy.ext.asyncio import AsyncSession


async def _owner(db_session: AsyncSession, *, approved: bool = True) -> Owner:
    owner = Owner(
        id=uuid4(),
        email=f"{uuid4().hex}@example.com",
        password_hash=hash_password("Strong123"),
        representative_name="대표",
        phone_number="010-0000-0000",
        verification_status=(
            VerificationStatus.APPROVED if approved else VerificationStatus.PENDING
        ),
    )
    db_session.add(owner)
    await db_session.flush()
    return owner


async def _shop(
    db_session: AsyncSession,
    owner: Owner,
    *,
    visibility: Visibility = Visibility.ACTIVE,
    region: str = "강남",
) -> Shop:
    shop = Shop(
        id=uuid4(),
        owner_id=owner.id,
        name="테스트 샵",
        address="서울시 강남구",
        region=region,
        phone_number="02-0000-0000",
        visibility=visibility,
    )
    db_session.add(shop)
    await db_session.flush()
    return shop


async def _designer(db_session: AsyncSession, shop: Shop) -> Designer:
    designer = Designer(
        id=uuid4(),
        shop_id=shop.id,
        name="디자이너",
        specialty_tags=[],
        is_active=True,
    )
    db_session.add(designer)
    await db_session.flush()
    return designer


async def _upload(
    db_session: AsyncSession,
    owner_id: UUID,
    *,
    object_key: str | None = None,
) -> UploadObject:
    key = object_key or f"design/{uuid4().hex}.jpg"
    upload = UploadObject(
        id=uuid4(),
        owner_actor_type=ActorType.OWNER.value,
        owner_actor_id=owner_id,
        target_type=UploadTargetType.DESIGN,
        object_key=key,
        content_type="image/jpeg",
        byte_size=1024,
        original_url=f"https://cdn.test/{key}",
    )
    db_session.add(upload)
    await db_session.flush()
    return upload


async def _design(
    db_session: AsyncSession,
    shop: Shop,
    *,
    visibility: Visibility = Visibility.ACTIVE,
    ai_status: AiAnalysisStatus = AiAnalysisStatus.DONE,
) -> Design:
    design = Design(
        id=uuid4(),
        shop_id=shop.id,
        title="핑크 프렌치 네일",
        base_price=30000,
        duration_minutes=60,
        visibility=visibility,
        ai_analysis_status=ai_status,
    )
    db_session.add(design)
    await db_session.flush()
    return design


def _payload(designer: Designer, upload: UploadObject) -> DesignCreate:
    return DesignCreate(
        title="러블리 핑크",
        description="테스트 디자인",
        base_price=30000,
        duration_minutes=60,
        designer_ids=[designer.id],
        image_upload_keys=[upload.object_key],
        owner_tags=["러블리"],
    )


@pytest.mark.asyncio
async def test_create_design_without_shop_returns_404(db_session: AsyncSession) -> None:
    owner = await _owner(db_session)
    upload = await _upload(db_session, owner.id)
    designer = Designer(id=uuid4(), shop_id=uuid4(), name="없는 디자이너", specialty_tags=[])

    with pytest.raises(AppError) as exc_info:
        await design_service.create_design(db_session, owner.id, _payload(designer, upload))

    assert exc_info.value.code == "SHOP_NOT_FOUND"
    assert exc_info.value.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_create_design_rejects_other_shop_designer(db_session: AsyncSession) -> None:
    owner = await _owner(db_session)
    shop = await _shop(db_session, owner)
    other_owner = await _owner(db_session)
    other_shop = await _shop(db_session, other_owner)
    other_designer = await _designer(db_session, other_shop)
    upload = await _upload(db_session, owner.id)
    await _designer(db_session, shop)

    with pytest.raises(AppError) as exc_info:
        await design_service.create_design(db_session, owner.id, _payload(other_designer, upload))

    assert exc_info.value.code == "INVALID_DESIGNER"
    assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_create_design_rejects_other_owner_upload(db_session: AsyncSession) -> None:
    owner = await _owner(db_session)
    shop = await _shop(db_session, owner)
    designer = await _designer(db_session, shop)
    other_owner = await _owner(db_session)
    other_upload = await _upload(db_session, other_owner.id)

    with pytest.raises(AppError) as exc_info:
        await design_service.create_design(db_session, owner.id, _payload(designer, other_upload))

    assert exc_info.value.code == "INVALID_UPLOAD"
    assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_enqueue_analysis_job_targets_analyze_design(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design_id = uuid4()
    pool = SimpleNamespace(enqueue_job=AsyncMock())
    monkeypatch.setattr(design_service, "get_arq_pool", lambda: pool)

    await design_service._enqueue_analysis_job(design_id)

    pool.enqueue_job.assert_awaited_once_with("analyze_design", str(design_id))


@pytest.mark.asyncio
async def test_create_design_keeps_pending_when_llm_worker_missing(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = await _owner(db_session)
    shop = await _shop(db_session, owner)
    designer = await _designer(db_session, shop)
    upload = await _upload(db_session, owner.id)

    def fail_import(name: str) -> object:
        if name == "app.workers.llm_pipeline":
            raise ImportError("not ready")
        return __import__(name)

    monkeypatch.setattr("importlib.import_module", fail_import)

    created = await design_service.create_design(db_session, owner.id, _payload(designer, upload))

    assert created.ai_analysis_status == AiAnalysisStatus.PENDING


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("approved", "shop_visibility", "design_visibility", "ai_status"),
    [
        (False, Visibility.ACTIVE, Visibility.ACTIVE, AiAnalysisStatus.DONE),
        (True, Visibility.HIDDEN, Visibility.ACTIVE, AiAnalysisStatus.DONE),
        (True, Visibility.ACTIVE, Visibility.DRAFT, AiAnalysisStatus.DONE),
        (True, Visibility.ACTIVE, Visibility.ACTIVE, AiAnalysisStatus.PENDING),
    ],
)
async def test_get_public_design_enforces_visibility_guards(
    db_session: AsyncSession,
    approved: bool,
    shop_visibility: Visibility,
    design_visibility: Visibility,
    ai_status: AiAnalysisStatus,
) -> None:
    owner = await _owner(db_session, approved=approved)
    shop = await _shop(db_session, owner, visibility=shop_visibility)
    design = await _design(
        db_session,
        shop,
        visibility=design_visibility,
        ai_status=ai_status,
    )

    with pytest.raises(AppError) as exc_info:
        await design_service.get_public_design(db_session, None, design.id)

    assert exc_info.value.code == "DESIGN_NOT_FOUND"
    assert exc_info.value.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_request_reanalyze_resets_pending_status(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pool = SimpleNamespace(enqueue_job=AsyncMock())
    monkeypatch.setattr(design_service, "get_arq_pool", lambda: pool)
    owner = await _owner(db_session)
    shop = await _shop(db_session, owner)
    design = await _design(db_session, shop, ai_status=AiAnalysisStatus.FAILED)
    design.ai_error_code = "VISION_FAILED"
    design.ai_error_message = "비전 실패"

    result = await design_service.request_reanalyze(db_session, owner.id, design.id)

    assert result.ai_analysis_status == AiAnalysisStatus.PENDING
    assert design.ai_error_code is None
    assert design.ai_error_message is None
    pool.enqueue_job.assert_awaited_once_with("analyze_design", str(design.id))
