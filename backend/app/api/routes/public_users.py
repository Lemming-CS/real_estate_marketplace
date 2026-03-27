from __future__ import annotations

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.enums import ListingPurpose, PropertyType
from app.modules.listings.schemas import ListingQueryParams, ListingSortOption, PaginatedListingsResponseSchema
from app.modules.listings.service import list_public_user_listings
from app.modules.users.schemas import PublicUserProfileSchema
from app.modules.users.service import get_public_user_profile

router = APIRouter(prefix="/public/users", tags=["public-users"])


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

@router.get(
    "/{user_public_id}",
    response_model=PublicUserProfileSchema,
    summary="View a public user profile",
)
def public_user_profile(user_public_id: str, db: Session = Depends(get_db)) -> PublicUserProfileSchema:
    return get_public_user_profile(db, public_id=user_public_id)


@router.get(
    "/{user_public_id}/listings",
    response_model=PaginatedListingsResponseSchema,
    summary="Browse active listings for a public seller page",
)
def public_user_listings(
    user_public_id: str,
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
    promoted_first: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    locale: Literal["en", "ru"] = Query(default="en"),
    db: Session = Depends(get_db),
) -> PaginatedListingsResponseSchema:
    filters = _validated_listing_filters(
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
    return list_public_user_listings(
        db,
        owner_public_id=user_public_id,
        locale=locale,
        filters=filters,
    )
