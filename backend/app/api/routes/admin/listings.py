from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status, require_roles
from app.db.enums import RoleCode, UserStatus
from app.db.models import User
from app.modules.listings.schemas import ListingDetailSchema, ListingSummarySchema, ModerationReviewRequest
from app.modules.listings.service import list_moderation_queue, review_listing

router = APIRouter(prefix="/admin/listings", tags=["admin-listings"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get(
    "/moderation",
    response_model=list[ListingSummarySchema],
    summary="List listings currently awaiting moderation",
)
def moderation_queue(
    locale: Literal["en", "ru"] = Query(default="en"),
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    __: User = Depends(require_roles(RoleCode.ADMIN)),
) -> list[ListingSummarySchema]:
    return list_moderation_queue(db, locale=locale)


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
