from uuid import UUID, uuid4

import pytest
from app.core.security import decode_token, hash_password, issue_access_token
from app.models.accounts import Owner
from app.models.enums import ActorType, VerificationStatus
from app.models.shop import Designer, Shop
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


def _auth_headers(token: str, idempotency_key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    return headers


async def _approve_owner(db_session: AsyncSession, owner_token: str) -> Owner:
    owner_id = UUID(str(decode_token(owner_token)["sub"]))
    owner = await db_session.get(Owner, owner_id)
    assert owner is not None
    owner.verification_status = VerificationStatus.APPROVED
    await db_session.flush()
    return owner


async def _create_owner_with_shop(db_session: AsyncSession) -> tuple[Owner, str, Shop]:
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
        phone_number="02-0000-0000",
    )
    db_session.add(shop)
    await db_session.flush()
    return owner, issue_access_token(ActorType.OWNER, owner.id), shop


@pytest.mark.asyncio
async def test_designer_management_happy_path(
    api_client: AsyncClient,
    db_session: AsyncSession,
    owner_token: str,
) -> None:
    owner = await _approve_owner(db_session, owner_token)
    db_session.add(
        Shop(
            id=uuid4(),
            owner_id=owner.id,
            name="테스트 샵",
            address="서울시 강남구",
            phone_number="02-0000-0000",
        )
    )
    await db_session.flush()

    create_response = await api_client.post(
        "/api/v1/shops/me/designers",
        json={"name": "민지", "position": "원장", "career_years": 5, "specialty_tags": ["art"]},
        headers=_auth_headers(owner_token, f"designer-create-{uuid4()}"),
    )
    assert create_response.status_code == 201
    designer_id = create_response.json()["id"]

    list_response = await api_client.get(
        "/api/v1/shops/me/designers",
        headers=_auth_headers(owner_token),
    )
    assert list_response.status_code == 200
    assert [designer["id"] for designer in list_response.json()] == [designer_id]

    patch_response = await api_client.patch(
        f"/api/v1/shops/me/designers/{designer_id}",
        json={"position": "실장", "specialty_tags": ["art", "care"]},
        headers=_auth_headers(owner_token, f"designer-patch-{uuid4()}"),
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["position"] == "실장"

    schedule_response = await api_client.put(
        f"/api/v1/shops/me/designers/{designer_id}/schedule",
        json={
            "entries": [
                {
                    "weekday": weekday,
                    "start_time": "10:00:00",
                    "end_time": "18:00:00",
                    "break_start_time": "13:00:00",
                    "break_end_time": "14:00:00",
                    "is_day_off": False,
                }
                for weekday in range(7)
            ]
        },
        headers=_auth_headers(owner_token, f"designer-schedule-{uuid4()}"),
    )
    assert schedule_response.status_code == 204

    time_off_response = await api_client.post(
        f"/api/v1/shops/me/designers/{designer_id}/time-off",
        json={"off_date": "2026-06-01", "reason": "개인 휴무"},
        headers=_auth_headers(owner_token, f"designer-time-off-{uuid4()}"),
    )
    assert time_off_response.status_code == 201

    delete_time_off_response = await api_client.delete(
        f"/api/v1/shops/me/designers/{designer_id}/time-off/{time_off_response.json()['id']}",
        headers=_auth_headers(owner_token, f"designer-time-off-delete-{uuid4()}"),
    )
    assert delete_time_off_response.status_code == 204

    delete_response = await api_client.delete(
        f"/api/v1/shops/me/designers/{designer_id}",
        headers=_auth_headers(owner_token, f"designer-delete-{uuid4()}"),
    )
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_other_shop_designer_access_returns_not_found(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    _, _, first_shop = await _create_owner_with_shop(db_session)
    _, second_token, _ = await _create_owner_with_shop(db_session)
    designer = Designer(
        id=uuid4(),
        shop_id=first_shop.id,
        name="타샵 디자이너",
        specialty_tags=[],
    )
    db_session.add(designer)
    await db_session.flush()

    response = await api_client.patch(
        f"/api/v1/shops/me/designers/{designer.id}",
        json={"name": "수정 시도"},
        headers=_auth_headers(second_token, f"designer-cross-shop-{uuid4()}"),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DESIGNER_NOT_FOUND"
