from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from app.core.auth import create_access_token
from app.core.auth import utcnow
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.enums import CategoryAttributeType, ListingCondition, ListingStatus, MediaType, PromotionStatus, RoleCode, UserStatus
from app.db.models import (
    AdminAuditLog,
    Category,
    CategoryAttribute,
    CategoryAttributeOption,
    CategoryTranslation,
    Conversation,
    Favorite,
    Listing,
    ListingAttributeValue,
    ListingMedia,
    Message,
    PaymentRecord,
    Promotion,
    PromotionPackage,
    Report,
    Role,
    User,
    UserRole,
)


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _create_user(session, *, email: str, username: str, roles: list[RoleCode], status: UserStatus = UserStatus.ACTIVE) -> User:
    user = User(
        email=email,
        username=username,
        full_name=username.replace("_", " ").title(),
        phone="+15550001111",
        password_hash=hash_password("UserPass123!"),
        locale="en",
        status=status,
        is_email_verified=True,
    )
    session.add(user)
    session.flush()

    role_map = {role.code: role for role in session.query(Role).all()}
    for role_code in roles:
        session.add(UserRole(user_id=user.id, role_id=role_map[role_code].id))
    session.commit()
    session.refresh(user)
    return user


def _access_token_for_user(user: User, *, roles: list[RoleCode]) -> str:
    settings = get_settings()
    return create_access_token(
        settings=settings,
        subject=user.public_id,
        roles=[role.value for role in roles],
    )


def _create_category_with_attributes(session) -> Category:
    category = Category(slug="smartphones", internal_name="Smartphones", is_active=True, sort_order=10)
    category.translations = [
        CategoryTranslation(locale="en", name="Smartphones", description="Phones and accessories"),
        CategoryTranslation(locale="ru", name="Smartfony", description="Telefony i aksessuary"),
    ]
    brand_attribute = CategoryAttribute(
        code="brand",
        display_name="Brand",
        data_type=CategoryAttributeType.SELECT,
        is_required=True,
        is_filterable=True,
        sort_order=1,
        options=[
            CategoryAttributeOption(option_value="apple", option_label="Apple", sort_order=1),
            CategoryAttributeOption(option_value="samsung", option_label="Samsung", sort_order=2),
        ],
    )
    storage_attribute = CategoryAttribute(
        code="storage_gb",
        display_name="Storage",
        data_type=CategoryAttributeType.NUMBER,
        unit="GB",
        is_required=True,
        is_filterable=True,
        sort_order=2,
    )
    category.attributes = [brand_attribute, storage_attribute]
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def _create_category_without_attributes(session, *, slug: str, name: str) -> Category:
    category = Category(slug=slug, internal_name=name, is_active=True, sort_order=20)
    category.translations = [
        CategoryTranslation(locale="en", name=name, description=f"{name} category"),
        CategoryTranslation(locale="ru", name=f"{name} ru", description=f"{name} ru category"),
    ]
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def _create_published_listing(
    session,
    *,
    seller: User,
    category: Category,
    title: str,
    description: str,
    price_amount: str,
    city: str,
    brand_option: str | None = None,
    storage_value: str | None = None,
    promoted: bool = False,
    published_offset_days: int = 0,
) -> Listing:
    listing = Listing(
        seller_id=seller.id,
        category_id=category.id,
        title=title,
        description=description,
        price_amount=Decimal(price_amount),
        currency_code="USD",
        item_condition=ListingCondition.LIKE_NEW,
        status=ListingStatus.PUBLISHED,
        city=city,
        published_at=utcnow() - timedelta(days=published_offset_days),
    )
    session.add(listing)
    session.flush()

    session.add(
        ListingMedia(
            listing_id=listing.id,
            media_type=MediaType.IMAGE,
            storage_key=f"demo/{listing.public_id}/cover.jpg",
            mime_type="image/jpeg",
            file_size_bytes=256,
            sort_order=0,
            is_primary=True,
        )
    )

    attribute_by_code = {attribute.code: attribute for attribute in category.attributes}
    if brand_option and "brand" in attribute_by_code:
        session.add(
            ListingAttributeValue(
                listing_id=listing.id,
                category_attribute_id=attribute_by_code["brand"].id,
                option_value=brand_option,
            )
        )
    if storage_value and "storage_gb" in attribute_by_code:
        session.add(
            ListingAttributeValue(
                listing_id=listing.id,
                category_attribute_id=attribute_by_code["storage_gb"].id,
                numeric_value=Decimal(storage_value),
            )
        )

    if promoted:
        package = PromotionPackage(
            code=f"featured_{listing.public_id}",
            name="Featured",
            duration_days=7,
            price_amount=Decimal("9.99"),
            boost_level=5,
            is_active=True,
        )
        session.add(package)
        session.flush()
        session.add(
            Promotion(
                listing_id=listing.id,
                promotion_package_id=package.id,
                status=PromotionStatus.ACTIVE,
                duration_days=package.duration_days,
                price_amount=package.price_amount,
                currency_code=package.currency_code,
                starts_at=utcnow() - timedelta(days=1),
                ends_at=utcnow() + timedelta(days=6),
                activated_at=utcnow() - timedelta(days=1),
            )
        )

    session.commit()
    session.refresh(listing)
    return listing


def test_admin_category_crud_and_public_localization(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]

    with session_factory() as session:
        admin = _create_user(session, email="admin.categories@example.com", username="admin_categories", roles=[RoleCode.ADMIN, RoleCode.USER])
        user = _create_user(session, email="user.categories@example.com", username="user_categories", roles=[RoleCode.USER])

    admin_headers = _auth_headers(_access_token_for_user(admin, roles=[RoleCode.ADMIN, RoleCode.USER]))
    user_headers = _auth_headers(_access_token_for_user(user, roles=[RoleCode.USER]))

    payload = {
        "slug": "tablets",
        "internal_name": "Tablets",
        "translations": [
            {"locale": "en", "name": "Tablets", "description": "Tablet computers"},
            {"locale": "ru", "name": "Planshety", "description": "Planshetnye komp'yutery"},
        ],
        "attributes": [
            {
                "code": "storage_gb",
                "display_name": "Storage",
                "data_type": "number",
                "unit": "GB",
                "is_required": True,
                "is_filterable": True,
                "sort_order": 1,
            }
        ],
    }

    forbidden_response = client.post("/api/v1/admin/categories", headers=user_headers, json=payload)
    assert forbidden_response.status_code == 403

    create_response = client.post("/api/v1/admin/categories", headers=admin_headers, json=payload)
    assert create_response.status_code == 201
    category_public_id = create_response.json()["public_id"]

    update_response = client.patch(
        f"/api/v1/admin/categories/{category_public_id}",
        headers=admin_headers,
        json={"slug": "tablet-devices"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["slug"] == "tablet-devices"

    public_response = client.get("/api/v1/categories", params={"locale": "ru"})
    assert public_response.status_code == 200
    categories = public_response.json()
    tablets = next(category for category in categories if category["slug"] == "tablet-devices")
    assert tablets["name"] == "Planshety"
    assert tablets["attributes"][0]["code"] == "storage_gb"

    delete_response = client.delete(f"/api/v1/admin/categories/{category_public_id}", headers=admin_headers)
    assert delete_response.status_code == 200

    public_after_delete = client.get("/api/v1/categories", params={"locale": "en"})
    assert all(category["slug"] != "tablet-devices" for category in public_after_delete.json())


def test_listing_crud_moderation_and_public_visibility(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]
    media_path = test_environment["media_path"]

    with session_factory() as session:
        category = _create_category_with_attributes(session)
        seller = _create_user(session, email="seller.listings@example.com", username="seller_listings", roles=[RoleCode.USER, RoleCode.SELLER])
        admin = _create_user(session, email="admin.listings@example.com", username="admin_listings", roles=[RoleCode.ADMIN, RoleCode.USER])

    seller_headers = _auth_headers(_access_token_for_user(seller, roles=[RoleCode.USER, RoleCode.SELLER]))
    admin_headers = _auth_headers(_access_token_for_user(admin, roles=[RoleCode.ADMIN, RoleCode.USER]))

    create_response = client.post(
        "/api/v1/listings",
        headers=seller_headers,
        json={
            "category_public_id": category.public_id,
            "title": "iPhone 15 Pro 256GB",
            "description": "Single-owner device in excellent condition with charging cable and box.",
            "price_amount": "1050.00",
            "currency_code": "usd",
            "item_condition": "like_new",
            "city": "Bishkek",
            "attribute_values": [
                {"attribute_code": "brand", "option_value": "apple"},
                {"attribute_code": "storage_gb", "numeric_value": "256"},
            ],
        },
    )
    assert create_response.status_code == 201
    listing = create_response.json()
    listing_public_id = listing["public_id"]
    assert listing["status"] == "draft"

    upload_response = client.post(
        f"/api/v1/listings/{listing_public_id}/media",
        headers=seller_headers,
        files={"upload": ("front.jpg", b"listing-image", "image/jpeg")},
    )
    assert upload_response.status_code == 201
    media_public_id = upload_response.json()["public_id"]
    assert (media_path / upload_response.json()["asset_key"]).exists()

    submit_response = client.post(f"/api/v1/listings/{listing_public_id}/submit-review", headers=seller_headers)
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "pending_review"

    moderation_queue = client.get("/api/v1/admin/listings/moderation", headers=admin_headers)
    assert moderation_queue.status_code == 200
    assert moderation_queue.json()["items"][0]["public_id"] == listing_public_id

    public_before_approval = client.get("/api/v1/listings")
    assert public_before_approval.status_code == 200
    assert public_before_approval.json()["items"] == []

    approve_response = client.post(
        f"/api/v1/admin/listings/{listing_public_id}/review",
        headers=admin_headers,
        json={"action": "approve", "moderation_note": "Looks good."},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "published"

    seller_notifications = client.get("/api/v1/notifications", headers=seller_headers)
    assert seller_notifications.status_code == 200
    assert seller_notifications.json()["items"][0]["notification_type"] == "listing.approved"

    public_after_approval = client.get("/api/v1/listings", params={"locale": "ru"})
    assert public_after_approval.status_code == 200
    assert public_after_approval.json()["items"][0]["public_id"] == listing_public_id
    assert public_after_approval.json()["items"][0]["category"]["name"] == "Smartfony"

    replace_response = client.put(
        f"/api/v1/listings/{listing_public_id}/media/{media_public_id}",
        headers=seller_headers,
        files={"upload": ("replacement.png", b"replacement-image", "image/png")},
    )
    assert replace_response.status_code == 200

    update_response = client.patch(
        f"/api/v1/listings/{listing_public_id}",
        headers=seller_headers,
        json={"title": "iPhone 15 Pro 256GB Updated"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "pending_review"

    public_after_edit = client.get("/api/v1/listings")
    assert public_after_edit.status_code == 200
    assert public_after_edit.json()["items"] == []


def test_listing_permissions_media_management_and_suspension_rules(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]

    with session_factory() as session:
        category = _create_category_with_attributes(session)
        owner = _create_user(session, email="owner@example.com", username="owner_user", roles=[RoleCode.USER, RoleCode.SELLER])
        other_user = _create_user(session, email="other@example.com", username="other_user", roles=[RoleCode.USER, RoleCode.SELLER])
        suspended_user = _create_user(
            session,
            email="suspended@example.com",
            username="suspended_owner",
            roles=[RoleCode.USER, RoleCode.SELLER],
            status=UserStatus.SUSPENDED,
        )

    owner_headers = _auth_headers(_access_token_for_user(owner, roles=[RoleCode.USER, RoleCode.SELLER]))
    other_headers = _auth_headers(_access_token_for_user(other_user, roles=[RoleCode.USER, RoleCode.SELLER]))
    suspended_headers = _auth_headers(_access_token_for_user(suspended_user, roles=[RoleCode.USER, RoleCode.SELLER]))

    create_response = client.post(
        "/api/v1/listings",
        headers=owner_headers,
        json={
            "category_public_id": category.public_id,
            "title": "Samsung Galaxy S24 128GB",
            "description": "Factory unlocked phone with valid receipt and very light use.",
            "price_amount": "780.00",
            "item_condition": "new",
            "city": "Bishkek",
            "attribute_values": [
                {"attribute_code": "brand", "option_value": "samsung"},
                {"attribute_code": "storage_gb", "numeric_value": "128"},
            ],
        },
    )
    assert create_response.status_code == 201
    listing_public_id = create_response.json()["public_id"]

    first_media = client.post(
        f"/api/v1/listings/{listing_public_id}/media",
        headers=owner_headers,
        files={"upload": ("front.jpg", b"front", "image/jpeg")},
    )
    second_media = client.post(
        f"/api/v1/listings/{listing_public_id}/media",
        headers=owner_headers,
        files={"upload": ("back.jpg", b"back", "image/jpeg")},
    )
    assert first_media.status_code == 201
    assert second_media.status_code == 201

    forbidden_patch = client.patch(
        f"/api/v1/listings/{listing_public_id}",
        headers=other_headers,
        json={"title": "Unauthorized edit"},
    )
    assert forbidden_patch.status_code == 403

    reorder_response = client.patch(
        f"/api/v1/listings/{listing_public_id}/media/order",
        headers=owner_headers,
        json={"media_public_ids": [second_media.json()["public_id"], first_media.json()["public_id"]]},
    )
    assert reorder_response.status_code == 200
    assert reorder_response.json()[0]["sort_order"] == 0

    primary_response = client.post(
        f"/api/v1/listings/{listing_public_id}/media/{second_media.json()['public_id']}/primary",
        headers=owner_headers,
    )
    assert primary_response.status_code == 200
    assert primary_response.json()[0]["is_primary"] is True

    submit_response = client.post(f"/api/v1/listings/{listing_public_id}/submit-review", headers=owner_headers)
    assert submit_response.status_code == 200

    delete_second = client.delete(
        f"/api/v1/listings/{listing_public_id}/media/{second_media.json()['public_id']}",
        headers=owner_headers,
    )
    assert delete_second.status_code == 200

    delete_last = client.delete(
        f"/api/v1/listings/{listing_public_id}/media/{first_media.json()['public_id']}",
        headers=owner_headers,
    )
    assert delete_last.status_code == 409
    assert delete_last.json()["error"]["code"] == "listing_requires_media"

    suspended_create = client.post(
        "/api/v1/listings",
        headers=suspended_headers,
        json={
            "category_public_id": category.public_id,
            "title": "Suspended listing",
            "description": "This should not be created because the account is suspended.",
            "price_amount": "100.00",
            "item_condition": "used_good",
            "city": "Bishkek",
            "attribute_values": [
                {"attribute_code": "brand", "option_value": "apple"},
                {"attribute_code": "storage_gb", "numeric_value": "64"},
            ],
        },
    )
    assert suspended_create.status_code == 403


def test_discovery_search_filters_sort_pagination_and_public_owner_pages(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]

    with session_factory() as session:
        smartphones = _create_category_with_attributes(session)
        tablets = _create_category_without_attributes(session, slug="tablets", name="Tablets")
        seller = _create_user(session, email="seller.discovery@example.com", username="seller_discovery", roles=[RoleCode.USER, RoleCode.SELLER])

        promoted_listing = _create_published_listing(
            session,
            seller=seller,
            category=smartphones,
            title="iPhone 14 Pro 256GB",
            description="Premium iPhone listing with full комплект and clean history.",
            price_amount="900.00",
            city="Bishkek",
            brand_option="apple",
            storage_value="256",
            promoted=True,
            published_offset_days=2,
        )
        _create_published_listing(
            session,
            seller=seller,
            category=smartphones,
            title="Samsung Galaxy S24 128GB",
            description="Samsung flagship with charger, receipt, and low battery cycles.",
            price_amount="700.00",
            city="Osh",
            brand_option="samsung",
            storage_value="128",
            published_offset_days=1,
        )
        _create_published_listing(
            session,
            seller=seller,
            category=tablets,
            title="iPad Air 64GB",
            description="Tablet listing with keyboard case and excellent screen condition.",
            price_amount="500.00",
            city="Bishkek",
            published_offset_days=0,
        )

    search_response = client.get("/api/v1/listings", params={"q": "iphone", "page": 1, "page_size": 10})
    assert search_response.status_code == 200
    assert search_response.json()["meta"]["total_items"] == 1
    assert search_response.json()["items"][0]["title"] == "iPhone 14 Pro 256GB"

    filter_response = client.get(
        "/api/v1/listings",
        params={
            "city": "Bishkek",
            "min_price": "400",
            "max_price": "950",
            "sort": "price_desc",
            "page": 1,
            "page_size": 1,
        },
    )
    assert filter_response.status_code == 200
    assert filter_response.json()["meta"]["total_items"] == 2
    assert filter_response.json()["meta"]["total_pages"] == 2
    assert filter_response.json()["items"][0]["price_amount"] == "900.00"

    promoted_response = client.get("/api/v1/listings", params={"promoted_first": True, "sort": "oldest"})
    assert promoted_response.status_code == 200
    assert promoted_response.json()["items"][0]["public_id"] == promoted_listing.public_id
    assert promoted_response.json()["items"][0]["is_promoted"] is True

    owner_profile = client.get(f"/api/v1/public/users/{seller.public_id}")
    assert owner_profile.status_code == 200
    assert owner_profile.json()["active_listing_count"] == 3

    owner_listings = client.get(
        f"/api/v1/public/users/{seller.public_id}/listings",
        params={"sort": "price_asc", "page": 1, "page_size": 2},
    )
    assert owner_listings.status_code == 200
    assert owner_listings.json()["meta"]["total_items"] == 3
    assert owner_listings.json()["items"][0]["price_amount"] == "500.00"


def test_favorites_add_remove_list_and_unavailable_listing_handling(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]

    with session_factory() as session:
        category = _create_category_with_attributes(session)
        seller = _create_user(session, email="seller.favorites@example.com", username="seller_favorites", roles=[RoleCode.USER, RoleCode.SELLER])
        buyer = _create_user(session, email="buyer.favorites@example.com", username="buyer_favorites", roles=[RoleCode.USER])
        listing = _create_published_listing(
            session,
            seller=seller,
            category=category,
            title="Google Pixel 9 128GB",
            description="Pixel phone listing with original charger and boxed accessories.",
            price_amount="650.00",
            city="Bishkek",
            brand_option="apple",
            storage_value="128",
        )

    buyer_headers = _auth_headers(_access_token_for_user(buyer, roles=[RoleCode.USER]))

    add_response = client.post(f"/api/v1/favorites/{listing.public_id}", headers=buyer_headers)
    assert add_response.status_code == 201
    assert add_response.json()["is_favorited"] is True

    duplicate_add_response = client.post(f"/api/v1/favorites/{listing.public_id}", headers=buyer_headers)
    assert duplicate_add_response.status_code == 201
    assert duplicate_add_response.json()["is_favorited"] is True

    with session_factory() as session:
        favorite_count = session.query(Favorite).filter(Favorite.user_id == buyer.id, Favorite.listing_id == listing.id).count()
        assert favorite_count == 1

    favorites_response = client.get("/api/v1/favorites", headers=buyer_headers)
    assert favorites_response.status_code == 200
    assert favorites_response.json()["meta"]["total_items"] == 1
    assert favorites_response.json()["items"][0]["is_available"] is True

    with session_factory() as session:
        listing_to_archive = session.query(Listing).filter(Listing.public_id == listing.public_id).one()
        listing_to_archive.status = ListingStatus.ARCHIVED
        session.commit()

    favorites_after_archive = client.get("/api/v1/favorites", headers=buyer_headers)
    assert favorites_after_archive.status_code == 200
    assert favorites_after_archive.json()["items"][0]["is_available"] is False
    assert favorites_after_archive.json()["items"][0]["unavailable_reason"] == "listing_archived"

    remove_response = client.delete(f"/api/v1/favorites/{listing.public_id}", headers=buyer_headers)
    assert remove_response.status_code == 200
    assert remove_response.json()["is_favorited"] is False


def test_invalid_discovery_filters_return_422_across_listing_routes(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]

    with session_factory() as session:
        seller = _create_user(session, email="seller.validation@example.com", username="seller_validation", roles=[RoleCode.USER, RoleCode.SELLER])
        admin = _create_user(session, email="admin.validation@example.com", username="admin_validation", roles=[RoleCode.ADMIN, RoleCode.USER])

    owner_headers = _auth_headers(_access_token_for_user(seller, roles=[RoleCode.USER, RoleCode.SELLER]))
    admin_headers = _auth_headers(_access_token_for_user(admin, roles=[RoleCode.ADMIN, RoleCode.USER]))

    routes = [
        ("/api/v1/listings", None),
        ("/api/v1/listings/me", owner_headers),
        (f"/api/v1/public/users/{seller.public_id}/listings", None),
        ("/api/v1/admin/listings/moderation", admin_headers),
    ]
    invalid_params = [
        {"min_price": "100", "max_price": "10"},
        {"q": "x" * 121},
        {"city": "x" * 121},
    ]

    for path, headers in routes:
        for params in invalid_params:
            response = client.get(path, headers=headers, params=params)
            assert response.status_code == 422
            assert isinstance(response.json()["detail"], list)


def test_messaging_permissions_notifications_and_self_message_protection(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]

    with session_factory() as session:
        category = _create_category_with_attributes(session)
        seller = _create_user(session, email="seller.messaging@example.com", username="seller_messaging", roles=[RoleCode.USER, RoleCode.SELLER])
        buyer = _create_user(session, email="buyer.messaging@example.com", username="buyer_messaging", roles=[RoleCode.USER])
        other_user = _create_user(session, email="other.messaging@example.com", username="other_messaging", roles=[RoleCode.USER])
        listing = _create_published_listing(
            session,
            seller=seller,
            category=category,
            title="MacBook Pro 14 M3",
            description="Powerful laptop listing with charger and low cycle count.",
            price_amount="1800.00",
            city="Bishkek",
            brand_option="apple",
            storage_value="512",
        )

    seller_headers = _auth_headers(_access_token_for_user(seller, roles=[RoleCode.USER, RoleCode.SELLER]))
    buyer_headers = _auth_headers(_access_token_for_user(buyer, roles=[RoleCode.USER]))
    other_headers = _auth_headers(_access_token_for_user(other_user, roles=[RoleCode.USER]))

    self_message_response = client.post(
        f"/api/v1/conversations/from-listing/{listing.public_id}",
        headers=seller_headers,
        data={"initial_message": "Hello myself"},
    )
    assert self_message_response.status_code == 400
    assert self_message_response.json()["error"]["code"] == "cannot_message_self"

    create_response = client.post(
        f"/api/v1/conversations/from-listing/{listing.public_id}",
        headers=buyer_headers,
        data={"initial_message": "Is this still available?"},
    )
    assert create_response.status_code == 201
    conversation_public_id = create_response.json()["public_id"]
    assert create_response.json()["messages"][0]["body"] == "Is this still available?"

    duplicate_create_response = client.post(
        f"/api/v1/conversations/from-listing/{listing.public_id}",
        headers=buyer_headers,
        data={"initial_message": "Following up on my first message."},
    )
    assert duplicate_create_response.status_code == 201
    assert duplicate_create_response.json()["public_id"] == conversation_public_id
    assert len(duplicate_create_response.json()["messages"]) == 2
    assert duplicate_create_response.json()["messages"][-1]["body"] == "Following up on my first message."

    seller_inbox = client.get("/api/v1/conversations", headers=seller_headers)
    assert seller_inbox.status_code == 200
    assert seller_inbox.json()["items"][0]["unread_count"] == 2
    assert seller_inbox.json()["items"][0]["last_message_preview"] == "Following up on my first message."

    forbidden_detail = client.get(f"/api/v1/conversations/{conversation_public_id}", headers=other_headers)
    assert forbidden_detail.status_code == 403

    seller_unread_notifications = client.get("/api/v1/notifications/unread-count", headers=seller_headers)
    assert seller_unread_notifications.status_code == 200
    assert seller_unread_notifications.json()["unread_count"] == 2

    seller_notifications = client.get("/api/v1/notifications", headers=seller_headers)
    assert seller_notifications.status_code == 200
    assert seller_notifications.json()["items"][0]["notification_type"] == "message.new"
    notification_id = seller_notifications.json()["items"][0]["id"]

    read_notification = client.post(f"/api/v1/notifications/{notification_id}/read", headers=seller_headers)
    assert read_notification.status_code == 200
    assert read_notification.json()["status"] == "read"

    mark_read_response = client.post(f"/api/v1/conversations/{conversation_public_id}/read", headers=seller_headers)
    assert mark_read_response.status_code == 200
    assert mark_read_response.json()["unread_count"] == 0


def test_duplicate_conversation_creation_is_idempotent(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]

    with session_factory() as session:
        category = _create_category_with_attributes(session)
        seller = _create_user(session, email="seller.conversation@example.com", username="seller_conversation", roles=[RoleCode.USER, RoleCode.SELLER])
        buyer = _create_user(session, email="buyer.conversation@example.com", username="buyer_conversation", roles=[RoleCode.USER])
        listing = _create_published_listing(
            session,
            seller=seller,
            category=category,
            title="Nintendo Switch OLED",
            description="Clean console bundle with dock and extra controller.",
            price_amount="320.00",
            city="Bishkek",
            brand_option="apple",
            storage_value="128",
        )
        listing_public_id = listing.public_id
        listing_id = listing.id

    buyer_headers = _auth_headers(_access_token_for_user(buyer, roles=[RoleCode.USER]))

    first_response = client.post(
        f"/api/v1/conversations/from-listing/{listing_public_id}",
        headers=buyer_headers,
        data={"initial_message": "Hi, is this available today?"},
    )
    assert first_response.status_code == 201
    conversation_public_id = first_response.json()["public_id"]

    duplicate_response = client.post(
        f"/api/v1/conversations/from-listing/{listing_public_id}",
        headers=buyer_headers,
        data={"initial_message": "Following up before I place an order."},
    )
    assert duplicate_response.status_code == 201
    assert duplicate_response.json()["public_id"] == conversation_public_id
    assert len(duplicate_response.json()["messages"]) == 2
    assert duplicate_response.json()["messages"][-1]["body"] == "Following up before I place an order."

    with session_factory() as session:
        conversation = session.query(Conversation).filter(Conversation.public_id == conversation_public_id).one()
        assert session.query(Conversation).filter(Conversation.listing_id == listing_id).count() == 1
        assert session.query(Message).filter(Message.conversation_id == conversation.id).count() == 2


def test_message_attachments_validation_and_secure_download(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]

    with session_factory() as session:
        category = _create_category_with_attributes(session)
        seller = _create_user(session, email="seller.attach@example.com", username="seller_attach", roles=[RoleCode.USER, RoleCode.SELLER])
        buyer = _create_user(session, email="buyer.attach@example.com", username="buyer_attach", roles=[RoleCode.USER])
        other_user = _create_user(session, email="other.attach@example.com", username="other_attach", roles=[RoleCode.USER])
        listing = _create_published_listing(
            session,
            seller=seller,
            category=category,
            title="Sony A7 IV Camera",
            description="Camera listing with extra battery and pristine sensor condition.",
            price_amount="1500.00",
            city="Bishkek",
            brand_option="apple",
            storage_value="128",
        )

    seller_headers = _auth_headers(_access_token_for_user(seller, roles=[RoleCode.USER, RoleCode.SELLER]))
    buyer_headers = _auth_headers(_access_token_for_user(buyer, roles=[RoleCode.USER]))
    other_headers = _auth_headers(_access_token_for_user(other_user, roles=[RoleCode.USER]))

    create_response = client.post(
        f"/api/v1/conversations/from-listing/{listing.public_id}",
        headers=buyer_headers,
        data={"initial_message": "Interested in the camera."},
    )
    assert create_response.status_code == 201
    conversation_public_id = create_response.json()["public_id"]

    invalid_attachment = client.post(
        f"/api/v1/conversations/{conversation_public_id}/messages",
        headers=seller_headers,
        data={"body": "Unsupported file"},
        files={"files": ("script.sh", b"echo hi", "application/x-sh")},
    )
    assert invalid_attachment.status_code == 400
    assert invalid_attachment.json()["error"]["code"] == "invalid_attachment_type"

    valid_attachment = client.post(
        f"/api/v1/conversations/{conversation_public_id}/messages",
        headers=seller_headers,
        data={"body": "See attached invoice."},
        files={"files": ("invoice.pdf", b"%PDF-1.4 mock", "application/pdf")},
    )
    assert valid_attachment.status_code == 201
    attachment_public_id = valid_attachment.json()["message"]["attachments"][0]["public_id"]

    forbidden_download = client.get(
        f"/api/v1/conversations/{conversation_public_id}/attachments/{attachment_public_id}",
        headers=other_headers,
    )
    assert forbidden_download.status_code == 403

    allowed_download = client.get(
        f"/api/v1/conversations/{conversation_public_id}/attachments/{attachment_public_id}",
        headers=buyer_headers,
    )
    assert allowed_download.status_code == 200
    assert allowed_download.headers["content-type"] == "application/pdf"


def test_reporting_queue_resolution_and_audit_logging(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]

    with session_factory() as session:
        category = _create_category_with_attributes(session)
        admin = _create_user(session, email="admin.reports@example.com", username="admin_reports", roles=[RoleCode.ADMIN, RoleCode.USER])
        seller = _create_user(session, email="seller.reports@example.com", username="seller_reports", roles=[RoleCode.USER, RoleCode.SELLER])
        buyer = _create_user(session, email="buyer.reports@example.com", username="buyer_reports", roles=[RoleCode.USER])
        listing = _create_published_listing(
            session,
            seller=seller,
            category=category,
            title="Canon EOS R6 Body",
            description="Camera body in good condition with shutter count under 10k.",
            price_amount="1350.00",
            city="Bishkek",
            brand_option="apple",
            storage_value="128",
        )

    buyer_headers = _auth_headers(_access_token_for_user(buyer, roles=[RoleCode.USER]))
    admin_headers = _auth_headers(_access_token_for_user(admin, roles=[RoleCode.ADMIN, RoleCode.USER]))

    listing_report = client.post(
        "/api/v1/reports",
        headers=buyer_headers,
        json={
            "listing_public_id": listing.public_id,
            "reported_user_public_id": seller.public_id,
            "reason_code": "suspicious_listing",
            "description": "The price looks suspiciously low for this model.",
        },
    )
    assert listing_report.status_code == 201
    listing_report_public_id = listing_report.json()["public_id"]
    assert listing_report.json()["status"] == "open"

    user_report = client.post(
        "/api/v1/reports",
        headers=buyer_headers,
        json={
            "reported_user_public_id": seller.public_id,
            "reason_code": "abusive_behavior",
            "description": "The seller used abusive language in chat.",
        },
    )
    assert user_report.status_code == 201
    user_report_public_id = user_report.json()["public_id"]

    my_reports = client.get("/api/v1/reports/me", headers=buyer_headers)
    assert my_reports.status_code == 200
    assert my_reports.json()["meta"]["total_items"] == 2

    admin_queue = client.get("/api/v1/admin/reports", headers=admin_headers, params={"status": "open"})
    assert admin_queue.status_code == 200
    assert admin_queue.json()["meta"]["total_items"] == 2

    resolve_listing_report = client.post(
        f"/api/v1/admin/reports/{listing_report_public_id}/resolve",
        headers=admin_headers,
        json={"action": "resolve", "resolution_note": "Listing escalated for manual moderator review."},
    )
    assert resolve_listing_report.status_code == 200
    assert resolve_listing_report.json()["status"] == "resolved"

    dismiss_user_report = client.post(
        f"/api/v1/admin/reports/{user_report_public_id}/resolve",
        headers=admin_headers,
        json={"action": "dismiss", "resolution_note": "Insufficient evidence in the report payload."},
    )
    assert dismiss_user_report.status_code == 200
    assert dismiss_user_report.json()["status"] == "rejected"

    with session_factory() as session:
        reports = session.query(Report).order_by(Report.created_at.asc()).all()
        assert reports[0].status.value == "resolved"
        assert reports[1].status.value == "rejected"
        audit_actions = {log.action for log in session.query(AdminAuditLog).all()}
        assert "report.resolve" in audit_actions
        assert "report.dismiss" in audit_actions


def test_payment_to_promotion_activation_flow_and_invalid_attempts(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]

    with session_factory() as session:
        category = _create_category_with_attributes(session)
        admin = _create_user(session, email="admin.commerce@example.com", username="admin_commerce", roles=[RoleCode.ADMIN, RoleCode.USER])
        seller = _create_user(session, email="seller.commerce@example.com", username="seller_commerce", roles=[RoleCode.USER, RoleCode.SELLER])
        listing = _create_published_listing(
            session,
            seller=seller,
            category=category,
            title="DJI Mini 4 Pro",
            description="Drone kit with spare battery, controller, and original packaging.",
            price_amount="990.00",
            city="Bishkek",
            brand_option="apple",
            storage_value="256",
        )
        draft_listing = _create_published_listing(
            session,
            seller=seller,
            category=category,
            title="Steam Deck OLED Draft",
            description="Draft console listing waiting for final photos and moderation review.",
            price_amount="650.00",
            city="Bishkek",
            brand_option="apple",
            storage_value="512",
        )
        draft_listing.status = ListingStatus.DRAFT
        draft_listing.published_at = None
        session.commit()
        session.refresh(draft_listing)

    admin_headers = _auth_headers(_access_token_for_user(admin, roles=[RoleCode.ADMIN, RoleCode.USER]))
    seller_headers = _auth_headers(_access_token_for_user(seller, roles=[RoleCode.USER, RoleCode.SELLER]))

    create_package = client.post(
        "/api/v1/admin/promotion-packages",
        headers=admin_headers,
        json={
            "code": "featured_bishkek_7d",
            "name": "Featured Bishkek 7 Days",
            "description": "Boost listing visibility in Bishkek category feeds.",
            "duration_days": 7,
            "price_amount": "10.00",
            "currency_code": "USD",
            "boost_level": 8,
        },
    )
    assert create_package.status_code == 201
    package_public_id = create_package.json()["public_id"]

    public_packages = client.get("/api/v1/promotion-packages")
    assert public_packages.status_code == 200
    assert public_packages.json()[0]["public_id"] == package_public_id

    invalid_draft_attempt = client.post(
        "/api/v1/payments/promotions/initiate",
        headers=seller_headers,
        json={
            "listing_public_id": draft_listing.public_id,
            "package_public_id": package_public_id,
            "duration_days": 7,
            "target_city": "Bishkek",
            "target_category_public_id": category.public_id,
        },
    )
    assert invalid_draft_attempt.status_code == 409
    assert invalid_draft_attempt.json()["error"]["code"] == "listing_not_promotable"

    initiate_payment = client.post(
        "/api/v1/payments/promotions/initiate",
        headers=seller_headers,
        json={
            "listing_public_id": listing.public_id,
            "package_public_id": package_public_id,
            "duration_days": 14,
            "target_city": "Bishkek",
            "target_category_public_id": category.public_id,
        },
    )
    assert initiate_payment.status_code == 201
    assert initiate_payment.json()["payment"]["status"] == "pending"
    assert initiate_payment.json()["promotion"]["status"] == "pending_payment"
    assert initiate_payment.json()["price_breakdown"]["total_amount"] == "20.00"
    payment_public_id = initiate_payment.json()["payment"]["public_id"]
    promotion_public_id = initiate_payment.json()["promotion"]["public_id"]

    seller_payments = client.get("/api/v1/payments", headers=seller_headers)
    assert seller_payments.status_code == 200
    assert seller_payments.json()["meta"]["total_items"] == 1

    seller_promotions = client.get("/api/v1/promotions/me", headers=seller_headers)
    assert seller_promotions.status_code == 200
    assert seller_promotions.json()["items"][0]["status"] == "pending_payment"

    admin_payments = client.get("/api/v1/admin/payments", headers=admin_headers)
    assert admin_payments.status_code == 200
    assert admin_payments.json()["meta"]["total_items"] == 1

    simulate_success = client.post(
        f"/api/v1/payments/{payment_public_id}/simulate",
        headers=seller_headers,
        json={"result": "successful"},
    )
    assert simulate_success.status_code == 200
    assert simulate_success.json()["payment"]["status"] == "successful"
    assert simulate_success.json()["promotion"]["status"] == "active"

    listing_detail = client.get(f"/api/v1/listings/{listing.public_id}")
    assert listing_detail.status_code == 200
    assert listing_detail.json()["is_promoted"] is True
    assert listing_detail.json()["promotion_state"]["public_id"] == promotion_public_id
    assert listing_detail.json()["promotion_state"]["status"] == "active"

    seller_notifications = client.get("/api/v1/notifications", headers=seller_headers)
    assert seller_notifications.status_code == 200
    notification_types = [item["notification_type"] for item in seller_notifications.json()["items"]]
    assert "payment.successful" in notification_types
    assert "promotion.activated" in notification_types

    with session_factory() as session:
        promotion = session.query(Promotion).filter(Promotion.public_id == promotion_public_id).one()
        promotion.ends_at = utcnow() - timedelta(days=1)
        session.commit()

    expired_promotions = client.get("/api/v1/promotions/me", headers=seller_headers)
    assert expired_promotions.status_code == 200
    assert expired_promotions.json()["items"][0]["status"] == "expired"

    notifications_after_expiry = client.get("/api/v1/notifications", headers=seller_headers)
    assert notifications_after_expiry.status_code == 200
    notification_types_after_expiry = [item["notification_type"] for item in notifications_after_expiry.json()["items"]]
    assert "promotion.expired" in notification_types_after_expiry

    with session_factory() as session:
        payment = session.query(PaymentRecord).filter(PaymentRecord.public_id == payment_public_id).one()
        assert payment.status.value == "successful"
        promotion = session.query(Promotion).filter(Promotion.public_id == promotion_public_id).one()
        assert promotion.status.value == "expired"
