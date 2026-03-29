from __future__ import annotations

import re
from math import ceil
from pathlib import Path

from fastapi import UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import case

from app.core.auth import utcnow
from app.core.config import Settings
from app.core.exceptions import AppError
from app.db.enums import AttachmentType, ConversationStatus, ListingStatus, MessageStatus, MessageType, UserStatus
from app.db.models import Conversation, Listing, ListingMedia, Message, MessageAttachment, User
from app.modules.messaging.schemas import (
    ConversationCounterpartySchema,
    ConversationDetailSchema,
    ConversationListingSchema,
    ConversationReadStateSchema,
    ConversationSummarySchema,
    MessageAttachmentSchema,
    MessageCreateResponseSchema,
    MessageSchema,
    PaginatedConversationsResponseSchema,
)
from app.modules.notifications.service import notify_new_message
from app.shared.schemas import PaginationMetaSchema
from app.shared.storage import save_upload

MESSAGE_ATTACHMENT_MAX_SIZE_BYTES = 15 * 1024 * 1024
MAX_ATTACHMENTS_PER_MESSAGE = 5
ALLOWED_ATTACHMENT_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


def create_or_reopen_listing_conversation(
    session: Session,
    *,
    listing_public_id: str,
    actor: User,
    initial_message: str | None = None,
) -> ConversationDetailSchema:
    _ensure_can_message(actor)
    actor_id = actor.id
    listing = _get_messagable_listing_or_404(session, listing_public_id=listing_public_id)
    listing_id = listing.id
    seller_user_id = listing.seller_id

    if seller_user_id == actor_id:
        raise AppError(status_code=400, code="cannot_message_self", message="You cannot start a conversation with yourself.")

    conversation = session.execute(
        _conversation_query().where(
            Conversation.listing_id == listing_id,
            Conversation.buyer_user_id == actor_id,
            Conversation.seller_user_id == seller_user_id,
            Conversation.deleted_at.is_(None),
        )
    ).scalar_one_or_none()

    if conversation is None:
        conversation = Conversation(
            listing_id=listing_id,
            buyer_user_id=actor_id,
            seller_user_id=seller_user_id,
            status=ConversationStatus.ACTIVE,
            last_message_at=None,
        )
        session.add(conversation)
        try:
            session.flush()
        except IntegrityError as exc:
            session.rollback()
            conversation = session.execute(
                _conversation_query().where(
                    Conversation.listing_id == listing_id,
                    Conversation.buyer_user_id == actor_id,
                    Conversation.seller_user_id == seller_user_id,
                    Conversation.deleted_at.is_(None),
                )
            ).scalar_one_or_none()
            if conversation is None:
                raise AppError(
                    status_code=500,
                    code="conversation_create_failed",
                    message="Conversation could not be created.",
                ) from exc
            actor = session.execute(select(User).where(User.id == actor_id)).scalar_one()

    if conversation.status == ConversationStatus.BLOCKED:
        raise AppError(status_code=403, code="conversation_blocked", message="This conversation is blocked.")

    conversation.status = ConversationStatus.ACTIVE

    if initial_message is not None and initial_message.strip():
        _create_message(
            session,
            conversation=conversation,
            sender=actor,
            body=initial_message,
            uploads=[],
        )

    session.flush()
    session.expire_all()

    fresh_conversation = _get_conversation_or_404(
        session,
        conversation_public_id=conversation.public_id,
        actor=actor,
    )

    return _build_conversation_detail_schema(
        session,
        conversation=fresh_conversation,
        actor=actor,
    )


def list_conversations(session: Session, *, actor: User, page: int, page_size: int) -> PaginatedConversationsResponseSchema:
    _ensure_can_message(actor)
    base_query = (
        select(Conversation)
        .options(*_conversation_load_options())
        .where(
            Conversation.deleted_at.is_(None),
            or_(Conversation.buyer_user_id == actor.id, Conversation.seller_user_id == actor.id),
        )
        .order_by(
    case(
        (Conversation.last_message_at == None, 1),
        else_=0,
    ),
    Conversation.last_message_at.desc(),
    Conversation.updated_at.desc(),
    Conversation.id.desc(),
)
    )
    total_items = session.execute(select(func.count()).select_from(base_query.subquery())).scalar_one()
    conversations = session.execute(
        base_query.offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    unread_map = _conversation_unread_map(session, actor=actor, conversation_ids=[conversation.id for conversation in conversations])
    return PaginatedConversationsResponseSchema(
        items=[
            _build_conversation_summary_schema(session, conversation=conversation, actor=actor, unread_count=unread_map.get(conversation.id, 0))
            for conversation in conversations
        ],
        meta=PaginationMetaSchema(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=ceil(total_items / page_size) if total_items else 0,
        ),
    )


def get_conversation_detail(session: Session, *, conversation_public_id: str, actor: User) -> ConversationDetailSchema:
    _ensure_can_message(actor)
    conversation = _get_conversation_or_404(session, conversation_public_id=conversation_public_id, actor=actor)
    return _build_conversation_detail_schema(session, conversation=conversation, actor=actor)


def send_message(
    session: Session,
    *,
    settings: Settings,
    conversation_public_id: str,
    actor: User,
    body: str | None,
    uploads: list[UploadFile],
) -> MessageCreateResponseSchema:
    _ensure_can_message(actor)
    conversation = _get_conversation_or_404(session, conversation_public_id=conversation_public_id, actor=actor)
    if conversation.status == ConversationStatus.BLOCKED:
        raise AppError(status_code=403, code="conversation_blocked", message="This conversation is blocked.")
    if conversation.status == ConversationStatus.CLOSED:
        conversation.status = ConversationStatus.ACTIVE

    message = _create_message(session, conversation=conversation, sender=actor, body=body, uploads=uploads, settings=settings)
    session.flush()
    conversation = _get_conversation_or_404(session, conversation_public_id=conversation.public_id, actor=actor)
    return MessageCreateResponseSchema(
        conversation=_build_conversation_detail_schema(session, conversation=conversation, actor=actor),
        message=_build_message_schema(message),
    )


def mark_conversation_read(
    session: Session,
    *,
    conversation_public_id: str,
    actor: User,
) -> ConversationReadStateSchema:
    _ensure_can_message(actor)
    conversation = _get_conversation_or_404(session, conversation_public_id=conversation_public_id, actor=actor)
    unread_messages = session.execute(
        select(Message).where(
            Message.conversation_id == conversation.id,
            Message.sender_user_id != actor.id,
            Message.deleted_at.is_(None),
            Message.read_at.is_(None),
        )
    ).scalars().all()
    for message in unread_messages:
        message.read_at = utcnow()
        message.status = MessageStatus.READ
    session.flush()
    return ConversationReadStateSchema(conversation_public_id=conversation.public_id, unread_count=0)


def download_message_attachment(
    session: Session,
    *,
    settings: Settings,
    conversation_public_id: str,
    attachment_public_id: str,
    actor: User,
) -> FileResponse:
    _ensure_can_message(actor)
    conversation = _get_conversation_or_404(session, conversation_public_id=conversation_public_id, actor=actor)
    attachment = session.execute(
        select(MessageAttachment)
        .join(Message, Message.id == MessageAttachment.message_id)
        .where(
            Message.conversation_id == conversation.id,
            MessageAttachment.public_id == attachment_public_id,
        )
    ).scalar_one_or_none()
    if attachment is None:
        raise AppError(status_code=404, code="message_attachment_not_found", message="Message attachment was not found.")

    absolute_path = _safe_storage_path(settings=settings, storage_key=attachment.storage_key)
    if not absolute_path.exists():
        raise AppError(status_code=404, code="message_attachment_missing", message="Stored attachment file is missing.")

    return FileResponse(
        path=absolute_path,
        media_type=attachment.mime_type,
        filename=attachment.file_name,
    )


def _conversation_query():
    return select(Conversation).options(*_conversation_load_options())


def _conversation_load_options():
    return (
        selectinload(Conversation.messages).selectinload(Message.attachments),
        selectinload(Conversation.listing).selectinload(Listing.media_items),
        selectinload(Conversation.buyer),
        selectinload(Conversation.seller),
    )


def _get_messagable_listing_or_404(session: Session, *, listing_public_id: str) -> Listing:
    listing = session.execute(
        select(Listing)
        .options(selectinload(Listing.seller))
        .where(Listing.public_id == listing_public_id, Listing.deleted_at.is_(None))
    ).scalar_one_or_none()
    if listing is None or listing.status != ListingStatus.PUBLISHED or listing.seller.status != UserStatus.ACTIVE:
        raise AppError(status_code=404, code="listing_not_found", message="Listing was not found.")
    return listing


def _get_conversation_or_404(session: Session, *, conversation_public_id: str, actor: User) -> Conversation:
    conversation = session.execute(
        _conversation_query().where(
            Conversation.public_id == conversation_public_id,
            Conversation.deleted_at.is_(None),
        )
    ).scalar_one_or_none()
    if conversation is None:
        raise AppError(status_code=404, code="conversation_not_found", message="Conversation was not found.")
    if actor.id not in {conversation.buyer_user_id, conversation.seller_user_id}:
        raise AppError(status_code=403, code="conversation_forbidden", message="You do not have access to this conversation.")
    return conversation


def _ensure_can_message(user: User) -> None:
    if user.status == UserStatus.ACTIVE:
        return
    if user.status == UserStatus.SUSPENDED:
        raise AppError(status_code=403, code="account_suspended", message="Suspended users cannot use messaging.")
    if user.status == UserStatus.PENDING_VERIFICATION:
        raise AppError(
            status_code=403,
            code="account_pending_verification",
            message="Pending-verification users cannot use messaging yet.",
        )
    raise AppError(status_code=403, code="account_deleted", message="Deactivated users cannot use messaging.")


def _create_message(
    session: Session,
    *,
    conversation: Conversation,
    sender: User,
    body: str | None,
    uploads: list[UploadFile],
    settings: Settings | None = None,
) -> Message:
    normalized_body = body.strip() if body else None
    uploads = uploads or []
    if normalized_body is None and not uploads:
        raise AppError(status_code=400, code="message_empty", message="Message must contain text or at least one attachment.")
    if len(uploads) > MAX_ATTACHMENTS_PER_MESSAGE:
        raise AppError(
            status_code=400,
            code="too_many_attachments",
            message="Too many attachments in a single message.",
            details={"max_attachments": MAX_ATTACHMENTS_PER_MESSAGE},
        )

    attachment_payloads = []
    has_image_attachment = False
    if uploads:
        if settings is None:
            raise AppError(status_code=500, code="message_storage_unavailable", message="Attachment storage is unavailable.")
        for upload in uploads:
            if not upload.content_type or upload.content_type not in ALLOWED_ATTACHMENT_MIME_TYPES:
                raise AppError(
                    status_code=400,
                    code="invalid_attachment_type",
                    message="Unsupported attachment type.",
                    details={"allowed_mime_types": sorted(ALLOWED_ATTACHMENT_MIME_TYPES)},
                )
            storage_key, file_size_bytes = save_upload(
                settings=settings,
                upload=upload,
                relative_dir=Path("messages") / conversation.public_id,
                allowed_mime_types=ALLOWED_ATTACHMENT_MIME_TYPES,
                max_size_bytes=MESSAGE_ATTACHMENT_MAX_SIZE_BYTES,
            )
            attachment_type = AttachmentType.IMAGE if upload.content_type.startswith("image/") else AttachmentType.FILE
            if attachment_type == AttachmentType.IMAGE:
                has_image_attachment = True
            attachment_payloads.append(
                {
                    "attachment_type": attachment_type,
                    "file_name": _safe_display_name(upload.filename),
                    "storage_key": storage_key,
                    "mime_type": upload.content_type,
                    "file_size_bytes": file_size_bytes,
                }
            )

    message_type = MessageType.TEXT
    if normalized_body is None and attachment_payloads:
        message_type = MessageType.IMAGE if has_image_attachment and all(item["attachment_type"] == AttachmentType.IMAGE for item in attachment_payloads) else MessageType.TEXT

    message = Message(
        conversation_id=conversation.id,
        sender_user_id=sender.id,
        body=normalized_body,
        message_type=message_type,
        status=MessageStatus.SENT,
    )
    session.add(message)
    session.flush()

    for attachment_payload in attachment_payloads:
        session.add(
            MessageAttachment(
                message_id=message.id,
                **attachment_payload,
            )
        )

    conversation.last_message_at = utcnow()
    conversation.status = ConversationStatus.ACTIVE

    recipient = conversation.seller if sender.id == conversation.buyer_user_id else conversation.buyer
    notify_new_message(
        session,
        recipient=recipient,
        conversation_public_id=conversation.public_id,
        listing_public_id=conversation.listing.public_id if conversation.listing else None,
        sender_public_id=sender.public_id,
        sender_name=sender.full_name,
        message_preview=(normalized_body[:120] if normalized_body else "Attachment"),
    )
    session.flush()
    session.refresh(message)
    return message


def _conversation_unread_map(session: Session, *, actor: User, conversation_ids: list[int]) -> dict[int, int]:
    if not conversation_ids:
        return {}
    rows = session.execute(
        select(Message.conversation_id, func.count(Message.id))
        .where(
            Message.conversation_id.in_(conversation_ids),
            Message.sender_user_id != actor.id,
            Message.deleted_at.is_(None),
            Message.read_at.is_(None),
        )
        .group_by(Message.conversation_id)
    ).all()
    return {conversation_id: count for conversation_id, count in rows}


def _build_conversation_summary_schema(
    session: Session,
    *,
    conversation: Conversation,
    actor: User,
    unread_count: int,
) -> ConversationSummarySchema:
    counterparty = conversation.seller if actor.id == conversation.buyer_user_id else conversation.buyer
    last_message = _last_message(conversation)
    return ConversationSummarySchema(
        public_id=conversation.public_id,
        status=conversation.status,
        listing=_build_conversation_listing_schema(conversation.listing),
        counterparty=ConversationCounterpartySchema(
            public_id=counterparty.public_id,
            username=counterparty.username,
            full_name=counterparty.full_name,
            profile_image_path=counterparty.profile_image_path,
        ),
        unread_count=unread_count,
        last_message_preview=_message_preview(last_message),
        last_message_at=conversation.last_message_at,
        updated_at=conversation.updated_at,
    )


def _build_conversation_detail_schema(session: Session, *, conversation: Conversation, actor: User) -> ConversationDetailSchema:
    unread_count = _conversation_unread_map(session, actor=actor, conversation_ids=[conversation.id]).get(conversation.id, 0)
    counterparty = conversation.seller if actor.id == conversation.buyer_user_id else conversation.buyer
    messages = sorted(
        [message for message in conversation.messages if message.deleted_at is None],
        key=lambda item: (item.created_at, item.id),
    )
    return ConversationDetailSchema(
        public_id=conversation.public_id,
        status=conversation.status,
        listing=_build_conversation_listing_schema(conversation.listing),
        buyer_user_id=conversation.buyer.public_id,
        seller_user_id=conversation.seller.public_id,
        counterparty=ConversationCounterpartySchema(
            public_id=counterparty.public_id,
            username=counterparty.username,
            full_name=counterparty.full_name,
            profile_image_path=counterparty.profile_image_path,
        ),
        unread_count=unread_count,
        last_message_at=conversation.last_message_at,
        messages=[_build_message_schema(message) for message in messages],
    )


def _build_conversation_listing_schema(listing: Listing | None) -> ConversationListingSchema | None:
    if listing is None:
        return None
    primary_media = next((media for media in listing.media_items if media.deleted_at is None and media.is_primary), None)
    if primary_media is None:
        primary_media = next((media for media in listing.media_items if media.deleted_at is None), None)
    return ConversationListingSchema(
        public_id=listing.public_id,
        title=listing.title,
        status=listing.status.value,
        primary_media_asset_key=primary_media.storage_key if primary_media else None,
    )


def _build_message_schema(message: Message) -> MessageSchema:
    return MessageSchema(
        public_id=message.public_id,
        sender_user_id=message.sender.public_id,
        body=message.body,
        message_type=message.message_type,
        status=message.status,
        read_at=message.read_at,
        created_at=message.created_at,
        attachments=[
            MessageAttachmentSchema(
                public_id=attachment.public_id,
                attachment_type=attachment.attachment_type,
                file_name=attachment.file_name,
                mime_type=attachment.mime_type,
                file_size_bytes=attachment.file_size_bytes,
                download_url=f"/api/v1/conversations/{message.conversation.public_id}/attachments/{attachment.public_id}",
            )
            for attachment in message.attachments
        ],
    )


def _last_message(conversation: Conversation) -> Message | None:
    messages = [message for message in conversation.messages if message.deleted_at is None]
    if not messages:
        return None
    return max(messages, key=lambda item: (item.created_at, item.id))


def _message_preview(message: Message | None) -> str | None:
    if message is None:
        return None
    if message.body:
        return message.body[:120]
    if message.attachments:
        return "Attachment"
    return None


def _safe_display_name(filename: str | None) -> str:
    original = Path(filename or "attachment").name
    cleaned = re.sub(r"[^\w.\- ]+", "_", original, flags=re.UNICODE).strip(" ._")
    return cleaned or "attachment"


def _safe_storage_path(*, settings: Settings, storage_key: str) -> Path:
    base_path = Path(settings.media_storage_path).resolve()
    target_path = (base_path / storage_key).resolve()
    if base_path not in target_path.parents and target_path != base_path:
        raise AppError(status_code=400, code="invalid_attachment_path", message="Invalid attachment path.")
    return target_path
