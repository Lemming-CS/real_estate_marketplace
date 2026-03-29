from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.db.enums import ListingStatus, PaymentStatus, PromotionStatus, ReportStatus, UserStatus
from app.shared.schemas import PaginationMetaSchema


class AdminDashboardSchema(BaseModel):
    total_users: int
    active_users: int
    blocked_users: int
    total_listings: int
    pending_listings: int
    approved_listings: int
    rejected_listings: int
    total_conversations: int
    total_messages: int
    total_reports: int
    total_payments: int
    total_revenue_from_promotions: Decimal
    active_promotions: int


class AdminUserSummarySchema(BaseModel):
    public_id: str
    email: EmailStr
    username: str
    full_name: str
    status: UserStatus
    roles: list[str]
    created_at: datetime
    last_login_at: datetime | None = None


class AdminUserListingSchema(BaseModel):
    public_id: str
    title: str
    status: ListingStatus
    price_amount: Decimal
    currency_code: str
    created_at: datetime


class AdminUserPromotionSchema(BaseModel):
    public_id: str
    status: PromotionStatus
    listing_public_id: str
    listing_title: str
    package_name: str
    price_amount: Decimal
    currency_code: str
    ends_at: datetime | None = None
    created_at: datetime


class AdminUserPaymentSchema(BaseModel):
    public_id: str
    status: PaymentStatus
    amount: Decimal
    currency_code: str
    payment_type: str
    created_at: datetime


class AdminUserReportSchema(BaseModel):
    public_id: str
    reason_code: str
    status: ReportStatus
    listing_public_id: str | None = None
    listing_title: str | None = None
    created_at: datetime


class AdminUserStatusHistorySchema(BaseModel):
    previous_status: UserStatus | None = None
    new_status: UserStatus
    reason: str | None = None
    changed_by_user_public_id: str | None = None
    changed_by_email: str | None = None
    created_at: datetime


class AdminUserDetailSchema(AdminUserSummarySchema):
    phone: str | None = None
    bio: str | None = None
    locale: str
    is_email_verified: bool
    listing_count: int
    active_listing_count: int
    latest_status_note: str | None = None
    latest_status_note_created_at: datetime | None = None
    status_history: list[AdminUserStatusHistorySchema]
    listings: list[AdminUserListingSchema]
    promotions: list[AdminUserPromotionSchema]
    payments: list[AdminUserPaymentSchema]
    reports: list[AdminUserReportSchema]


class PaginatedAdminUsersResponseSchema(BaseModel):
    items: list[AdminUserSummarySchema]
    meta: PaginationMetaSchema


class AdminUserStatusUpdateRequest(BaseModel):
    action: Literal["suspend", "unsuspend"]
    reason: str | None = Field(default=None, max_length=500)


class AdminAuditLogSchema(BaseModel):
    id: int
    actor_user_public_id: str | None = None
    actor_email: str | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    description: str | None = None
    before_json: dict | None = None
    after_json: dict | None = None
    created_at: datetime


class PaginatedAdminAuditLogsResponseSchema(BaseModel):
    items: list[AdminAuditLogSchema]
    meta: PaginationMetaSchema


class AdminPromotionSchema(BaseModel):
    public_id: str
    listing_public_id: str
    listing_title: str
    seller_public_id: str
    seller_username: str
    package_name: str
    status: PromotionStatus
    target_city: str | None = None
    target_category_name: str | None = None
    price_amount: Decimal
    currency_code: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    created_at: datetime


class PaginatedAdminPromotionsResponseSchema(BaseModel):
    items: list[AdminPromotionSchema]
    meta: PaginationMetaSchema


class AdminConversationReviewSummarySchema(BaseModel):
    public_id: str
    listing_public_id: str | None = None
    listing_title: str | None = None
    buyer_public_id: str
    buyer_username: str
    seller_public_id: str
    seller_username: str
    message_count: int
    last_message_at: datetime | None = None


class AdminMessageAttachmentReviewSchema(BaseModel):
    public_id: str
    file_name: str
    mime_type: str
    download_url: str


class AdminMessageReviewSchema(BaseModel):
    public_id: str
    sender_public_id: str
    sender_username: str
    body: str | None = None
    created_at: datetime
    attachments: list[AdminMessageAttachmentReviewSchema]


class AdminConversationReviewDetailSchema(AdminConversationReviewSummarySchema):
    messages: list[AdminMessageReviewSchema]


class PaginatedAdminConversationsResponseSchema(BaseModel):
    items: list[AdminConversationReviewSummarySchema]
    meta: PaginationMetaSchema
