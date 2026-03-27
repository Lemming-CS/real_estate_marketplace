from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status
from app.db.enums import UserStatus
from app.db.models import User
from app.modules.commerce.schemas import PaginatedPromotionsResponseSchema
from app.modules.commerce.service import list_my_promotions

router = APIRouter(prefix="/promotions", tags=["promotions"])


@router.get(
    "/me",
    response_model=PaginatedPromotionsResponseSchema,
    summary="List promotion attempts and active boosts for the authenticated seller",
)
def my_promotions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> PaginatedPromotionsResponseSchema:
    response = list_my_promotions(db, user=current_user, page=page, page_size=page_size)
    db.commit()
    return response
