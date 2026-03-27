from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status, require_roles
from app.db.enums import PromotionStatus, RoleCode, UserStatus
from app.db.models import User
from app.modules.admin_console.schemas import PaginatedAdminPromotionsResponseSchema
from app.modules.admin_console.service import list_admin_promotions

router = APIRouter(prefix="/admin/promotions", tags=["admin-promotions"])


@router.get("", response_model=PaginatedAdminPromotionsResponseSchema, summary="List promotions for admin visibility")
def promotions_admin(
    status: PromotionStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    __: User = Depends(require_roles(RoleCode.ADMIN)),
) -> PaginatedAdminPromotionsResponseSchema:
    return list_admin_promotions(db, status=status, page=page, page_size=page_size)
