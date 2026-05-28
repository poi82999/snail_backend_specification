from uuid import UUID, uuid4

import pytest
from app.core.security import decode_token
from app.models.enums import ActorType, UploadTargetType
from app.models.ops import UploadObject
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_submit_and_get_business_verification(
    api_client: AsyncClient,
    db_session: AsyncSession,
    owner_token: str,
    mock_gcs: None,
) -> None:
    owner_id = UUID(str(decode_token(owner_token)["sub"]))
    object_key = "business_license/00/license.jpg"
    db_session.add(
        UploadObject(
            id=uuid4(),
            owner_actor_type=ActorType.OWNER.value,
            owner_actor_id=owner_id,
            target_type=UploadTargetType.BUSINESS_LICENSE,
            object_key=object_key,
            content_type="image/jpeg",
            byte_size=1024,
        )
    )
    await db_session.flush()

    post_response = await api_client.post(
        "/api/v1/owners/me/business-verification",
        json={
            "business_registration_number": "123-45-67890",
            "document_object_key": object_key,
        },
        headers={
            "Authorization": f"Bearer {owner_token}",
            "Idempotency-Key": f"business-verification-{uuid4()}",
        },
    )
    assert post_response.status_code == 201
    assert post_response.json()["status"] == "pending"

    get_response = await api_client.get(
        "/api/v1/owners/me/business-verification",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == post_response.json()["id"]
