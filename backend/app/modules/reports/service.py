from __future__ import annotations

from math import ceil

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.auth import utcnow
from app.core.exceptions import AppError
from app.db.enums import ListingStatus, ReportStatus, UserStatus
from app.db.models import Conversation, Listing, Report, User, UserStatusHistory
from app.modules.reports.schemas import PaginatedReportsResponseSchema, ReportActionRequest, ReportCreateRequest, ReportSchema
from app.shared.audit import record_admin_audit_log
from app.shared.schemas import PaginationMetaSchema


def create_report(session: Session, *, reporter: User, payload: ReportCreateRequest) -> ReportSchema:
    normalized_reason_code = payload.reason_code.strip().lower()
    listing = None
    reported_user = None
    conversation = None

    if payload.listing_public_id:
        listing = session.execute(
            select(Listing)
            .options(joinedload(Listing.seller))
            .where(Listing.public_id == payload.listing_public_id, Listing.deleted_at.is_(None))
        ).scalar_one_or_none()
        if listing is None:
            raise AppError(status_code=404, code="listing_not_found", message="Listing was not found.")
        reported_user = listing.seller

    if payload.conversation_public_id:
        conversation = session.execute(
            select(Conversation)
            .options(
                joinedload(Conversation.listing).joinedload(Listing.seller),
                joinedload(Conversation.buyer),
                joinedload(Conversation.seller),
            )
            .where(Conversation.public_id == payload.conversation_public_id, Conversation.deleted_at.is_(None))
        ).scalar_one_or_none()
        if conversation is None:
            raise AppError(status_code=404, code="conversation_not_found", message="Conversation was not found.")
        if reporter.id not in {conversation.buyer_user_id, conversation.seller_user_id}:
            raise AppError(
                status_code=403,
                code="conversation_report_forbidden",
                message="You can only report conversations you participate in.",
            )
        listing = conversation.listing or listing
        reported_user = (
            conversation.seller
            if reporter.id == conversation.buyer_user_id
            else conversation.buyer
        )

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
    if conversation is not None:
        if payload.listing_public_id and conversation.listing_id != listing.id:
            raise AppError(
                status_code=400,
                code="report_target_mismatch",
                message="The conversation does not match the selected listing.",
            )
        if payload.reported_user_public_id and conversation.buyer_user_id != reported_user.id and conversation.seller_user_id != reported_user.id:
            raise AppError(
                status_code=400,
                code="report_target_mismatch",
                message="The conversation does not include the reported user.",
            )

    existing = session.execute(
        select(Report)
        .where(
            Report.reporter_user_id == reporter.id,
            Report.reported_user_id == (reported_user.id if reported_user else None),
            Report.listing_id == (listing.id if listing else None),
            Report.conversation_id == (conversation.id if conversation else None),
            Report.reason_code == normalized_reason_code,
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
        conversation_id=conversation.id if conversation else None,
        reason_code=normalized_reason_code,
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
    listing_public_id: str | None = None,
    reported_user_public_id: str | None = None,
) -> PaginatedReportsResponseSchema:
    base_query = _report_query()
    if status is not None:
        base_query = base_query.where(Report.status == status)
    if listing_public_id is not None:
        listing = session.execute(select(Listing).where(Listing.public_id == listing_public_id)).scalar_one_or_none()
        if listing is None:
            raise AppError(status_code=404, code="listing_not_found", message="Listing was not found.")
        base_query = base_query.where(Report.listing_id == listing.id)
    if reported_user_public_id is not None:
        reported_user = session.execute(select(User).where(User.public_id == reported_user_public_id)).scalar_one_or_none()
        if reported_user is None:
            raise AppError(status_code=404, code="user_not_found", message="User was not found.")
        base_query = base_query.where(Report.reported_user_id == reported_user.id)
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
    resolution_note = payload.resolution_note.strip() if payload.resolution_note else None

    if payload.action == "in_review":
        report.status = ReportStatus.IN_REVIEW
        report.resolution_note = resolution_note
        report.resolved_by_user_id = None
        report.resolved_at = None
        action_name = "report.mark_in_review"
    else:
        report.status = ReportStatus.RESOLVED if payload.action == "resolve" else ReportStatus.REJECTED
        report.resolution_note = resolution_note
        report.resolved_by_user_id = actor.id
        report.resolved_at = utcnow()
        action_name = "report.resolve" if payload.action == "resolve" else "report.dismiss"

    if payload.listing_action is not None:
        if report.listing is None:
            raise AppError(status_code=400, code="report_has_no_listing_target", message="This report is not linked to a listing.")
        _apply_listing_action_from_report(
            session,
            report=report,
            actor=actor,
            listing_action=payload.listing_action,
            note=resolution_note,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    if payload.user_action is not None:
        if report.reported_user is None:
            raise AppError(status_code=400, code="report_has_no_user_target", message="This report is not linked to a reported user.")
        _apply_user_action_from_report(
            session,
            report=report,
            actor=actor,
            user_action=payload.user_action,
            note=resolution_note,
            ip_address=ip_address,
            user_agent=user_agent,
        )

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
        joinedload(Report.conversation),
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
        conversation_public_id=report.conversation.public_id if report.conversation else None,
        listing_public_id=listing.public_id if listing else None,
        listing_title=listing.title if listing else None,
        listing_status=listing.status if listing else None,
        listing_moderation_note=listing.moderation_note if listing else None,
        reason_code=report.reason_code,
        description=report.description,
        reported_user_status=reported_user.status if reported_user else None,
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
        "conversation_public_id": report.conversation.public_id if report.conversation else None,
        "listing_public_id": report.listing.public_id if report.listing else None,
        "reported_user_public_id": report.reported_user.public_id if report.reported_user else None,
    }


def _apply_listing_action_from_report(
    session: Session,
    *,
    report: Report,
    actor: User,
    listing_action: str,
    note: str | None,
    ip_address: str | None,
    user_agent: str | None,
) -> None:
    listing = report.listing
    before_json = {
        "status": listing.status.value,
        "moderation_note": listing.moderation_note,
    }
    if listing_action == "hide":
        listing.status = ListingStatus.INACTIVE
        action_name = "listing.hide_from_report"
        action_label = "hid"
    else:
        listing.status = ListingStatus.ARCHIVED
        action_name = "listing.archive_from_report"
        action_label = "archived"
    listing.moderation_note = note
    record_admin_audit_log(
        session,
        actor=actor,
        action=action_name,
        entity_type="listing",
        entity_id=listing.public_id,
        description=f"{actor.full_name} {action_label} listing from report {report.public_id}.",
        ip_address=ip_address,
        user_agent=user_agent,
        before_json=before_json,
        after_json={"status": listing.status.value, "moderation_note": note, "report_public_id": report.public_id},
    )


def _apply_user_action_from_report(
    session: Session,
    *,
    report: Report,
    actor: User,
    user_action: str,
    note: str | None,
    ip_address: str | None,
    user_agent: str | None,
) -> None:
    reported_user = report.reported_user
    previous_status = reported_user.status
    if user_action == "suspend":
        if reported_user.id == actor.id:
            raise AppError(
                status_code=400,
                code="cannot_suspend_self",
                message="Admins cannot suspend their own account.",
            )
        reported_user.status = UserStatus.SUSPENDED
        session.add(
            UserStatusHistory(
                user_id=reported_user.id,
                previous_status=previous_status,
                new_status=UserStatus.SUSPENDED,
                changed_by_user_id=actor.id,
                reason=note,
            )
        )
        record_admin_audit_log(
            session,
            actor=actor,
            action="user.suspend_from_report",
            entity_type="user",
            entity_id=reported_user.public_id,
            description=f"Suspended user from report {report.public_id}.",
            ip_address=ip_address,
            user_agent=user_agent,
            before_json={"status": previous_status.value},
            after_json={"status": reported_user.status.value, "reason": note, "report_public_id": report.public_id},
        )
