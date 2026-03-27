from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.db.enums import ListingStatus, UserStatus

LocaleCode = Literal["en", "ru"]


class CurrentUserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: str
    email: EmailStr
    username: str
    full_name: str
    phone: str | None = None
    bio: str | None = None
    locale: str
    status: UserStatus
    profile_image_path: str | None = None
    profile_image_mime_type: str | None = None
    roles: list[str]


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    bio: str | None = Field(default=None, max_length=1000)
    locale: LocaleCode | None = None


class ProfileImageResponse(BaseModel):
    profile_image_path: str
    profile_image_mime_type: str


class PublicUserProfileSchema(BaseModel):
    public_id: str
    username: str
    full_name: str
    bio: str | None = None
    profile_image_path: str | None = None
    status: UserStatus
    published_listing_count: int
    created_at: datetime


class OwnerListingSchema(BaseModel):
    public_id: str
    title: str
    status: ListingStatus
    price_amount: Decimal
    currency_code: str
    city: str
    published_at: datetime | None = None
    created_at: datetime

