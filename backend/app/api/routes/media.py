from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError

router = APIRouter(prefix="/media", tags=["media"])

_ALLOWED_PUBLIC_PREFIXES = ("listings/", "profile-images/")


@router.get(
    "/{asset_key:path}",
    summary="Serve public listing and profile media by opaque storage key",
)
def serve_public_media(
    asset_key: str,
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    normalized_key = asset_key.strip().lstrip("/")
    if not normalized_key or not normalized_key.startswith(_ALLOWED_PUBLIC_PREFIXES):
        raise AppError(status_code=404, code="media_not_found", message="Media was not found.")

    base_path = Path(settings.media_storage_path).resolve()
    absolute_path = (base_path / normalized_key).resolve()
    if base_path not in absolute_path.parents and absolute_path != base_path:
        raise AppError(status_code=404, code="media_not_found", message="Media was not found.")
    if not absolute_path.is_file():
        raise AppError(status_code=404, code="media_not_found", message="Media was not found.")

    return FileResponse(absolute_path)
