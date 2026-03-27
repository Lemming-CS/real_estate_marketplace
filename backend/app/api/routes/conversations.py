from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status
from app.core.config import Settings, get_settings
from app.db.enums import UserStatus
from app.db.models import User
from app.modules.messaging.schemas import (
    ConversationDetailSchema,
    ConversationReadStateSchema,
    ConversationSummarySchema,
    MessageCreateResponseSchema,
    PaginatedConversationsResponseSchema,
)
from app.modules.messaging.service import (
    create_or_reopen_listing_conversation,
    download_message_attachment,
    get_conversation_detail,
    list_conversations,
    mark_conversation_read,
    send_message,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post(
    "/from-listing/{listing_public_id}",
    response_model=ConversationDetailSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create or reopen a listing-linked conversation",
)
def create_or_reopen_conversation(
    listing_public_id: str,
    initial_message: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> ConversationDetailSchema:
    conversation = create_or_reopen_listing_conversation(
        db,
        listing_public_id=listing_public_id,
        actor=current_user,
        initial_message=initial_message,
    )
    db.commit()
    return conversation


@router.get(
    "",
    response_model=PaginatedConversationsResponseSchema,
    summary="List the authenticated user's inbox conversations",
)
def inbox(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> PaginatedConversationsResponseSchema:
    return list_conversations(db, actor=current_user, page=page, page_size=page_size)


@router.get(
    "/{conversation_public_id}",
    response_model=ConversationDetailSchema,
    summary="Get conversation detail for a participant",
)
def conversation_detail(
    conversation_public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> ConversationDetailSchema:
    return get_conversation_detail(db, conversation_public_id=conversation_public_id, actor=current_user)


@router.post(
    "/{conversation_public_id}/messages",
    response_model=MessageCreateResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message with optional attachments",
)
def send_conversation_message(
    conversation_public_id: str,
    body: str | None = Form(default=None),
    files: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> MessageCreateResponseSchema:
    response = send_message(
        db,
        settings=settings,
        conversation_public_id=conversation_public_id,
        actor=current_user,
        body=body,
        uploads=files,
    )
    db.commit()
    return response


@router.post(
    "/{conversation_public_id}/read",
    response_model=ConversationReadStateSchema,
    summary="Mark incoming messages in a conversation as read",
)
def mark_read(
    conversation_public_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> ConversationReadStateSchema:
    response = mark_conversation_read(db, conversation_public_id=conversation_public_id, actor=current_user)
    db.commit()
    return response


@router.get(
    "/{conversation_public_id}/attachments/{attachment_public_id}",
    response_class=FileResponse,
    summary="Download a message attachment if you are a conversation participant",
)
def conversation_attachment_download(
    conversation_public_id: str,
    attachment_public_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> FileResponse:
    return download_message_attachment(
        db,
        settings=settings,
        conversation_public_id=conversation_public_id,
        attachment_public_id=attachment_public_id,
        actor=current_user,
    )
