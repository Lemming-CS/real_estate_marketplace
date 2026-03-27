from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status, require_roles
from app.db.enums import RoleCode, UserStatus
from app.db.models import User
from app.modules.admin_console.schemas import AdminDashboardSchema
from app.modules.admin_console.service import get_dashboard_metrics

router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])


@router.get("", response_model=AdminDashboardSchema, summary="Return admin dashboard metrics")
def dashboard_metrics(
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    __: User = Depends(require_roles(RoleCode.ADMIN)),
) -> AdminDashboardSchema:
    return get_dashboard_metrics(db)
