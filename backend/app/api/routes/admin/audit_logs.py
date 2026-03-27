from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status, require_roles
from app.db.enums import RoleCode, UserStatus
from app.db.models import User
from app.modules.admin_console.schemas import PaginatedAdminAuditLogsResponseSchema
from app.modules.admin_console.service import list_admin_audit_logs

router = APIRouter(prefix="/admin/audit-logs", tags=["admin-audit-logs"])


@router.get("", response_model=PaginatedAdminAuditLogsResponseSchema, summary="Browse admin audit log records")
def audit_logs(
    q: str | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    __: User = Depends(require_roles(RoleCode.ADMIN)),
) -> PaginatedAdminAuditLogsResponseSchema:
    return list_admin_audit_logs(db, q=q, action=action, entity_type=entity_type, page=page, page_size=page_size)
