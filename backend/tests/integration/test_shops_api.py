from uuid import UUID, uuid4

import pytest
from app.core.security import decode_token
from app.models.accounts import Owner
from app.models.enums import ActorType, UploadTargetType, VerificationStatus
from app.models.ops import UploadObject
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

SHOP_PAYLOAD = {
    "name": "테스트 네일",
    "address": "서울시 강남구 테헤란로 1",
    "address_detail": "2층",
    "region": "강남",
    "phone_number": "02-1234-5678",
    "introduction": "예약제로 운영합니다.",
    "payment_method": "on_site",
    "auto_accept": False,
    "reservation_policy": "예약 시간 10분 전 도착해주세요.",
}


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


@pytest.mark.asyncio
async def test_unapproved_owner_cannot_create_shop(
    api_client: AsyncClient,
    owner_token: str,
) -> None:
    response = await api_client.post(
        "/api/v1/shops/me",
        json=SHOP_PAYLOAD,
        headers=_auth_headers(owner_token, f"shop-create-{uuid4()}"),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "OWNER_NOT_APPROVED"


@pytest.mark.asyncio
async def test_approved_owner_shop_happy_path_and_idempotency(
    api_client: AsyncClient,
    db_session: AsyncSession,
    owner_token: str,
) -> None:
    owner = await _approve_owner(db_session, owner_token)
    create_key = f"shop-create-{uuid4()}"

    create_response = await api_client.post(
        "/api/v1/shops/me",
        json=SHOP_PAYLOAD,
        headers=_auth_headers(owner_token, create_key),
    )
    replay_response = await api_client.post(
        "/api/v1/shops/me",
        json=SHOP_PAYLOAD,
        headers=_auth_headers(owner_token, create_key),
    )

    assert create_response.status_code == 201
    assert replay_response.status_code == 201
    assert replay_response.json() == create_response.json()

    get_response = await api_client.get(
        "/api/v1/shops/me",
        headers=_auth_headers(owner_token),
    )
    assert get_response.status_code == 200
    assert get_response.json()["name"] == SHOP_PAYLOAD["name"]

    patch_response = await api_client.patch(
        "/api/v1/shops/me",
        json={"introduction": "소개를 수정했습니다."},
        headers=_auth_headers(owner_token, f"shop-patch-{uuid4()}"),
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["introduction"] == "소개를 수정했습니다."

    object_key = f"shop/{uuid4().hex}/image.jpg"
    db_session.add(
        UploadObject(
            id=uuid4(),
            owner_actor_type=ActorType.OWNER.value,
            owner_actor_id=owner.id,
            target_type=UploadTargetType.SHOP,
            object_key=object_key,
            content_type="image/jpeg",
            byte_size=1234,
            original_url="https://cdn.test/shop.jpg",
        )
    )
    await db_session.flush()

    image_response = await api_client.post(
        "/api/v1/shops/me/images",
        json={"upload_object_key": object_key, "sort_order": 1, "is_thumbnail": True},
        headers=_auth_headers(owner_token, f"shop-image-{uuid4()}"),
    )
    assert image_response.status_code == 201
    assert image_response.json()["image_url"] == "https://cdn.test/shop.jpg"

    delete_image_response = await api_client.delete(
        f"/api/v1/shops/me/images/{image_response.json()['id']}",
        headers=_auth_headers(owner_token, f"shop-image-delete-{uuid4()}"),
    )
    assert delete_image_response.status_code == 204

    hours_response = await api_client.put(
        "/api/v1/shops/me/business-hours",
        json={
            "entries": [
                {
                    "weekday": weekday,
                    "open_time": "10:00:00",
                    "close_time": "19:00:00",
                    "is_closed": False,
                }
                for weekday in range(7)
            ]
        },
        headers=_auth_headers(owner_token, f"shop-hours-{uuid4()}"),
    )
    assert hours_response.status_code == 204


@pytest.mark.asyncio
async def test_shop_create_with_valid_location_tags(
    api_client: AsyncClient,
    db_session: AsyncSession,
    owner_token: str,
) -> None:
    await _approve_owner(db_session, owner_token)
    response = await api_client.post(
        "/api/v1/shops/me",
        json={**SHOP_PAYLOAD, "location_tags": ["홍대", "성수"]},
        headers=_auth_headers(owner_token, f"shop-create-{uuid4()}"),
    )

    assert response.status_code == 201
    assert response.json()["location_tags"] == ["홍대", "성수"]


@pytest.mark.asyncio
async def test_shop_create_rejects_invalid_location_tag(
    api_client: AsyncClient,
    db_session: AsyncSession,
    owner_token: str,
) -> None:
    await _approve_owner(db_session, owner_token)
    response = await api_client.post(
        "/api/v1/shops/me",
        json={**SHOP_PAYLOAD, "location_tags": ["없는동네"]},
        headers=_auth_headers(owner_token, f"shop-create-{uuid4()}"),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_LOCATION_TAG"


@pytest.mark.asyncio
async def test_list_public_shops_filters_by_location_tag(
    api_client: AsyncClient,
    db_session: AsyncSession,
    owner_token: str,
) -> None:
    from app.models.enums import Visibility
    from app.models.shop import Shop

    owner = await _approve_owner(db_session, owner_token)
    create_response = await api_client.post(
        "/api/v1/shops/me",
        json={**SHOP_PAYLOAD, "location_tags": ["연남"]},
        headers=_auth_headers(owner_token, f"shop-create-{uuid4()}"),
    )
    assert create_response.status_code == 201
    shop_id = create_response.json()["id"]

    shop = await db_session.get(Shop, UUID(shop_id))
    assert shop is not None
    shop.visibility = Visibility.ACTIVE
    await db_session.flush()

    response = await api_client.get("/api/v1/shops", params={"location_tag": "연남"})
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert shop_id in ids
    assert all("연남" in item["location_tags"] for item in response.json())

    # owner는 한 개만 만들었고 seed 샵은 위치 태그가 비어 있어 매칭되지 않아야 함
    assert len(response.json()) == 1
    _ = owner


@pytest.mark.asyncio
async def test_list_public_shops_rejects_malformed_bbox(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/shops", params={"bbox": "1,2,3"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_BBOX"
