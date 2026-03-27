from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.core.auth import utcnow
from app.core.config import Settings
from app.core.exceptions import AppError
from app.db.enums import ListingStatus, MediaType, RoleCode, UserStatus
from app.db.models import (
    Category,
    CategoryAttribute,
    CategoryTranslation,
    Listing,
    ListingAttributeValue,
    ListingMedia,
    Role,
    User,
    UserRole,
)
from app.modules.listings.schemas import (
    ListingAttributeValueInput,
    ListingAttributeValueSchema,
    ListingCategorySummarySchema,
    ListingCreateRequest,
    ListingDetailSchema,
    ListingMediaOrderRequest,
    ListingMediaSchema,
    ListingSellerSummarySchema,
    ListingStatusSchema,
    ListingSummarySchema,
    ListingUpdateRequest,
    ModerationReviewRequest,
)
from app.shared.audit import record_admin_audit_log
from app.shared.storage import delete_storage_key, save_upload

MAX_LISTING_MEDIA_COUNT = 10
MAX_LISTING_MEDIA_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_LISTING_MEDIA_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


def list_public_listings(
    session: Session,
    *,
    locale: str,
    category_public_id: str | None = None,
) -> list[ListingSummarySchema]:
    query = _listing_query().where(Listing.deleted_at.is_(None), Listing.status == ListingStatus.PUBLISHED)
    if category_public_id:
        category = session.execute(
            select(Category).where(Category.public_id == category_public_id, Category.deleted_at.is_(None))
        ).scalar_one_or_none()
        if category is None:
            raise AppError(status_code=404, code="category_not_found", message="Category was not found.")
        query = query.where(Listing.category_id == category.id)

    listings = session.execute(
        query
        .join(Listing.seller)
        .where(User.status == UserStatus.ACTIVE, User.deleted_at.is_(None))
        .order_by(Listing.published_at.desc(), Listing.created_at.desc())
    ).scalars().all()
    return [_build_listing_summary_schema(listing, locale=locale) for listing in listings]


def get_listing_detail(
    session: Session,
    *,
    listing_public_id: str,
    actor: User | None,
    locale: str,
) -> ListingDetailSchema:
    listing = _get_listing_or_404(session, listing_public_id=listing_public_id)
    if not _can_view_listing(session=session, listing=listing, actor=actor):
        raise AppError(status_code=404, code="listing_not_found", message="Listing was not found.")
    return _build_listing_detail_schema(listing, locale=locale)


def list_owner_listings(session: Session, *, owner: User, locale: str) -> list[ListingSummarySchema]:
    listings = session.execute(
        _listing_query()
        .where(Listing.seller_id == owner.id, Listing.deleted_at.is_(None))
        .order_by(Listing.created_at.desc())
    ).scalars().all()
    return [_build_listing_summary_schema(listing, locale=locale) for listing in listings]


def create_listing(
    session: Session,
    *,
    owner: User,
    payload: ListingCreateRequest,
    locale: str,
) -> ListingDetailSchema:
    _ensure_user_can_manage_listings(owner)
    category = _get_active_category_or_404(session, category_public_id=payload.category_public_id)

    listing = Listing(
        seller_id=owner.id,
        category_id=category.id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        price_amount=payload.price_amount,
        currency_code=payload.currency_code.upper(),
        item_condition=payload.item_condition,
        status=ListingStatus.DRAFT,
        city=payload.city.strip(),
    )
    session.add(listing)
    session.flush()

    _replace_attribute_values(
        listing=listing,
        category=category,
        attribute_inputs=payload.attribute_values,
    )
    session.flush()
    session.refresh(listing)
    return _build_listing_detail_schema(_get_listing_or_404(session, listing_public_id=listing.public_id), locale=locale)


def update_listing(
    session: Session,
    *,
    listing_public_id: str,
    actor: User,
    payload: ListingUpdateRequest,
    locale: str,
) -> ListingDetailSchema:
    listing = _get_listing_or_404(session, listing_public_id=listing_public_id)
    _ensure_listing_write_access(session, listing=listing, actor=actor)
    _ensure_user_can_manage_listings(actor)

    if listing.status == ListingStatus.SOLD:
        raise AppError(status_code=409, code="listing_sold", message="Sold listings cannot be edited.")

    updates = payload.model_dump(exclude_unset=True)
    category = listing.category
    category_changed = False

    if "category_public_id" in updates:
        category = _get_active_category_or_404(session, category_public_id=updates["category_public_id"])
        listing.category_id = category.id
        category_changed = True
    if "title" in updates:
        listing.title = updates["title"].strip()
    if "description" in updates:
        listing.description = updates["description"].strip()
    if "price_amount" in updates:
        listing.price_amount = updates["price_amount"]
    if "currency_code" in updates:
        listing.currency_code = updates["currency_code"].upper()
    if "item_condition" in updates:
        listing.item_condition = updates["item_condition"]
    if "city" in updates:
        listing.city = updates["city"].strip()

    if category_changed and "attribute_values" not in updates:
        raise AppError(
            status_code=400,
            code="attribute_values_required",
            message="Attribute values must be supplied when changing the listing category.",
        )

    if "attribute_values" in updates:
        _replace_attribute_values(
            listing=listing,
            category=category,
            attribute_inputs=updates["attribute_values"],
        )

    if listing.status in {ListingStatus.PUBLISHED, ListingStatus.INACTIVE}:
        _move_listing_to_pending_review(listing)

    session.flush()
    session.refresh(listing)
    return _build_listing_detail_schema(_get_listing_or_404(session, listing_public_id=listing.public_id), locale=locale)


def submit_listing_for_review(
    session: Session,
    *,
    listing_public_id: str,
    actor: User,
) -> ListingStatusSchema:
    listing = _get_listing_or_404(session, listing_public_id=listing_public_id)
    _ensure_listing_write_access(session, listing=listing, actor=actor)
    _ensure_user_can_manage_listings(actor)

    if listing.status not in {ListingStatus.DRAFT, ListingStatus.REJECTED, ListingStatus.INACTIVE, ListingStatus.ARCHIVED}:
        raise AppError(
            status_code=409,
            code="invalid_listing_transition",
            message="Listing cannot be submitted for review from its current status.",
        )

    _ensure_listing_has_media(listing)
    _validate_existing_attribute_values(listing=listing, category=listing.category)
    listing.status = ListingStatus.PENDING_REVIEW
    listing.moderation_note = None
    listing.published_at = None
    session.flush()
    return _build_listing_status_schema(listing)


def archive_listing(session: Session, *, listing_public_id: str, actor: User) -> ListingStatusSchema:
    listing = _get_listing_or_404(session, listing_public_id=listing_public_id)
    _ensure_listing_write_access(session, listing=listing, actor=actor)
    _ensure_user_can_manage_listings(actor)
    if listing.status not in {
        ListingStatus.DRAFT,
        ListingStatus.PENDING_REVIEW,
        ListingStatus.PUBLISHED,
        ListingStatus.REJECTED,
        ListingStatus.INACTIVE,
    }:
        raise AppError(
            status_code=409,
            code="invalid_listing_transition",
            message="Listing cannot be archived from its current status.",
        )
    listing.status = ListingStatus.ARCHIVED
    session.flush()
    return _build_listing_status_schema(listing)


def deactivate_listing(session: Session, *, listing_public_id: str, actor: User) -> ListingStatusSchema:
    listing = _get_listing_or_404(session, listing_public_id=listing_public_id)
    _ensure_listing_write_access(session, listing=listing, actor=actor)
    _ensure_user_can_manage_listings(actor)
    if listing.status != ListingStatus.PUBLISHED:
        raise AppError(
            status_code=409,
            code="invalid_listing_transition",
            message="Only published listings can be deactivated.",
        )
    listing.status = ListingStatus.INACTIVE
    session.flush()
    return _build_listing_status_schema(listing)


def reactivate_listing(session: Session, *, listing_public_id: str, actor: User) -> ListingStatusSchema:
    listing = _get_listing_or_404(session, listing_public_id=listing_public_id)
    _ensure_listing_write_access(session, listing=listing, actor=actor)
    _ensure_user_can_manage_listings(actor)
    if listing.status not in {ListingStatus.INACTIVE, ListingStatus.ARCHIVED}:
        raise AppError(
            status_code=409,
            code="invalid_listing_transition",
            message="Listing cannot be reactivated from its current status.",
        )

    _ensure_listing_has_media(listing)
    if listing.status == ListingStatus.INACTIVE:
        listing.status = ListingStatus.PUBLISHED
    else:
        listing.status = ListingStatus.PUBLISHED if listing.published_at else ListingStatus.DRAFT
    session.flush()
    return _build_listing_status_schema(listing)


def mark_listing_sold(session: Session, *, listing_public_id: str, actor: User) -> ListingStatusSchema:
    listing = _get_listing_or_404(session, listing_public_id=listing_public_id)
    _ensure_listing_write_access(session, listing=listing, actor=actor)
    _ensure_user_can_manage_listings(actor)
    if listing.status not in {ListingStatus.PUBLISHED, ListingStatus.INACTIVE}:
        raise AppError(
            status_code=409,
            code="invalid_listing_transition",
            message="Only active listings can be marked as sold.",
        )
    listing.status = ListingStatus.SOLD
    session.flush()
    return _build_listing_status_schema(listing)


def upload_listing_media(
    session: Session,
    *,
    settings: Settings,
    listing_public_id: str,
    actor: User,
    upload: UploadFile,
) -> ListingMediaSchema:
    listing = _get_listing_or_404(session, listing_public_id=listing_public_id)
    _ensure_listing_write_access(session, listing=listing, actor=actor)
    _ensure_user_can_manage_listings(actor)
    if listing.status == ListingStatus.SOLD:
        raise AppError(status_code=409, code="listing_sold", message="Sold listings cannot accept new media.")

    active_media = _active_media(listing)
    if len(active_media) >= MAX_LISTING_MEDIA_COUNT:
        raise AppError(
            status_code=400,
            code="listing_media_limit_reached",
            message="Listing has reached the maximum number of media items.",
            details={"max_media_count": MAX_LISTING_MEDIA_COUNT},
        )

    storage_key, file_size_bytes = save_upload(
        settings=settings,
        upload=upload,
        relative_dir=Path("listings") / listing.public_id,
        allowed_mime_types=ALLOWED_LISTING_MEDIA_MIME_TYPES,
        max_size_bytes=MAX_LISTING_MEDIA_SIZE_BYTES,
    )

    media = ListingMedia(
        listing_id=listing.id,
        media_type=MediaType.IMAGE,
        storage_key=storage_key,
        mime_type=upload.content_type,
        file_size_bytes=file_size_bytes,
        sort_order=(max([item.sort_order for item in active_media], default=-1) + 1),
        is_primary=not active_media,
    )
    session.add(media)
    _move_listing_to_pending_review_if_needed(listing)
    session.flush()
    return _build_listing_media_schema(media)


def replace_listing_media(
    session: Session,
    *,
    settings: Settings,
    listing_public_id: str,
    media_public_id: str,
    actor: User,
    upload: UploadFile,
) -> ListingMediaSchema:
    listing = _get_listing_or_404(session, listing_public_id=listing_public_id)
    _ensure_listing_write_access(session, listing=listing, actor=actor)
    _ensure_user_can_manage_listings(actor)
    if listing.status == ListingStatus.SOLD:
        raise AppError(status_code=409, code="listing_sold", message="Sold listings cannot modify media.")
    media = _get_listing_media_or_404(listing=listing, media_public_id=media_public_id)

    old_storage_key = media.storage_key
    storage_key, file_size_bytes = save_upload(
        settings=settings,
        upload=upload,
        relative_dir=Path("listings") / listing.public_id,
        allowed_mime_types=ALLOWED_LISTING_MEDIA_MIME_TYPES,
        max_size_bytes=MAX_LISTING_MEDIA_SIZE_BYTES,
    )
    media.storage_key = storage_key
    media.mime_type = upload.content_type
    media.file_size_bytes = file_size_bytes
    delete_storage_key(settings=settings, storage_key=old_storage_key)
    _move_listing_to_pending_review_if_needed(listing)
    session.flush()
    return _build_listing_media_schema(media)


def reorder_listing_media(
    session: Session,
    *,
    listing_public_id: str,
    actor: User,
    payload: ListingMediaOrderRequest,
) -> list[ListingMediaSchema]:
    listing = _get_listing_or_404(session, listing_public_id=listing_public_id)
    _ensure_listing_write_access(session, listing=listing, actor=actor)
    _ensure_user_can_manage_listings(actor)
    if listing.status == ListingStatus.SOLD:
        raise AppError(status_code=409, code="listing_sold", message="Sold listings cannot modify media.")

    active_media = _active_media(listing)
    current_ids = {media.public_id for media in active_media}
    requested_ids = set(payload.media_public_ids)
    if current_ids != requested_ids:
        raise AppError(
            status_code=400,
            code="invalid_media_order",
            message="Media ordering request must contain every active media item exactly once.",
        )

    media_by_public_id = {media.public_id: media for media in active_media}

    # First move all current sort orders out of the way so unique(listing_id, sort_order)
    # is never violated during reordering.
    offset = len(active_media) + 1000
    for media in active_media:
        media.sort_order = media.sort_order + offset
    session.flush()

    # Then assign the final desired order.
    for index, media_public_id in enumerate(payload.media_public_ids):
        media_by_public_id[media_public_id].sort_order = index

    # Keep exactly one primary item: the first item in the requested order.
    primary_public_id = payload.media_public_ids[0] if payload.media_public_ids else None
    for media in active_media:
        media.is_primary = media.public_id == primary_public_id

    session.flush()
    return [
        _build_listing_media_schema(media_by_public_id[media_public_id])
        for media_public_id in payload.media_public_ids
    ]

def set_primary_listing_media(
    session: Session,
    *,
    listing_public_id: str,
    media_public_id: str,
    actor: User,
) -> list[ListingMediaSchema]:
    listing = _get_listing_or_404(session, listing_public_id=listing_public_id)
    _ensure_listing_write_access(session, listing=listing, actor=actor)
    _ensure_user_can_manage_listings(actor)
    if listing.status == ListingStatus.SOLD:
        raise AppError(status_code=409, code="listing_sold", message="Sold listings cannot modify media.")

    active_media = _active_media(listing)
    selected_media = _get_listing_media_or_404(listing=listing, media_public_id=media_public_id)
    for media in active_media:
        media.is_primary = media.public_id == selected_media.public_id
    session.flush()
    return [_build_listing_media_schema(media) for media in sorted(active_media, key=lambda item: item.sort_order)]


def delete_listing_media(
    session: Session,
    *,
    settings: Settings,
    listing_public_id: str,
    media_public_id: str,
    actor: User,
) -> None:
    listing = _get_listing_or_404(session, listing_public_id=listing_public_id)
    _ensure_listing_write_access(session, listing=listing, actor=actor)
    _ensure_user_can_manage_listings(actor)
    if listing.status == ListingStatus.SOLD:
        raise AppError(status_code=409, code="listing_sold", message="Sold listings cannot modify media.")

    active_media = _active_media(listing)
    media = _get_listing_media_or_404(listing=listing, media_public_id=media_public_id)
    if listing.status in {ListingStatus.PUBLISHED, ListingStatus.PENDING_REVIEW, ListingStatus.INACTIVE} and len(active_media) == 1:
        raise AppError(
            status_code=409,
            code="listing_requires_media",
            message="This listing status requires at least one active media item.",
        )

    media.deleted_at = utcnow()
    delete_storage_key(settings=settings, storage_key=media.storage_key)
    remaining = [item for item in active_media if item.public_id != media.public_id]
    if media.is_primary and remaining:
        remaining.sort(key=lambda item: item.sort_order)
        remaining[0].is_primary = True
    _move_listing_to_pending_review_if_needed(listing)
    session.flush()


def list_moderation_queue(session: Session, *, locale: str) -> list[ListingSummarySchema]:
    listings = session.execute(
        _listing_query()
        .where(Listing.deleted_at.is_(None), Listing.status == ListingStatus.PENDING_REVIEW)
        .order_by(Listing.updated_at.asc(), Listing.created_at.asc())
    ).scalars().all()
    return [_build_listing_summary_schema(listing, locale=locale) for listing in listings]


def review_listing(
    session: Session,
    *,
    listing_public_id: str,
    actor: User,
    payload: ModerationReviewRequest,
    locale: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ListingDetailSchema:
    listing = _get_listing_or_404(session, listing_public_id=listing_public_id)
    if listing.status != ListingStatus.PENDING_REVIEW:
        raise AppError(
            status_code=409,
            code="invalid_listing_transition",
            message="Only pending-review listings can be moderated.",
        )

    before_json = _listing_snapshot(listing)
    if payload.action == "approve":
        _ensure_listing_has_media(listing)
        _validate_existing_attribute_values(listing=listing, category=listing.category)
        listing.status = ListingStatus.PUBLISHED
        listing.published_at = utcnow()
        listing.moderation_note = payload.moderation_note
    else:
        listing.status = ListingStatus.REJECTED
        listing.published_at = None
        listing.moderation_note = payload.moderation_note

    session.flush()
    record_admin_audit_log(
        session,
        actor=actor,
        action=f"listing.review.{payload.action}",
        entity_type="listing",
        entity_id=listing.public_id,
        description=f"{payload.action.title()}d listing '{listing.title}'.",
        ip_address=ip_address,
        user_agent=user_agent,
        before_json=before_json,
        after_json=_listing_snapshot(listing),
    )
    return _build_listing_detail_schema(_get_listing_or_404(session, listing_public_id=listing.public_id), locale=locale)


def _listing_query() -> Select[tuple[Listing]]:
    return select(Listing).options(
        selectinload(Listing.seller),
        selectinload(Listing.category).selectinload(Category.translations),
        selectinload(Listing.category).selectinload(Category.attributes).selectinload(CategoryAttribute.options),
        selectinload(Listing.media_items),
        selectinload(Listing.attribute_values).selectinload(ListingAttributeValue.category_attribute).selectinload(
            CategoryAttribute.options
        ),
    )


def _get_listing_or_404(session: Session, *, listing_public_id: str) -> Listing:
    listing = session.execute(
        _listing_query().where(Listing.public_id == listing_public_id, Listing.deleted_at.is_(None))
    ).scalar_one_or_none()
    if listing is None:
        raise AppError(status_code=404, code="listing_not_found", message="Listing was not found.")
    return listing


def _get_active_category_or_404(session: Session, *, category_public_id: str) -> Category:
    category = session.execute(
        select(Category)
        .options(
            selectinload(Category.translations),
            selectinload(Category.attributes).selectinload(CategoryAttribute.options),
        )
        .where(
            Category.public_id == category_public_id,
            Category.deleted_at.is_(None),
            Category.is_active.is_(True),
        )
    ).scalar_one_or_none()
    if category is None:
        raise AppError(status_code=404, code="category_not_found", message="Category was not found.")
    return category


def _ensure_user_can_manage_listings(user: User) -> None:
    if user.status == UserStatus.ACTIVE:
        return
    if user.status == UserStatus.SUSPENDED:
        raise AppError(status_code=403, code="account_suspended", message="Suspended users cannot manage listings.")
    if user.status == UserStatus.PENDING_VERIFICATION:
        raise AppError(
            status_code=403,
            code="account_pending_verification",
            message="Pending-verification users cannot manage listings yet.",
        )
    raise AppError(status_code=403, code="account_deleted", message="Deactivated users cannot manage listings.")


def _get_user_role_codes(session: Session, *, user_id: int) -> set[str]:
    return set(
        role.value
        for role in session.execute(
            select(Role.code).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id)
        ).scalars()
    )


def _is_admin(session: Session, *, user: User) -> bool:
    return RoleCode.ADMIN.value in _get_user_role_codes(session, user_id=user.id)


def _ensure_listing_write_access(session: Session, *, listing: Listing, actor: User) -> None:
    if listing.seller_id == actor.id:
        return
    if _is_admin(session, user=actor):
        return
    raise AppError(
        status_code=403,
        code="listing_forbidden",
        message="Only the listing owner or an admin can modify this listing.",
    )


def _replace_attribute_values(
    *,
    listing: Listing,
    category: Category,
    attribute_inputs: list[ListingAttributeValueInput],
) -> None:
    attribute_map = {attribute.code: attribute for attribute in category.attributes}
    provided_codes = [item.attribute_code for item in attribute_inputs]
    if len(provided_codes) != len(set(provided_codes)):
        raise AppError(
            status_code=400,
            code="duplicate_attribute_value",
            message="Each listing attribute can only be provided once.",
        )

    missing_required = [
        attribute.code
        for attribute in category.attributes
        if attribute.is_required and attribute.code not in provided_codes
    ]
    if missing_required:
        raise AppError(
            status_code=400,
            code="missing_required_attributes",
            message="Required category attributes are missing.",
            details={"attribute_codes": missing_required},
        )

    values: list[ListingAttributeValue] = []
    for attribute_input in attribute_inputs:
        attribute = attribute_map.get(attribute_input.attribute_code)
        if attribute is None:
            raise AppError(
                status_code=400,
                code="unknown_attribute",
                message="Listing contains an attribute that does not belong to the selected category.",
                details={"attribute_code": attribute_input.attribute_code},
            )
        values.append(_build_attribute_value(attribute=attribute, attribute_input=attribute_input))
    listing.attribute_values = values


def _build_attribute_value(
    *,
    attribute: CategoryAttribute,
    attribute_input: ListingAttributeValueInput,
) -> ListingAttributeValue:
    if attribute.data_type.value == "text" and attribute_input.text_value is None:
        raise AppError(status_code=400, code="invalid_attribute_value", message="Text attribute requires text_value.")
    if attribute.data_type.value == "number" and attribute_input.numeric_value is None:
        raise AppError(status_code=400, code="invalid_attribute_value", message="Number attribute requires numeric_value.")
    if attribute.data_type.value == "boolean" and attribute_input.boolean_value is None:
        raise AppError(
            status_code=400,
            code="invalid_attribute_value",
            message="Boolean attribute requires boolean_value.",
        )
    if attribute.data_type.value == "json" and attribute_input.json_value is None:
        raise AppError(status_code=400, code="invalid_attribute_value", message="JSON attribute requires json_value.")
    if attribute.data_type.value == "select":
        if attribute_input.option_value is None:
            raise AppError(
                status_code=400,
                code="invalid_attribute_value",
                message="Select attribute requires option_value.",
            )
        valid_options = {option.option_value for option in attribute.options}
        if attribute_input.option_value not in valid_options:
            raise AppError(
                status_code=400,
                code="invalid_attribute_option",
                message="Listing attribute option is not valid for this category.",
                details={"attribute_code": attribute.code, "option_value": attribute_input.option_value},
            )

    return ListingAttributeValue(
        category_attribute_id=attribute.id,
        text_value=attribute_input.text_value,
        numeric_value=attribute_input.numeric_value,
        boolean_value=attribute_input.boolean_value,
        option_value=attribute_input.option_value,
        json_value=attribute_input.json_value,
    )


def _validate_existing_attribute_values(*, listing: Listing, category: Category) -> None:
    required_codes = {attribute.code for attribute in category.attributes if attribute.is_required}
    existing_codes = {
        value.category_attribute.code
        for value in listing.attribute_values
        if value.category_attribute is not None
    }
    missing_codes = sorted(required_codes - existing_codes)
    if missing_codes:
        raise AppError(
            status_code=400,
            code="missing_required_attributes",
            message="Listing is missing required attributes for moderation.",
            details={"attribute_codes": missing_codes},
        )


def _move_listing_to_pending_review(listing: Listing) -> None:
    listing.status = ListingStatus.PENDING_REVIEW
    listing.published_at = None
    listing.moderation_note = None


def _move_listing_to_pending_review_if_needed(listing: Listing) -> None:
    if listing.status in {ListingStatus.PUBLISHED, ListingStatus.INACTIVE}:
        _move_listing_to_pending_review(listing)


def _ensure_listing_has_media(listing: Listing) -> None:
    if not _active_media(listing):
        raise AppError(
            status_code=400,
            code="listing_requires_media",
            message="Listing must have at least one active media item.",
        )


def _get_listing_media_or_404(*, listing: Listing, media_public_id: str) -> ListingMedia:
    for media in _active_media(listing):
        if media.public_id == media_public_id:
            return media
    raise AppError(status_code=404, code="listing_media_not_found", message="Listing media was not found.")


def _active_media(listing: Listing) -> list[ListingMedia]:
    return [media for media in listing.media_items if media.deleted_at is None]


def _resolved_translation(category: Category, *, locale: str) -> CategoryTranslation | None:
    by_locale = {translation.locale: translation for translation in category.translations}
    return by_locale.get(locale) or by_locale.get("en") or next(iter(category.translations), None)


def _can_view_listing(*, session: Session, listing: Listing, actor: User | None) -> bool:
    if listing.deleted_at is not None:
        return False
    if actor is not None and actor.id == listing.seller_id:
        return True
    if actor is not None and _is_admin(session, user=actor):
        return True
    return (
        listing.status == ListingStatus.PUBLISHED
        and listing.seller.deleted_at is None
        and listing.seller.status == UserStatus.ACTIVE
    )


def _build_listing_media_schema(media: ListingMedia) -> ListingMediaSchema:
    return ListingMediaSchema(
        public_id=media.public_id,
        media_type=media.media_type,
        asset_key=media.storage_key,
        mime_type=media.mime_type,
        file_size_bytes=media.file_size_bytes,
        sort_order=media.sort_order,
        is_primary=media.is_primary,
    )


def _build_listing_category_schema(category: Category, *, locale: str) -> ListingCategorySummarySchema:
    translation = _resolved_translation(category, locale=locale)
    return ListingCategorySummarySchema(
        public_id=category.public_id,
        slug=category.slug,
        name=translation.name if translation else category.internal_name,
    )


def _build_listing_seller_schema(seller: User) -> ListingSellerSummarySchema:
    return ListingSellerSummarySchema(
        public_id=seller.public_id,
        username=seller.username,
        full_name=seller.full_name,
    )


def _primary_media(listing: Listing) -> ListingMedia | None:
    media_items = sorted(_active_media(listing), key=lambda item: (0 if item.is_primary else 1, item.sort_order, item.id))
    return media_items[0] if media_items else None


def _build_listing_summary_schema(listing: Listing, *, locale: str) -> ListingSummarySchema:
    primary_media = _primary_media(listing)
    return ListingSummarySchema(
        public_id=listing.public_id,
        title=listing.title,
        price_amount=listing.price_amount,
        currency_code=listing.currency_code,
        item_condition=listing.item_condition,
        status=listing.status,
        city=listing.city,
        category=_build_listing_category_schema(listing.category, locale=locale),
        seller=_build_listing_seller_schema(listing.seller),
        primary_media=_build_listing_media_schema(primary_media) if primary_media else None,
        published_at=listing.published_at,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
    )


def _build_listing_detail_schema(listing: Listing, *, locale: str) -> ListingDetailSchema:
    summary = _build_listing_summary_schema(listing, locale=locale)
    return ListingDetailSchema(
        **summary.model_dump(),
        description=listing.description,
        moderation_note=listing.moderation_note,
        media_items=[
            _build_listing_media_schema(media)
            for media in sorted(_active_media(listing), key=lambda item: (item.sort_order, item.id))
        ],
        attribute_values=[
            ListingAttributeValueSchema(
                attribute_code=value.category_attribute.code,
                display_name=value.category_attribute.display_name,
                data_type=value.category_attribute.data_type,
                unit=value.category_attribute.unit,
                text_value=value.text_value,
                numeric_value=value.numeric_value,
                boolean_value=value.boolean_value,
                option_value=value.option_value,
                json_value=value.json_value,
            )
            for value in sorted(listing.attribute_values, key=lambda item: item.category_attribute.code)
        ],
    )


def _build_listing_status_schema(listing: Listing) -> ListingStatusSchema:
    return ListingStatusSchema(
        public_id=listing.public_id,
        status=listing.status,
        moderation_note=listing.moderation_note,
        published_at=listing.published_at,
    )


def _listing_snapshot(listing: Listing) -> dict:
    return {
        "public_id": listing.public_id,
        "status": listing.status.value,
        "title": listing.title,
        "category_public_id": listing.category.public_id,
        "price_amount": str(Decimal(listing.price_amount)),
        "media_count": len(_active_media(listing)),
    }
