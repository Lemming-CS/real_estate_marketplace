from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.modules.users.schemas import PublicUserProfileSchema
from app.modules.users.service import get_public_user_profile

router = APIRouter(prefix="/public/users", tags=["public-users"])


@router.get(
    "/{user_public_id}",
    response_model=PublicUserProfileSchema,
    summary="View a public user profile",
)
def public_user_profile(user_public_id: str, db: Session = Depends(get_db)) -> PublicUserProfileSchema:
    return get_public_user_profile(db, public_id=user_public_id)

