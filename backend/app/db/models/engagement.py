from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import NotificationStatus, ReportStatus
from app.db.mixins import PublicIdMixin, TimestampMixin


class Favorite(TimestampMixin, Base):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "listing_id", name="uq_favorites_user_listing"),
        Index("ix_favorites_listing_id", "listing_id"),
        Index("ix_favorites_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)

    user: Mapped["User"] = relationship()
    listing: Mapped["Listing"] = relationship()


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_id_status_created_at", "user_id", "status", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    data_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, native_enum=False),
        nullable=False,
        default=NotificationStatus.UNREAD,
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship()


class Report(PublicIdMixin, TimestampMixin, Base):
    __tablename__ = "reports"
    __table_args__ = (
        Index("ix_reports_status_created_at", "status", "created_at"),
        Index("ix_reports_listing_id", "listing_id"),
        Index("ix_reports_reporter_user_id_created_at", "reporter_user_id", "created_at"),
        Index("ix_reports_reported_user_id", "reported_user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reported_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("listings.id", ondelete="SET NULL"),
        nullable=True,
    )
    conversation_id: Mapped[int | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, native_enum=False),
        nullable=False,
        default=ReportStatus.OPEN,
    )
    resolved_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    reporter_user: Mapped["User"] = relationship(foreign_keys=[reporter_user_id])
    reported_user: Mapped["User | None"] = relationship(foreign_keys=[reported_user_id])
    listing: Mapped["Listing | None"] = relationship()
    conversation: Mapped["Conversation | None"] = relationship()
    resolved_by_user: Mapped["User | None"] = relationship(foreign_keys=[resolved_by_user_id])
