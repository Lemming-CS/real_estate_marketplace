from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status, require_roles
from app.db.enums import RoleCode, UserStatus
from app.db.models import User
from app.modules.auth.schemas import MessageResponse
from app.modules.categories.schemas import AdminCategorySchema, CategoryCreateRequest, CategoryUpdateRequest
from app.modules.categories.service import create_category, delete_category, get_admin_category, list_admin_categories, update_category

router = APIRouter(prefix="/admin/categories", tags=["admin-categories"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[AdminCategorySchema], summary="List all non-deleted categories for admin management")
def admin_categories_list(
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    __: User = Depends(require_roles(RoleCode.ADMIN)),
) -> list[AdminCategorySchema]:
    return list_admin_categories(db)


@router.post(
    "",
    response_model=AdminCategorySchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category with translations and dynamic attributes",
)
def admin_create_category(
    payload: CategoryCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    current_user: User = Depends(require_roles(RoleCode.ADMIN)),
) -> AdminCategorySchema:
    category = create_category(
        db,
        payload=payload,
        actor=current_user,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return category


@router.get(
    "/{category_public_id}",
    response_model=AdminCategorySchema,
    summary="Get a single category with translations and attributes",
)
def admin_get_category(
    category_public_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    __: User = Depends(require_roles(RoleCode.ADMIN)),
) -> AdminCategorySchema:
    return get_admin_category(db, category_public_id=category_public_id)


@router.patch(
    "/{category_public_id}",
    response_model=AdminCategorySchema,
    summary="Update category metadata, translations, or attributes",
)
def admin_update_category(
    category_public_id: str,
    payload: CategoryUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    current_user: User = Depends(require_roles(RoleCode.ADMIN)),
) -> AdminCategorySchema:
    category = update_category(
        db,
        category_public_id=category_public_id,
        payload=payload,
        actor=current_user,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return category


@router.delete(
    "/{category_public_id}",
    response_model=MessageResponse,
    summary="Soft-delete a category that has no active children or listings",
)
def admin_delete_category(
    category_public_id: str,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    current_user: User = Depends(require_roles(RoleCode.ADMIN)),
) -> MessageResponse:
    delete_category(
        db,
        category_public_id=category_public_id,
        actor=current_user,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return MessageResponse(message="Category deleted successfully.")
