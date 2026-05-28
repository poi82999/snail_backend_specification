from uuid import uuid4

import pytest
from app.core.config import get_settings
from app.models.design import DesignImage
from app.services.llm.processed_image import upload_and_attach_processed_image
from sqlalchemy.ext.asyncio import AsyncSession
from tests.community_factories import create_design, create_owner, create_shop


@pytest.mark.asyncio
async def test_upload_and_attach_processed_image_updates_url(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GCS_BUCKET_DESIGNS", "test-designs")
    monkeypatch.setenv("GCS_PUBLIC_BASE_URL", "https://cdn.test")
    get_settings.cache_clear()
    captured: dict[str, object] = {}

    class FakeBlob:
        def __init__(self, name: str) -> None:
            self.name = name

        def upload_from_string(self, data: bytes, *, content_type: str) -> None:
            captured["object_key"] = self.name
            captured["bytes"] = data
            captured["content_type"] = content_type

    class FakeBucket:
        def blob(self, name: str) -> FakeBlob:
            return FakeBlob(name)

    class FakeGcsClient:
        def bucket(self, name: str) -> FakeBucket:
            captured["bucket"] = name
            return FakeBucket()

    owner = await create_owner(db_session)
    shop = await create_shop(db_session, owner)
    design = await create_design(db_session, shop)
    image = DesignImage(
        id=uuid4(),
        design_id=design.id,
        original_url="https://cdn.test/original.jpg",
        sort_order=0,
        is_thumbnail=True,
    )
    db_session.add(image)
    await db_session.flush()

    url = await upload_and_attach_processed_image(
        db_session,
        FakeGcsClient(),
        image.id,
        b"processed-image-bytes",
    )

    expected_key = f"designs/processed/{image.id}.png"
    assert captured["bucket"] == "test-designs"
    assert captured["object_key"] == expected_key
    assert captured["bytes"] == b"processed-image-bytes"
    assert captured["content_type"] == "image/png"
    assert url == f"https://cdn.test/{expected_key}"
    assert image.processed_url == url
    get_settings.cache_clear()
