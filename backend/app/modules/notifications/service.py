from __future__ import annotations

from math import ceil

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import utcnow
from app.core.exceptions import AppError
from app.db.enums import NotificationStatus
from app.db.models import Notification, User
from app.modules.notifications.schemas import (
    NotificationSchema,
    NotificationUnreadCountSchema,
    PaginatedNotificationsResponseSchema,
)
from app.shared.schemas import PaginationMetaSchema


def create_notification(
    session: Session,
    *,
    user_id: int,
    notification_type: str,
    title: str,
    body: str,
    data_json: dict | list | None = None,
) -> None:
    session.add(
        Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            data_json=data_json,
            status=NotificationStatus.UNREAD,
        )
    )


def notify_listing_reviewed(
    session: Session,
    *,
    user: User,
    listing_public_id: str,
    listing_title: str,
    approved: bool,
    moderation_note: str | None,
) -> None:
    create_notification(
        session,
        user_id=user.id,
        notification_type="listing.approved" if approved else "listing.rejected",
        title="Listing approved" if approved else "Listing rejected",
        body=(
            f"Your listing '{listing_title}' is now live."
            if approved
            else f"Your listing '{listing_title}' was rejected."
        ),
        data_json={
            "listing_public_id": listing_public_id,
            "moderation_note": moderation_note,
        },
    )


def notify_new_message(
    session: Session,
    *,
    recipient: User,
    conversation_public_id: str,
    listing_public_id: str | None,
    sender_public_id: str,
    sender_name: str,
    message_preview: str | None,
) -> None:
    create_notification(
        session,
        user_id=recipient.id,
        notification_type="message.new",
        title="New message",
        body=f"{sender_name} sent you a message.",
        data_json={
            "conversation_public_id": conversation_public_id,
            "listing_public_id": listing_public_id,
            "sender_public_id": sender_public_id,
            "message_preview": message_preview,
        },
    )


def notify_payment_successful(
    session: Session,
    *,
    user: User,
    payment_public_id: str,
    amount: str,
    currency_code: str,
) -> None:
    create_notification(
        session,
        user_id=user.id,
        notification_type="payment.successful",
        title="Payment successful",
        body=f"Your payment of {amount} {currency_code} was successful.",
        data_json={"payment_public_id": payment_public_id},
    )


def notify_promotion_activated(
    session: Session,
    *,
    user: User,
    promotion_public_id: str,
    listing_public_id: str,
) -> None:
    create_notification(
        session,
        user_id=user.id,
        notification_type="promotion.activated",
        title="Promotion activated",
        body="Your promotion is now active.",
        data_json={
            "promotion_public_id": promotion_public_id,
            "listing_public_id": listing_public_id,
        },
    )


def notify_promotion_expired(
    session: Session,
    *,
    user: User,
    promotion_public_id: str,
    listing_public_id: str,
) -> None:
    create_notification(
        session,
        user_id=user.id,
        notification_type="promotion.expired",
        title="Promotion expired",
        body="Your promotion has expired.",
        data_json={
            "promotion_public_id": promotion_public_id,
            "listing_public_id": listing_public_id,
        },
    )


def list_notifications(
    session: Session,
    *,
    user: User,
    page: int,
    page_size: int,
) -> PaginatedNotificationsResponseSchema:
    base_query = select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc(), Notification.id.desc())
    total_items = session.execute(select(func.count()).select_from(base_query.subquery())).scalar_one()
    notifications = session.execute(
        base_query.offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    return PaginatedNotificationsResponseSchema(
        items=[
            NotificationSchema(
                id=notification.id,
                notification_type=notification.notification_type,
                title=notification.title,
                body=notification.body,
                data_json=notification.data_json,
                status=notification.status,
                read_at=notification.read_at,
                created_at=notification.created_at,
            )
            for notification in notifications
        ],
        meta=PaginationMetaSchema(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=ceil(total_items / page_size) if total_items else 0,
        ),
    )


def mark_notification_read(session: Session, *, user: User, notification_id: int) -> NotificationSchema:
    notification = session.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id)
    ).scalar_one_or_none()
    if notification is None:
        raise AppError(status_code=404, code="notification_not_found", message="Notification was not found.")
    if notification.status != NotificationStatus.READ:
        notification.status = NotificationStatus.READ
        notification.read_at = utcnow()
        session.flush()
    return NotificationSchema(
        id=notification.id,
        notification_type=notification.notification_type,
        title=notification.title,
        body=notification.body,
        data_json=notification.data_json,
        status=notification.status,
        read_at=notification.read_at,
        created_at=notification.created_at,
    )


def unread_notification_count(session: Session, *, user: User) -> NotificationUnreadCountSchema:
    unread_count = session.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user.id,
            Notification.status == NotificationStatus.UNREAD,
        )
    ).scalar_one()
    return NotificationUnreadCountSchema(unread_count=unread_count)
