from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.modules.categories.schemas import PublicCategorySchema
from app.modules.categories.service import list_public_categories

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get(
    "",
    response_model=list[PublicCategorySchema],
    summary="List active marketplace categories with localized names",
)
def categories_list(
    locale: Literal["en", "ru"] = Query(default="en"),
    db: Session = Depends(get_db),
) -> list[PublicCategorySchema]:
    return list_public_categories(db, locale=locale)
