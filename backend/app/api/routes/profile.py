from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_account_status
from app.core.config import Settings, get_settings
from app.db.enums import UserStatus
from app.db.models import User
from app.modules.users.schemas import CurrentUserSchema, ProfileImageResponse, ProfileUpdateRequest
from app.modules.users.service import get_current_user_profile, update_profile, upload_profile_image

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=CurrentUserSchema, summary="View the current user's editable profile")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CurrentUserSchema:
    return get_current_user_profile(db, user=current_user)


@router.patch("/me", response_model=CurrentUserSchema, summary="Update the current user's profile")
def patch_my_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE, UserStatus.PENDING_VERIFICATION)),
) -> CurrentUserSchema:
    profile = update_profile(db, user=current_user, payload=payload)
    db.commit()
    return profile


@router.post("/me/image", response_model=ProfileImageResponse, summary="Upload a profile image")
def upload_my_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE, UserStatus.PENDING_VERIFICATION)),
) -> ProfileImageResponse:
    response = upload_profile_image(db, settings=settings, user=current_user, upload=file)
    db.commit()
    return response

