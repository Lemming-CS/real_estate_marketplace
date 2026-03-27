from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status
from app.db.enums import UserStatus
from app.db.models import User
from app.modules.listings.schemas import FavoriteStatusSchema, PaginatedFavoritesResponseSchema
from app.modules.listings.service import add_favorite, list_favorites, remove_favorite

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get(
    "",
    response_model=PaginatedFavoritesResponseSchema,
    summary="List the authenticated user's favorites with pagination metadata",
)
def favorites_list(
    locale: Literal["en", "ru"] | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> PaginatedFavoritesResponseSchema:
    return list_favorites(
        db,
        user=current_user,
        locale=locale or current_user.locale,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/{listing_public_id}",
    response_model=FavoriteStatusSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add a visible listing to favorites",
)
def favorite_listing(
    listing_public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> FavoriteStatusSchema:
    response = add_favorite(db, user=current_user, listing_public_id=listing_public_id)
    db.commit()
    return response


@router.delete(
    "/{listing_public_id}",
    response_model=FavoriteStatusSchema,
    summary="Remove a listing from favorites",
)
def unfavorite_listing(
    listing_public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> FavoriteStatusSchema:
    response = remove_favorite(db, user=current_user, listing_public_id=listing_public_id)
    db.commit()
    return response
