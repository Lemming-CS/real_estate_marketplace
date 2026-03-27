from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status
from app.db.enums import UserStatus
from app.db.models import User
from app.modules.reports.schemas import PaginatedReportsResponseSchema, ReportCreateRequest, ReportSchema
from app.modules.reports.service import create_report, list_my_reports

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post(
    "",
    response_model=ReportSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a listing or user report",
)
def submit_report(
    payload: ReportCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> ReportSchema:
    report = create_report(db, reporter=current_user, payload=payload)
    db.commit()
    return report


@router.get(
    "/me",
    response_model=PaginatedReportsResponseSchema,
    summary="List reports submitted by the authenticated user",
)
def my_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> PaginatedReportsResponseSchema:
    return list_my_reports(db, user=current_user, page=page, page_size=page_size)
