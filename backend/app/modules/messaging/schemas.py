from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.db.enums import AttachmentType, ConversationStatus, MessageStatus, MessageType
from app.shared.schemas import PaginationMetaSchema


class ConversationCounterpartySchema(BaseModel):
    public_id: str
    username: str
    full_name: str
    profile_image_path: str | None = None


class ConversationListingSchema(BaseModel):
    public_id: str
    title: str
    status: str
    primary_media_asset_key: str | None = None


class MessageAttachmentSchema(BaseModel):
    public_id: str
    attachment_type: AttachmentType
    file_name: str
    mime_type: str
    file_size_bytes: int | None = None
    download_url: str


class MessageSchema(BaseModel):
    public_id: str
    sender_user_id: str
    body: str | None = None
    message_type: MessageType
    status: MessageStatus
    read_at: datetime | None = None
    created_at: datetime
    attachments: list[MessageAttachmentSchema]


class ConversationSummarySchema(BaseModel):
    public_id: str
    status: ConversationStatus
    listing: ConversationListingSchema | None = None
    counterparty: ConversationCounterpartySchema
    unread_count: int
    last_message_preview: str | None = None
    last_message_at: datetime | None = None
    updated_at: datetime


class ConversationDetailSchema(BaseModel):
    public_id: str
    status: ConversationStatus
    listing: ConversationListingSchema | None = None
    buyer_user_id: str
    seller_user_id: str
    counterparty: ConversationCounterpartySchema
    unread_count: int
    last_message_at: datetime | None = None
    messages: list[MessageSchema]


class PaginatedConversationsResponseSchema(BaseModel):
    items: list[ConversationSummarySchema]
    meta: PaginationMetaSchema


class MessageCreateResponseSchema(BaseModel):
    conversation: ConversationDetailSchema
    message: MessageSchema


class ConversationReadStateSchema(BaseModel):
    conversation_public_id: str
    unread_count: int


class ConversationCreateRequest(BaseModel):
    initial_message: str | None = Field(default=None, max_length=4000)
