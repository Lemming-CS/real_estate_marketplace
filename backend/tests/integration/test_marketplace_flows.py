from __future__ import annotations

from app.core.auth import create_access_token
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.enums import CategoryAttributeType, RoleCode, UserStatus
from app.db.models import Category, CategoryAttribute, CategoryAttributeOption, CategoryTranslation, Role, User, UserRole


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
    assert moderation_queue.json()[0]["public_id"] == listing_public_id

    public_before_approval = client.get("/api/v1/listings")
    assert public_before_approval.status_code == 200
    assert public_before_approval.json() == []

    approve_response = client.post(
        f"/api/v1/admin/listings/{listing_public_id}/review",
        headers=admin_headers,
        json={"action": "approve", "moderation_note": "Looks good."},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "published"

    public_after_approval = client.get("/api/v1/listings", params={"locale": "ru"})
    assert public_after_approval.status_code == 200
    assert public_after_approval.json()[0]["public_id"] == listing_public_id
    assert public_after_approval.json()[0]["category"]["name"] == "Smartfony"

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
    assert public_after_edit.json() == []


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
