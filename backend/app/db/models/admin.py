from __future__ import annotations

from sqlalchemy import ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin


class AdminAuditLog(TimestampMixin, Base):
    __tablename__ = "admin_audit_logs"
    __table_args__ = (
        Index("ix_admin_audit_logs_actor_created_at", "actor_user_id", "created_at"),
        Index("ix_admin_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_admin_audit_logs_action", "action"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    before_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    after_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

    actor: Mapped["User | None"] = relationship(foreign_keys=[actor_user_id])
