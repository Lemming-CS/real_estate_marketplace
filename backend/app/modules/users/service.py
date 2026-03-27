from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import AppError
from app.db.enums import ListingStatus
from app.db.models import Listing, Role, User, UserRole
from app.modules.users.schemas import (
    CurrentUserSchema,
    OwnerListingSchema,
    ProfileImageResponse,
    ProfileUpdateRequest,
    PublicUserProfileSchema,
)


def _get_role_codes(session: Session, *, user_id: int) -> list[str]:
    return [
        role.value
        for role in session.execute(
            select(Role.code).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id)
        ).scalars()
    ]


def get_current_user_profile(session: Session, *, user: User) -> CurrentUserSchema:
    return CurrentUserSchema(
        public_id=user.public_id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        phone=user.phone,
        bio=user.bio,
        locale=user.locale,
        status=user.status,
        profile_image_path=user.profile_image_path,
        profile_image_mime_type=user.profile_image_mime_type,
        roles=_get_role_codes(session, user_id=user.id),
    )


def update_profile(session: Session, *, user: User, payload: ProfileUpdateRequest) -> CurrentUserSchema:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)
    session.flush()
    return get_current_user_profile(session, user=user)


def upload_profile_image(
    session: Session,
    *,
    settings: Settings,
    user: User,
    upload: UploadFile,
) -> ProfileImageResponse:
    if not upload.content_type or not upload.content_type.startswith("image/"):
        raise AppError(status_code=400, code="invalid_profile_image", message="Only image uploads are allowed.")

    suffix = Path(upload.filename or "profile-image").suffix or ".bin"
    relative_path = Path("profile-images") / user.public_id / f"{uuid4()}{suffix}"
    absolute_path = Path(settings.media_storage_path) / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_bytes(upload.file.read())

    user.profile_image_path = str(relative_path)
    user.profile_image_mime_type = upload.content_type
    session.flush()
    return ProfileImageResponse(
        profile_image_path=user.profile_image_path,
        profile_image_mime_type=user.profile_image_mime_type,
    )


def get_public_user_profile(session: Session, *, public_id: str) -> PublicUserProfileSchema:
    user = session.execute(
        select(User).where(User.public_id == public_id, User.deleted_at.is_(None))
    ).scalar_one_or_none()
    if user is None:
        raise AppError(status_code=404, code="user_not_found", message="User was not found.")

    published_listing_count = session.execute(
        select(func.count(Listing.id)).where(
            Listing.seller_id == user.id,
            Listing.status == ListingStatus.PUBLISHED,
            Listing.deleted_at.is_(None),
        )
    ).scalar_one()

    return PublicUserProfileSchema(
        public_id=user.public_id,
        username=user.username,
        full_name=user.full_name,
        bio=user.bio,
        profile_image_path=user.profile_image_path,
        status=user.status,
        published_listing_count=published_listing_count,
        created_at=user.created_at,
    )


def get_owner_listings(session: Session, *, user: User) -> list[OwnerListingSchema]:
    listings = session.execute(
        select(Listing)
        .where(Listing.seller_id == user.id, Listing.deleted_at.is_(None))
        .order_by(Listing.created_at.desc())
    ).scalars()

    return [
        OwnerListingSchema(
            public_id=listing.public_id,
            title=listing.title,
            status=listing.status,
            price_amount=listing.price_amount,
            currency_code=listing.currency_code,
            city=listing.city,
            published_at=listing.published_at,
            created_at=listing.created_at,
        )
        for listing in listings
    ]
