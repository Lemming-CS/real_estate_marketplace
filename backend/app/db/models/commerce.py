from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import PaymentStatus, PaymentType, PromotionStatus
from app.db.mixins import PublicIdMixin, TimestampMixin


class PaymentRecord(PublicIdMixin, TimestampMixin, Base):
    __tablename__ = "payment_records"
    __table_args__ = (
        Index("ix_payment_records_payer_status_created_at", "payer_user_id", "status", "created_at"),
        Index("ix_payment_records_provider_reference", "provider_reference"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    payer_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("listings.id", ondelete="SET NULL"),
        nullable=True,
    )
    payment_type: Mapped[PaymentType] = mapped_column(
        Enum(PaymentType, native_enum=False),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="demo")
    provider_reference: Mapped[str | None] = mapped_column(String(150), nullable=True, unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False),
        nullable=False,
        default=PaymentStatus.PENDING,
    )
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    refunded_ready_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    payer: Mapped["User | None"] = relationship(foreign_keys=[payer_user_id])
    listing: Mapped["Listing | None"] = relationship(foreign_keys=[listing_id])
    promotion: Mapped["Promotion | None"] = relationship(back_populates="payment_record")


class PromotionPackage(PublicIdMixin, TimestampMixin, Base):
    __tablename__ = "promotion_packages"
    __table_args__ = (Index("ix_promotion_packages_is_active", "is_active"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_days: Mapped[int] = mapped_column(nullable=False)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    boost_level: Mapped[int] = mapped_column(nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    promotions: Mapped[list["Promotion"]] = relationship(back_populates="package")


class Promotion(PublicIdMixin, TimestampMixin, Base):
    __tablename__ = "promotions"
    __table_args__ = (
        Index("ix_promotions_status_starts_at_ends_at", "status", "starts_at", "ends_at"),
        Index("ix_promotions_listing_id_status", "listing_id", "status"),
        Index("ix_promotions_target_city_status", "target_city", "status"),
        Index("ix_promotions_target_category_status", "target_category_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    promotion_package_id: Mapped[int] = mapped_column(
        ForeignKey("promotion_packages.id", ondelete="RESTRICT"),
        nullable=False,
    )
    payment_record_id: Mapped[int | None] = mapped_column(
        ForeignKey("payment_records.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    activated_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[PromotionStatus] = mapped_column(
        Enum(PromotionStatus, native_enum=False),
        nullable=False,
        default=PromotionStatus.PENDING_PAYMENT,
    )
    target_city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    target_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    duration_days: Mapped[int] = mapped_column(nullable=False, default=0)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    listing: Mapped["Listing"] = relationship(back_populates="promotions")
    package: Mapped["PromotionPackage"] = relationship(back_populates="promotions")
    payment_record: Mapped["PaymentRecord | None"] = relationship(back_populates="promotion")
    target_category: Mapped["Category | None"] = relationship(foreign_keys=[target_category_id])
