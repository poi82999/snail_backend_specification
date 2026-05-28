from datetime import datetime
from typing import Any

import pytest
from app.core import gcs
from app.core.config import Settings
from app.models.enums import UploadTargetType


@pytest.mark.asyncio
async def test_issue_signed_upload_url_with_storage_client_mock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/d",
        REDIS_URL="redis://localhost:6379/0",
        JWT_SECRET="x" * 32,
        GCS_BUCKET_DESIGNS="snail-designs",
    )
    captured: dict[str, Any] = {}

    class FakeBlob:
        def __init__(self, name: str) -> None:
            self.name = name

        def generate_signed_url(self, **kwargs: object) -> str:
            captured.update(kwargs)
            return f"https://signed.example.test/{self.name}"

    class FakeBucket:
        def blob(self, name: str) -> FakeBlob:
            captured["object_key"] = name
            return FakeBlob(name)

    class FakeClient:
        def bucket(self, name: str) -> FakeBucket:
            captured["bucket"] = name
            return FakeBucket()

    monkeypatch.setattr(gcs, "get_settings", lambda: settings)
    monkeypatch.setattr(gcs, "get_storage_client", lambda: FakeClient())

    response = await gcs.issue_signed_upload_url(
        UploadTargetType.DESIGN,
        "image/jpeg",
        max_bytes=1024,
    )

    assert captured["bucket"] == "snail-designs"
    assert response.upload_url.startswith("https://signed.example.test/design/")
    assert response.object_key.startswith("design/")
    assert response.object_key.endswith(".jpg")
    assert response.gcs_uri == f"gs://snail-designs/{response.object_key}"
    assert response.headers["Content-Type"] == "image/jpeg"
    assert response.headers["x-goog-content-length-range"] == "0,1024"
    assert captured["method"] == "PUT"
    assert captured["version"] == "v4"
    assert isinstance(captured["expiration"], datetime)
