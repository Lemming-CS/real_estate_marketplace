from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.db.enums import PaymentStatus, PaymentType, PromotionStatus
from app.shared.schemas import PaginationMetaSchema


class PromotionPackageCreateRequest(BaseModel):
    code: str = Field(min_length=3, max_length=100)
    name: str = Field(min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    duration_days: int = Field(ge=1, le=365)
    price_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency_code: str = Field(default="USD", min_length=3, max_length=3)
    boost_level: int = Field(ge=1, le=100)


class PromotionPackageUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    duration_days: int | None = Field(default=None, ge=1, le=365)
    price_amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    boost_level: int | None = Field(default=None, ge=1, le=100)
    is_active: bool | None = None


class PromotionPackageSchema(BaseModel):
    public_id: str
    code: str
    name: str
    description: str | None = None
    duration_days: int
    price_amount: Decimal
    currency_code: str
    boost_level: int
    is_active: bool
    status: Literal["active", "inactive"]
    created_at: datetime
    updated_at: datetime


class PaymentPromotionInitiateRequest(BaseModel):
    listing_public_id: str
    package_public_id: str
    duration_days: int = Field(ge=1, le=365)
    target_city: str | None = Field(default=None, min_length=2, max_length=120)
    target_category_public_id: str | None = None

    @model_validator(mode="after")
    def validate_target(self) -> "PaymentPromotionInitiateRequest":
        if not self.target_city and not self.target_category_public_id:
            raise ValueError("At least one target scope must be selected.")
        return self


class PaymentSimulationRequest(BaseModel):
    result: Literal["successful", "failed", "cancelled", "refunded_ready"]


class PromotionSummarySchema(BaseModel):
    public_id: str
    listing_public_id: str
    listing_title: str
    package_public_id: str
    package_code: str
    package_name: str
    status: PromotionStatus
    target_city: str | None = None
    target_category_public_id: str | None = None
    target_category_name: str | None = None
    duration_days: int
    price_amount: Decimal
    currency_code: str
    payment_public_id: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    activated_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PaymentSchema(BaseModel):
    public_id: str
    payment_type: PaymentType
    provider: str
    provider_reference: str | None = None
    amount: Decimal
    currency_code: str
    status: PaymentStatus
    failure_reason: str | None = None
    listing_public_id: str | None = None
    listing_title: str | None = None
    promotion_public_id: str | None = None
    checkout_url: str | None = None
    paid_at: datetime | None = None
    failed_at: datetime | None = None
    cancelled_at: datetime | None = None
    refunded_ready_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PaymentPriceBreakdownSchema(BaseModel):
    base_duration_days: int
    selected_duration_days: int
    base_price_amount: Decimal
    total_amount: Decimal
    currency_code: str


class PaymentInitiationResponseSchema(BaseModel):
    payment: PaymentSchema
    promotion: PromotionSummarySchema
    price_breakdown: PaymentPriceBreakdownSchema


class PaymentSimulationResponseSchema(BaseModel):
    payment: PaymentSchema
    promotion: PromotionSummarySchema | None = None


class PaginatedPaymentsResponseSchema(BaseModel):
    items: list[PaymentSchema]
    meta: PaginationMetaSchema


class PaginatedPromotionsResponseSchema(BaseModel):
    items: list[PromotionSummarySchema]
    meta: PaginationMetaSchema
