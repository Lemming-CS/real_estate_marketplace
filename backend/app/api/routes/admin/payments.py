from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status, require_roles
from app.core.config import Settings, get_settings
from app.db.enums import PaymentStatus, RoleCode, UserStatus
from app.db.models import User
from app.modules.commerce.schemas import PaginatedPaymentsResponseSchema
from app.modules.commerce.service import list_admin_payments

router = APIRouter(prefix="/admin/payments", tags=["admin-payments"])


@router.get(
    "",
    response_model=PaginatedPaymentsResponseSchema,
    summary="List payments for admin operational visibility",
)
def payments_queue(
    status: PaymentStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    __: User = Depends(require_roles(RoleCode.ADMIN)),
) -> PaginatedPaymentsResponseSchema:
    response = list_admin_payments(db, settings=settings, status=status, page=page, page_size=page_size)
    db.commit()
    return response
