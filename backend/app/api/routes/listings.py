from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_optional_current_user, require_account_status
from app.db.enums import UserStatus
from app.db.models import User
from app.modules.auth.schemas import MessageResponse
from app.modules.listings.schemas import (
    ListingCreateRequest,
    ListingDetailSchema,
    ListingMediaOrderRequest,
    ListingMediaSchema,
    ListingStatusSchema,
    ListingSummarySchema,
    ListingUpdateRequest,
)
from app.modules.listings.service import (
    archive_listing,
    create_listing,
    deactivate_listing,
    delete_listing_media,
    get_listing_detail,
    list_owner_listings,
    list_public_listings,
    mark_listing_sold,
    reactivate_listing,
    reorder_listing_media,
    replace_listing_media,
    set_primary_listing_media,
    submit_listing_for_review,
    update_listing,
    upload_listing_media,
)
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/listings", tags=["listings"])


def _resolved_locale(current_user: User | None, locale: str | None) -> str:
    return locale or (current_user.locale if current_user else "en")


@router.get(
    "",
    response_model=list[ListingSummarySchema],
    summary="List publicly visible approved marketplace listings",
)
def public_listings(
    category_public_id: str | None = Query(default=None),
    locale: Literal["en", "ru"] | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> list[ListingSummarySchema]:
    return list_public_listings(
        db,
        locale=_resolved_locale(current_user, locale),
        category_public_id=category_public_id,
    )


@router.get(
    "/me",
    response_model=list[ListingSummarySchema],
    summary="List all listings owned by the authenticated user, including hidden statuses",
)
def own_listings(
    locale: Literal["en", "ru"] | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> list[ListingSummarySchema]:
    return list_owner_listings(db, owner=current_user, locale=_resolved_locale(current_user, locale))


@router.post(
    "",
    response_model=ListingDetailSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a draft listing",
)
def create_listing_endpoint(
    payload: ListingCreateRequest,
    locale: Literal["en", "ru"] | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> ListingDetailSchema:
    listing = create_listing(db, owner=current_user, payload=payload, locale=_resolved_locale(current_user, locale))
    db.commit()
    return listing


@router.patch(
    "/{listing_public_id}",
    response_model=ListingDetailSchema,
    summary="Update a listing owned by the authenticated user or by an admin",
)
def update_listing_endpoint(
    listing_public_id: str,
    payload: ListingUpdateRequest,
    locale: Literal["en", "ru"] | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> ListingDetailSchema:
    listing = update_listing(
        db,
        listing_public_id=listing_public_id,
        actor=current_user,
        payload=payload,
        locale=_resolved_locale(current_user, locale),
    )
    db.commit()
    return listing


@router.post(
    "/{listing_public_id}/submit-review",
    response_model=ListingStatusSchema,
    summary="Submit a listing for moderation review",
)
def submit_review_endpoint(
    listing_public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> ListingStatusSchema:
    response = submit_listing_for_review(db, listing_public_id=listing_public_id, actor=current_user)
    db.commit()
    return response


@router.post(
    "/{listing_public_id}/archive",
    response_model=ListingStatusSchema,
    summary="Archive a listing",
)
def archive_listing_endpoint(
    listing_public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> ListingStatusSchema:
    response = archive_listing(db, listing_public_id=listing_public_id, actor=current_user)
    db.commit()
    return response


@router.post(
    "/{listing_public_id}/deactivate",
    response_model=ListingStatusSchema,
    summary="Deactivate a published listing",
)
def deactivate_listing_endpoint(
    listing_public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> ListingStatusSchema:
    response = deactivate_listing(db, listing_public_id=listing_public_id, actor=current_user)
    db.commit()
    return response


@router.post(
    "/{listing_public_id}/reactivate",
    response_model=ListingStatusSchema,
    summary="Reactivate an inactive or archived listing",
)
def reactivate_listing_endpoint(
    listing_public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> ListingStatusSchema:
    response = reactivate_listing(db, listing_public_id=listing_public_id, actor=current_user)
    db.commit()
    return response


@router.post(
    "/{listing_public_id}/mark-sold",
    response_model=ListingStatusSchema,
    summary="Mark a listing as sold or closed",
)
def mark_listing_sold_endpoint(
    listing_public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> ListingStatusSchema:
    response = mark_listing_sold(db, listing_public_id=listing_public_id, actor=current_user)
    db.commit()
    return response


@router.post(
    "/{listing_public_id}/media",
    response_model=ListingMediaSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a media item for a listing",
)
def upload_listing_media_endpoint(
    listing_public_id: str,
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> ListingMediaSchema:
    media = upload_listing_media(
        db,
        settings=settings,
        listing_public_id=listing_public_id,
        actor=current_user,
        upload=upload,
    )
    db.commit()
    return media


@router.put(
    "/{listing_public_id}/media/{media_public_id}",
    response_model=ListingMediaSchema,
    summary="Replace an existing listing media asset",
)
def replace_listing_media_endpoint(
    listing_public_id: str,
    media_public_id: str,
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> ListingMediaSchema:
    media = replace_listing_media(
        db,
        settings=settings,
        listing_public_id=listing_public_id,
        media_public_id=media_public_id,
        actor=current_user,
        upload=upload,
    )
    db.commit()
    return media


@router.patch(
    "/{listing_public_id}/media/order",
    response_model=list[ListingMediaSchema],
    summary="Reorder active listing media items",
)
def reorder_listing_media_endpoint(
    listing_public_id: str,
    payload: ListingMediaOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> list[ListingMediaSchema]:
    media = reorder_listing_media(db, listing_public_id=listing_public_id, actor=current_user, payload=payload)
    db.commit()
    return media


@router.post(
    "/{listing_public_id}/media/{media_public_id}/primary",
    response_model=list[ListingMediaSchema],
    summary="Set the primary media for a listing",
)
def set_primary_listing_media_endpoint(
    listing_public_id: str,
    media_public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> list[ListingMediaSchema]:
    media = set_primary_listing_media(
        db,
        listing_public_id=listing_public_id,
        media_public_id=media_public_id,
        actor=current_user,
    )
    db.commit()
    return media


@router.delete(
    "/{listing_public_id}/media/{media_public_id}",
    response_model=MessageResponse,
    summary="Delete a media item from a listing",
)
def delete_listing_media_endpoint(
    listing_public_id: str,
    media_public_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> MessageResponse:
    delete_listing_media(
        db,
        settings=settings,
        listing_public_id=listing_public_id,
        media_public_id=media_public_id,
        actor=current_user,
    )
    db.commit()
    return MessageResponse(message="Listing media deleted successfully.")


@router.get(
    "/{listing_public_id}",
    response_model=ListingDetailSchema,
    summary="Get a listing detail view. Owners and admins can view hidden listings.",
)
def listing_detail(
    listing_public_id: str,
    locale: Literal["en", "ru"] | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> ListingDetailSchema:
    return get_listing_detail(
        db,
        listing_public_id=listing_public_id,
        actor=current_user,
        locale=_resolved_locale(current_user, locale),
    )
