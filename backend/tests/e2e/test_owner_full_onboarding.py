from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from app.models.accounts import BusinessVerification, Owner
from app.models.design import Design
from app.models.enums import (
    ActorType,
    UploadTargetType,
    VerificationStatus,
    Visibility,
)
from app.models.shop import Shop
from app.workers.llm_pipeline import analyze_design
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_owner_signup_to_analyzed_design_search_discovery(
    api_client: AsyncClient,
    db_session: AsyncSession,
    e2e_factory,
    worker_sessionmaker: None,
    mock_openai: type[object],
    mock_apple_signin: object,
) -> None:
    email = f"owner-{uuid4().hex}@example.com"
    signup = await api_client.post(
        "/api/v1/auth/owner/signup",
        json={
            "email": email,
            "password": "Strong123",
            "representative_name": "온보딩 대표",
            "phone_number": "010-1111-2222",
            "accepted_terms_version": "1.0",
            "accepted_privacy_version": "1.0",
        },
        headers={"Idempotency-Key": f"owner-signup-{uuid4()}"},
    )
    assert signup.status_code == 201, signup.text
    owner_id = UUID(signup.json()["id"])

    login = await api_client.post(
        "/api/v1/auth/owner/login",
        json={"email": email, "password": "Strong123"},
    )
    assert login.status_code == 200, login.text
    owner_token = login.json()["access_token"]

    license_upload = await e2e_factory.create_upload(
        ActorType.OWNER,
        owner_id,
        UploadTargetType.BUSINESS_LICENSE,
        object_key=f"business_license/{uuid4().hex}.jpg",
    )
    verification = await api_client.post(
        "/api/v1/owners/me/business-verification",
        json={
            "business_registration_number": "123-45-67890",
            "document_object_key": license_upload.object_key,
        },
        headers=e2e_factory.auth_headers(owner_token, f"business-verification-{uuid4()}"),
    )
    assert verification.status_code == 201, verification.text
    assert verification.json()["status"] == "pending"

    owner = await db_session.get(Owner, owner_id)
    business_verification = await db_session.get(
        BusinessVerification,
        UUID(verification.json()["id"]),
    )
    assert owner is not None
    assert business_verification is not None
    owner.verification_status = VerificationStatus.APPROVED
    business_verification.status = VerificationStatus.APPROVED
    await db_session.flush()

    shop_response = await api_client.post(
        "/api/v1/shops/me",
        json={
            "name": "온보딩 네일",
            "address": "서울시 강남구 테헤란로",
            "address_detail": "3층",
            "region": "강남",
            "phone_number": "02-1234-5678",
            "introduction": "온보딩 e2e 샵",
            "payment_method": "on_site",
            "auto_accept": False,
            "reservation_policy": "예약 변경은 샵에 문의해주세요.",
        },
        headers=e2e_factory.auth_headers(owner_token, f"shop-create-{uuid4()}"),
    )
    assert shop_response.status_code == 201, shop_response.text
    shop = await db_session.get(Shop, UUID(shop_response.json()["id"]))
    assert shop is not None
    shop.visibility = Visibility.ACTIVE
    await db_session.flush()

    hours = [
        {
            "weekday": weekday,
            "open_time": "09:00:00",
            "close_time": "18:00:00",
            "is_closed": False,
        }
        for weekday in range(7)
    ]
    hours_response = await api_client.put(
        "/api/v1/shops/me/business-hours",
        json={"entries": hours},
        headers=e2e_factory.auth_headers(owner_token, f"business-hours-{uuid4()}"),
    )
    assert hours_response.status_code == 204, hours_response.text

    designer_response = await api_client.post(
        "/api/v1/shops/me/designers",
        json={
            "name": "지우",
            "position": "시니어",
            "career_years": 5,
            "specialty_tags": ["핑크", "심플"],
        },
        headers=e2e_factory.auth_headers(owner_token, f"designer-create-{uuid4()}"),
    )
    assert designer_response.status_code == 201, designer_response.text
    designer_id = designer_response.json()["id"]

    schedule = [
        {
            "weekday": weekday,
            "start_time": "09:00:00",
            "end_time": "18:00:00",
            "break_start_time": "12:00:00",
            "break_end_time": "13:00:00",
            "is_day_off": False,
        }
        for weekday in range(7)
    ]
    schedule_response = await api_client.put(
        f"/api/v1/shops/me/designers/{designer_id}/schedule",
        json={"entries": schedule},
        headers=e2e_factory.auth_headers(owner_token, f"designer-schedule-{uuid4()}"),
    )
    assert schedule_response.status_code == 204, schedule_response.text

    design_upload = await e2e_factory.create_upload(
        ActorType.OWNER,
        owner_id,
        UploadTargetType.DESIGN,
        object_key=f"design/{uuid4().hex}.jpg",
    )
    created_design = await api_client.post(
        "/api/v1/shops/me/designs",
        json={
            "title": "Pink clean nail",
            "description": "LLM 분석 후 검색 노출되는 디자인",
            "base_price": 45000,
            "duration_minutes": 60,
            "designer_ids": [designer_id],
            "image_upload_keys": [design_upload.object_key],
            "owner_tags": ["pink"],
        },
        headers=e2e_factory.auth_headers(owner_token, f"design-create-{uuid4()}"),
    )
    assert created_design.status_code == 201, created_design.text
    design_id = UUID(created_design.json()["id"])

    await analyze_design({"job_try": 1, "redis": None}, str(design_id))
    analyzed = await db_session.get(Design, design_id)
    assert analyzed is not None
    assert analyzed.ai_analysis_status == "done"
    assert analyzed.ai_tags == ["clean", "pink"]

    visibility = await api_client.post(
        f"/api/v1/shops/me/designs/{design_id}/visibility",
        json={"visibility": "active"},
        headers=e2e_factory.auth_headers(owner_token, f"design-visible-{uuid4()}"),
    )
    assert visibility.status_code == 200, visibility.text

    apple = await api_client.post(
        "/api/v1/auth/apple",
        json={
            "id_token": "apple-id-token",
            "accepted_terms_version": "1.0",
            "accepted_privacy_version": "1.0",
        },
        headers={"Idempotency-Key": f"apple-signin-{uuid4()}"},
    )
    assert apple.status_code == 200, apple.text

    search = await api_client.get(
        "/api/v1/search",
        params={"q": "pink", "scope": "designs"},
        headers=e2e_factory.auth_headers(apple.json()["tokens"]["access_token"]),
    )
    assert search.status_code == 200, search.text
    assert str(design_id) in [item["id"] for item in search.json()["items"]]
