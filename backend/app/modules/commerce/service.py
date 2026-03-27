from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.auth import utcnow
from app.core.config import Settings
from app.core.exceptions import AppError
from app.db.enums import ListingStatus, PaymentStatus, PaymentType, PromotionStatus, RoleCode, UserStatus
from app.db.models import (
    Category,
    CategoryTranslation,
    Listing,
    PaymentRecord,
    Promotion,
    PromotionPackage,
    Role,
    User,
    UserRole,
)
from app.modules.commerce.schemas import (
    PaginatedPaymentsResponseSchema,
    PaginatedPromotionsResponseSchema,
    PaymentInitiationResponseSchema,
    PaymentPriceBreakdownSchema,
    PaymentPromotionInitiateRequest,
    PaymentSchema,
    PaymentSimulationRequest,
    PaymentSimulationResponseSchema,
    PromotionPackageCreateRequest,
    PromotionPackageSchema,
    PromotionPackageUpdateRequest,
    PromotionSummarySchema,
)
from app.modules.notifications.service import notify_payment_successful, notify_promotion_activated, notify_promotion_expired
from app.shared.audit import record_admin_audit_log
from app.shared.schemas import PaginationMetaSchema


def list_active_promotion_packages(session: Session) -> list[PromotionPackageSchema]:
    packages = session.execute(
        select(PromotionPackage).where(PromotionPackage.is_active.is_(True)).order_by(
            PromotionPackage.boost_level.desc(),
            PromotionPackage.price_amount.asc(),
            PromotionPackage.id.asc(),
        )
    ).scalars().all()
    return [_build_package_schema(package) for package in packages]


def list_admin_promotion_packages(session: Session) -> list[PromotionPackageSchema]:
    packages = session.execute(
        select(PromotionPackage).order_by(PromotionPackage.is_active.desc(), PromotionPackage.boost_level.desc(), PromotionPackage.id.asc())
    ).scalars().all()
    return [_build_package_schema(package) for package in packages]


def create_promotion_package(
    session: Session,
    *,
    payload: PromotionPackageCreateRequest,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> PromotionPackageSchema:
    existing = session.execute(
        select(PromotionPackage).where(PromotionPackage.code == payload.code.strip().lower())
    ).scalar_one_or_none()
    if existing is not None:
        raise AppError(status_code=409, code="promotion_package_exists", message="Promotion package code already exists.")

    package = PromotionPackage(
        code=payload.code.strip().lower(),
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        duration_days=payload.duration_days,
        price_amount=payload.price_amount,
        currency_code=payload.currency_code.upper(),
        boost_level=payload.boost_level,
        is_active=True,
    )
    session.add(package)
    session.flush()
    record_admin_audit_log(
        session,
        actor=actor,
        action="promotion_package.create",
        entity_type="promotion_package",
        entity_id=package.public_id,
        description=f"Created promotion package '{package.code}'.",
        ip_address=ip_address,
        user_agent=user_agent,
        after_json=_package_snapshot(package),
    )
    return _build_package_schema(package)


def update_promotion_package(
    session: Session,
    *,
    package_public_id: str,
    payload: PromotionPackageUpdateRequest,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> PromotionPackageSchema:
    package = _get_package_or_404(session, package_public_id=package_public_id)
    before_json = _package_snapshot(package)
    updates = payload.model_dump(exclude_unset=True)

    if "name" in updates:
        package.name = updates["name"].strip()
    if "description" in updates:
        package.description = updates["description"].strip() if updates["description"] else None
    if "duration_days" in updates:
        package.duration_days = updates["duration_days"]
    if "price_amount" in updates:
        package.price_amount = updates["price_amount"]
    if "currency_code" in updates:
        package.currency_code = updates["currency_code"].upper()
    if "boost_level" in updates:
        package.boost_level = updates["boost_level"]
    if "is_active" in updates:
        package.is_active = updates["is_active"]

    session.flush()
    record_admin_audit_log(
        session,
        actor=actor,
        action="promotion_package.update",
        entity_type="promotion_package",
        entity_id=package.public_id,
        description=f"Updated promotion package '{package.code}'.",
        ip_address=ip_address,
        user_agent=user_agent,
        before_json=before_json,
        after_json=_package_snapshot(package),
    )
    return _build_package_schema(package)


def deactivate_promotion_package(
    session: Session,
    *,
    package_public_id: str,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> PromotionPackageSchema:
    package = _get_package_or_404(session, package_public_id=package_public_id)
    before_json = _package_snapshot(package)
    package.is_active = False
    session.flush()
    record_admin_audit_log(
        session,
        actor=actor,
        action="promotion_package.deactivate",
        entity_type="promotion_package",
        entity_id=package.public_id,
        description=f"Deactivated promotion package '{package.code}'.",
        ip_address=ip_address,
        user_agent=user_agent,
        before_json=before_json,
        after_json=_package_snapshot(package),
    )
    return _build_package_schema(package)


def initiate_promotion_payment(
    session: Session,
    *,
    settings: Settings,
    actor: User,
    payload: PaymentPromotionInitiateRequest,
) -> PaymentInitiationResponseSchema:
    _ensure_user_can_purchase(actor)
    expire_due_promotions(session)

    listing = _get_owned_listing_or_404(session, listing_public_id=payload.listing_public_id, owner=actor)
    _ensure_listing_can_be_promoted(listing)
    package = _get_active_package_or_404(session, package_public_id=payload.package_public_id)
    target_category = _resolve_target_category(
        session,
        listing=listing,
        target_category_public_id=payload.target_category_public_id,
    )
    target_city = _resolve_target_city(listing=listing, target_city=payload.target_city)

    existing = session.execute(
        select(Promotion)
        .where(
            Promotion.listing_id == listing.id,
            Promotion.status.in_([PromotionStatus.PENDING_PAYMENT, PromotionStatus.ACTIVE]),
        )
        .order_by(Promotion.created_at.desc(), Promotion.id.desc())
    ).scalars().all()
    for promotion in existing:
        if _effective_promotion_status(promotion) in {PromotionStatus.PENDING_PAYMENT, PromotionStatus.ACTIVE}:
            raise AppError(
                status_code=409,
                code="promotion_already_exists",
                message="This listing already has a pending or active promotion.",
            )

    if payload.duration_days % package.duration_days != 0:
        raise AppError(
            status_code=400,
            code="invalid_promotion_duration",
            message="Selected duration must be a whole multiple of the package duration.",
        )

    total_amount = _calculate_total_amount(
        base_price=package.price_amount,
        base_duration_days=package.duration_days,
        selected_duration_days=payload.duration_days,
    )
    promotion = Promotion(
        listing_id=listing.id,
        promotion_package_id=package.id,
        activated_by_user_id=actor.id,
        status=PromotionStatus.PENDING_PAYMENT,
        target_city=target_city,
        target_category_id=target_category.id if target_category else None,
        duration_days=payload.duration_days,
        price_amount=total_amount,
        currency_code=package.currency_code,
    )
    session.add(promotion)
    session.flush()

    payment = PaymentRecord(
        payer_user_id=actor.id,
        listing_id=listing.id,
        payment_type=PaymentType.PROMOTION_PURCHASE,
        provider="mock",
        amount=total_amount,
        currency_code=package.currency_code,
        status=PaymentStatus.PENDING,
        metadata_json={
            "promotion_public_id": promotion.public_id,
            "promotion_package_public_id": package.public_id,
            "target_city": target_city,
            "target_category_public_id": target_category.public_id if target_category else None,
            "duration_days": payload.duration_days,
        },
    )
    session.add(payment)
    session.flush()

    payment.provider_reference = f"mockpay_{payment.public_id}"
    promotion.payment_record_id = payment.id
    session.flush()

    return PaymentInitiationResponseSchema(
        payment=_build_payment_schema(settings=settings, payment=payment, promotion=promotion),
        promotion=_build_promotion_schema(promotion),
        price_breakdown=PaymentPriceBreakdownSchema(
            base_duration_days=package.duration_days,
            selected_duration_days=payload.duration_days,
            base_price_amount=package.price_amount,
            total_amount=total_amount,
            currency_code=package.currency_code,
        ),
    )


def simulate_payment_result(
    session: Session,
    *,
    settings: Settings,
    payment_public_id: str,
    payload: PaymentSimulationRequest,
    actor: User,
) -> PaymentSimulationResponseSchema:
    expire_due_promotions(session)
    payment = _get_payment_or_404(session, payment_public_id=payment_public_id)
    promotion = payment.promotion
    _ensure_payment_access(session, payment=payment, actor=actor)

    if payload.result == "successful":
        if payment.status == PaymentStatus.SUCCESSFUL:
            if promotion is not None and _effective_promotion_status(promotion) == PromotionStatus.PENDING_PAYMENT:
                _activate_promotion(session, promotion=promotion, payment=payment)
            return PaymentSimulationResponseSchema(
                payment=_build_payment_schema(settings=settings, payment=payment, promotion=promotion),
                promotion=_build_promotion_schema(promotion) if promotion else None,
            )
        if payment.status != PaymentStatus.PENDING:
            raise AppError(status_code=409, code="invalid_payment_transition", message="Payment cannot be marked successful.")
        if promotion is not None:
            _ensure_listing_can_be_promoted(promotion.listing)
        payment.status = PaymentStatus.SUCCESSFUL
        payment.paid_at = utcnow()
        payment.failed_at = None
        payment.failure_reason = None
        payment.cancelled_at = None
        payment.refunded_ready_at = None
        if promotion is not None:
            _activate_promotion(session, promotion=promotion, payment=payment)
        notify_payment_successful(
            session,
            user=payment.payer,
            payment_public_id=payment.public_id,
            amount=str(payment.amount),
            currency_code=payment.currency_code,
        )
    elif payload.result == "failed":
        if payment.status == PaymentStatus.FAILED:
            return PaymentSimulationResponseSchema(
                payment=_build_payment_schema(settings=settings, payment=payment, promotion=promotion),
                promotion=_build_promotion_schema(promotion) if promotion else None,
            )
        if payment.status != PaymentStatus.PENDING:
            raise AppError(status_code=409, code="invalid_payment_transition", message="Payment cannot be marked failed.")
        payment.status = PaymentStatus.FAILED
        payment.failed_at = utcnow()
        payment.failure_reason = "Mock payment provider reported a failed transaction."
        if promotion is not None:
            promotion.status = PromotionStatus.CANCELLED
            promotion.cancelled_at = utcnow()
    elif payload.result == "cancelled":
        if payment.status == PaymentStatus.CANCELLED:
            return PaymentSimulationResponseSchema(
                payment=_build_payment_schema(settings=settings, payment=payment, promotion=promotion),
                promotion=_build_promotion_schema(promotion) if promotion else None,
            )
        if payment.status != PaymentStatus.PENDING:
            raise AppError(status_code=409, code="invalid_payment_transition", message="Payment cannot be cancelled.")
        payment.status = PaymentStatus.CANCELLED
        payment.cancelled_at = utcnow()
        if promotion is not None:
            promotion.status = PromotionStatus.CANCELLED
            promotion.cancelled_at = utcnow()
    else:
        if payment.status == PaymentStatus.REFUNDED_READY:
            return PaymentSimulationResponseSchema(
                payment=_build_payment_schema(settings=settings, payment=payment, promotion=promotion),
                promotion=_build_promotion_schema(promotion) if promotion else None,
            )
        if payment.status != PaymentStatus.SUCCESSFUL:
            raise AppError(
                status_code=409,
                code="invalid_payment_transition",
                message="Only successful payments can be marked refund-ready.",
            )
        payment.status = PaymentStatus.REFUNDED_READY
        payment.refunded_ready_at = utcnow()
        if promotion is not None and _effective_promotion_status(promotion) == PromotionStatus.ACTIVE:
            promotion.status = PromotionStatus.CANCELLED
            promotion.cancelled_at = utcnow()

    session.flush()
    return PaymentSimulationResponseSchema(
        payment=_build_payment_schema(settings=settings, payment=payment, promotion=promotion),
        promotion=_build_promotion_schema(promotion) if promotion else None,
    )


def list_user_payments(
    session: Session,
    *,
    settings: Settings,
    user: User,
    page: int,
    page_size: int,
) -> PaginatedPaymentsResponseSchema:
    expire_due_promotions(session)
    base_query = _payment_query().where(PaymentRecord.payer_user_id == user.id).order_by(PaymentRecord.created_at.desc(), PaymentRecord.id.desc())
    return _paginate_payments(session, settings=settings, base_query=base_query, page=page, page_size=page_size)


def list_admin_payments(
    session: Session,
    *,
    settings: Settings,
    page: int,
    page_size: int,
    status: PaymentStatus | None = None,
) -> PaginatedPaymentsResponseSchema:
    expire_due_promotions(session)
    base_query = _payment_query()
    if status is not None:
        base_query = base_query.where(PaymentRecord.status == status)
    base_query = base_query.order_by(PaymentRecord.created_at.desc(), PaymentRecord.id.desc())
    return _paginate_payments(session, settings=settings, base_query=base_query, page=page, page_size=page_size)


def list_my_promotions(
    session: Session,
    *,
    user: User,
    page: int,
    page_size: int,
) -> PaginatedPromotionsResponseSchema:
    expire_due_promotions(session)
    base_query = _promotion_query().join(Promotion.listing).where(Listing.seller_id == user.id).order_by(Promotion.created_at.desc(), Promotion.id.desc())
    total_items = session.execute(select(func.count()).select_from(base_query.subquery())).scalar_one()
    promotions = session.execute(
        base_query.offset((page - 1) * page_size).limit(page_size)
    ).unique().scalars().all()
    return PaginatedPromotionsResponseSchema(
        items=[_build_promotion_schema(promotion) for promotion in promotions],
        meta=_pagination_meta(page=page, page_size=page_size, total_items=total_items),
    )


def expire_due_promotions(session: Session) -> int:
    now = utcnow()
    promotions = session.execute(
        _promotion_query().where(
            Promotion.status == PromotionStatus.ACTIVE,
            Promotion.ends_at.is_not(None),
            Promotion.ends_at < now,
        )
    ).unique().scalars().all()
    for promotion in promotions:
        promotion.status = PromotionStatus.EXPIRED
        notify_promotion_expired(
            session,
            user=promotion.listing.seller,
            promotion_public_id=promotion.public_id,
            listing_public_id=promotion.listing.public_id,
        )
    if promotions:
        session.flush()
    return len(promotions)


def _payment_query() -> Select[tuple[PaymentRecord]]:
    return select(PaymentRecord).options(
        joinedload(PaymentRecord.promotion)
        .joinedload(Promotion.package),
        joinedload(PaymentRecord.promotion)
        .joinedload(Promotion.target_category)
        .joinedload(Category.translations),
        joinedload(PaymentRecord.promotion).joinedload(Promotion.listing),
        joinedload(PaymentRecord.payer),
        joinedload(PaymentRecord.listing),
    )


def _promotion_query() -> Select[tuple[Promotion]]:
    return select(Promotion).options(
        joinedload(Promotion.listing),
        joinedload(Promotion.package),
        joinedload(Promotion.payment_record),
        joinedload(Promotion.target_category).joinedload(Category.translations),
    )


def _get_active_package_or_404(session: Session, *, package_public_id: str) -> PromotionPackage:
    package = session.execute(
        select(PromotionPackage).where(PromotionPackage.public_id == package_public_id, PromotionPackage.is_active.is_(True))
    ).scalar_one_or_none()
    if package is None:
        raise AppError(status_code=404, code="promotion_package_not_found", message="Promotion package was not found.")
    return package


def _get_package_or_404(session: Session, *, package_public_id: str) -> PromotionPackage:
    package = session.execute(
        select(PromotionPackage).where(PromotionPackage.public_id == package_public_id)
    ).scalar_one_or_none()
    if package is None:
        raise AppError(status_code=404, code="promotion_package_not_found", message="Promotion package was not found.")
    return package


def _get_owned_listing_or_404(session: Session, *, listing_public_id: str, owner: User) -> Listing:
    listing = session.execute(
        select(Listing)
        .options(joinedload(Listing.category), joinedload(Listing.seller))
        .where(Listing.public_id == listing_public_id, Listing.deleted_at.is_(None))
    ).scalar_one_or_none()
    if listing is None:
        raise AppError(status_code=404, code="listing_not_found", message="Listing was not found.")
    if listing.seller_id != owner.id:
        raise AppError(status_code=403, code="listing_forbidden", message="You can only promote your own listings.")
    return listing


def _resolve_target_category(
    session: Session,
    *,
    listing: Listing,
    target_category_public_id: str | None,
) -> Category | None:
    if target_category_public_id is None:
        return None
    category = session.execute(
        select(Category)
        .options(joinedload(Category.translations))
        .where(Category.public_id == target_category_public_id, Category.deleted_at.is_(None))
    ).unique().scalar_one_or_none()
    if category is None:
        raise AppError(status_code=404, code="category_not_found", message="Category was not found.")
    if category.id != listing.category_id:
        raise AppError(
            status_code=400,
            code="invalid_promotion_target_category",
            message="Promotion target category must match the listing category for this MVP.",
        )
    return category


def _resolve_target_city(*, listing: Listing, target_city: str | None) -> str | None:
    if target_city is None:
        return None
    normalized = target_city.strip()
    if normalized.lower() != listing.city.strip().lower():
        raise AppError(
            status_code=400,
            code="invalid_promotion_target_city",
            message="Promotion target city must match the listing city for this MVP.",
        )
    return normalized


def _get_payment_or_404(session: Session, *, payment_public_id: str) -> PaymentRecord:
    payment = session.execute(
        _payment_query().where(PaymentRecord.public_id == payment_public_id)
    ).unique().scalar_one_or_none()
    if payment is None:
        raise AppError(status_code=404, code="payment_not_found", message="Payment was not found.")
    return payment


def _ensure_payment_access(session: Session, *, payment: PaymentRecord, actor: User) -> None:
    if payment.payer_user_id == actor.id:
        return
    if _is_admin(session, user=actor):
        return
    raise AppError(status_code=403, code="payment_forbidden", message="You do not have access to this payment.")


def _ensure_user_can_purchase(user: User) -> None:
    if user.status != UserStatus.ACTIVE:
        raise AppError(
            status_code=403,
            code=f"account_{user.status.value}",
            message="Only active users can initiate payments and promotions.",
        )


def _ensure_listing_can_be_promoted(listing: Listing) -> None:
    if listing.status != ListingStatus.PUBLISHED:
        raise AppError(
            status_code=409,
            code="listing_not_promotable",
            message="Only approved and published listings can be promoted.",
        )
    if listing.seller.status != UserStatus.ACTIVE or listing.seller.deleted_at is not None:
        raise AppError(
            status_code=409,
            code="seller_not_promotable",
            message="Listing owner is not eligible for promotion.",
        )


def _activate_promotion(session: Session, *, promotion: Promotion, payment: PaymentRecord) -> None:
    listing = promotion.listing
    _ensure_listing_can_be_promoted(listing)
    now = utcnow()
    promotion.status = PromotionStatus.ACTIVE
    promotion.starts_at = now
    promotion.ends_at = now + _days_delta(promotion.duration_days)
    promotion.activated_at = now
    promotion.cancelled_at = None
    notify_promotion_activated(
        session,
        user=listing.seller,
        promotion_public_id=promotion.public_id,
        listing_public_id=listing.public_id,
    )


def _days_delta(days: int):
    from datetime import timedelta

    return timedelta(days=days)


def _calculate_total_amount(*, base_price: Decimal, base_duration_days: int, selected_duration_days: int) -> Decimal:
    ratio = Decimal(selected_duration_days) / Decimal(base_duration_days)
    return (base_price * ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _paginate_payments(
    session: Session,
    *,
    settings: Settings,
    base_query: Select[tuple[PaymentRecord]],
    page: int,
    page_size: int,
) -> PaginatedPaymentsResponseSchema:
    total_items = session.execute(select(func.count()).select_from(base_query.subquery())).scalar_one()
    payments = session.execute(
        base_query.offset((page - 1) * page_size).limit(page_size)
    ).unique().scalars().all()
    return PaginatedPaymentsResponseSchema(
        items=[_build_payment_schema(settings=settings, payment=payment, promotion=payment.promotion) for payment in payments],
        meta=_pagination_meta(page=page, page_size=page_size, total_items=total_items),
    )


def _effective_promotion_status(promotion: Promotion) -> PromotionStatus:
    if (
        promotion.status == PromotionStatus.ACTIVE
        and promotion.ends_at is not None
        and promotion.ends_at < utcnow()
    ):
        return PromotionStatus.EXPIRED
    return promotion.status


def _build_package_schema(package: PromotionPackage) -> PromotionPackageSchema:
    return PromotionPackageSchema(
        public_id=package.public_id,
        code=package.code,
        name=package.name,
        description=package.description,
        duration_days=package.duration_days,
        price_amount=package.price_amount,
        currency_code=package.currency_code,
        boost_level=package.boost_level,
        is_active=package.is_active,
        created_at=package.created_at,
        updated_at=package.updated_at,
    )


def _build_promotion_schema(promotion: Promotion) -> PromotionSummarySchema:
    target_category = promotion.target_category
    target_translation = _category_translation_name(target_category) if target_category else None
    return PromotionSummarySchema(
        public_id=promotion.public_id,
        listing_public_id=promotion.listing.public_id,
        listing_title=promotion.listing.title,
        package_public_id=promotion.package.public_id,
        package_code=promotion.package.code,
        package_name=promotion.package.name,
        status=_effective_promotion_status(promotion),
        target_city=promotion.target_city,
        target_category_public_id=target_category.public_id if target_category else None,
        target_category_name=target_translation,
        duration_days=promotion.duration_days,
        price_amount=promotion.price_amount,
        currency_code=promotion.currency_code,
        payment_public_id=promotion.payment_record.public_id if promotion.payment_record else None,
        starts_at=promotion.starts_at,
        ends_at=promotion.ends_at,
        activated_at=promotion.activated_at,
        cancelled_at=promotion.cancelled_at,
        created_at=promotion.created_at,
        updated_at=promotion.updated_at,
    )


def _build_payment_schema(
    *,
    settings: Settings,
    payment: PaymentRecord,
    promotion: Promotion | None,
) -> PaymentSchema:
    listing = payment.listing or (promotion.listing if promotion else None)
    return PaymentSchema(
        public_id=payment.public_id,
        payment_type=payment.payment_type,
        provider=payment.provider,
        provider_reference=payment.provider_reference,
        amount=payment.amount,
        currency_code=payment.currency_code,
        status=payment.status,
        failure_reason=payment.failure_reason,
        listing_public_id=listing.public_id if listing else None,
        listing_title=listing.title if listing else None,
        promotion_public_id=promotion.public_id if promotion else None,
        checkout_url=_mock_checkout_url(settings=settings, payment=payment) if payment.status == PaymentStatus.PENDING else None,
        paid_at=payment.paid_at,
        failed_at=payment.failed_at,
        cancelled_at=payment.cancelled_at,
        refunded_ready_at=payment.refunded_ready_at,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )


def _mock_checkout_url(*, settings: Settings, payment: PaymentRecord) -> str:
    base_url = settings.mock_payment_checkout_base_url.rstrip("/")
    return f"{base_url}/payments/{payment.public_id}/simulate?result=successful"


def _category_translation_name(category: Category | None) -> str | None:
    if category is None:
        return None
    translations = {translation.locale: translation for translation in category.translations}
    translation = translations.get("en") or next(iter(category.translations), None)
    return translation.name if translation else category.internal_name


def _pagination_meta(*, page: int, page_size: int, total_items: int) -> PaginationMetaSchema:
    total_pages = ceil(total_items / page_size) if total_items else 0
    return PaginationMetaSchema(page=page, page_size=page_size, total_items=total_items, total_pages=total_pages)


def _package_snapshot(package: PromotionPackage) -> dict[str, str | int | bool]:
    return {
        "public_id": package.public_id,
        "code": package.code,
        "duration_days": package.duration_days,
        "price_amount": str(package.price_amount),
        "is_active": package.is_active,
        "boost_level": package.boost_level,
    }


def _is_admin(session: Session, *, user: User) -> bool:
    assigned_roles = set(
        role.value
        for role in session.execute(
            select(Role.code).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user.id)
        ).scalars()
    )
    return RoleCode.ADMIN.value in assigned_roles
