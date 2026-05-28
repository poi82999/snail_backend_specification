from app.core import gcs
from app.models.ops import UploadObject


def upload_public_url(upload: UploadObject) -> str:
    return upload.processed_url or upload.original_url or gcs.get_public_url(upload.object_key)
