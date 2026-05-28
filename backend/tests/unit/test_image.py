from io import BytesIO

import pytest
from app.utils.image import normalize_image
from PIL import Image


@pytest.mark.asyncio
async def test_normalize_image_applies_exif_orientation() -> None:
    source = Image.new("RGB", (80, 40), color=(255, 0, 0))
    exif = Image.Exif()
    exif[274] = 6
    raw = BytesIO()
    source.save(raw, format="JPEG", exif=exif)

    normalized = await normalize_image(raw.getvalue(), max_dim=1024)

    with Image.open(BytesIO(normalized)) as result:
        assert result.format == "JPEG"
        assert result.size == (40, 80)
