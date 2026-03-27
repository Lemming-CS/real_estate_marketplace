from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.db.enums import NotificationStatus
from app.shared.schemas import PaginationMetaSchema


class NotificationSchema(BaseModel):
    id: int
    notification_type: str
    title: str
    body: str
    data_json: dict | list | None = None
    status: NotificationStatus
    read_at: datetime | None = None
    created_at: datetime


class PaginatedNotificationsResponseSchema(BaseModel):
    items: list[NotificationSchema]
    meta: PaginationMetaSchema


class NotificationUnreadCountSchema(BaseModel):
    unread_count: int
