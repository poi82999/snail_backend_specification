import asyncio
from http import HTTPStatus
from io import BytesIO

from PIL import Image, ImageOps

from app.api.errors import AppError


def _to_rgb(image: Image.Image) -> Image.Image:
    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def _normalize_image_sync(raw: bytes, max_dim: int) -> bytes:
    if max_dim < 1:
        raise AppError(
            "INVALID_IMAGE_SIZE", "이미지 크기 제한이 올바르지 않습니다.", HTTPStatus.BAD_REQUEST
        )

    try:
        with Image.open(BytesIO(raw)) as source:
            transposed = ImageOps.exif_transpose(source)
            image = transposed if transposed is not None else source.copy()
            image = _to_rgb(image)

            width, height = image.size
            max_side = max(width, height)
            if max_side > max_dim:
                ratio = max_dim / max_side
                resized = (max(1, round(width * ratio)), max(1, round(height * ratio)))
                image = image.resize(resized, Image.Resampling.LANCZOS)

            output = BytesIO()
            image.save(output, format="JPEG", quality=85, optimize=True)
            return output.getvalue()
    except AppError:
        raise
    except Exception as exc:
        raise AppError(
            "INVALID_IMAGE", "이미지를 처리할 수 없습니다.", HTTPStatus.BAD_REQUEST
        ) from exc


async def normalize_image(raw: bytes, max_dim: int = 1024) -> bytes:
    return await asyncio.to_thread(_normalize_image_sync, raw, max_dim)
