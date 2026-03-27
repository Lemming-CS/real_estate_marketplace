from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import ListingCondition, ListingStatus, MediaType
from app.db.mixins import PublicIdMixin, SoftDeleteMixin, TimestampMixin


class Listing(PublicIdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "listings"
    __table_args__ = (
        Index("ix_listings_seller_id_status_created_at", "seller_id", "status", "created_at"),
        Index("ix_listings_category_id_status_price", "category_id", "status", "price_amount"),
        Index("ix_listings_status_published_at", "status", "published_at"),
        Index("ix_listings_status_city_published_at", "status", "city", "published_at"),
        Index("ix_listings_status_price_amount", "status", "price_amount"),
        Index("ix_listings_title", "title"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    item_condition: Mapped[ListingCondition] = mapped_column(
        Enum(ListingCondition, native_enum=False),
        nullable=False,
    )
    status: Mapped[ListingStatus] = mapped_column(
        Enum(ListingStatus, native_enum=False),
        nullable=False,
        default=ListingStatus.DRAFT,
    )
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    moderation_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    seller: Mapped["User"] = relationship(back_populates="listings")
    category: Mapped["Category"] = relationship(back_populates="listings")
    media_items: Mapped[list["ListingMedia"]] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
    )
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="listing")
    promotions: Mapped[list["Promotion"]] = relationship(back_populates="listing")
    attribute_values: Mapped[list["ListingAttributeValue"]] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
    )


class ListingMedia(PublicIdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "listing_media"
    __table_args__ = (
        UniqueConstraint("public_id", name="uq_listing_media_public_id"),
        UniqueConstraint("listing_id", "sort_order", name="uq_listing_media_listing_sort_order"),
        Index("ix_listing_media_listing_id_is_primary", "listing_id", "is_primary"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    media_type: Mapped[MediaType] = mapped_column(Enum(MediaType, native_enum=False), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    listing: Mapped["Listing"] = relationship(back_populates="media_items")


class ListingAttributeValue(TimestampMixin, Base):
    __tablename__ = "listing_attribute_values"
    __table_args__ = (
        UniqueConstraint(
            "listing_id",
            "category_attribute_id",
            name="uq_listing_attribute_values_listing_attribute",
        ),
        Index(
            "ix_listing_attribute_values_attribute_text",
            "category_attribute_id",
            "text_value",
        ),
        Index(
            "ix_listing_attribute_values_attribute_numeric",
            "category_attribute_id",
            "numeric_value",
        ),
        Index(
            "ix_listing_attribute_values_attribute_option",
            "category_attribute_id",
            "option_value",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    category_attribute_id: Mapped[int] = mapped_column(
        ForeignKey("category_attributes.id", ondelete="CASCADE"),
        nullable=False,
    )
    text_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    numeric_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    boolean_value: Mapped[bool | None] = mapped_column(nullable=True)
    option_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    json_value: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

    listing: Mapped["Listing"] = relationship(back_populates="attribute_values")
    category_attribute: Mapped["CategoryAttribute"] = relationship()
