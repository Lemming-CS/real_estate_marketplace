from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status, require_roles
from app.db.enums import RoleCode, UserStatus
from app.db.models import User
from app.modules.admin_console.schemas import (
    AdminUserDetailSchema,
    AdminUserStatusUpdateRequest,
    PaginatedAdminUsersResponseSchema,
)
from app.modules.admin_console.service import get_admin_user_detail, list_admin_users, update_admin_user_status

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=PaginatedAdminUsersResponseSchema, summary="Search and list users for admin operations")
def admin_users(
    q: str | None = Query(default=None),
    status: UserStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    __: User = Depends(require_roles(RoleCode.ADMIN)),
) -> PaginatedAdminUsersResponseSchema:
    return list_admin_users(db, q=q, status=status, page=page, page_size=page_size)


@router.get("/{user_public_id}", response_model=AdminUserDetailSchema, summary="Inspect a user and recent operational context")
def admin_user_detail(
    user_public_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    __: User = Depends(require_roles(RoleCode.ADMIN)),
) -> AdminUserDetailSchema:
    return get_admin_user_detail(db, user_public_id=user_public_id)


@router.post(
    "/{user_public_id}/status",
    response_model=AdminUserDetailSchema,
    summary="Suspend or unsuspend a user account",
)
def admin_user_status_update(
    user_public_id: str,
    payload: AdminUserStatusUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    current_user: User = Depends(require_roles(RoleCode.ADMIN)),
) -> AdminUserDetailSchema:
    response = update_admin_user_status(
        db,
        user_public_id=user_public_id,
        payload=payload,
        actor=current_user,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return response
