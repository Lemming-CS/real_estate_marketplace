from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.db.enums import CategoryAttributeType, ListingCondition, ListingPurpose, ListingStatus, MediaType, PropertyType
from app.shared.schemas import PaginationMetaSchema

LocaleCode = Literal["en", "ru"]
ListingSortOption = Literal["newest", "oldest", "price_asc", "price_desc"]


class ListingAttributeValueInput(BaseModel):
    attribute_code: str = Field(min_length=2, max_length=100)
    text_value: str | None = Field(default=None, max_length=255)
    numeric_value: Decimal | None = None
    boolean_value: bool | None = None
    option_value: str | None = Field(default=None, max_length=100)
    json_value: dict[str, Any] | list[Any] | None = None

    @model_validator(mode="after")
    def validate_single_value(self) -> "ListingAttributeValueInput":
        populated = [
            self.text_value is not None,
            self.numeric_value is not None,
            self.boolean_value is not None,
            self.option_value is not None,
            self.json_value is not None,
        ]
        if sum(populated) != 1:
            raise ValueError("Exactly one typed attribute value must be provided.")
        self.attribute_code = self.attribute_code.strip().lower().replace("-", "_")
        return self


class ListingCreateRequest(BaseModel):
    category_public_id: str
    title: str = Field(min_length=5, max_length=255)
    description: str = Field(min_length=20, max_length=5000)
    purpose: ListingPurpose
    property_type: PropertyType
    price_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency_code: str = Field(default="USD", min_length=3, max_length=3)
    city: str = Field(min_length=2, max_length=120)
    district: str | None = Field(default=None, max_length=120)
    address_text: str = Field(min_length=5, max_length=255)
    map_label: str | None = Field(default=None, max_length=120)
    latitude: Decimal = Field(ge=-90, le=90, max_digits=10, decimal_places=7)
    longitude: Decimal = Field(ge=-180, le=180, max_digits=10, decimal_places=7)
    room_count: int = Field(ge=1, le=50)
    area_sqm: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    floor: int | None = Field(default=None, ge=0, le=200)
    total_floors: int | None = Field(default=None, ge=1, le=300)
    furnished: bool | None = None
    item_condition: ListingCondition | None = None
    attribute_values: list[ListingAttributeValueInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_real_estate_fields(self) -> "ListingCreateRequest":
        if self.total_floors is not None and self.floor is not None and self.floor > self.total_floors:
            raise ValueError("floor cannot be greater than total_floors.")
        if self.property_type == PropertyType.APARTMENT and self.total_floors is None:
            raise ValueError("Apartment listings require total_floors.")
        return self


class ListingUpdateRequest(BaseModel):
    category_public_id: str | None = None
    title: str | None = Field(default=None, min_length=5, max_length=255)
    description: str | None = Field(default=None, min_length=20, max_length=5000)
    purpose: ListingPurpose | None = None
    property_type: PropertyType | None = None
    price_amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    city: str | None = Field(default=None, min_length=2, max_length=120)
    district: str | None = Field(default=None, max_length=120)
    address_text: str | None = Field(default=None, min_length=5, max_length=255)
    map_label: str | None = Field(default=None, max_length=120)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90, max_digits=10, decimal_places=7)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180, max_digits=10, decimal_places=7)
    room_count: int | None = Field(default=None, ge=1, le=50)
    area_sqm: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    floor: int | None = Field(default=None, ge=0, le=200)
    total_floors: int | None = Field(default=None, ge=1, le=300)
    furnished: bool | None = None
    item_condition: ListingCondition | None = None
    attribute_values: list[ListingAttributeValueInput] | None = None

    @model_validator(mode="after")
    def validate_floor_range(self) -> "ListingUpdateRequest":
        if self.total_floors is not None and self.floor is not None and self.floor > self.total_floors:
            raise ValueError("floor cannot be greater than total_floors.")
        return self


class ListingMediaOrderRequest(BaseModel):
    media_public_ids: list[str] = Field(min_length=1)


class ModerationReviewRequest(BaseModel):
    action: Literal["publish", "hide", "archive", "reject", "send_to_review"]
    moderation_note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_rejection_note(self) -> "ModerationReviewRequest":
        if self.action in {"reject", "hide", "archive", "send_to_review"} and not self.moderation_note:
            raise ValueError("A moderation note is required for this moderation action.")
        return self


class ListingQueryParams(BaseModel):
    query: str | None = Field(default=None, max_length=120)
    category_public_id: str | None = None
    purpose: ListingPurpose | None = None
    property_type: PropertyType | None = None
    city: str | None = Field(default=None, max_length=120)
    district: str | None = Field(default=None, max_length=120)
    min_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    max_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    min_area_sqm: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    max_area_sqm: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    room_count: int | None = Field(default=None, ge=1, le=50)
    status: ListingStatus | None = None
    sort: ListingSortOption = "newest"
    promoted_first: bool = False
    reported_only: bool = False
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=50)

    @model_validator(mode="after")
    def validate_price_range(self) -> "ListingQueryParams":
        if self.min_price is not None and self.max_price is not None and self.min_price > self.max_price:
            raise ValueError("min_price cannot be greater than max_price.")
        if self.min_area_sqm is not None and self.max_area_sqm is not None and self.min_area_sqm > self.max_area_sqm:
            raise ValueError("min_area_sqm cannot be greater than max_area_sqm.")
        return self


class ListingCategorySummarySchema(BaseModel):
    public_id: str
    slug: str
    name: str


class ListingSellerSummarySchema(BaseModel):
    public_id: str
    username: str
    full_name: str
    profile_image_path: str | None = None


class ListingOwnerCardSchema(BaseModel):
    public_id: str
    username: str
    full_name: str
    bio: str | None = None
    profile_image_path: str | None = None
    created_at: datetime
    active_listing_count: int


class ListingMediaSchema(BaseModel):
    public_id: str
    media_type: MediaType
    asset_key: str
    mime_type: str
    file_size_bytes: int | None = None
    sort_order: int
    is_primary: bool


class ListingPromotionStateSchema(BaseModel):
    public_id: str
    package_public_id: str
    package_name: str
    status: str
    target_city: str | None = None
    target_category_public_id: str | None = None
    target_category_name: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    activated_at: datetime | None = None


class ListingAttributeValueSchema(BaseModel):
    attribute_code: str
    display_name: str
    data_type: CategoryAttributeType
    unit: str | None = None
    text_value: str | None = None
    numeric_value: Decimal | None = None
    boolean_value: bool | None = None
    option_value: str | None = None
    json_value: dict[str, Any] | list[Any] | None = None


class ListingSummarySchema(BaseModel):
    public_id: str
    title: str
    purpose: ListingPurpose
    property_type: PropertyType
    price_amount: Decimal
    currency_code: str
    item_condition: ListingCondition | None = None
    status: ListingStatus
    city: str
    district: str | None = None
    map_label: str | None = None
    latitude: Decimal
    longitude: Decimal
    room_count: int
    area_sqm: Decimal
    floor: int | None = None
    total_floors: int | None = None
    furnished: bool | None = None
    category: ListingCategorySummarySchema
    seller: ListingSellerSummarySchema
    primary_media: ListingMediaSchema | None = None
    is_promoted: bool = False
    promotion_state: ListingPromotionStateSchema | None = None
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ListingDetailSchema(ListingSummarySchema):
    description: str
    address_text: str
    moderation_note: str | None = None
    owner: ListingOwnerCardSchema
    media_items: list[ListingMediaSchema]
    attribute_values: list[ListingAttributeValueSchema]


class ListingStatusSchema(BaseModel):
    public_id: str
    status: ListingStatus
    moderation_note: str | None = None
    published_at: datetime | None = None


class PaginatedListingsResponseSchema(BaseModel):
    items: list[ListingSummarySchema]
    meta: PaginationMetaSchema


class FavoriteItemSchema(BaseModel):
    created_at: datetime
    listing_public_id: str | None = None
    listing: ListingSummarySchema | None = None
    is_available: bool
    unavailable_reason: str | None = None


class PaginatedFavoritesResponseSchema(BaseModel):
    items: list[FavoriteItemSchema]
    meta: PaginationMetaSchema


class FavoriteStatusSchema(BaseModel):
    listing_public_id: str
    is_favorited: bool
