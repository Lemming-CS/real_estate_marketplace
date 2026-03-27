from __future__ import annotations

from math import ceil

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.auth import utcnow
from app.core.exceptions import AppError
from app.db.enums import ReportStatus
from app.db.models import Listing, Report, User
from app.modules.reports.schemas import PaginatedReportsResponseSchema, ReportActionRequest, ReportCreateRequest, ReportSchema
from app.shared.audit import record_admin_audit_log
from app.shared.schemas import PaginationMetaSchema


def create_report(session: Session, *, reporter: User, payload: ReportCreateRequest) -> ReportSchema:
    listing = None
    reported_user = None

    if payload.listing_public_id:
        listing = session.execute(
            select(Listing)
            .options(joinedload(Listing.seller))
            .where(Listing.public_id == payload.listing_public_id, Listing.deleted_at.is_(None))
        ).scalar_one_or_none()
        if listing is None:
            raise AppError(status_code=404, code="listing_not_found", message="Listing was not found.")
        reported_user = listing.seller

    if payload.reported_user_public_id:
        reported_user = session.execute(
            select(User).where(User.public_id == payload.reported_user_public_id, User.deleted_at.is_(None))
        ).scalar_one_or_none()
        if reported_user is None:
            raise AppError(status_code=404, code="user_not_found", message="User was not found.")

    if reported_user is not None and reported_user.id == reporter.id:
        raise AppError(status_code=400, code="cannot_report_self", message="You cannot submit a report against yourself.")

    if listing is not None and reported_user is not None and listing.seller_id != reported_user.id:
        raise AppError(
            status_code=400,
            code="report_target_mismatch",
            message="The reported user does not match the listing owner.",
        )

    existing = session.execute(
        select(Report)
        .where(
            Report.reporter_user_id == reporter.id,
            Report.reported_user_id == (reported_user.id if reported_user else None),
            Report.listing_id == (listing.id if listing else None),
            Report.reason_code == payload.reason_code,
            Report.status.in_([ReportStatus.OPEN, ReportStatus.IN_REVIEW]),
        )
        .order_by(Report.created_at.desc(), Report.id.desc())
    ).scalar_one_or_none()
    if existing is not None:
        return _build_report_schema(existing)

    report = Report(
        reporter_user_id=reporter.id,
        reported_user_id=reported_user.id if reported_user else None,
        listing_id=listing.id if listing else None,
        reason_code=payload.reason_code.strip().lower(),
        description=payload.description.strip() if payload.description else None,
        status=ReportStatus.OPEN,
    )
    session.add(report)
    session.flush()
    return _build_report_schema(_get_report_or_404(session, report_public_id=report.public_id))


def list_my_reports(
    session: Session,
    *,
    user: User,
    page: int,
    page_size: int,
) -> PaginatedReportsResponseSchema:
    base_query = _report_query().where(Report.reporter_user_id == user.id).order_by(Report.created_at.desc(), Report.id.desc())
    return _paginate_reports(session, base_query=base_query, page=page, page_size=page_size)


def list_admin_reports(
    session: Session,
    *,
    page: int,
    page_size: int,
    status: ReportStatus | None = None,
) -> PaginatedReportsResponseSchema:
    base_query = _report_query()
    if status is not None:
        base_query = base_query.where(Report.status == status)
    base_query = base_query.order_by(Report.created_at.desc(), Report.id.desc())
    return _paginate_reports(session, base_query=base_query, page=page, page_size=page_size)


def update_report_status(
    session: Session,
    *,
    report_public_id: str,
    payload: ReportActionRequest,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ReportSchema:
    report = _get_report_or_404(session, report_public_id=report_public_id)
    before_json = _report_snapshot(report)

    if payload.action == "in_review":
        report.status = ReportStatus.IN_REVIEW
        report.resolution_note = payload.resolution_note
        report.resolved_by_user_id = None
        report.resolved_at = None
        action_name = "report.mark_in_review"
    else:
        report.status = ReportStatus.RESOLVED if payload.action == "resolve" else ReportStatus.REJECTED
        report.resolution_note = payload.resolution_note.strip() if payload.resolution_note else None
        report.resolved_by_user_id = actor.id
        report.resolved_at = utcnow()
        action_name = "report.resolve" if payload.action == "resolve" else "report.dismiss"

    session.flush()
    record_admin_audit_log(
        session,
        actor=actor,
        action=action_name,
        entity_type="report",
        entity_id=report.public_id,
        description=f"{payload.action.replace('_', ' ').title()} report {report.public_id}.",
        ip_address=ip_address,
        user_agent=user_agent,
        before_json=before_json,
        after_json=_report_snapshot(report),
    )
    return _build_report_schema(report)


def _report_query() -> Select[tuple[Report]]:
    return select(Report).options(
        joinedload(Report.reporter_user),
        joinedload(Report.reported_user),
        joinedload(Report.listing),
    )


def _get_report_or_404(session: Session, *, report_public_id: str) -> Report:
    report = session.execute(
        _report_query().where(Report.public_id == report_public_id)
    ).scalar_one_or_none()
    if report is None:
        raise AppError(status_code=404, code="report_not_found", message="Report was not found.")
    return report


def _paginate_reports(
    session: Session,
    *,
    base_query: Select[tuple[Report]],
    page: int,
    page_size: int,
) -> PaginatedReportsResponseSchema:
    total_items = session.execute(select(func.count()).select_from(base_query.subquery())).scalar_one()
    reports = session.execute(
        base_query.offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    total_pages = ceil(total_items / page_size) if total_items else 0
    return PaginatedReportsResponseSchema(
        items=[_build_report_schema(report) for report in reports],
        meta=PaginationMetaSchema(page=page, page_size=page_size, total_items=total_items, total_pages=total_pages),
    )


def _build_report_schema(report: Report) -> ReportSchema:
    reporter = report.reporter_user
    reported_user = report.reported_user
    listing = report.listing
    return ReportSchema(
        public_id=report.public_id,
        reporter_user_public_id=reporter.public_id,
        reporter_username=reporter.username,
        reported_user_public_id=reported_user.public_id if reported_user else None,
        reported_username=reported_user.username if reported_user else None,
        listing_public_id=listing.public_id if listing else None,
        listing_title=listing.title if listing else None,
        reason_code=report.reason_code,
        description=report.description,
        status=report.status,
        resolution_note=report.resolution_note,
        resolved_at=report.resolved_at,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


def _report_snapshot(report: Report) -> dict[str, str | None]:
    return {
        "public_id": report.public_id,
        "status": report.status.value,
        "reason_code": report.reason_code,
        "listing_public_id": report.listing.public_id if report.listing else None,
        "reported_user_public_id": report.reported_user.public_id if report.reported_user else None,
    }
