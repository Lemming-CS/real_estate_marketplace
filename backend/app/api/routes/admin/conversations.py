from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.api.deps import get_db, require_account_status, require_roles
from app.db.enums import RoleCode, UserStatus
from app.db.models import User
from app.modules.admin_console.schemas import (
    AdminConversationReviewDetailSchema,
    PaginatedAdminConversationsResponseSchema,
)
from app.modules.admin_console.service import (
    download_scoped_conversation_attachment,
    get_scoped_conversation_detail,
    list_scoped_conversations,
)

router = APIRouter(prefix="/admin/conversations", tags=["admin-conversations"])


@router.get(
    "/review",
    response_model=PaginatedAdminConversationsResponseSchema,
    summary="Review conversations within a listing or user abuse scope",
)
def review_conversations(
    listing_public_id: str | None = Query(default=None),
    user_public_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    __: User = Depends(require_roles(RoleCode.ADMIN)),
) -> PaginatedAdminConversationsResponseSchema:
    return list_scoped_conversations(
        db,
        listing_public_id=listing_public_id,
        user_public_id=user_public_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{conversation_public_id}/review",
    response_model=AdminConversationReviewDetailSchema,
    summary="Review a single conversation within a required abuse scope",
)
def review_conversation_detail(
    conversation_public_id: str,
    listing_public_id: str | None = Query(default=None),
    user_public_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    __: User = Depends(require_roles(RoleCode.ADMIN)),
) -> AdminConversationReviewDetailSchema:
    return get_scoped_conversation_detail(
        db,
        conversation_public_id=conversation_public_id,
        listing_public_id=listing_public_id,
        user_public_id=user_public_id,
    )


@router.get(
    "/{conversation_public_id}/attachments/{attachment_public_id}",
    summary="Download a reviewed conversation attachment within an admin abuse scope",
)
def review_conversation_attachment(
    conversation_public_id: str,
    attachment_public_id: str,
    listing_public_id: str | None = Query(default=None),
    user_public_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    __: User = Depends(require_roles(RoleCode.ADMIN)),
) -> FileResponse:
    return download_scoped_conversation_attachment(
        db,
        settings=settings,
        conversation_public_id=conversation_public_id,
        attachment_public_id=attachment_public_id,
        listing_public_id=listing_public_id,
        user_public_id=user_public_id,
    )
