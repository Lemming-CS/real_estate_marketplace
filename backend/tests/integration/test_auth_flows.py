from __future__ import annotations

from decimal import Decimal

from app.core.security import hash_password
from app.db.enums import ListingPurpose, ListingStatus, PropertyType, RoleCode, UserStatus
from app.db.models import Category, Listing, Role, User, UserRole


def _register_user(client, *, email: str, username: str, password: str = "UserPass123!"):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "full_name": username.replace("_", " ").title(),
            "password": password,
            "locale": "en",
        },
    )
    assert response.status_code == 201
    return response.json()


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_register_login_refresh_and_logout_flow(test_environment):
    client = test_environment["client"]

    register_payload = _register_user(
        client,
        email="flow.user@example.com",
        username="flow_user",
    )
    assert register_payload["user"]["email"] == "flow.user@example.com"
    assert "user" in register_payload["user"]["roles"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "flow.user@example.com", "password": "UserPass123!"},
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["access_token"]
    assert login_payload["refresh_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_payload["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    refreshed_payload = refresh_response.json()
    assert refreshed_payload["refresh_token"] != login_payload["refresh_token"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refreshed_payload["refresh_token"]},
    )
    assert logout_response.status_code == 200

    refresh_after_logout = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refreshed_payload["refresh_token"]},
    )
    assert refresh_after_logout.status_code == 401
    assert refresh_after_logout.json()["error"]["code"] == "invalid_refresh_token"


def test_forgot_reset_and_login_with_new_password(test_environment):
    client = test_environment["client"]
    _register_user(client, email="reset.user@example.com", username="reset_user")

    forgot_response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "reset.user@example.com"},
    )
    assert forgot_response.status_code == 200
    debug_token = forgot_response.json()["debug_reset_token"]
    assert debug_token

    reset_response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": debug_token, "new_password": "NewPass456!"},
    )
    assert reset_response.status_code == 200

    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "reset.user@example.com", "password": "UserPass123!"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "reset.user@example.com", "password": "NewPass456!"},
    )
    assert new_login.status_code == 200


def test_current_user_profile_update_image_upload_and_owner_listings(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]
    media_path = test_environment["media_path"]

    register_payload = _register_user(
        client,
        email="seller.user@example.com",
        username="seller_user",
    )
    access_token = register_payload["access_token"]

    with session_factory() as session:
        user = session.query(User).filter(User.email == "seller.user@example.com").one()
        seller_role = session.query(Role).filter(Role.code == RoleCode.SELLER).one()
        category = Category(slug="test-category", internal_name="Test Category")
        session.add(category)
        session.flush()
        session.add(UserRole(user_id=user.id, role_id=seller_role.id))
        session.add(
            Listing(
                seller_id=user.id,
                category_id=category.id,
                title="Temporary test apartment listing",
                description="This property listing exists to test the owner endpoint and profile foundations.",
                purpose=ListingPurpose.RENT,
                property_type=PropertyType.APARTMENT,
                price_amount=Decimal("100.00"),
                item_condition=None,
                status=ListingStatus.PUBLISHED,
                city="Bishkek",
                district="Lenin District",
                address_text="100 Test Address, Bishkek",
                map_label="Test area",
                latitude=Decimal("42.8746210"),
                longitude=Decimal("74.5697620"),
                room_count=1,
                area_sqm=Decimal("32.00"),
                floor=2,
                total_floors=5,
                furnished=True,
            )
        )
        session.commit()

    me_response = client.get("/api/v1/auth/me", headers=_auth_headers(access_token))
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "seller.user@example.com"

    patch_response = client.patch(
        "/api/v1/profile/me",
        headers=_auth_headers(access_token),
        json={"bio": "Electronics enthusiast", "locale": "ru"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["bio"] == "Electronics enthusiast"
    assert patch_response.json()["locale"] == "ru"

    image_response = client.post(
        "/api/v1/profile/me/image",
        headers=_auth_headers(access_token),
        files={"file": ("avatar.png", b"fake-image-bytes", "image/png")},
    )
    assert image_response.status_code == 200
    image_path = image_response.json()["profile_image_path"]
    assert (media_path / image_path).exists()

    listings_response = client.get("/api/v1/users/me/listings", headers=_auth_headers(access_token))
    assert listings_response.status_code == 200
    assert len(listings_response.json()) == 1
    assert listings_response.json()[0]["title"] == "Temporary test apartment listing"


def test_suspended_user_cannot_login_or_access_restricted_routes(test_environment):
    client = test_environment["client"]
    session_factory = test_environment["session_factory"]

    with session_factory() as session:
        user_role = session.query(Role).filter(Role.code == RoleCode.USER).one()
        user = User(
            email="suspended.user@example.com",
            username="suspended_user",
            full_name="Suspended User",
            phone="+15551110000",
            password_hash=hash_password("Suspended123!"),
            locale="en",
            status=UserStatus.SUSPENDED,
            is_email_verified=True,
        )
        session.add(user)
        session.flush()
        session.add(UserRole(user_id=user.id, role_id=user_role.id))
        session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "suspended.user@example.com", "password": "Suspended123!"},
    )
    assert login_response.status_code == 403
    assert login_response.json()["error"]["code"] == "account_suspended"
