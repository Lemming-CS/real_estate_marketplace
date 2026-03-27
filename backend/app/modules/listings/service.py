from __future__ import annotations

from math import ceil
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import Select, case, exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.auth import utcnow
from app.core.config import Settings
from app.core.exceptions import AppError
from app.db.enums import ListingStatus, MediaType, PromotionStatus, ReportStatus, RoleCode, UserStatus
from app.db.models import (
    Category,
    CategoryAttribute,
    CategoryTranslation,
    Favorite,
    Listing,
    ListingAttributeValue,
    ListingMedia,
    Promotion,
    PromotionPackage,
    Report,
    Role,
    User,
    UserRole,
)
from app.modules.listings.schemas import (
    FavoriteItemSchema,
    FavoriteStatusSchema,
    ListingAttributeValueInput,
    ListingAttributeValueSchema,
    ListingCategorySummarySchema,
    ListingCreateRequest,
    ListingDetailSchema,
    ListingMediaOrderRequest,
    ListingMediaSchema,
    ListingOwnerCardSchema,
    ListingPromotionStateSchema,
    ListingQueryParams,
    ListingSellerSummarySchema,
    ListingStatusSchema,
    ListingSummarySchema,
    ListingUpdateRequest,
    ModerationReviewRequest,
    PaginatedFavoritesResponseSchema,
    PaginatedListingsResponseSchema,
)
from app.modules.notifications.service import notify_listing_reviewed
from app.shared.audit import record_admin_audit_log
from app.shared.schemas import PaginationMetaSchema
from app.shared.storage import delete_storage_key, save_upload

MAX_LISTING_MEDIA_COUNT = 20
MAX_LISTING_IMAGE_SIZE_BYTES = 10 * 1024 * 1024
MAX_LISTING_VIDEO_SIZE_BYTES = 50 * 1024 * 1024
ALLOWED_LISTING_MEDIA_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "video/mp4"}


def list_public_listings(
    session: Session,
    *,
    locale: str,
    filters: ListingQueryParams,
) -> PaginatedListingsResponseSchema:
    base_query = (
        select(Listing.id)
        .join(Listing.seller)
        .where(
            Listing.deleted_at.is_(None),
            Listing.status == ListingStatus.PUBLISHED,
            User.deleted_at.is_(None),
            User.status == UserStatus.ACTIVE,
        )
    )
    base_query = _apply_common_listing_filters(session, query=base_query, filters=filters)
    return _paginate_listings(session, base_query=base_query, locale=locale, filters=filters)


def list_owner_discovery_listings(
    session: Session,
    *,
    owner: User,
    locale: str,
    filters: ListingQueryParams,
) -> PaginatedListingsResponseSchema:
    base_query = select(Listing.id).where(
        Listing.seller_id == owner.id,
        Listing.deleted_at.is_(None),
    )
    base_query = _apply_common_listing_filters(session, query=base_query, filters=filters, include_status=True)
    return _paginate_listings(session, base_query=base_query, locale=locale, filters=filters)


def list_public_user_listings(
    session: Session,
    *,
    owner_public_id: str,
    locale: str,
    filters: ListingQueryParams,
) -> PaginatedListingsResponseSchema:
    owner = _get_public_owner_or_404(session, user_public_id=owner_public_id)
    base_query = (
        select(Listing.id)
        .join(Listing.seller)
        .where(
            Listing.seller_id == owner.id,
            Listing.deleted_at.is_(None),
            Listing.status == ListingStatus.PUBLISHED,
            User.deleted_at.is_(None),
            User.status == UserStatus.ACTIVE,
        )
    )
    base_query = _apply_common_listing_filters(session, query=base_query, filters=filters)
    return _paginate_listings(session, base_query=base_query, locale=locale, filters=filters)


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
    return _build_listing_detail_schema(
        session,
        listing=listing,
        locale=locale,
        is_promoted=_active_promotion_map(session, [listing.id]).get(listing.id, False),
        promotion_state=_active_promotion_state_map(session, [listing.id], locale=locale).get(listing.id),
        include_exact_address=_can_view_exact_listing_location(session=session, listing=listing, actor=actor),
    )


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
        purpose=payload.purpose,
        property_type=payload.property_type,
        price_amount=payload.price_amount,
        currency_code=payload.currency_code.upper(),
        item_condition=payload.item_condition,
        status=ListingStatus.DRAFT,
        city=payload.city.strip(),
        district=payload.district.strip() if payload.district else None,
        address_text=payload.address_text.strip(),
        map_label=payload.map_label.strip() if payload.map_label else None,
        latitude=payload.latitude,
        longitude=payload.longitude,
        room_count=payload.room_count,
        area_sqm=payload.area_sqm,
        floor=payload.floor,
        total_floors=payload.total_floors,
        furnished=payload.furnished,
    )
    session.add(listing)
    session.flush()

    _replace_attribute_values(
        listing=listing,
        category=category,
        attribute_inputs=payload.attribute_values,
    )
    session.flush()
    return _build_listing_detail_schema(
        session,
        listing=_get_listing_or_404(session, listing_public_id=listing.public_id),
        locale=locale,
        is_promoted=False,
        promotion_state=None,
        include_exact_address=True,
    )


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
    if "purpose" in updates:
        listing.purpose = updates["purpose"]
    if "property_type" in updates:
        listing.property_type = updates["property_type"]
    if "price_amount" in updates:
        listing.price_amount = updates["price_amount"]
    if "currency_code" in updates:
        listing.currency_code = updates["currency_code"].upper()
    if "item_condition" in updates:
        listing.item_condition = updates["item_condition"]
    if "city" in updates:
        listing.city = updates["city"].strip()
    if "district" in updates:
        listing.district = updates["district"].strip() if updates["district"] else None
    if "address_text" in updates:
        listing.address_text = updates["address_text"].strip()
    if "map_label" in updates:
        listing.map_label = updates["map_label"].strip() if updates["map_label"] else None
    if "latitude" in updates:
        listing.latitude = updates["latitude"]
    if "longitude" in updates:
        listing.longitude = updates["longitude"]
    if "room_count" in updates:
        listing.room_count = updates["room_count"]
    if "area_sqm" in updates:
        listing.area_sqm = updates["area_sqm"]
    if "floor" in updates:
        listing.floor = updates["floor"]
    if "total_floors" in updates:
        listing.total_floors = updates["total_floors"]
    if "furnished" in updates:
        listing.furnished = updates["furnished"]

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

    session.flush()
    return _build_listing_detail_schema(
        session,
        listing=_get_listing_or_404(session, listing_public_id=listing.public_id),
        locale=locale,
        is_promoted=_active_promotion_map(session, [listing.id]).get(listing.id, False),
        promotion_state=_active_promotion_state_map(session, [listing.id], locale=locale).get(listing.id),
        include_exact_address=True,
    )


def submit_listing_for_review(
    session: Session,
    *,
    listing_public_id: str,
    actor: User,
) -> ListingStatusSchema:
    return publish_listing(session, listing_public_id=listing_public_id, actor=actor)


def publish_listing(
    session: Session,
    *,
    listing_public_id: str,
    actor: User,
) -> ListingStatusSchema:
    listing = _get_listing_or_404(session, listing_public_id=listing_public_id)
    _ensure_listing_write_access(session, listing=listing, actor=actor)
    _ensure_user_can_manage_listings(actor)

    if listing.status == ListingStatus.SOLD:
        raise AppError(
            status_code=409,
            code="invalid_listing_transition",
            message="Sold listings cannot be published again.",
        )

    _ensure_listing_publishable(listing)
    listing.status = ListingStatus.PUBLISHED
    listing.moderation_note = None
    listing.published_at = utcnow()
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

    _ensure_listing_publishable(listing)
    if listing.status == ListingStatus.INACTIVE:
        listing.status = ListingStatus.PUBLISHED
    else:
        listing.status = ListingStatus.PUBLISHED
    if listing.published_at is None:
        listing.published_at = utcnow()
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

    media_type, max_size_bytes = _listing_media_upload_rules(upload)
    storage_key, file_size_bytes = save_upload(
        settings=settings,
        upload=upload,
        relative_dir=Path("listings") / listing.public_id,
        allowed_mime_types=ALLOWED_LISTING_MEDIA_MIME_TYPES,
        max_size_bytes=max_size_bytes,
    )

    existing_images = [item for item in active_media if item.media_type == MediaType.IMAGE]
    media = ListingMedia(
        listing_id=listing.id,
        media_type=media_type,
        storage_key=storage_key,
        mime_type=upload.content_type,
        file_size_bytes=file_size_bytes,
        sort_order=(max([item.sort_order for item in active_media], default=-1) + 1),
        is_primary=media_type == MediaType.IMAGE and not existing_images,
    )
    session.add(media)
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

    media_type, max_size_bytes = _listing_media_upload_rules(upload)
    if media.is_primary and media_type != MediaType.IMAGE:
        raise AppError(
            status_code=400,
            code="primary_media_must_be_image",
            message="The primary property media must be an image.",
        )

    old_storage_key = media.storage_key
    storage_key, file_size_bytes = save_upload(
        settings=settings,
        upload=upload,
        relative_dir=Path("listings") / listing.public_id,
        allowed_mime_types=ALLOWED_LISTING_MEDIA_MIME_TYPES,
        max_size_bytes=max_size_bytes,
    )
    media.storage_key = storage_key
    media.media_type = media_type
    media.mime_type = upload.content_type
    media.file_size_bytes = file_size_bytes
    delete_storage_key(settings=settings, storage_key=old_storage_key)
    if media.is_primary and media_type == MediaType.IMAGE:
        _ensure_single_primary_image(listing)
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
    offset = len(active_media) + 1000
    for media in active_media:
        media.sort_order = media.sort_order + offset
    session.flush()

    for index, media_public_id in enumerate(payload.media_public_ids):
        media_by_public_id[media_public_id].sort_order = index

    primary_public_id = next(
        (media_public_id for media_public_id in payload.media_public_ids if media_by_public_id[media_public_id].media_type == MediaType.IMAGE),
        None,
    )
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
    if selected_media.media_type != MediaType.IMAGE:
        raise AppError(
            status_code=400,
            code="primary_media_must_be_image",
            message="Only image media can be selected as the primary property photo.",
        )
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
    if media.media_type == MediaType.IMAGE and listing.status in {ListingStatus.PUBLISHED, ListingStatus.PENDING_REVIEW, ListingStatus.INACTIVE}:
        remaining_images = [
            item for item in active_media if item.public_id != media.public_id and item.media_type == MediaType.IMAGE
        ]
        if not remaining_images:
            raise AppError(
                status_code=409,
                code="listing_requires_primary_image",
                message="Published property listings must keep at least one image.",
            )

    media.deleted_at = utcnow()
    delete_storage_key(settings=settings, storage_key=media.storage_key)
    remaining = [item for item in active_media if item.public_id != media.public_id]
    if media.is_primary:
        next_primary = next((item for item in sorted(remaining, key=lambda item: item.sort_order) if item.media_type == MediaType.IMAGE), None)
        if next_primary is not None:
            next_primary.is_primary = True
    session.flush()


def list_moderation_queue(
    session: Session,
    *,
    locale: str,
    filters: ListingQueryParams,
) -> PaginatedListingsResponseSchema:
    effective_filters = filters.model_copy()
    base_query = select(Listing.id).where(Listing.deleted_at.is_(None))
    base_query = _apply_common_listing_filters(
        session,
        query=base_query,
        filters=effective_filters,
        include_status=True,
    )
    return _paginate_listings(session, base_query=base_query, locale=locale, filters=effective_filters)


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
    if listing.status == ListingStatus.SOLD and payload.action != "archive":
        raise AppError(
            status_code=409,
            code="invalid_listing_transition",
            message="Sold listings can only be archived by moderation.",
        )
    before_json = _listing_snapshot(listing)
    if payload.action == "publish":
        _ensure_listing_publishable(listing)
        listing.status = ListingStatus.PUBLISHED
        listing.moderation_note = payload.moderation_note.strip() if payload.moderation_note else None
        if listing.published_at is None:
            listing.published_at = utcnow()
        notify_listing_reviewed(
            session,
            user=listing.seller,
            listing_public_id=listing.public_id,
            listing_title=listing.title,
            approved=True,
            moderation_note=payload.moderation_note,
        )
    elif payload.action == "hide":
        listing.status = ListingStatus.INACTIVE
        listing.moderation_note = payload.moderation_note.strip() if payload.moderation_note else None
    elif payload.action == "archive":
        listing.status = ListingStatus.ARCHIVED
        listing.moderation_note = payload.moderation_note.strip() if payload.moderation_note else None
    elif payload.action == "send_to_review":
        listing.status = ListingStatus.PENDING_REVIEW
        listing.moderation_note = payload.moderation_note.strip() if payload.moderation_note else None
    else:
        listing.status = ListingStatus.REJECTED
        listing.published_at = None
        listing.moderation_note = payload.moderation_note.strip() if payload.moderation_note else None
        notify_listing_reviewed(
            session,
            user=listing.seller,
            listing_public_id=listing.public_id,
            listing_title=listing.title,
            approved=False,
            moderation_note=payload.moderation_note,
        )

    session.flush()
    record_admin_audit_log(
        session,
        actor=actor,
        action=f"listing.moderation.{payload.action}",
        entity_type="listing",
        entity_id=listing.public_id,
        description=f"{payload.action.replace('_', ' ').title()} listing '{listing.title}'.",
        ip_address=ip_address,
        user_agent=user_agent,
        before_json=before_json,
        after_json=_listing_snapshot(listing),
    )
    return _build_listing_detail_schema(
        session,
        listing=_get_listing_or_404(session, listing_public_id=listing.public_id),
        locale=locale,
        is_promoted=_active_promotion_map(session, [listing.id]).get(listing.id, False),
        promotion_state=_active_promotion_state_map(session, [listing.id], locale=locale).get(listing.id),
        include_exact_address=True,
    )


def add_favorite(session: Session, *, user: User, listing_public_id: str) -> FavoriteStatusSchema:
    listing = _get_listing_or_404(session, listing_public_id=listing_public_id)
    listing_id = listing.id
    listing_public_id_value = listing.public_id
    if listing.seller_id == user.id:
        raise AppError(status_code=400, code="favorite_own_listing", message="You cannot favorite your own listing.")
    if not _is_publicly_available(listing):
        raise AppError(
            status_code=409,
            code="listing_not_favoritable",
            message="Only publicly visible listings can be added to favorites.",
        )

    existing = session.execute(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.listing_id == listing_id)
    ).scalar_one_or_none()
    if existing is None:
        session.add(Favorite(user_id=user.id, listing_id=listing_id))
        try:
            session.flush()
        except IntegrityError as exc:
            session.rollback()
            existing = session.execute(
                select(Favorite).where(Favorite.user_id == user.id, Favorite.listing_id == listing_id)
            ).scalar_one_or_none()
            if existing is None:
                raise AppError(
                    status_code=500,
                    code="favorite_create_failed",
                    message="Favorite could not be created.",
                ) from exc
    return FavoriteStatusSchema(listing_public_id=listing_public_id_value, is_favorited=True)


def remove_favorite(session: Session, *, user: User, listing_public_id: str) -> FavoriteStatusSchema:
    listing = session.execute(
        select(Listing).where(Listing.public_id == listing_public_id)
    ).scalar_one_or_none()
    listing_id = listing.id if listing is not None else None
    if listing_id is not None:
        favorite = session.execute(
            select(Favorite).where(Favorite.user_id == user.id, Favorite.listing_id == listing_id)
        ).scalar_one_or_none()
        if favorite is not None:
            session.delete(favorite)
            session.flush()
    return FavoriteStatusSchema(listing_public_id=listing_public_id, is_favorited=False)


def list_favorites(
    session: Session,
    *,
    user: User,
    locale: str,
    page: int,
    page_size: int,
) -> PaginatedFavoritesResponseSchema:
    base_query = select(Favorite).where(Favorite.user_id == user.id).order_by(Favorite.created_at.desc(), Favorite.id.desc())
    total_items = session.execute(select(func.count()).select_from(base_query.subquery())).scalar_one()
    favorites = session.execute(
        base_query.offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    listing_ids = [favorite.listing_id for favorite in favorites]
    listings = (
        session.execute(_listing_query().where(Listing.id.in_(listing_ids))).scalars().all()
        if listing_ids
        else []
    )
    listings_by_id = {listing.id: listing for listing in listings}
    promoted_map = _active_promotion_map(session, listing_ids)

    items = []
    for favorite in favorites:
        listing = listings_by_id.get(favorite.listing_id)
        unavailable_reason = _favorite_unavailable_reason(listing)
        items.append(
            FavoriteItemSchema(
                created_at=favorite.created_at,
                listing_public_id=listing.public_id if listing else None,
                listing=(
                    _build_listing_summary_schema(
                        listing,
                        locale=locale,
                        is_promoted=promoted_map.get(listing.id, False),
                    )
                    if listing
                    else None
                ),
                is_available=unavailable_reason is None,
                unavailable_reason=unavailable_reason,
            )
        )

    return PaginatedFavoritesResponseSchema(
        items=items,
        meta=_pagination_meta(page=page, page_size=page_size, total_items=total_items),
    )


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


def _get_public_owner_or_404(session: Session, *, user_public_id: str) -> User:
    user = session.execute(
        select(User).where(
            User.public_id == user_public_id,
            User.deleted_at.is_(None),
            User.status == UserStatus.ACTIVE,
        )
    ).scalar_one_or_none()
    if user is None:
        raise AppError(status_code=404, code="user_not_found", message="User was not found.")
    return user


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


def _ensure_listing_publishable(listing: Listing) -> None:
    _ensure_listing_has_media(listing)
    _validate_existing_attribute_values(listing=listing, category=listing.category)
    _validate_listing_real_estate_shape(listing)


def _ensure_listing_has_media(listing: Listing) -> None:
    media_items = _active_media(listing)
    if not media_items:
        raise AppError(
            status_code=400,
            code="listing_requires_media",
            message="Listing must have at least one active media item.",
        )
    if not any(media.media_type == MediaType.IMAGE for media in media_items):
        raise AppError(
            status_code=400,
            code="listing_requires_primary_image",
            message="Property listings require at least one image.",
        )


def _validate_listing_real_estate_shape(listing: Listing) -> None:
    if listing.property_type.value == "apartment" and listing.total_floors is None:
        raise AppError(
            status_code=400,
            code="total_floors_required",
            message="Apartment listings require total_floors.",
        )
    if listing.total_floors is not None and listing.floor is not None and listing.floor > listing.total_floors:
        raise AppError(
            status_code=400,
            code="invalid_floor_range",
            message="floor cannot be greater than total_floors.",
        )


def _listing_media_upload_rules(upload: UploadFile) -> tuple[MediaType, int]:
    if upload.content_type == "video/mp4":
        return MediaType.VIDEO, MAX_LISTING_VIDEO_SIZE_BYTES
    return MediaType.IMAGE, MAX_LISTING_IMAGE_SIZE_BYTES


def _ensure_single_primary_image(listing: Listing) -> None:
    active_media = sorted(_active_media(listing), key=lambda item: (item.sort_order, item.id))
    primary_image = next((item for item in active_media if item.media_type == MediaType.IMAGE and item.is_primary), None)
    if primary_image is not None:
        for media in active_media:
            media.is_primary = media.public_id == primary_image.public_id
        return
    fallback = next((item for item in active_media if item.media_type == MediaType.IMAGE), None)
    for media in active_media:
        media.is_primary = fallback is not None and media.public_id == fallback.public_id


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
    return _is_publicly_available(listing)


def _can_view_exact_listing_location(*, session: Session, listing: Listing, actor: User | None) -> bool:
    if actor is None:
        return False
    if actor.id == listing.seller_id:
        return True
    return _is_admin(session, user=actor)


def _is_publicly_available(listing: Listing) -> bool:
    return (
        listing.deleted_at is None
        and listing.status == ListingStatus.PUBLISHED
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
        profile_image_path=seller.profile_image_path,
    )


def _build_owner_card_schema(session: Session, *, seller: User) -> ListingOwnerCardSchema:
    active_listing_count = session.execute(
        select(func.count(Listing.id)).where(
            Listing.seller_id == seller.id,
            Listing.status == ListingStatus.PUBLISHED,
            Listing.deleted_at.is_(None),
        )
    ).scalar_one()
    return ListingOwnerCardSchema(
        public_id=seller.public_id,
        username=seller.username,
        full_name=seller.full_name,
        bio=seller.bio,
        profile_image_path=seller.profile_image_path,
        created_at=seller.created_at,
        active_listing_count=active_listing_count,
    )


def _primary_media(listing: Listing) -> ListingMedia | None:
    media_items = sorted(_active_media(listing), key=lambda item: (0 if item.is_primary else 1, item.sort_order, item.id))
    return media_items[0] if media_items else None


def _build_listing_summary_schema(
    listing: Listing,
    *,
    locale: str,
    is_promoted: bool,
    promotion_state: ListingPromotionStateSchema | None = None,
) -> ListingSummarySchema:
    primary_media = _primary_media(listing)
    return ListingSummarySchema(
        public_id=listing.public_id,
        title=listing.title,
        purpose=listing.purpose,
        property_type=listing.property_type,
        price_amount=listing.price_amount,
        currency_code=listing.currency_code,
        item_condition=listing.item_condition,
        status=listing.status,
        city=listing.city,
        district=listing.district,
        map_label=listing.map_label,
        latitude=listing.latitude,
        longitude=listing.longitude,
        room_count=listing.room_count,
        area_sqm=listing.area_sqm,
        floor=listing.floor,
        total_floors=listing.total_floors,
        furnished=listing.furnished,
        category=_build_listing_category_schema(listing.category, locale=locale),
        seller=_build_listing_seller_schema(listing.seller),
        primary_media=_build_listing_media_schema(primary_media) if primary_media else None,
        is_promoted=is_promoted,
        promotion_state=promotion_state,
        published_at=listing.published_at,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
    )


def _build_listing_detail_schema(
    session: Session,
    *,
    listing: Listing,
    locale: str,
    is_promoted: bool,
    promotion_state: ListingPromotionStateSchema | None = None,
    include_exact_address: bool = False,
) -> ListingDetailSchema:
    summary = _build_listing_summary_schema(
        listing,
        locale=locale,
        is_promoted=is_promoted,
        promotion_state=promotion_state,
    )
    return ListingDetailSchema(
        **summary.model_dump(),
        description=listing.description,
        address_text=listing.address_text if include_exact_address else (listing.map_label or ", ".join([part for part in [listing.district, listing.city] if part])),
        moderation_note=listing.moderation_note,
        owner=_build_owner_card_schema(session, seller=listing.seller),
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


def _apply_common_listing_filters(
    session: Session,
    *,
    query: Select,
    filters: ListingQueryParams,
    include_status: bool = False,
) -> Select:
    if filters.query:
        term = f"%{filters.query.strip()}%"
        query = query.where(or_(Listing.title.ilike(term), Listing.description.ilike(term)))
    if filters.category_public_id:
        category = session.execute(
            select(Category).where(Category.public_id == filters.category_public_id, Category.deleted_at.is_(None))
        ).scalar_one_or_none()
        if category is None:
            raise AppError(status_code=404, code="category_not_found", message="Category was not found.")
        query = query.where(Listing.category_id == category.id)
    if filters.purpose is not None:
        query = query.where(Listing.purpose == filters.purpose)
    if filters.property_type is not None:
        query = query.where(Listing.property_type == filters.property_type)
    if filters.city:
        query = query.where(Listing.city.ilike(f"%{filters.city.strip()}%"))
    if filters.district:
        query = query.where(Listing.district.ilike(f"%{filters.district.strip()}%"))
    if filters.min_price is not None:
        query = query.where(Listing.price_amount >= filters.min_price)
    if filters.max_price is not None:
        query = query.where(Listing.price_amount <= filters.max_price)
    if filters.min_area_sqm is not None:
        query = query.where(Listing.area_sqm >= filters.min_area_sqm)
    if filters.max_area_sqm is not None:
        query = query.where(Listing.area_sqm <= filters.max_area_sqm)
    if filters.room_count is not None:
        query = query.where(Listing.room_count == filters.room_count)
    if include_status and filters.status is not None:
        query = query.where(Listing.status == filters.status)
    if filters.reported_only:
        query = query.where(
            exists(
                select(Report.id).where(
                    Report.listing_id == Listing.id,
                    Report.status.in_([ReportStatus.OPEN, ReportStatus.IN_REVIEW]),
                )
            )
        )
    return query


def _paginate_listings(
    session: Session,
    *,
    base_query: Select,
    locale: str,
    filters: ListingQueryParams,
) -> PaginatedListingsResponseSchema:
    total_items = session.execute(select(func.count()).select_from(base_query.subquery())).scalar_one()
    if total_items == 0:
        return PaginatedListingsResponseSchema(
            items=[],
            meta=_pagination_meta(page=filters.page, page_size=filters.page_size, total_items=0),
        )

    now = utcnow()
    promotion_expr = _active_promotion_exists_expr(now).label("is_promoted")
    order_by_clauses = _listing_order_by(filters=filters, promotion_expr=promotion_expr)

    rows = session.execute(
        base_query.add_columns(promotion_expr)
        .order_by(*order_by_clauses)
        .offset((filters.page - 1) * filters.page_size)
        .limit(filters.page_size)
    ).all()
    listing_ids = [row[0] for row in rows]
    promoted_map = {row[0]: bool(row[1]) for row in rows}
    promotion_state_map = _active_promotion_state_map(session, listing_ids, locale=locale)

    listings = session.execute(_listing_query().where(Listing.id.in_(listing_ids))).scalars().all()
    listings_by_id = {listing.id: listing for listing in listings}
    items = [
        _build_listing_summary_schema(
            listings_by_id[listing_id],
            locale=locale,
            is_promoted=promoted_map.get(listing_id, False),
            promotion_state=promotion_state_map.get(listing_id),
        )
        for listing_id in listing_ids
        if listing_id in listings_by_id
    ]
    return PaginatedListingsResponseSchema(
        items=items,
        meta=_pagination_meta(page=filters.page, page_size=filters.page_size, total_items=total_items),
    )


def _listing_order_by(*, filters: ListingQueryParams, promotion_expr) -> list:
    newest_column = func.coalesce(Listing.published_at, Listing.created_at)
    if filters.sort == "oldest":
        ordering = [newest_column.asc(), Listing.id.asc()]
    elif filters.sort == "price_asc":
        ordering = [Listing.price_amount.asc(), newest_column.desc(), Listing.id.desc()]
    elif filters.sort == "price_desc":
        ordering = [Listing.price_amount.desc(), newest_column.desc(), Listing.id.desc()]
    else:
        ordering = [newest_column.desc(), Listing.id.desc()]

    if filters.promoted_first:
        return [case((promotion_expr, 0), else_=1).asc(), *ordering]
    return ordering


def _active_promotion_exists_expr(now):
    return exists(
        select(Promotion.id).where(
            Promotion.listing_id == Listing.id,
            Promotion.status == PromotionStatus.ACTIVE,
            or_(Promotion.starts_at.is_(None), Promotion.starts_at <= now),
            or_(Promotion.ends_at.is_(None), Promotion.ends_at >= now),
        )
    )


def _active_promotion_map(session: Session, listing_ids: list[int]) -> dict[int, bool]:
    if not listing_ids:
        return {}
    now = utcnow()
    promoted_listing_ids = session.execute(
        select(Promotion.listing_id)
        .where(
            Promotion.listing_id.in_(listing_ids),
            Promotion.status == PromotionStatus.ACTIVE,
            or_(Promotion.starts_at.is_(None), Promotion.starts_at <= now),
            or_(Promotion.ends_at.is_(None), Promotion.ends_at >= now),
        )
        .group_by(Promotion.listing_id)
    ).scalars().all()
    promoted_set = set(promoted_listing_ids)
    return {listing_id: listing_id in promoted_set for listing_id in listing_ids}


def _active_promotion_state_map(
    session: Session,
    listing_ids: list[int],
    *,
    locale: str,
) -> dict[int, ListingPromotionStateSchema]:
    if not listing_ids:
        return {}
    now = utcnow()
    promotions = session.execute(
        select(Promotion)
        .options(
            selectinload(Promotion.package),
            selectinload(Promotion.target_category).selectinload(Category.translations),
        )
        .where(
            Promotion.listing_id.in_(listing_ids),
            Promotion.status == PromotionStatus.ACTIVE,
            or_(Promotion.starts_at.is_(None), Promotion.starts_at <= now),
            or_(Promotion.ends_at.is_(None), Promotion.ends_at >= now),
        )
        .order_by(Promotion.created_at.desc(), Promotion.id.desc())
    ).scalars().all()
    promotion_map: dict[int, ListingPromotionStateSchema] = {}
    for promotion in promotions:
        if promotion.listing_id in promotion_map:
            continue
        target_translation = _resolved_translation(promotion.target_category, locale=locale) if promotion.target_category else None
        promotion_map[promotion.listing_id] = ListingPromotionStateSchema(
            public_id=promotion.public_id,
            package_public_id=promotion.package.public_id,
            package_name=promotion.package.name,
            status=promotion.status.value,
            target_city=promotion.target_city,
            target_category_public_id=promotion.target_category.public_id if promotion.target_category else None,
            target_category_name=target_translation.name if target_translation else None,
            starts_at=promotion.starts_at,
            ends_at=promotion.ends_at,
            activated_at=promotion.activated_at,
        )
    return promotion_map


def _favorite_unavailable_reason(listing: Listing | None) -> str | None:
    if listing is None or listing.deleted_at is not None:
        return "listing_removed"
    if listing.seller.deleted_at is not None or listing.seller.status != UserStatus.ACTIVE:
        return "seller_unavailable"
    if listing.status == ListingStatus.ARCHIVED:
        return "listing_archived"
    if listing.status != ListingStatus.PUBLISHED:
        return "listing_hidden"
    return None


def _pagination_meta(*, page: int, page_size: int, total_items: int) -> PaginationMetaSchema:
    total_pages = ceil(total_items / page_size) if total_items else 0
    return PaginationMetaSchema(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )


def _listing_snapshot(listing: Listing) -> dict:
    return {
        "public_id": listing.public_id,
        "status": listing.status.value,
        "title": listing.title,
        "category_public_id": listing.category.public_id,
        "price_amount": str(listing.price_amount),
        "media_count": len(_active_media(listing)),
    }
