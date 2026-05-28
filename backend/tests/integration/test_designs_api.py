from uuid import UUID, uuid4

import pytest
from app.core.security import decode_token, hash_password, issue_access_token
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
from app.services import design_service
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


def _auth_headers(token: str, idempotency_key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    return headers


async def _owner_from_token(db_session: AsyncSession, token: str) -> Owner:
    owner_id = UUID(str(decode_token(token)["sub"]))
    owner = await db_session.get(Owner, owner_id)
    assert owner is not None
    owner.verification_status = VerificationStatus.APPROVED
    await db_session.flush()
    return owner


async def _owner_with_shop(db_session: AsyncSession) -> tuple[Owner, str, Shop]:
    owner = Owner(
        id=uuid4(),
        email=f"{uuid4().hex}@example.com",
        password_hash=hash_password("Strong123"),
        representative_name="대표",
        phone_number="010-0000-0000",
        verification_status=VerificationStatus.APPROVED,
    )
    db_session.add(owner)
    await db_session.flush()
    shop = Shop(
        id=uuid4(),
        owner_id=owner.id,
        name="테스트 샵",
        address="서울시 강남구",
        region="강남",
        phone_number="02-0000-0000",
        visibility=Visibility.ACTIVE,
    )
    db_session.add(shop)
    await db_session.flush()
    return owner, issue_access_token(ActorType.OWNER, owner.id), shop


async def _designer(db_session: AsyncSession, shop: Shop) -> Designer:
    designer = Designer(
        id=uuid4(),
        shop_id=shop.id,
        name="민지",
        specialty_tags=[],
    )
    db_session.add(designer)
    await db_session.flush()
    return designer


async def _upload(db_session: AsyncSession, owner: Owner) -> UploadObject:
    object_key = f"design/{uuid4().hex}.jpg"
    upload = UploadObject(
        id=uuid4(),
        owner_actor_type=ActorType.OWNER.value,
        owner_actor_id=owner.id,
        target_type=UploadTargetType.DESIGN,
        object_key=object_key,
        content_type="image/jpeg",
        byte_size=1024,
        original_url=f"https://cdn.test/{object_key}",
    )
    db_session.add(upload)
    await db_session.flush()
    return upload


async def _design(
    db_session: AsyncSession,
    shop: Shop,
    *,
    visibility: Visibility,
    ai_status: AiAnalysisStatus,
) -> Design:
    design = Design(
        id=uuid4(),
        shop_id=shop.id,
        title="핑크 프렌치 네일",
        base_price=30000,
        duration_minutes=60,
        visibility=visibility,
        ai_analysis_status=ai_status,
        ai_tags=["핑크", "러블리"],
        color_palette=["핑크"],
    )
    db_session.add(design)
    await db_session.flush()
    return design


@pytest.mark.asyncio
async def test_owner_design_happy_path(
    api_client: AsyncClient,
    db_session: AsyncSession,
    owner_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def skip_enqueue(_: UUID) -> None:
        return None

    monkeypatch.setattr(design_service, "_enqueue_analysis_job", skip_enqueue)
    owner = await _owner_from_token(db_session, owner_token)
    shop = Shop(
        id=uuid4(),
        owner_id=owner.id,
        name="테스트 샵",
        address="서울시 강남구",
        region="강남",
        phone_number="02-0000-0000",
        visibility=Visibility.ACTIVE,
    )
    db_session.add(shop)
    await db_session.flush()
    designer = await _designer(db_session, shop)
    upload = await _upload(db_session, owner)

    create_response = await api_client.post(
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
        headers=_auth_headers(owner_token, f"design-create-{uuid4()}"),
    )
    assert create_response.status_code == 201
    design_id = create_response.json()["id"]

    list_response = await api_client.get(
        "/api/v1/shops/me/designs",
        headers=_auth_headers(owner_token),
    )
    assert list_response.status_code == 200
    assert [design["id"] for design in list_response.json()] == [design_id]

    patch_response = await api_client.patch(
        f"/api/v1/shops/me/designs/{design_id}",
        json={"title": "수정한 핑크", "base_price": 45000},
        headers=_auth_headers(owner_token, f"design-patch-{uuid4()}"),
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["title"] == "수정한 핑크"

    design = await db_session.get(Design, UUID(design_id))
    assert design is not None
    design.ai_analysis_status = AiAnalysisStatus.DONE
    await db_session.flush()

    reanalyze_response = await api_client.post(
        f"/api/v1/shops/me/designs/{design_id}/reanalyze",
        headers=_auth_headers(owner_token, f"design-reanalyze-{uuid4()}"),
    )
    assert reanalyze_response.status_code == 202
    assert reanalyze_response.json()["design_id"] == design_id

    visibility_response = await api_client.post(
        f"/api/v1/shops/me/designs/{design_id}/visibility",
        json={"visibility": "active"},
        headers=_auth_headers(owner_token, f"design-visibility-{uuid4()}"),
    )
    assert visibility_response.status_code == 200
    assert visibility_response.json()["visibility"] == "active"

    delete_response = await api_client.delete(
        f"/api/v1/shops/me/designs/{design_id}",
        headers=_auth_headers(owner_token, f"design-delete-{uuid4()}"),
    )
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_other_owner_cannot_patch_design(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    _, _, shop = await _owner_with_shop(db_session)
    _, other_token, _ = await _owner_with_shop(db_session)
    design = await _design(
        db_session,
        shop,
        visibility=Visibility.DRAFT,
        ai_status=AiAnalysisStatus.PENDING,
    )

    response = await api_client.patch(
        f"/api/v1/shops/me/designs/{design.id}",
        json={"title": "수정 시도"},
        headers=_auth_headers(other_token, f"design-cross-owner-{uuid4()}"),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DESIGN_NOT_FOUND"


@pytest.mark.asyncio
async def test_draft_design_public_get_returns_404(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    _, _, shop = await _owner_with_shop(db_session)
    design = await _design(
        db_session,
        shop,
        visibility=Visibility.DRAFT,
        ai_status=AiAnalysisStatus.DONE,
    )

    response = await api_client.get(f"/api/v1/designs/{design.id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_pending_design_public_get_returns_404(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    _, _, shop = await _owner_with_shop(db_session)
    design = await _design(
        db_session,
        shop,
        visibility=Visibility.ACTIVE,
        ai_status=AiAnalysisStatus.PENDING,
    )

    response = await api_client.get(f"/api/v1/designs/{design.id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_done_design_with_public_guards_returns_200(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    _, _, shop = await _owner_with_shop(db_session)
    design = await _design(
        db_session,
        shop,
        visibility=Visibility.ACTIVE,
        ai_status=AiAnalysisStatus.DONE,
    )

    response = await api_client.get(f"/api/v1/designs/{design.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(design.id)
