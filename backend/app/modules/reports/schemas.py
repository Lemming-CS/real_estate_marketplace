from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.db.enums import ListingStatus, ReportStatus, UserStatus
from app.shared.schemas import PaginationMetaSchema


class ReportCreateRequest(BaseModel):
    listing_public_id: str | None = None
    reported_user_public_id: str | None = None
    conversation_public_id: str | None = None
    reason_code: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_target(self) -> "ReportCreateRequest":
        if not self.listing_public_id and not self.reported_user_public_id and not self.conversation_public_id:
            raise ValueError("A listing, conversation, or user target is required.")
        return self


class ReportActionRequest(BaseModel):
    action: Literal["in_review", "resolve", "dismiss"]
    resolution_note: str | None = Field(default=None, max_length=2000)
    listing_action: Literal["hide", "archive"] | None = None
    user_action: Literal["suspend"] | None = None

    @model_validator(mode="after")
    def validate_resolution_note(self) -> "ReportActionRequest":
        if self.action in {"resolve", "dismiss"} and not self.resolution_note:
            raise ValueError("A resolution note is required for resolve or dismiss actions.")
        if (self.listing_action or self.user_action) and not self.resolution_note:
            raise ValueError("A moderation note is required when taking listing or user action from a report.")
        return self


class ReportSchema(BaseModel):
    public_id: str
    reporter_user_public_id: str
    reporter_username: str
    reported_user_public_id: str | None = None
    reported_username: str | None = None
    conversation_public_id: str | None = None
    listing_public_id: str | None = None
    listing_title: str | None = None
    listing_status: ListingStatus | None = None
    listing_moderation_note: str | None = None
    reason_code: str
    description: str | None = None
    reported_user_status: UserStatus | None = None
    status: ReportStatus
    resolution_note: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PaginatedReportsResponseSchema(BaseModel):
    items: list[ReportSchema]
    meta: PaginationMetaSchema
