from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from app.core.auth import create_access_token
from app.core.auth import utcnow
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.enums import (
    CategoryAttributeType,
    ListingPurpose,
    ListingStatus,
    MediaType,
    PromotionStatus,
    PropertyType,
    RoleCode,
    UserStatus,
)
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
    ListingView,
    Message,
    PaymentRecord,
    Promotion,
    PromotionPackage,
    Report,
    Role,
    User,
    UserStatusHistory,
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
    category = Category(slug="apartments", internal_name="Apartments", is_active=True, sort_order=10)
    category.translations = [
        CategoryTranslation(locale="en", name="Apartments", description="Apartment listings"),
        CategoryTranslation(locale="ru", name="Квартиры", description="Объявления о квартирах"),
    ]
    bathrooms_attribute = CategoryAttribute(
        code="bathrooms",
        display_name="Bathrooms",
        data_type=CategoryAttributeType.NUMBER,
        is_required=True,
        is_filterable=True,
        sort_order=1,
    )
    heating_attribute = CategoryAttribute(
        code="heating_type",
        display_name="Heating type",
        data_type=CategoryAttributeType.SELECT,
        is_required=True,
        is_filterable=True,
        sort_order=2,
        options=[
            CategoryAttributeOption(option_value="central", option_label="Central", sort_order=1),
            CategoryAttributeOption(option_value="gas", option_label="Gas", sort_order=2),
        ],
    )
    pet_attribute = CategoryAttribute(
        code="pet_friendly",
        display_name="Pet friendly",
        data_type=CategoryAttributeType.BOOLEAN,
        is_required=False,
        is_filterable=True,
        sort_order=3,
    )
    category.attributes = [bathrooms_attribute, heating_attribute, pet_attribute]
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def _create_category_without_attributes(session, *, slug: str, name: str) -> Category:
    category = Category(slug=slug, internal_name=name, is_active=True, sort_order=20)
    category.translations = [
        CategoryTranslation(locale="en", name=name, description=f"{name} category"),
        CategoryTranslation(
            locale="ru",
            name="Дома" if slug == "houses" else f"{name} RU",
            description="Категория недвижимости",
        ),
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
    currency_code: str = "USD",
    purpose: ListingPurpose = ListingPurpose.SALE,
    property_type: PropertyType = PropertyType.APARTMENT,
    district: str = "Lenin District",
    room_count: int = 2,
    area_sqm: str = "68.00",
    heating_option: str | None = None,
    bathrooms_value: str | None = None,
    promoted: bool = False,
    published_offset_days: int = 0,
) -> Listing:
    listing = Listing(
        seller_id=seller.id,
        category_id=category.id,
        title=title,
        description=description,
        purpose=purpose,
        property_type=property_type,
        price_amount=Decimal(price_amount),
        currency_code=currency_code,
        item_condition=None,
        status=ListingStatus.PUBLISHED,
        city=city,
        district=district,
        address_text=f"100 Test Address, {city}",
        map_label=f"{district}, {city}",
        latitude=Decimal("42.8746210"),
        longitude=Decimal("74.5697620"),
        room_count=room_count,
        area_sqm=Decimal(area_sqm),
        floor=5 if property_type == PropertyType.APARTMENT else 2,
        total_floors=9 if property_type == PropertyType.APARTMENT else 2,
        furnished=True,
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
    if bathrooms_value and "bathrooms" in attribute_by_code:
        session.add(
            ListingAttributeValue(
                listing_id=listing.id,
                category_attribute_id=attribute_by_code["bathrooms"].id,
                numeric_value=Decimal(bathrooms_value),
            )
        )
    if heating_option and "heating_type" in attribute_by_code:
        session.add(
            ListingAttributeValue(
                listing_id=listing.id,
                category_attribute_id=attribute_by_code["heating_type"].id,
                option_value=heating_option,
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
        "slug": "commercial-space",
        "internal_name": "Commercial Space",
        "translations": [
            {"locale": "en", "name": "Commercial Space", "description": "Commercial real-estate listings"},
            {"locale": "ru", "name": "Коммерческие помещения", "description": "Коммерческая недвижимость"},
        ],
        "attributes": [
            {
                "code": "parking_spaces",
                "display_name": "Parking spaces",
                "data_type": "number",
                "unit": "spots",
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
        json={"slug": "commercial-properties"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["slug"] == "commercial-properties"

    public_response = client.get("/api/v1/categories", params={"locale": "ru"})
    assert public_response.status_code == 200
    categories = public_response.json()
    commercial = next(category for category in categories if category["slug"] == "commercial-properties")
    assert commercial["name"] == "Коммерческие помещения"
    assert commercial["attributes"][0]["code"] == "parking_spaces"

    delete_response = client.delete(f"/api/v1/admin/categories/{category_public_id}", headers=admin_headers)
    assert delete_response.status_code == 200

    public_after_delete = client.get("/api/v1/categories", params={"locale": "en"})
    assert all(category["slug"] != "commercial-properties" for category in public_after_delete.json())


def test_admin_cannot_suspend_self(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]

    with session_factory() as session:
        admin = _create_user(
            session,
            email="admin.self.block@example.com",
            username="admin_self_block",
            roles=[RoleCode.ADMIN, RoleCode.USER],
        )

    admin_headers = _auth_headers(_access_token_for_user(admin, roles=[RoleCode.ADMIN, RoleCode.USER]))

    response = client.post(
        f"/api/v1/admin/users/{admin.public_id}/status",
        headers=admin_headers,
        json={"action": "suspend", "reason": "Trying to suspend self should fail."},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "cannot_suspend_self"

    with session_factory() as session:
        refreshed_admin = session.query(User).filter(User.public_id == admin.public_id).one()
        assert refreshed_admin.status == UserStatus.ACTIVE


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
            "title": "2-room apartment with balcony",
            "description": "Freshly renovated apartment with balcony, appliances, and stable internet in a central neighborhood.",
            "purpose": "rent",
            "property_type": "apartment",
            "price_amount": "850.00",
            "currency_code": "usd",
            "city": "Bishkek",
            "district": "Lenin District",
            "address_text": "105 Chui Avenue, Bishkek",
            "map_label": "Ala-Too area",
            "latitude": "42.8746210",
            "longitude": "74.5697620",
            "room_count": 2,
            "area_sqm": "68.00",
            "floor": 7,
            "total_floors": 12,
            "furnished": True,
            "attribute_values": [
                {"attribute_code": "bathrooms", "numeric_value": "1"},
                {"attribute_code": "heating_type", "option_value": "central"},
                {"attribute_code": "pet_friendly", "boolean_value": True},
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

    submit_response = client.post(f"/api/v1/listings/{listing_public_id}/publish", headers=seller_headers)
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "published"

    moderation_queue = client.get("/api/v1/admin/listings/moderation", headers=admin_headers, params={"status": "published"})
    assert moderation_queue.status_code == 200
    assert moderation_queue.json()["items"][0]["public_id"] == listing_public_id

    public_after_publish = client.get("/api/v1/listings")
    assert public_after_publish.status_code == 200
    assert public_after_publish.json()["items"][0]["public_id"] == listing_public_id

    hide_response = client.post(
        f"/api/v1/admin/listings/{listing_public_id}/review",
        headers=admin_headers,
        json={"action": "hide", "moderation_note": "Temporarily hidden during abuse review."},
    )
    assert hide_response.status_code == 200
    assert hide_response.json()["status"] == "inactive"

    public_hidden = client.get("/api/v1/listings", params={"locale": "ru"})
    assert public_hidden.status_code == 200
    assert public_hidden.json()["items"] == []

    reactivate_response = client.post(f"/api/v1/listings/{listing_public_id}/reactivate", headers=seller_headers)
    assert reactivate_response.status_code == 200
    assert reactivate_response.json()["status"] == "published"

    public_after_reactivate = client.get("/api/v1/listings", params={"locale": "ru"})
    assert public_after_reactivate.status_code == 200
    assert public_after_reactivate.json()["items"][0]["public_id"] == listing_public_id
    assert public_after_reactivate.json()["items"][0]["category"]["name"] == "Квартиры"

    replace_response = client.put(
        f"/api/v1/listings/{listing_public_id}/media/{media_public_id}",
        headers=seller_headers,
        files={"upload": ("replacement.png", b"replacement-image", "image/png")},
    )
    assert replace_response.status_code == 200

    update_response = client.patch(
        f"/api/v1/listings/{listing_public_id}",
        headers=seller_headers,
        json={"title": "2-room apartment with balcony and new furniture"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "published"

    public_after_edit = client.get("/api/v1/listings")
    assert public_after_edit.status_code == 200
    assert public_after_edit.json()["items"][0]["title"] == "2-room apartment with balcony and new furniture"


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
            "title": "Compact studio in city center",
            "description": "Compact studio apartment with recent cosmetic repairs, washing machine, and central heating.",
            "purpose": "rent",
            "property_type": "apartment",
            "price_amount": "540.00",
            "city": "Bishkek",
            "district": "Sverdlov District",
            "address_text": "22 Toktogul Street, Bishkek",
            "map_label": "Toktogul area",
            "latitude": "42.8799400",
            "longitude": "74.5901500",
            "room_count": 1,
            "area_sqm": "34.00",
            "floor": 4,
            "total_floors": 5,
            "furnished": False,
            "attribute_values": [
                {"attribute_code": "bathrooms", "numeric_value": "1"},
                {"attribute_code": "heating_type", "option_value": "gas"},
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

    submit_response = client.post(f"/api/v1/listings/{listing_public_id}/publish", headers=owner_headers)
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "published"

    delete_second = client.delete(
        f"/api/v1/listings/{listing_public_id}/media/{second_media.json()['public_id']}",
        headers=owner_headers,
    )
    assert delete_second.status_code == 200

    delete_last = client.delete(
        f"/api/v1/listings/{listing_public_id}/media/{first_media.json()['public_id']}",
        headers=owner_headers,
    )
    assert delete_last.status_code == 200

    suspended_create = client.post(
        "/api/v1/listings",
        headers=suspended_headers,
        json={
            "category_public_id": category.public_id,
            "title": "Suspended seller listing",
            "description": "This should not be created because the account is suspended and property posting is restricted.",
            "purpose": "sale",
            "property_type": "apartment",
            "price_amount": "38000.00",
            "city": "Bishkek",
            "district": "Lenin District",
            "address_text": "1 Demo Street, Bishkek",
            "map_label": "Demo area",
            "latitude": "42.8700000",
            "longitude": "74.5800000",
            "room_count": 1,
            "area_sqm": "32.00",
            "floor": 2,
            "total_floors": 5,
            "attribute_values": [
                {"attribute_code": "bathrooms", "numeric_value": "1"},
                {"attribute_code": "heating_type", "option_value": "central"},
            ],
        },
    )
    assert suspended_create.status_code == 403


def test_discovery_search_filters_sort_pagination_and_public_owner_pages(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]

    with session_factory() as session:
        apartments = _create_category_with_attributes(session)
        houses = _create_category_without_attributes(session, slug="houses", name="Houses")
        seller = _create_user(session, email="seller.discovery@example.com", username="seller_discovery", roles=[RoleCode.USER, RoleCode.SELLER])

        promoted_listing = _create_published_listing(
            session,
            seller=seller,
            category=apartments,
            title="2-room apartment near the park",
            description="Bright apartment with furniture, balcony, and flexible move-in date.",
            price_amount="900.00",
            city="Bishkek",
            purpose=ListingPurpose.RENT,
            property_type=PropertyType.APARTMENT,
            bathrooms_value="1",
            heating_option="central",
            promoted=True,
            published_offset_days=2,
        )
        _create_published_listing(
            session,
            seller=seller,
            category=apartments,
            title="1-room apartment in Osh center",
            description="Compact rental apartment close to transport and supermarkets.",
            price_amount="700.00",
            city="Osh",
            purpose=ListingPurpose.RENT,
            property_type=PropertyType.APARTMENT,
            room_count=1,
            area_sqm="38.00",
            bathrooms_value="1",
            heating_option="gas",
            published_offset_days=1,
        )
        _create_published_listing(
            session,
            seller=seller,
            category=houses,
            title="Family house with garden",
            description="Detached house with landscaped yard, covered garage, and renovated kitchen.",
            price_amount="185000.00",
            city="Bishkek",
            purpose=ListingPurpose.SALE,
            property_type=PropertyType.HOUSE,
            room_count=5,
            area_sqm="210.00",
            published_offset_days=0,
        )

    search_response = client.get("/api/v1/listings", params={"q": "park", "page": 1, "page_size": 10})
    assert search_response.status_code == 200
    assert search_response.json()["meta"]["total_items"] == 1
    assert search_response.json()["items"][0]["title"] == "2-room apartment near the park"

    filter_response = client.get(
        "/api/v1/listings",
        params={
            "city": "Bishkek",
            "purpose": "rent",
            "property_type": "apartment",
            "min_price": "40000",
            "max_price": "95000",
            "min_area_sqm": "50",
            "sort": "price_desc",
            "page": 1,
            "page_size": 1,
        },
    )
    assert filter_response.status_code == 200
    assert filter_response.json()["meta"]["total_items"] == 1
    assert filter_response.json()["meta"]["total_pages"] == 1
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
        params={"purpose": "rent", "sort": "price_asc", "page": 1, "page_size": 2},
    )
    assert owner_listings.status_code == 200
    assert owner_listings.json()["meta"]["total_items"] == 2
    assert owner_listings.json()["items"][0]["price_amount"] == "700.00"


def test_discovery_price_sort_and_filter_use_normalized_kgs_across_currencies(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]

    with session_factory() as session:
        category = _create_category_with_attributes(session)
        seller = _create_user(
            session,
            email="seller.currency@example.com",
            username="seller_currency",
            roles=[RoleCode.USER, RoleCode.SELLER],
        )

        usd_listing = _create_published_listing(
            session,
            seller=seller,
            category=category,
            title="Sale apartment priced in USD",
            description="Apartment for sale with price stored in USD for normalized sorting checks.",
            price_amount="1500.00",
            currency_code="USD",
            city="Bishkek",
            purpose=ListingPurpose.SALE,
            property_type=PropertyType.APARTMENT,
            bathrooms_value="1",
            heating_option="central",
        )
        kgs_listing = _create_published_listing(
            session,
            seller=seller,
            category=category,
            title="Sale apartment priced in KGS",
            description="Apartment for sale with price stored in KGS for normalized sorting checks.",
            price_amount="120000.00",
            currency_code="KGS",
            city="Bishkek",
            purpose=ListingPurpose.SALE,
            property_type=PropertyType.APARTMENT,
            bathrooms_value="1",
            heating_option="central",
        )

    ascending_response = client.get(
        "/api/v1/listings",
        params={"purpose": "sale", "sort": "price_asc", "page": 1, "page_size": 10},
    )
    assert ascending_response.status_code == 200
    ascending_ids = [item["public_id"] for item in ascending_response.json()["items"]]
    assert ascending_ids.index(kgs_listing.public_id) < ascending_ids.index(usd_listing.public_id)

    descending_response = client.get(
        "/api/v1/listings",
        params={"purpose": "sale", "sort": "price_desc", "page": 1, "page_size": 10},
    )
    assert descending_response.status_code == 200
    descending_ids = [item["public_id"] for item in descending_response.json()["items"]]
    assert descending_ids.index(usd_listing.public_id) < descending_ids.index(kgs_listing.public_id)

    min_price_response = client.get(
        "/api/v1/listings",
        params={"purpose": "sale", "min_price": "125000", "page": 1, "page_size": 10},
    )
    assert min_price_response.status_code == 200
    min_price_ids = [item["public_id"] for item in min_price_response.json()["items"]]
    assert usd_listing.public_id in min_price_ids
    assert kgs_listing.public_id not in min_price_ids

    max_price_response = client.get(
        "/api/v1/listings",
        params={"purpose": "sale", "max_price": "125000", "page": 1, "page_size": 10},
    )
    assert max_price_response.status_code == 200
    max_price_ids = [item["public_id"] for item in max_price_response.json()["items"]]
    assert kgs_listing.public_id in max_price_ids
    assert usd_listing.public_id not in max_price_ids


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
            title="1-room apartment with fresh renovation",
            description="Compact apartment listing with fresh renovation, appliances, and a walkable location.",
            price_amount="650.00",
            city="Bishkek",
            purpose=ListingPurpose.RENT,
            property_type=PropertyType.APARTMENT,
            bathrooms_value="1",
            heating_option="central",
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


def test_owner_can_soft_delete_listing_and_deleted_listing_disappears_from_views(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]

    with session_factory() as session:
        category = _create_category_with_attributes(session)
        owner = _create_user(
            session,
            email="seller.delete@example.com",
            username="seller_delete",
            roles=[RoleCode.USER, RoleCode.SELLER],
        )
        other_user = _create_user(
            session,
            email="other.delete@example.com",
            username="other_delete",
            roles=[RoleCode.USER, RoleCode.SELLER],
        )
        buyer = _create_user(
            session,
            email="buyer.delete@example.com",
            username="buyer_delete",
            roles=[RoleCode.USER],
        )
        listing = _create_published_listing(
            session,
            seller=owner,
            category=category,
            title="Apartment that will be deleted",
            description="Published apartment listing prepared for delete flow verification.",
            price_amount="850.00",
            city="Bishkek",
            purpose=ListingPurpose.RENT,
            property_type=PropertyType.APARTMENT,
            bathrooms_value="1",
            heating_option="central",
        )

    owner_headers = _auth_headers(
        _access_token_for_user(owner, roles=[RoleCode.USER, RoleCode.SELLER])
    )
    other_headers = _auth_headers(
        _access_token_for_user(other_user, roles=[RoleCode.USER, RoleCode.SELLER])
    )
    buyer_headers = _auth_headers(_access_token_for_user(buyer, roles=[RoleCode.USER]))

    favorite_response = client.post(f"/api/v1/favorites/{listing.public_id}", headers=buyer_headers)
    assert favorite_response.status_code == 201

    forbidden_delete = client.delete(f"/api/v1/listings/{listing.public_id}", headers=other_headers)
    assert forbidden_delete.status_code == 403

    delete_response = client.delete(f"/api/v1/listings/{listing.public_id}", headers=owner_headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Listing deleted successfully."

    public_feed = client.get("/api/v1/listings")
    assert public_feed.status_code == 200
    assert all(item["public_id"] != listing.public_id for item in public_feed.json()["items"])

    owner_listings = client.get("/api/v1/listings/me", headers=owner_headers)
    assert owner_listings.status_code == 200
    assert all(item["public_id"] != listing.public_id for item in owner_listings.json()["items"])

    public_detail = client.get(f"/api/v1/listings/{listing.public_id}")
    assert public_detail.status_code == 404

    favorites_response = client.get("/api/v1/favorites", headers=buyer_headers)
    assert favorites_response.status_code == 200
    assert favorites_response.json()["meta"]["total_items"] == 0
    assert favorites_response.json()["items"] == []


def test_listing_counters_are_exposed_and_views_are_deduplicated_by_viewer(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]

    with session_factory() as session:
        category = _create_category_with_attributes(session)
        seller = _create_user(
            session,
            email="seller.counters@example.com",
            username="seller_counters",
            roles=[RoleCode.USER, RoleCode.SELLER],
        )
        buyer = _create_user(
            session,
            email="buyer.counters@example.com",
            username="buyer_counters",
            roles=[RoleCode.USER],
        )
        second_buyer = _create_user(
            session,
            email="buyer.second.counters@example.com",
            username="buyer_second_counters",
            roles=[RoleCode.USER],
        )
        listing = _create_published_listing(
            session,
            seller=seller,
            category=category,
            title="Family house with garden",
            description="Spacious family house listing with garden, parking, and recent renovations in a quiet area.",
            price_amount="145000.00",
            city="Bishkek",
            purpose=ListingPurpose.SALE,
            property_type=PropertyType.HOUSE,
            bathrooms_value="2",
            heating_option="gas",
        )
        session.add(Favorite(user_id=buyer.id, listing_id=listing.id))
        session.commit()

    seller_headers = _auth_headers(
        _access_token_for_user(seller, roles=[RoleCode.USER, RoleCode.SELLER])
    )
    buyer_headers = _auth_headers(_access_token_for_user(buyer, roles=[RoleCode.USER]))
    second_buyer_headers = _auth_headers(
        _access_token_for_user(second_buyer, roles=[RoleCode.USER])
    )

    feed_response = client.get("/api/v1/listings")
    assert feed_response.status_code == 200
    assert feed_response.json()["items"][0]["favorites_count"] == 1
    assert feed_response.json()["items"][0]["view_count"] == 0

    owner_detail = client.get(
        f"/api/v1/listings/{listing.public_id}",
        headers=seller_headers,
    )
    assert owner_detail.status_code == 200
    assert owner_detail.json()["favorites_count"] == 1
    assert owner_detail.json()["view_count"] == 0

    buyer_detail = client.get(
        f"/api/v1/listings/{listing.public_id}",
        headers=buyer_headers,
    )
    assert buyer_detail.status_code == 200
    assert buyer_detail.json()["favorites_count"] == 1
    assert buyer_detail.json()["view_count"] == 1

    buyer_detail_repeat = client.get(
        f"/api/v1/listings/{listing.public_id}",
        headers=buyer_headers,
    )
    assert buyer_detail_repeat.status_code == 200
    assert buyer_detail_repeat.json()["view_count"] == 1

    first_guest_detail = client.get(
        f"/api/v1/listings/{listing.public_id}",
        headers={"X-Guest-Token": "guest-a"},
    )
    assert first_guest_detail.status_code == 200
    assert first_guest_detail.json()["view_count"] == 2

    repeated_guest_detail = client.get(
        f"/api/v1/listings/{listing.public_id}",
        headers={"X-Guest-Token": "guest-a"},
    )
    assert repeated_guest_detail.status_code == 200
    assert repeated_guest_detail.json()["view_count"] == 2

    second_guest_detail = client.get(
        f"/api/v1/listings/{listing.public_id}",
        headers={"X-Guest-Token": "guest-b"},
    )
    assert second_guest_detail.status_code == 200
    assert second_guest_detail.json()["view_count"] == 3

    second_buyer_detail = client.get(
        f"/api/v1/listings/{listing.public_id}",
        headers=second_buyer_headers,
    )
    assert second_buyer_detail.status_code == 200
    assert second_buyer_detail.json()["view_count"] == 4

    with session_factory() as session:
        listing_row = session.query(Listing).filter(Listing.public_id == listing.public_id).one()
        assert listing_row.view_count == 4
        assert (
            session.query(ListingView)
            .filter(ListingView.listing_id == listing_row.id)
            .count()
            == 4
        )


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
            title="3-room apartment with mountain view",
            description="Large apartment with mountain view, renovated bathrooms, and underground parking.",
            price_amount="1350.00",
            city="Bishkek",
            purpose=ListingPurpose.RENT,
            property_type=PropertyType.APARTMENT,
            room_count=3,
            area_sqm="96.00",
            bathrooms_value="2",
            heating_option="central",
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
            title="Townhouse listing for duplicate thread test",
            description="Townhouse listing used to verify duplicate conversation creation remains idempotent.",
            price_amount="120000.00",
            city="Bishkek",
            purpose=ListingPurpose.SALE,
            property_type=PropertyType.HOUSE,
            room_count=4,
            area_sqm="160.00",
            bathrooms_value="2",
            heating_option="gas",
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
        data={"initial_message": "Подтверждаю интерес к объекту и жду ответ владельца."},
    )
    assert duplicate_response.status_code == 201
    assert duplicate_response.json()["public_id"] == conversation_public_id
    assert len(duplicate_response.json()["messages"]) == 2
    assert duplicate_response.json()["messages"][-1]["body"] == "Подтверждаю интерес к объекту и жду ответ владельца."

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
            title="Apartment listing with attachment exchange",
            description="Apartment listing used to test secure message attachment uploads and downloads.",
            price_amount="980.00",
            city="Bishkek",
            purpose=ListingPurpose.RENT,
            property_type=PropertyType.APARTMENT,
            room_count=2,
            area_sqm="72.00",
            bathrooms_value="1",
            heating_option="central",
        )

    seller_headers = _auth_headers(_access_token_for_user(seller, roles=[RoleCode.USER, RoleCode.SELLER]))
    buyer_headers = _auth_headers(_access_token_for_user(buyer, roles=[RoleCode.USER]))
    other_headers = _auth_headers(_access_token_for_user(other_user, roles=[RoleCode.USER]))

    create_response = client.post(
        f"/api/v1/conversations/from-listing/{listing.public_id}",
        headers=buyer_headers,
        data={"initial_message": "Здравствуйте, интересует эта квартира."},
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
            title="Reported sale apartment",
            description="Apartment listing used to exercise report resolution and audit logging flows.",
            price_amount="72000.00",
            city="Bishkek",
            purpose=ListingPurpose.SALE,
            property_type=PropertyType.APARTMENT,
            room_count=2,
            area_sqm="58.00",
            bathrooms_value="1",
            heating_option="gas",
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
            "description": "Слишком низкая цена для этой квартиры, похоже на сомнительное объявление.",
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
            "description": "Продавец использовал оскорбительные выражения в переписке.",
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
        json={
            "action": "resolve",
            "resolution_note": "Listing hidden and seller suspended while documents are checked.",
            "listing_action": "hide",
            "user_action": "suspend",
        },
    )
    assert resolve_listing_report.status_code == 200
    assert resolve_listing_report.json()["status"] == "resolved"
    assert resolve_listing_report.json()["listing_status"] == "inactive"
    assert resolve_listing_report.json()["reported_user_status"] == "suspended"

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
        status_history = (
            session.query(UserStatusHistory)
            .filter(UserStatusHistory.user_id == seller.id)
            .order_by(UserStatusHistory.created_at.desc(), UserStatusHistory.id.desc())
            .first()
        )
        assert status_history is not None
        assert status_history.new_status.value == "suspended"
        assert "documents are checked" in (status_history.reason or "")
        audit_actions = {log.action for log in session.query(AdminAuditLog).all()}
        assert "report.resolve" in audit_actions
        assert "report.dismiss" in audit_actions
        assert "listing.hide_from_report" in audit_actions
        assert "user.suspend_from_report" in audit_actions


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
            title="Featured apartment in city center",
            description="City-center apartment used to verify payment to promotion activation flow.",
            price_amount="99000.00",
            city="Bishkek",
            purpose=ListingPurpose.SALE,
            property_type=PropertyType.APARTMENT,
            room_count=3,
            area_sqm="92.00",
            bathrooms_value="2",
            heating_option="central",
        )
        draft_listing = _create_published_listing(
            session,
            seller=seller,
            category=category,
            title="Draft apartment listing",
            description="Draft property listing waiting for final photos before publication.",
            price_amount="65000.00",
            city="Bishkek",
            purpose=ListingPurpose.SALE,
            property_type=PropertyType.APARTMENT,
            room_count=2,
            area_sqm="60.00",
            bathrooms_value="1",
            heating_option="gas",
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
            "name": "Featured Bishkek Homes 7 Days",
            "description": "Boost property visibility in Bishkek feed placements.",
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

    deactivate_package = client.delete(
        f"/api/v1/admin/promotion-packages/{package_public_id}",
        headers=admin_headers,
    )
    assert deactivate_package.status_code == 200
    assert deactivate_package.json()["status"] == "inactive"

    hidden_packages = client.get("/api/v1/promotion-packages")
    assert hidden_packages.status_code == 200
    assert package_public_id not in [item["public_id"] for item in hidden_packages.json()]

    reactivate_package = client.post(
        f"/api/v1/admin/promotion-packages/{package_public_id}/activate",
        headers=admin_headers,
    )
    assert reactivate_package.status_code == 200
    assert reactivate_package.json()["status"] == "active"

    visible_packages_again = client.get("/api/v1/promotion-packages")
    assert visible_packages_again.status_code == 200
    assert package_public_id in [item["public_id"] for item in visible_packages_again.json()]

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

    pending_duplicate_attempt = client.post(
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
    assert pending_duplicate_attempt.status_code == 409
    assert pending_duplicate_attempt.json()["error"]["code"] == "promotion_payment_pending"

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

    active_duplicate_attempt = client.post(
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
    assert active_duplicate_attempt.status_code == 409
    assert active_duplicate_attempt.json()["error"]["code"] == "promotion_already_active"

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
