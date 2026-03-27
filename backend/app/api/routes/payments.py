from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_account_status
from app.core.config import Settings, get_settings
from app.db.enums import UserStatus
from app.db.models import User
from app.modules.commerce.schemas import (
    PaginatedPaymentsResponseSchema,
    PaymentInitiationResponseSchema,
    PaymentPromotionInitiateRequest,
    PaymentSimulationRequest,
    PaymentSimulationResponseSchema,
)
from app.modules.commerce.service import initiate_promotion_payment, list_user_payments, simulate_payment_result

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "/promotions/initiate",
    response_model=PaymentInitiationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a pending payment and promotion request for a listing boost",
)
def initiate_promotion_checkout(
    payload: PaymentPromotionInitiateRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> PaymentInitiationResponseSchema:
    response = initiate_promotion_payment(db, settings=settings, actor=current_user, payload=payload)
    db.commit()
    return response


@router.post(
    "/{payment_public_id}/simulate",
    response_model=PaymentSimulationResponseSchema,
    summary="Simulate a mock payment provider result for local development",
)
def simulate_payment(
    payment_public_id: str,
    payload: PaymentSimulationRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> PaymentSimulationResponseSchema:
    response = simulate_payment_result(
        db,
        settings=settings,
        payment_public_id=payment_public_id,
        payload=payload,
        actor=current_user,
    )
    db.commit()
    return response


@router.get(
    "/{payment_public_id}/checkout",
    response_model=PaymentSimulationResponseSchema,
    summary="Complete a mock checkout flow through a functional GET endpoint",
)
def complete_mock_checkout(
    payment_public_id: str,
    result: str = Query(default="successful"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> PaymentSimulationResponseSchema:
    response = simulate_payment_result(
        db,
        settings=settings,
        payment_public_id=payment_public_id,
        payload=PaymentSimulationRequest(result=result),
        actor=current_user,
    )
    db.commit()
    return response


@router.get(
    "",
    response_model=PaginatedPaymentsResponseSchema,
    summary="List the authenticated user's payment transaction history",
)
def payment_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(require_account_status(UserStatus.ACTIVE)),
) -> PaginatedPaymentsResponseSchema:
    response = list_user_payments(db, settings=settings, user=current_user, page=page, page_size=page_size)
    return response
