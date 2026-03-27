from __future__ import annotations

from enum import StrEnum


class RoleCode(StrEnum):
    ADMIN = "admin"
    USER = "user"
    SELLER = "seller"


class UserStatus(StrEnum):
    ACTIVE = "active"
    PENDING_VERIFICATION = "pending_verification"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class CategoryAttributeType(StrEnum):
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"
    JSON = "json"


class ListingCondition(StrEnum):
    NEW = "new"
    LIKE_NEW = "like_new"
    USED_GOOD = "used_good"
    USED_FAIR = "used_fair"
    FOR_PARTS = "for_parts"


class ListingStatus(StrEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    INACTIVE = "inactive"
    SOLD = "sold"


class MediaType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    FILE = "file"


class ConversationStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"
    BLOCKED = "blocked"


class MessageType(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    SYSTEM = "system"


class MessageStatus(StrEnum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    DELETED = "deleted"


class AttachmentType(StrEnum):
    IMAGE = "image"
    FILE = "file"


class NotificationStatus(StrEnum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"


class ReportStatus(StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED_READY = "refunded_ready"


class PaymentType(StrEnum):
    LISTING_PURCHASE = "listing_purchase"
    PROMOTION_PURCHASE = "promotion_purchase"
    MANUAL_ADJUSTMENT = "manual_adjustment"


class PromotionStatus(StrEnum):
    PENDING_PAYMENT = "pending_payment"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
