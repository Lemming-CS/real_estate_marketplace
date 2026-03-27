from __future__ import annotations

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status, require_roles
from app.db.enums import ListingStatus, RoleCode, UserStatus
from app.db.models import User
from app.modules.listings.schemas import (
    ListingDetailSchema,
    ListingQueryParams,
    ListingSortOption,
    ModerationReviewRequest,
    PaginatedListingsResponseSchema,
)
from app.modules.listings.service import list_moderation_queue, review_listing

router = APIRouter(prefix="/admin/listings", tags=["admin-listings"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


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
    "/moderation",
    response_model=PaginatedListingsResponseSchema,
    summary="List listings for moderation with search, filters, sorting, and pagination",
)
def moderation_queue(
    q: str | None = Query(default=None),
    category_public_id: str | None = Query(default=None),
    city: str | None = Query(default=None),
    min_price: Decimal | None = Query(default=None),
    max_price: Decimal | None = Query(default=None),
    status: ListingStatus | None = Query(default=None),
    sort: ListingSortOption = Query(default="newest"),
    promoted_first: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    locale: Literal["en", "ru"] = Query(default="en"),
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    __: User = Depends(require_roles(RoleCode.ADMIN)),
) -> PaginatedListingsResponseSchema:
    filters = _validated_listing_filters(
        query=q,
        category_public_id=category_public_id,
        city=city,
        min_price=min_price,
        max_price=max_price,
        status=status,
        sort=sort,
        promoted_first=promoted_first,
        page=page,
        page_size=page_size,
    )
    return list_moderation_queue(db, locale=locale, filters=filters)


@router.post(
    "/{listing_public_id}/review",
    response_model=ListingDetailSchema,
    summary="Approve or reject a listing that is pending review",
)
def moderate_listing(
    listing_public_id: str,
    payload: ModerationReviewRequest,
    request: Request,
    locale: Literal["en", "ru"] = Query(default="en"),
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    current_user: User = Depends(require_roles(RoleCode.ADMIN)),
) -> ListingDetailSchema:
    listing = review_listing(
        db,
        listing_public_id=listing_public_id,
        actor=current_user,
        payload=payload,
        locale=locale,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return listing
