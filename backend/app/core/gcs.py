import asyncio
import os
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from urllib.parse import quote
from uuid import uuid4

from google.cloud import storage  # type: ignore[import-untyped]
from pydantic import BaseModel

from app.api.errors import AppError
from app.core.config import get_settings
from app.models.enums import UploadTargetType

SIGNED_UPLOAD_EXPIRE_MINUTES = 5
DEFAULT_UPLOAD_MAX_BYTES = 10 * 1024 * 1024

_storage_client: storage.Client | None = None


class SignedUploadResponse(BaseModel):
    upload_url: str
    object_key: str
    gcs_uri: str
    expires_at: datetime
    headers: dict[str, str]


def get_storage_client() -> storage.Client:
    global _storage_client
    if _storage_client is not None:
        return _storage_client

    settings = get_settings()
    if settings.GOOGLE_APPLICATION_CREDENTIALS:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS
        _storage_client = storage.Client.from_service_account_json(
            settings.GOOGLE_APPLICATION_CREDENTIALS,
            project=settings.GCP_PROJECT_ID or None,
        )
    else:
        _storage_client = storage.Client(project=settings.GCP_PROJECT_ID or None)
    return _storage_client


def _bucket_name_for(_: UploadTargetType) -> str:
    settings = get_settings()
    if not settings.GCS_BUCKET_DESIGNS:
        raise AppError(
            "GCS_BUCKET_NOT_CONFIGURED",
            "스토리지 설정이 없습니다.",
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
    return settings.GCS_BUCKET_DESIGNS


def _extension_from_content_type(content_type: str) -> str:
    normalized = content_type.split(";", maxsplit=1)[0].strip().lower()
    known_extensions = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
        "image/heic": "heic",
        "application/pdf": "pdf",
    }
    if normalized in known_extensions:
        return known_extensions[normalized]

    subtype = normalized.partition("/")[2]
    if subtype and subtype.replace("-", "").replace("+", "").isalnum():
        return subtype.split("+", maxsplit=1)[0]
    return "bin"


def _build_object_key(target_type: UploadTargetType, content_type: str) -> str:
    prefix = target_type.value
    shard = uuid4().hex[:2]
    ext = _extension_from_content_type(content_type)
    return f"{prefix}/{shard}/{uuid4()}.{ext}"


def _issue_signed_upload_url_sync(
    target_type: UploadTargetType, content_type: str, max_bytes: int
) -> SignedUploadResponse:
    if max_bytes < 1:
        raise AppError(
            "INVALID_UPLOAD_SIZE", "업로드 크기 제한이 올바르지 않습니다.", HTTPStatus.BAD_REQUEST
        )

    bucket_name = _bucket_name_for(target_type)
    object_key = _build_object_key(target_type, content_type)
    expires_at = datetime.now(UTC) + timedelta(minutes=SIGNED_UPLOAD_EXPIRE_MINUTES)
    headers = {
        "Content-Type": content_type,
        "x-goog-content-length-range": f"0,{max_bytes}",
    }

    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_key)
    upload_url = blob.generate_signed_url(
        version="v4",
        expiration=expires_at,
        method="PUT",
        content_type=content_type,
        headers={"x-goog-content-length-range": headers["x-goog-content-length-range"]},
    )
    return SignedUploadResponse(
        upload_url=str(upload_url),
        object_key=object_key,
        gcs_uri=f"gs://{bucket_name}/{object_key}",
        expires_at=expires_at,
        headers=headers,
    )


async def issue_signed_upload_url(
    target_type: UploadTargetType,
    content_type: str,
    max_bytes: int = DEFAULT_UPLOAD_MAX_BYTES,
) -> SignedUploadResponse:
    return await asyncio.to_thread(
        _issue_signed_upload_url_sync,
        target_type,
        content_type,
        max_bytes,
    )


def get_public_url(object_key: str) -> str:
    settings = get_settings()
    normalized_key = object_key.lstrip("/")
    if settings.GCS_PUBLIC_BASE_URL:
        return f"{settings.GCS_PUBLIC_BASE_URL.rstrip('/')}/{quote(normalized_key)}"

    bucket_name = _bucket_name_for(UploadTargetType.DESIGN)
    return f"https://storage.googleapis.com/{bucket_name}/{quote(normalized_key)}"
