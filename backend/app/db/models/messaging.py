from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import AttachmentType, ConversationStatus, MessageStatus, MessageType
from app.db.mixins import PublicIdMixin, SoftDeleteMixin, TimestampMixin


class Conversation(PublicIdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint(
            "listing_id",
            "buyer_user_id",
            "seller_user_id",
            name="uq_conversations_listing_buyer_seller",
        ),
        Index("ix_conversations_status_last_message_at", "status", "last_message_at"),
        Index("ix_conversations_buyer_last_message_at", "buyer_user_id", "last_message_at"),
        Index("ix_conversations_seller_last_message_at", "seller_user_id", "last_message_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("listings.id", ondelete="SET NULL"),
        nullable=True,
    )
    buyer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    seller_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, native_enum=False),
        nullable=False,
        default=ConversationStatus.ACTIVE,
    )
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    listing: Mapped["Listing | None"] = relationship(back_populates="conversations")
    buyer: Mapped["User"] = relationship(
        foreign_keys=[buyer_user_id],
        back_populates="buyer_conversations",
    )
    seller: Mapped["User"] = relationship(
        foreign_keys=[seller_user_id],
        back_populates="seller_conversations",
    )
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(PublicIdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_id_created_at", "conversation_id", "created_at"),
        Index("ix_messages_sender_user_id_created_at", "sender_user_id", "created_at"),
        Index("ix_messages_conversation_id_read_at", "conversation_id", "read_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_type: Mapped[MessageType] = mapped_column(
        Enum(MessageType, native_enum=False),
        nullable=False,
        default=MessageType.TEXT,
    )
    status: Mapped[MessageStatus] = mapped_column(
        Enum(MessageStatus, native_enum=False),
        nullable=False,
        default=MessageStatus.SENT,
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(back_populates="sent_messages")
    attachments: Mapped[list["MessageAttachment"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
    )


class MessageAttachment(PublicIdMixin, TimestampMixin, Base):
    __tablename__ = "message_attachments"
    __table_args__ = (
        Index("ix_message_attachments_message_id", "message_id"),
        UniqueConstraint("public_id", name="uq_message_attachments_public_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    attachment_type: Mapped[AttachmentType] = mapped_column(
        Enum(AttachmentType, native_enum=False),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(nullable=True)

    message: Mapped["Message"] = relationship(back_populates="attachments")
