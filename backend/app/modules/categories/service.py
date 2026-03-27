from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.auth import utcnow
from app.core.exceptions import AppError
from app.db.models import Category, CategoryAttribute, CategoryAttributeOption, CategoryTranslation, Listing, User
from app.modules.categories.schemas import (
    AdminCategorySchema,
    CategoryAttributeInput,
    CategoryAttributeOptionSchema,
    CategoryAttributeSchema,
    CategoryCreateRequest,
    CategoryTranslationInput,
    CategoryTranslationSchema,
    CategoryUpdateRequest,
    PublicCategorySchema,
)
from app.shared.audit import record_admin_audit_log


def list_admin_categories(session: Session) -> list[AdminCategorySchema]:
    categories = session.execute(_category_query().where(Category.deleted_at.is_(None)).order_by(Category.sort_order)).scalars().all()
    return [_build_admin_category_schema(category) for category in categories]


def get_admin_category(session: Session, *, category_public_id: str) -> AdminCategorySchema:
    category = _get_category_or_404(session, category_public_id=category_public_id)
    return _build_admin_category_schema(category)


def create_category(
    session: Session,
    *,
    payload: CategoryCreateRequest,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AdminCategorySchema:
    _ensure_unique_slug(session, slug=payload.slug)
    parent = _resolve_parent_category(session, parent_public_id=payload.parent_public_id)

    category = Category(
        parent_id=parent.id if parent else None,
        slug=payload.slug,
        internal_name=payload.internal_name,
        is_active=payload.is_active,
        sort_order=payload.sort_order,
    )
    session.add(category)
    session.flush()
    _sync_category_collections(category, translations=payload.translations, attributes=payload.attributes)
    session.flush()

    record_admin_audit_log(
        session,
        actor=actor,
        action="category.create",
        entity_type="category",
        entity_id=category.public_id,
        description=f"Created category '{category.slug}'.",
        ip_address=ip_address,
        user_agent=user_agent,
        after_json=_category_snapshot(category),
    )
    return _build_admin_category_schema(category)


def update_category(
    session: Session,
    *,
    category_public_id: str,
    payload: CategoryUpdateRequest,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AdminCategorySchema:
    category = _get_category_or_404(session, category_public_id=category_public_id)
    before_json = _category_snapshot(category)
    updates = payload.model_dump(exclude_unset=True)

    if "slug" in updates:
        _ensure_unique_slug(session, slug=updates["slug"], exclude_category_id=category.id)
        category.slug = updates["slug"]
    if "internal_name" in updates:
        category.internal_name = updates["internal_name"]
    if "is_active" in updates:
        category.is_active = updates["is_active"]
    if "sort_order" in updates:
        category.sort_order = updates["sort_order"]
    if "parent_public_id" in updates:
        parent = _resolve_parent_category(session, parent_public_id=updates["parent_public_id"])
        _ensure_no_category_cycle(category=category, parent=parent)
        category.parent_id = parent.id if parent else None
    if "translations" in updates:
        _replace_translations(category, updates["translations"])
    if "attributes" in updates:
        _replace_attributes(category, updates["attributes"])

    session.flush()
    record_admin_audit_log(
        session,
        actor=actor,
        action="category.update",
        entity_type="category",
        entity_id=category.public_id,
        description=f"Updated category '{category.slug}'.",
        ip_address=ip_address,
        user_agent=user_agent,
        before_json=before_json,
        after_json=_category_snapshot(category),
    )
    return _build_admin_category_schema(category)


def delete_category(
    session: Session,
    *,
    category_public_id: str,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    category = _get_category_or_404(session, category_public_id=category_public_id)

    has_children = session.execute(
        select(Category.id).where(Category.parent_id == category.id, Category.deleted_at.is_(None)).limit(1)
    ).scalar_one_or_none()
    if has_children is not None:
        raise AppError(
            status_code=409,
            code="category_has_children",
            message="Cannot delete a category that still has child categories.",
        )

    has_listings = session.execute(
        select(Listing.id).where(Listing.category_id == category.id, Listing.deleted_at.is_(None)).limit(1)
    ).scalar_one_or_none()
    if has_listings is not None:
        raise AppError(
            status_code=409,
            code="category_has_listings",
            message="Cannot delete a category that is already used by listings.",
        )

    before_json = _category_snapshot(category)
    category.is_active = False
    category.deleted_at = utcnow()
    session.flush()
    record_admin_audit_log(
        session,
        actor=actor,
        action="category.delete",
        entity_type="category",
        entity_id=category.public_id,
        description=f"Soft-deleted category '{category.slug}'.",
        ip_address=ip_address,
        user_agent=user_agent,
        before_json=before_json,
        after_json=_category_snapshot(category),
    )


def list_public_categories(session: Session, *, locale: str) -> list[PublicCategorySchema]:
    categories = session.execute(
        _category_query()
        .where(Category.deleted_at.is_(None), Category.is_active.is_(True))
        .order_by(Category.sort_order, Category.id)
    ).scalars().all()

    nodes = {
        category.id: _build_public_category_schema(category, locale=locale)
        for category in categories
    }
    roots: list[PublicCategorySchema] = []
    for category in categories:
        node = nodes[category.id]
        if category.parent_id and category.parent_id in nodes:
            nodes[category.parent_id].children.append(node)
        else:
            roots.append(node)
    return roots


def _category_query():
    return select(Category).options(
        selectinload(Category.translations),
        selectinload(Category.attributes).selectinload(CategoryAttribute.options),
    )


def _get_category_or_404(session: Session, *, category_public_id: str) -> Category:
    category = session.execute(
        _category_query().where(Category.public_id == category_public_id, Category.deleted_at.is_(None))
    ).scalar_one_or_none()
    if category is None:
        raise AppError(status_code=404, code="category_not_found", message="Category was not found.")
    return category


def _resolve_parent_category(session: Session, *, parent_public_id: str | None) -> Category | None:
    if not parent_public_id:
        return None
    parent = session.execute(
        select(Category).where(
            Category.public_id == parent_public_id,
            Category.deleted_at.is_(None),
        )
    ).scalar_one_or_none()
    if parent is None:
        raise AppError(status_code=404, code="parent_category_not_found", message="Parent category was not found.")
    return parent


def _ensure_unique_slug(session: Session, *, slug: str, exclude_category_id: int | None = None) -> None:
    query = select(Category).where(Category.slug == slug, Category.deleted_at.is_(None))
    if exclude_category_id is not None:
        query = query.where(Category.id != exclude_category_id)
    existing = session.execute(query).scalar_one_or_none()
    if existing is not None:
        raise AppError(status_code=409, code="category_slug_taken", message="Category slug is already in use.")


def _ensure_no_category_cycle(*, category: Category, parent: Category | None) -> None:
    if parent is None:
        return
    if parent.id == category.id:
        raise AppError(status_code=400, code="invalid_category_parent", message="A category cannot be its own parent.")

    current = parent
    while current.parent is not None:
        current = current.parent
        if current.id == category.id:
            raise AppError(
                status_code=400,
                code="invalid_category_parent",
                message="A category cannot be moved inside its own subtree.",
            )


def _sync_category_collections(
    category: Category,
    *,
    translations: list[CategoryTranslationInput],
    attributes: list[CategoryAttributeInput],
) -> None:
    _replace_translations(category, translations)
    _replace_attributes(category, attributes)


def _replace_translations(category: Category, translations: list[CategoryTranslationInput]) -> None:
    category.translations = [
        CategoryTranslation(
            locale=translation.locale,
            name=translation.name,
            description=translation.description,
        )
        for translation in translations
    ]


def _replace_attributes(category: Category, attributes: list[CategoryAttributeInput]) -> None:
    category.attributes = [
        CategoryAttribute(
            code=attribute.code,
            display_name=attribute.display_name,
            data_type=attribute.data_type,
            unit=attribute.unit,
            is_required=attribute.is_required,
            is_filterable=attribute.is_filterable,
            sort_order=attribute.sort_order,
            config_json=attribute.config_json,
            options=[
                CategoryAttributeOption(
                    option_value=option.option_value,
                    option_label=option.option_label,
                    sort_order=option.sort_order,
                )
                for option in attribute.options
            ],
        )
        for attribute in attributes
    ]


def _resolved_translation(category: Category, *, locale: str) -> CategoryTranslation | None:
    by_locale = {translation.locale: translation for translation in category.translations}
    return by_locale.get(locale) or by_locale.get("en") or next(iter(category.translations), None)


def _build_attribute_schema(attribute: CategoryAttribute) -> CategoryAttributeSchema:
    return CategoryAttributeSchema(
        code=attribute.code,
        display_name=attribute.display_name,
        data_type=attribute.data_type,
        unit=attribute.unit,
        is_required=attribute.is_required,
        is_filterable=attribute.is_filterable,
        sort_order=attribute.sort_order,
        config_json=attribute.config_json,
        options=[
            CategoryAttributeOptionSchema(
                option_value=option.option_value,
                option_label=option.option_label,
                sort_order=option.sort_order,
            )
            for option in sorted(attribute.options, key=lambda item: (item.sort_order, item.id))
        ],
    )


def _build_admin_category_schema(category: Category) -> AdminCategorySchema:
    return AdminCategorySchema(
        public_id=category.public_id,
        parent_public_id=category.parent.public_id if category.parent else None,
        slug=category.slug,
        internal_name=category.internal_name,
        is_active=category.is_active,
        sort_order=category.sort_order,
        deleted_at=category.deleted_at.isoformat() if isinstance(category.deleted_at, datetime) else None,
        translations=[
            CategoryTranslationSchema(
                locale=translation.locale,
                name=translation.name,
                description=translation.description,
            )
            for translation in sorted(category.translations, key=lambda item: item.locale)
        ],
        attributes=[
            _build_attribute_schema(attribute)
            for attribute in sorted(category.attributes, key=lambda item: (item.sort_order, item.id))
        ],
    )


def _build_public_category_schema(category: Category, *, locale: str) -> PublicCategorySchema:
    translation = _resolved_translation(category, locale=locale)
    return PublicCategorySchema(
        public_id=category.public_id,
        parent_public_id=category.parent.public_id if category.parent else None,
        slug=category.slug,
        name=translation.name if translation else category.internal_name,
        description=translation.description if translation else None,
        locale=translation.locale if translation else locale,
        sort_order=category.sort_order,
        attributes=[
            _build_attribute_schema(attribute)
            for attribute in sorted(category.attributes, key=lambda item: (item.sort_order, item.id))
        ],
    )


def _category_snapshot(category: Category) -> dict:
    return {
        "public_id": category.public_id,
        "parent_public_id": category.parent.public_id if category.parent else None,
        "slug": category.slug,
        "internal_name": category.internal_name,
        "is_active": category.is_active,
        "sort_order": category.sort_order,
        "deleted_at": category.deleted_at.isoformat() if category.deleted_at else None,
        "translations": [
            {
                "locale": translation.locale,
                "name": translation.name,
            }
            for translation in category.translations
        ],
        "attribute_codes": [attribute.code for attribute in category.attributes],
    }
