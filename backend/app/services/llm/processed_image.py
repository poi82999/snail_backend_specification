from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.core import gcs
from app.core.config import get_settings
from app.models.design import DesignImage


class ProcessedImageBlob(Protocol):
    def upload_from_string(self, data: bytes, *, content_type: str) -> object: ...


class ProcessedImageBucket(Protocol):
    def blob(self, blob_name: str) -> ProcessedImageBlob: ...


class ProcessedImageGcsClient(Protocol):
    def bucket(self, bucket_name: str) -> ProcessedImageBucket: ...


def _upload_processed_image_sync(
    gcs_client: ProcessedImageGcsClient,
    *,
    bucket_name: str,
    object_key: str,
    image_bytes: bytes,
    content_type: str,
) -> None:
    bucket = gcs_client.bucket(bucket_name)
    blob = bucket.blob(object_key)
    blob.upload_from_string(image_bytes, content_type=content_type)


async def upload_and_attach_processed_image(
    session: AsyncSession,
    gcs_client: ProcessedImageGcsClient,
    design_image_id: UUID,
    image_bytes: bytes,
    content_type: str = "image/png",
) -> str:
    settings = get_settings()
    if not settings.GCS_BUCKET_DESIGNS:
        raise AppError(
            "GCS_BUCKET_NOT_CONFIGURED",
            "스토리지 설정이 없습니다.",
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    image = await session.get(DesignImage, design_image_id)
    if image is None:
        raise AppError(
            "DESIGN_IMAGE_NOT_FOUND",
            "디자인 이미지를 찾을 수 없습니다.",
            HTTPStatus.NOT_FOUND,
        )

    object_key = f"designs/processed/{design_image_id}.png"
    await asyncio.to_thread(
        _upload_processed_image_sync,
        gcs_client,
        bucket_name=settings.GCS_BUCKET_DESIGNS,
        object_key=object_key,
        image_bytes=image_bytes,
        content_type=content_type,
    )

    public_url = gcs.get_public_url(object_key)
    image.processed_url = public_url
    await session.flush()
    return public_url
