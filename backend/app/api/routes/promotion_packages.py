from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.modules.commerce.schemas import PromotionPackageSchema
from app.modules.commerce.service import list_active_promotion_packages

router = APIRouter(prefix="/promotion-packages", tags=["promotion-packages"])


@router.get(
    "",
    response_model=list[PromotionPackageSchema],
    summary="List active promotion packages available for purchase",
)
def promotion_packages_list(
    db: Session = Depends(get_db),
) -> list[PromotionPackageSchema]:
    return list_active_promotion_packages(db)
