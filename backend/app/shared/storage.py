from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import AppError

MEDIA_EXTENSION_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def save_upload(
    *,
    settings: Settings,
    upload: UploadFile,
    relative_dir: Path,
    allowed_mime_types: set[str],
    max_size_bytes: int,
) -> tuple[str, int]:
    if not upload.content_type or upload.content_type not in allowed_mime_types:
        raise AppError(
            status_code=400,
            code="invalid_media_type",
            message="Unsupported media type for this upload.",
            details={"allowed_mime_types": sorted(allowed_mime_types)},
        )

    file_bytes = upload.file.read(max_size_bytes + 1)
    if len(file_bytes) > max_size_bytes:
        raise AppError(
            status_code=400,
            code="media_too_large",
            message="Uploaded file exceeds the maximum allowed size.",
            details={"max_size_bytes": max_size_bytes},
        )

    suffix = MEDIA_EXTENSION_BY_MIME.get(upload.content_type)
    if suffix is None:
        suffix = Path(upload.filename or "upload").suffix.lower() or ".bin"

    relative_path = relative_dir / f"{uuid4()}{suffix}"
    absolute_path = Path(settings.media_storage_path) / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_bytes(file_bytes)
    return str(relative_path), len(file_bytes)


def delete_storage_key(*, settings: Settings, storage_key: str) -> None:
    absolute_path = Path(settings.media_storage_path) / storage_key
    absolute_path.unlink(missing_ok=True)
