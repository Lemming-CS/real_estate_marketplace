from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status, require_roles
from app.db.enums import ReportStatus, RoleCode, UserStatus
from app.db.models import User
from app.modules.reports.schemas import PaginatedReportsResponseSchema, ReportActionRequest, ReportSchema
from app.modules.reports.service import list_admin_reports, update_report_status

router = APIRouter(prefix="/admin/reports", tags=["admin-reports"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get(
    "",
    response_model=PaginatedReportsResponseSchema,
    summary="List the admin reports queue",
)
def reports_queue(
    status: ReportStatus | None = Query(default=None),
    listing_public_id: str | None = Query(default=None),
    reported_user_public_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    __: User = Depends(require_roles(RoleCode.ADMIN)),
) -> PaginatedReportsResponseSchema:
    return list_admin_reports(
        db,
        status=status,
        listing_public_id=listing_public_id,
        reported_user_public_id=reported_user_public_id,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/{report_public_id}/resolve",
    response_model=ReportSchema,
    summary="Mark a report as in-review, resolved, or dismissed",
)
def resolve_report(
    report_public_id: str,
    payload: ReportActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    current_user: User = Depends(require_roles(RoleCode.ADMIN)),
) -> ReportSchema:
    response = update_report_status(
        db,
        report_public_id=report_public_id,
        payload=payload,
        actor=current_user,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return response
