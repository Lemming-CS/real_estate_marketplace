from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status
from app.db.enums import UserStatus
from app.db.models import User
from app.modules.notifications.schemas import (
    NotificationSchema,
    NotificationUnreadCountSchema,
    PaginatedNotificationsResponseSchema,
)
from app.modules.notifications.service import list_notifications, mark_notification_read, unread_notification_count

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get(
    "",
    response_model=PaginatedNotificationsResponseSchema,
    summary="List notifications for the authenticated user",
)
def notifications_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> PaginatedNotificationsResponseSchema:
    return list_notifications(db, user=current_user, page=page, page_size=page_size)


@router.post(
    "/{notification_id}/read",
    response_model=NotificationSchema,
    summary="Mark a notification as read",
)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> NotificationSchema:
    notification = mark_notification_read(db, user=current_user, notification_id=notification_id)
    db.commit()
    return notification


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCountSchema,
    summary="Return the unread notification badge count",
)
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> NotificationUnreadCountSchema:
    return unread_notification_count(db, user=current_user)
