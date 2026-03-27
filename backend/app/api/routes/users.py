from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status
from app.db.enums import UserStatus
from app.db.models import User
from app.modules.users.schemas import OwnerListingSchema
from app.modules.users.service import get_owner_listings

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me/listings",
    response_model=list[OwnerListingSchema],
    summary="List listings owned by the authenticated user",
)
def owner_listings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> list[OwnerListingSchema]:
    return get_owner_listings(db, user=current_user)

