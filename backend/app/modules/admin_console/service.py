from __future__ import annotations

from math import ceil

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.auth import utcnow
from app.core.exceptions import AppError
from app.db.enums import ListingStatus, PaymentStatus, PaymentType, PromotionStatus, ReportStatus, RoleCode, UserStatus
from app.db.models import (
    AdminAuditLog,
    Category,
    Conversation,
    Listing,
    Message,
    PaymentRecord,
    Promotion,
    Report,
    Role,
    User,
    UserRole,
    UserStatusHistory,
)
from app.modules.admin_console.schemas import (
    AdminAuditLogSchema,
    AdminConversationReviewDetailSchema,
    AdminConversationReviewSummarySchema,
    AdminDashboardSchema,
    AdminMessageAttachmentReviewSchema,
    AdminMessageReviewSchema,
    AdminPromotionSchema,
    AdminUserDetailSchema,
    AdminUserListingSchema,
    AdminUserPaymentSchema,
    AdminUserPromotionSchema,
    AdminUserReportSchema,
    AdminUserStatusHistorySchema,
    AdminUserStatusUpdateRequest,
    AdminUserSummarySchema,
    PaginatedAdminAuditLogsResponseSchema,
    PaginatedAdminConversationsResponseSchema,
    PaginatedAdminPromotionsResponseSchema,
    PaginatedAdminUsersResponseSchema,
)
from app.shared.audit import record_admin_audit_log
from app.shared.schemas import PaginationMetaSchema


def get_dashboard_metrics(session: Session) -> AdminDashboardSchema:
    now = utcnow()
    total_revenue = session.execute(
        select(func.coalesce(func.sum(PaymentRecord.amount), 0)).where(
            PaymentRecord.payment_type == PaymentType.PROMOTION_PURCHASE,
            PaymentRecord.status == PaymentStatus.SUCCESSFUL,
        )
    ).scalar_one()
    active_promotions = session.execute(
        select(func.count(Promotion.id)).where(
            Promotion.status == PromotionStatus.ACTIVE,
            or_(Promotion.ends_at.is_(None), Promotion.ends_at >= now),
        )
    ).scalar_one()
    return AdminDashboardSchema(
        total_users=_count(session, select(User.id).where(User.deleted_at.is_(None))),
        active_users=_count(session, select(User.id).where(User.deleted_at.is_(None), User.status == UserStatus.ACTIVE)),
        blocked_users=_count(session, select(User.id).where(User.deleted_at.is_(None), User.status == UserStatus.SUSPENDED)),
        total_listings=_count(session, select(Listing.id).where(Listing.deleted_at.is_(None))),
        pending_listings=_count(session, select(Listing.id).where(Listing.deleted_at.is_(None), Listing.status == ListingStatus.PENDING_REVIEW)),
        approved_listings=_count(session, select(Listing.id).where(Listing.deleted_at.is_(None), Listing.status == ListingStatus.PUBLISHED)),
        rejected_listings=_count(session, select(Listing.id).where(Listing.deleted_at.is_(None), Listing.status == ListingStatus.REJECTED)),
        total_conversations=_count(session, select(Conversation.id).where(Conversation.deleted_at.is_(None))),
        total_messages=_count(session, select(Message.id).where(Message.deleted_at.is_(None))),
        total_reports=_count(session, select(Report.id)),
        total_payments=_count(session, select(PaymentRecord.id)),
        total_revenue_from_promotions=total_revenue,
        active_promotions=active_promotions,
    )


def list_admin_users(
    session: Session,
    *,
    q: str | None,
    status: UserStatus | None,
    page: int,
    page_size: int,
) -> PaginatedAdminUsersResponseSchema:
    base_query = select(User).where(User.deleted_at.is_(None))
    if q:
        term = f"%{q.strip()}%"
        base_query = base_query.where(or_(User.email.ilike(term), User.username.ilike(term), User.full_name.ilike(term)))
    if status is not None:
        base_query = base_query.where(User.status == status)
    total_items = _count(session, select(User.id).select_from(base_query.subquery()))
    users = session.execute(
        base_query.order_by(User.created_at.desc(), User.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    role_map = _role_map(session, user_ids=[user.id for user in users])
    return PaginatedAdminUsersResponseSchema(
        items=[_build_admin_user_summary(user, role_map.get(user.id, [])) for user in users],
        meta=_pagination_meta(page=page, page_size=page_size, total_items=total_items),
    )


def get_admin_user_detail(session: Session, *, user_public_id: str) -> AdminUserDetailSchema:
    user = _get_user_or_404(session, user_public_id=user_public_id)
    role_codes = _role_map(session, user_ids=[user.id]).get(user.id, [])

    listings = session.execute(
        select(Listing).where(Listing.seller_id == user.id, Listing.deleted_at.is_(None)).order_by(Listing.created_at.desc()).limit(10)
    ).scalars().all()
    promotions = session.execute(
        select(Promotion)
        .options(joinedload(Promotion.listing), joinedload(Promotion.package))
        .join(Promotion.listing)
        .where(Listing.seller_id == user.id)
        .order_by(Promotion.created_at.desc())
        .limit(10)
    ).scalars().all()
    payments = session.execute(
        select(PaymentRecord).where(PaymentRecord.payer_user_id == user.id).order_by(PaymentRecord.created_at.desc()).limit(10)
    ).scalars().all()
    reports = session.execute(
        select(Report)
        .options(joinedload(Report.listing))
        .where(or_(Report.reported_user_id == user.id, Report.reporter_user_id == user.id))
        .order_by(Report.created_at.desc())
        .limit(10)
    ).scalars().all()
    status_history = session.execute(
        select(UserStatusHistory)
        .options(joinedload(UserStatusHistory.changed_by))
        .where(UserStatusHistory.user_id == user.id)
        .order_by(UserStatusHistory.created_at.desc(), UserStatusHistory.id.desc())
        .limit(10)
    ).scalars().all()

    listing_count = _count(session, select(Listing.id).where(Listing.seller_id == user.id, Listing.deleted_at.is_(None)))
    active_listing_count = _count(
        session,
        select(Listing.id).where(Listing.seller_id == user.id, Listing.deleted_at.is_(None), Listing.status == ListingStatus.PUBLISHED),
    )

    return AdminUserDetailSchema(
        **_build_admin_user_summary(user, role_codes).model_dump(),
        phone=user.phone,
        bio=user.bio,
        locale=user.locale,
        is_email_verified=user.is_email_verified,
        listing_count=listing_count,
        active_listing_count=active_listing_count,
        latest_status_note=next((entry.reason for entry in status_history if entry.reason), None),
        latest_status_note_created_at=next((entry.created_at for entry in status_history if entry.reason), None),
        status_history=[
            AdminUserStatusHistorySchema(
                previous_status=entry.previous_status,
                new_status=entry.new_status,
                reason=entry.reason,
                changed_by_user_public_id=entry.changed_by.public_id if entry.changed_by else None,
                changed_by_email=entry.changed_by.email if entry.changed_by else None,
                created_at=entry.created_at,
            )
            for entry in status_history
        ],
        listings=[
            AdminUserListingSchema(
                public_id=listing.public_id,
                title=listing.title,
                status=listing.status,
                price_amount=listing.price_amount,
                currency_code=listing.currency_code,
                created_at=listing.created_at,
            )
            for listing in listings
        ],
        promotions=[
            AdminUserPromotionSchema(
                public_id=promotion.public_id,
                status=_effective_promotion_status(promotion),
                listing_public_id=promotion.listing.public_id,
                listing_title=promotion.listing.title,
                package_name=promotion.package.name,
                price_amount=promotion.price_amount,
                currency_code=promotion.currency_code,
                ends_at=promotion.ends_at,
                created_at=promotion.created_at,
            )
            for promotion in promotions
        ],
        payments=[
            AdminUserPaymentSchema(
                public_id=payment.public_id,
                status=payment.status,
                amount=payment.amount,
                currency_code=payment.currency_code,
                payment_type=payment.payment_type.value,
                created_at=payment.created_at,
            )
            for payment in payments
        ],
        reports=[
            AdminUserReportSchema(
                public_id=report.public_id,
                reason_code=report.reason_code,
                status=report.status,
                listing_public_id=report.listing.public_id if report.listing else None,
                listing_title=report.listing.title if report.listing else None,
                created_at=report.created_at,
            )
            for report in reports
        ],
    )


def update_admin_user_status(
    session: Session,
    *,
    user_public_id: str,
    payload: AdminUserStatusUpdateRequest,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AdminUserDetailSchema:
    user = _get_user_or_404(session, user_public_id=user_public_id)
    previous_status = user.status
    next_status = UserStatus.SUSPENDED if payload.action == "suspend" else UserStatus.ACTIVE
    user.status = next_status
    session.add(
        UserStatusHistory(
            user_id=user.id,
            previous_status=previous_status,
            new_status=next_status,
            changed_by_user_id=actor.id,
            reason=payload.reason,
        )
    )
    session.flush()
    record_admin_audit_log(
        session,
        actor=actor,
        action=f"user.{payload.action}",
        entity_type="user",
        entity_id=user.public_id,
        description=f"{payload.action.title()}ed user {user.email}.",
        ip_address=ip_address,
        user_agent=user_agent,
        before_json={"status": previous_status.value},
        after_json={"status": next_status.value, "reason": payload.reason},
    )
    return get_admin_user_detail(session, user_public_id=user.public_id)


def list_admin_audit_logs(
    session: Session,
    *,
    q: str | None,
    action: str | None,
    entity_type: str | None,
    page: int,
    page_size: int,
) -> PaginatedAdminAuditLogsResponseSchema:
    base_query = select(AdminAuditLog).options(joinedload(AdminAuditLog.actor)).order_by(
        AdminAuditLog.created_at.desc(),
        AdminAuditLog.id.desc(),
    )
    if q:
        term = f"%{q.strip()}%"
        base_query = base_query.where(
            or_(
                AdminAuditLog.action.ilike(term),
                AdminAuditLog.entity_type.ilike(term),
                AdminAuditLog.entity_id.ilike(term),
                AdminAuditLog.description.ilike(term),
            )
        )
    if action:
        base_query = base_query.where(AdminAuditLog.action == action)
    if entity_type:
        base_query = base_query.where(AdminAuditLog.entity_type == entity_type)
    total_items = _count(session, select(AdminAuditLog.id).select_from(base_query.subquery()))
    logs = session.execute(
        base_query.offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    return PaginatedAdminAuditLogsResponseSchema(
        items=[
            AdminAuditLogSchema(
                id=log.id,
                actor_user_public_id=log.actor.public_id if log.actor else None,
                actor_email=log.actor.email if log.actor else None,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                description=log.description,
                before_json=log.before_json,
                after_json=log.after_json,
                created_at=log.created_at,
            )
            for log in logs
        ],
        meta=_pagination_meta(page=page, page_size=page_size, total_items=total_items),
    )


def list_admin_promotions(
    session: Session,
    *,
    status: PromotionStatus | None,
    page: int,
    page_size: int,
) -> PaginatedAdminPromotionsResponseSchema:
    now = utcnow()
    base_query = (
        select(Promotion)
        .options(
            joinedload(Promotion.listing).joinedload(Listing.seller),
            joinedload(Promotion.package),
            joinedload(Promotion.target_category).selectinload(Category.translations),
        )
    )
    if status is not None:
        if status == PromotionStatus.EXPIRED:
            base_query = base_query.where(
                or_(
                    Promotion.status == PromotionStatus.EXPIRED,
                    (
                        (Promotion.status == PromotionStatus.ACTIVE)
                        & Promotion.ends_at.is_not(None)
                        & (Promotion.ends_at < now)
                    ),
                )
            )
        elif status == PromotionStatus.ACTIVE:
            base_query = base_query.where(
                Promotion.status == PromotionStatus.ACTIVE,
                or_(Promotion.ends_at.is_(None), Promotion.ends_at >= now),
            )
        else:
            base_query = base_query.where(Promotion.status == status)
    total_items = _count(session, select(Promotion.id).select_from(base_query.subquery()))
    promotions = session.execute(
        base_query.order_by(Promotion.created_at.desc(), Promotion.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).unique().scalars().all()
    return PaginatedAdminPromotionsResponseSchema(
        items=[
            AdminPromotionSchema(
                public_id=promotion.public_id,
                listing_public_id=promotion.listing.public_id,
                listing_title=promotion.listing.title,
                seller_public_id=promotion.listing.seller.public_id,
                seller_username=promotion.listing.seller.username,
                package_name=promotion.package.name,
                status=_effective_promotion_status(promotion),
                target_city=promotion.target_city,
                target_category_name=_category_name(promotion.target_category),
                price_amount=promotion.price_amount,
                currency_code=promotion.currency_code,
                starts_at=promotion.starts_at,
                ends_at=promotion.ends_at,
                created_at=promotion.created_at,
            )
            for promotion in promotions
        ],
        meta=_pagination_meta(page=page, page_size=page_size, total_items=total_items),
    )


def list_scoped_conversations(
    session: Session,
    *,
    listing_public_id: str | None,
    user_public_id: str | None,
    page: int,
    page_size: int,
) -> PaginatedAdminConversationsResponseSchema:
    scope = _conversation_scope_filters(session, listing_public_id=listing_public_id, user_public_id=user_public_id)
    base_query = (
        select(Conversation)
        .options(joinedload(Conversation.listing), joinedload(Conversation.buyer), joinedload(Conversation.seller))
        .where(*scope, Conversation.deleted_at.is_(None))
        .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.created_at.desc(), Conversation.id.desc())
    )
    total_items = _count(session, select(Conversation.id).select_from(base_query.subquery()))
    conversations = session.execute(
        base_query.offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    message_counts = _message_count_map(session, conversation_ids=[conversation.id for conversation in conversations])
    return PaginatedAdminConversationsResponseSchema(
        items=[
            AdminConversationReviewSummarySchema(
                public_id=conversation.public_id,
                listing_public_id=conversation.listing.public_id if conversation.listing else None,
                listing_title=conversation.listing.title if conversation.listing else None,
                buyer_public_id=conversation.buyer.public_id,
                buyer_username=conversation.buyer.username,
                seller_public_id=conversation.seller.public_id,
                seller_username=conversation.seller.username,
                message_count=message_counts.get(conversation.id, 0),
                last_message_at=conversation.last_message_at,
            )
            for conversation in conversations
        ],
        meta=_pagination_meta(page=page, page_size=page_size, total_items=total_items),
    )


def get_scoped_conversation_detail(
    session: Session,
    *,
    conversation_public_id: str,
    listing_public_id: str | None,
    user_public_id: str | None,
) -> AdminConversationReviewDetailSchema:
    scope = _conversation_scope_filters(session, listing_public_id=listing_public_id, user_public_id=user_public_id)
    conversation = session.execute(
        select(Conversation)
        .options(
            joinedload(Conversation.listing),
            joinedload(Conversation.buyer),
            joinedload(Conversation.seller),
            selectinload(Conversation.messages).joinedload(Message.sender),
            selectinload(Conversation.messages).selectinload(Message.attachments),
        )
        .where(Conversation.public_id == conversation_public_id, Conversation.deleted_at.is_(None), *scope)
    ).scalar_one_or_none()
    if conversation is None:
        raise AppError(
            status_code=404,
            code="conversation_review_not_found",
            message="Conversation was not found for the provided review scope.",
        )

    message_count = _message_count_map(session, conversation_ids=[conversation.id]).get(conversation.id, 0)
    return AdminConversationReviewDetailSchema(
        public_id=conversation.public_id,
        listing_public_id=conversation.listing.public_id if conversation.listing else None,
        listing_title=conversation.listing.title if conversation.listing else None,
        buyer_public_id=conversation.buyer.public_id,
        buyer_username=conversation.buyer.username,
        seller_public_id=conversation.seller.public_id,
        seller_username=conversation.seller.username,
        message_count=message_count,
        last_message_at=conversation.last_message_at,
        messages=[
            AdminMessageReviewSchema(
                public_id=message.public_id,
                sender_public_id=message.sender.public_id,
                sender_username=message.sender.username,
                body=message.body,
                created_at=message.created_at,
                attachments=[
                    AdminMessageAttachmentReviewSchema(
                        public_id=attachment.public_id,
                        file_name=attachment.file_name,
                        mime_type=attachment.mime_type,
                    )
                    for attachment in message.attachments
                ],
            )
            for message in sorted(conversation.messages, key=lambda item: (item.created_at, item.id))
            if message.deleted_at is None
        ],
    )


def _count(session: Session, query) -> int:
    return session.execute(select(func.count()).select_from(query.subquery())).scalar_one()


def _role_map(session: Session, *, user_ids: list[int]) -> dict[int, list[str]]:
    if not user_ids:
        return {}
    rows = session.execute(
        select(UserRole.user_id, Role.code).join(Role, Role.id == UserRole.role_id).where(UserRole.user_id.in_(user_ids))
    ).all()
    result: dict[int, list[str]] = {user_id: [] for user_id in user_ids}
    for user_id, role_code in rows:
        result.setdefault(user_id, []).append(role_code.value)
    return result


def _build_admin_user_summary(user: User, role_codes: list[str]) -> AdminUserSummarySchema:
    return AdminUserSummarySchema(
        public_id=user.public_id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        status=user.status,
        roles=sorted(role_codes),
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


def _get_user_or_404(session: Session, *, user_public_id: str) -> User:
    user = session.execute(
        select(User).where(User.public_id == user_public_id, User.deleted_at.is_(None))
    ).scalar_one_or_none()
    if user is None:
        raise AppError(status_code=404, code="user_not_found", message="User was not found.")
    return user


def _message_count_map(session: Session, *, conversation_ids: list[int]) -> dict[int, int]:
    if not conversation_ids:
        return {}
    rows = session.execute(
        select(Message.conversation_id, func.count(Message.id))
        .where(Message.conversation_id.in_(conversation_ids), Message.deleted_at.is_(None))
        .group_by(Message.conversation_id)
    ).all()
    return {conversation_id: count for conversation_id, count in rows}


def _conversation_scope_filters(
    session: Session,
    *,
    listing_public_id: str | None,
    user_public_id: str | None,
) -> list:
    if not listing_public_id and not user_public_id:
        raise AppError(
            status_code=400,
            code="conversation_review_scope_required",
            message="Admin conversation review requires a listing or user scope.",
        )
    filters = []
    if listing_public_id:
        listing = session.execute(select(Listing).where(Listing.public_id == listing_public_id)).scalar_one_or_none()
        if listing is None:
            raise AppError(status_code=404, code="listing_not_found", message="Listing was not found.")
        filters.append(Conversation.listing_id == listing.id)
    if user_public_id:
        user = _get_user_or_404(session, user_public_id=user_public_id)
        filters.append(or_(Conversation.buyer_user_id == user.id, Conversation.seller_user_id == user.id))
    return filters


def _pagination_meta(*, page: int, page_size: int, total_items: int) -> PaginationMetaSchema:
    total_pages = ceil(total_items / page_size) if total_items else 0
    return PaginationMetaSchema(page=page, page_size=page_size, total_items=total_items, total_pages=total_pages)


def _effective_promotion_status(promotion: Promotion) -> PromotionStatus:
    if promotion.status == PromotionStatus.ACTIVE and promotion.ends_at is not None and promotion.ends_at < utcnow():
        return PromotionStatus.EXPIRED
    return promotion.status


def _category_name(category: Category | None) -> str | None:
    if category is None:
        return None
    translations = {translation.locale: translation for translation in category.translations}
    translation = translations.get("en") or next(iter(category.translations), None)
    return translation.name if translation else category.internal_name
