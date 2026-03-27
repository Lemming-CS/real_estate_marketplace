from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status, require_roles
from app.db.enums import RoleCode, UserStatus
from app.db.models import User
from app.modules.commerce.schemas import (
    PromotionPackageCreateRequest,
    PromotionPackageSchema,
    PromotionPackageUpdateRequest,
)
from app.modules.commerce.service import (
    create_promotion_package,
    deactivate_promotion_package,
    list_admin_promotion_packages,
    update_promotion_package,
)

router = APIRouter(prefix="/admin/promotion-packages", tags=["admin-promotion-packages"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get(
    "",
    response_model=list[PromotionPackageSchema],
    summary="List promotion packages for admin management",
)
def admin_package_list(
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    __: User = Depends(require_roles(RoleCode.ADMIN)),
) -> list[PromotionPackageSchema]:
    return list_admin_promotion_packages(db)


@router.post(
    "",
    response_model=PromotionPackageSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a promotion package",
)
def admin_package_create(
    payload: PromotionPackageCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    current_user: User = Depends(require_roles(RoleCode.ADMIN)),
) -> PromotionPackageSchema:
    response = create_promotion_package(
        db,
        payload=payload,
        actor=current_user,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return response


@router.patch(
    "/{package_public_id}",
    response_model=PromotionPackageSchema,
    summary="Update a promotion package",
)
def admin_package_update(
    package_public_id: str,
    payload: PromotionPackageUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    current_user: User = Depends(require_roles(RoleCode.ADMIN)),
) -> PromotionPackageSchema:
    response = update_promotion_package(
        db,
        package_public_id=package_public_id,
        payload=payload,
        actor=current_user,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return response


@router.delete(
    "/{package_public_id}",
    response_model=PromotionPackageSchema,
    summary="Deactivate a promotion package",
)
def admin_package_delete(
    package_public_id: str,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_account_status(UserStatus.ACTIVE)),
    current_user: User = Depends(require_roles(RoleCode.ADMIN)),
) -> PromotionPackageSchema:
    response = deactivate_promotion_package(
        db,
        package_public_id=package_public_id,
        actor=current_user,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return response
