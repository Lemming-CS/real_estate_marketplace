from __future__ import annotations

from decimal import Decimal
from typing import Literal
from fastapi.encoders import jsonable_encoder
from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_optional_current_user, require_account_status
from app.core.config import Settings, get_settings
from app.db.enums import ListingPurpose, ListingStatus, PropertyType, UserStatus
from app.db.models import User
from app.modules.auth.schemas import MessageResponse
from app.modules.listings.schemas import (
    ListingCreateRequest,
    ListingDetailSchema,
    ListingMediaOrderRequest,
    ListingMediaSchema,
    ListingQueryParams,
    ListingSortOption,
    ListingStatusSchema,
    PaginatedListingsResponseSchema,
    ListingUpdateRequest,
)
from app.modules.listings.service import (
    archive_listing,
    create_listing,
    deactivate_listing,
    delete_listing_media,
    get_listing_detail,
    list_owner_discovery_listings,
    list_public_listings,
    mark_listing_sold,
    publish_listing,
    reactivate_listing,
    reorder_listing_media,
    replace_listing_media,
    set_primary_listing_media,
    submit_listing_for_review,
    update_listing,
    upload_listing_media,
)

router = APIRouter(prefix="/listings", tags=["listings"])


def _resolved_locale(current_user: User | None, locale: str | None) -> str:
    return locale or (current_user.locale if current_user else "en")


def _validated_listing_filters(**data) -> ListingQueryParams:
    try:
        return ListingQueryParams(**data)
    except ValidationError as exc:
        safe_errors = []

        for err in exc.errors():
            safe_errors.append(
                {
                    "loc": [str(x) for x in err.get("loc", [])],
                    "msg": str(err.get("msg", "Invalid request")),
                    "type": str(err.get("type", "value_error")),
                }
            )

        raise HTTPException(status_code=422, detail=safe_errors) from exc

def _public_listing_filters(
    q: str | None = Query(default=None),
    category_public_id: str | None = Query(default=None),
    purpose: ListingPurpose | None = Query(default=None),
    property_type: PropertyType | None = Query(default=None),
    city: str | None = Query(default=None),
    district: str | None = Query(default=None),
    min_price: Decimal | None = Query(default=None),
    max_price: Decimal | None = Query(default=None),
    min_area_sqm: Decimal | None = Query(default=None),
    max_area_sqm: Decimal | None = Query(default=None),
    room_count: int | None = Query(default=None, ge=1, le=50),
    sort: ListingSortOption = Query(default="newest"),
    promoted_first: bool = Query(default=True),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
) -> ListingQueryParams:
    return _validated_listing_filters(
        query=q,
        category_public_id=category_public_id,
        purpose=purpose,
        property_type=property_type,
        city=city,
        district=district,
        min_price=min_price,
        max_price=max_price,
        min_area_sqm=min_area_sqm,
        max_area_sqm=max_area_sqm,
        room_count=room_count,
        sort=sort,
        promoted_first=promoted_first,
        page=page,
        page_size=page_size,
    )


def _owner_listing_filters(
    q: str | None = Query(default=None),
    category_public_id: str | None = Query(default=None),
    purpose: ListingPurpose | None = Query(default=None),
    property_type: PropertyType | None = Query(default=None),
    city: str | None = Query(default=None),
    district: str | None = Query(default=None),
    min_price: Decimal | None = Query(default=None),
    max_price: Decimal | None = Query(default=None),
    min_area_sqm: Decimal | None = Query(default=None),
    max_area_sqm: Decimal | None = Query(default=None),
    room_count: int | None = Query(default=None, ge=1, le=50),
    status: ListingStatus | None = Query(default=None),
    sort: ListingSortOption = Query(default="newest"),
    promoted_first: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
) -> ListingQueryParams:
    return _validated_listing_filters(
        query=q,
        category_public_id=category_public_id,
        purpose=purpose,
        property_type=property_type,
        city=city,
        district=district,
        min_price=min_price,
        max_price=max_price,
        min_area_sqm=min_area_sqm,
        max_area_sqm=max_area_sqm,
        room_count=room_count,
        status=status,
        sort=sort,
        promoted_first=promoted_first,
        page=page,
        page_size=page_size,
    )


@router.get(
    "",
    response_model=PaginatedListingsResponseSchema,
    summary="List the marketplace home feed with search, filters, sorting, and pagination",
)
def public_listings(
    filters: ListingQueryParams = Depends(_public_listing_filters),
    locale: Literal["en", "ru"] | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> PaginatedListingsResponseSchema:
    return list_public_listings(
        db,
        locale=_resolved_locale(current_user, locale),
        filters=filters,
    )


@router.get(
    "/me",
    response_model=PaginatedListingsResponseSchema,
    summary="List all listings owned by the authenticated user with private-status filters",
)
def own_listings(
    filters: ListingQueryParams = Depends(_owner_listing_filters),
    locale: Literal["en", "ru"] | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> PaginatedListingsResponseSchema:
    return list_owner_discovery_listings(
        db,
        owner=current_user,
        locale=_resolved_locale(current_user, locale),
        filters=filters,
    )


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
    "/{listing_public_id}/publish",
    response_model=ListingStatusSchema,
    summary="Publish a listing directly when validation passes",
)
def publish_listing_endpoint(
    listing_public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> ListingStatusSchema:
    response = publish_listing(db, listing_public_id=listing_public_id, actor=current_user)
    db.commit()
    return response


@router.post(
    "/{listing_public_id}/submit-review",
    response_model=ListingStatusSchema,
    summary="Legacy alias for publish; active sellers can publish directly when validation passes",
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
    guest_token: str | None = Header(default=None, alias="X-Guest-Token"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> ListingDetailSchema:
    listing = get_listing_detail(
        db,
        listing_public_id=listing_public_id,
        actor=current_user,
        guest_token=guest_token,
        locale=_resolved_locale(current_user, locale),
    )
    db.commit()
    return listing
