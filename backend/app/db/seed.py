from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.enums import (
    AttachmentType,
    CategoryAttributeType,
    ConversationStatus,
    ListingCondition,
    ListingPurpose,
    ListingStatus,
    MediaType,
    MessageStatus,
    MessageType,
    NotificationStatus,
    PaymentStatus,
    PaymentType,
    PropertyType,
    PromotionStatus,
    ReportStatus,
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
    Message,
    MessageAttachment,
    Notification,
    PaymentRecord,
    Promotion,
    PromotionPackage,
    Report,
    Role,
    User,
    UserRole,
    UserStatusHistory,
)
from app.db.session import session_scope

ADMIN_EMAIL = "admin.demo@example.com"
ADMIN_PASSWORD = "AdminPass123!"
RENTER_EMAIL = "renter.demo@example.com"
RENTER_PASSWORD = "RenterPass123!"
RENT_SELLER_EMAIL = "rent.host@example.com"
RENT_SELLER_PASSWORD = "RentHostPass123!"
SALE_SELLER_EMAIL = "sale.agent@example.com"
SALE_SELLER_PASSWORD = "SaleAgentPass123!"
SUSPENDED_SELLER_EMAIL = "suspended.owner@example.com"
SUSPENDED_SELLER_PASSWORD = "SuspendedOwner123!"


def utcnow() -> datetime:
    return datetime.utcnow()


def get_or_create_role(session: Session, code: RoleCode, name: str, description: str) -> Role:
    role = session.execute(select(Role).where(Role.code == code)).scalar_one_or_none()
    if role is None:
        role = Role(code=code, name=name, description=description)
        session.add(role)
        session.flush()
    else:
        role.name = name
        role.description = description
    return role


def get_or_create_user(
    session: Session,
    *,
    email: str,
    username: str,
    full_name: str,
    phone: str,
    password: str,
    locale: str,
    status: UserStatus,
    verified: bool,
) -> User:
    user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            phone=phone,
            password_hash=hash_password(password),
            locale=locale,
            status=status,
            is_email_verified=verified,
        )
        session.add(user)
        session.flush()
    else:
        user.username = username
        user.full_name = full_name
        user.phone = phone
        user.password_hash = hash_password(password)
        user.locale = locale
        user.status = status
        user.is_email_verified = verified
    return user


def ensure_user_role(session: Session, user: User, role: Role) -> None:
    existing = session.execute(
        select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
    ).scalar_one_or_none()
    if existing is None:
        session.add(UserRole(user_id=user.id, role_id=role.id))


def get_or_create_category(
    session: Session,
    *,
    slug: str,
    internal_name: str,
    parent: Category | None = None,
    sort_order: int = 0,
) -> Category:
    category = session.execute(select(Category).where(Category.slug == slug)).scalar_one_or_none()
    if category is None:
        category = Category(
            slug=slug,
            internal_name=internal_name,
            parent_id=parent.id if parent else None,
            sort_order=sort_order,
        )
        session.add(category)
        session.flush()
    else:
        category.internal_name = internal_name
        category.parent_id = parent.id if parent else None
        category.sort_order = sort_order
        category.is_active = True
    return category


def upsert_category_translation(
    session: Session,
    *,
    category: Category,
    locale: str,
    name: str,
    description: str | None,
) -> None:
    translation = session.execute(
        select(CategoryTranslation).where(
            CategoryTranslation.category_id == category.id,
            CategoryTranslation.locale == locale,
        )
    ).scalar_one_or_none()
    if translation is None:
        session.add(
            CategoryTranslation(
                category_id=category.id,
                locale=locale,
                name=name,
                description=description,
            )
        )
        return

    translation.name = name
    translation.description = description


def get_or_create_category_attribute(
    session: Session,
    *,
    category: Category,
    code: str,
    display_name: str,
    data_type: CategoryAttributeType,
    unit: str | None,
    is_required: bool,
    is_filterable: bool,
    sort_order: int,
) -> CategoryAttribute:
    attribute = session.execute(
        select(CategoryAttribute).where(
            CategoryAttribute.category_id == category.id,
            CategoryAttribute.code == code,
        )
    ).scalar_one_or_none()
    if attribute is None:
        attribute = CategoryAttribute(
            category_id=category.id,
            code=code,
            display_name=display_name,
            data_type=data_type,
            unit=unit,
            is_required=is_required,
            is_filterable=is_filterable,
            sort_order=sort_order,
        )
        session.add(attribute)
        session.flush()
    else:
        attribute.display_name = display_name
        attribute.data_type = data_type
        attribute.unit = unit
        attribute.is_required = is_required
        attribute.is_filterable = is_filterable
        attribute.sort_order = sort_order
    return attribute


def upsert_attribute_option(
    session: Session,
    *,
    attribute: CategoryAttribute,
    option_value: str,
    option_label: str,
    sort_order: int,
) -> None:
    option = session.execute(
        select(CategoryAttributeOption).where(
            CategoryAttributeOption.category_attribute_id == attribute.id,
            CategoryAttributeOption.option_value == option_value,
        )
    ).scalar_one_or_none()
    if option is None:
        session.add(
            CategoryAttributeOption(
                category_attribute_id=attribute.id,
                option_value=option_value,
                option_label=option_label,
                sort_order=sort_order,
            )
        )
        return

    option.option_label = option_label
    option.sort_order = sort_order


def get_or_create_listing(
    session: Session,
    *,
    seller: User,
    category: Category,
    title: str,
    description: str,
    purpose: ListingPurpose,
    property_type: PropertyType,
    price_amount: Decimal,
    item_condition: ListingCondition | None,
    status: ListingStatus,
    city: str,
    district: str | None,
    address_text: str,
    map_label: str | None,
    latitude: Decimal,
    longitude: Decimal,
    room_count: int,
    area_sqm: Decimal,
    floor: int | None = None,
    total_floors: int | None = None,
    furnished: bool | None = None,
    moderation_note: str | None = None,
    published_at: datetime | None = None,
) -> Listing:
    listing = session.execute(select(Listing).where(Listing.title == title)).scalar_one_or_none()
    if listing is None:
        listing = Listing(
            seller_id=seller.id,
            category_id=category.id,
            title=title,
            description=description,
            purpose=purpose,
            property_type=property_type,
            price_amount=price_amount,
            item_condition=item_condition,
            status=status,
            city=city,
            district=district,
            address_text=address_text,
            map_label=map_label,
            latitude=latitude,
            longitude=longitude,
            room_count=room_count,
            area_sqm=area_sqm,
            floor=floor,
            total_floors=total_floors,
            furnished=furnished,
            moderation_note=moderation_note,
            published_at=published_at,
        )
        session.add(listing)
        session.flush()
    else:
        listing.seller_id = seller.id
        listing.category_id = category.id
        listing.description = description
        listing.purpose = purpose
        listing.property_type = property_type
        listing.price_amount = price_amount
        listing.item_condition = item_condition
        listing.status = status
        listing.city = city
        listing.district = district
        listing.address_text = address_text
        listing.map_label = map_label
        listing.latitude = latitude
        listing.longitude = longitude
        listing.room_count = room_count
        listing.area_sqm = area_sqm
        listing.floor = floor
        listing.total_floors = total_floors
        listing.furnished = furnished
        listing.moderation_note = moderation_note
        listing.published_at = published_at
    return listing


def upsert_listing_media(
    session: Session,
    *,
    listing: Listing,
    sort_order: int,
    storage_key: str,
    media_type: MediaType = MediaType.IMAGE,
    mime_type: str = "image/jpeg",
    is_primary: bool = False,
) -> None:
    media = session.execute(
        select(ListingMedia).where(
            ListingMedia.listing_id == listing.id,
            ListingMedia.sort_order == sort_order,
        )
    ).scalar_one_or_none()
    if media is None:
        session.add(
            ListingMedia(
                listing_id=listing.id,
                media_type=media_type,
                storage_key=storage_key,
                mime_type=mime_type,
                sort_order=sort_order,
                is_primary=is_primary,
            )
        )
        return

    media.media_type = media_type
    media.storage_key = storage_key
    media.mime_type = mime_type
    media.is_primary = is_primary


def upsert_listing_attribute_value(
    session: Session,
    *,
    listing: Listing,
    attribute: CategoryAttribute,
    text_value: str | None = None,
    numeric_value: Decimal | None = None,
    boolean_value: bool | None = None,
    option_value: str | None = None,
) -> None:
    existing = session.execute(
        select(ListingAttributeValue).where(
            ListingAttributeValue.listing_id == listing.id,
            ListingAttributeValue.category_attribute_id == attribute.id,
        )
    ).scalar_one_or_none()
    if existing is None:
        session.add(
            ListingAttributeValue(
                listing_id=listing.id,
                category_attribute_id=attribute.id,
                text_value=text_value,
                numeric_value=numeric_value,
                boolean_value=boolean_value,
                option_value=option_value,
            )
        )
        return

    existing.text_value = text_value
    existing.numeric_value = numeric_value
    existing.boolean_value = boolean_value
    existing.option_value = option_value


def ensure_favorite(session: Session, *, user: User, listing: Listing) -> None:
    favorite = session.execute(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.listing_id == listing.id)
    ).scalar_one_or_none()
    if favorite is None:
        session.add(Favorite(user_id=user.id, listing_id=listing.id))


def get_or_create_conversation(
    session: Session,
    *,
    listing: Listing,
    buyer: User,
    seller: User,
) -> Conversation:
    conversation = session.execute(
        select(Conversation).where(
            Conversation.listing_id == listing.id,
            Conversation.buyer_user_id == buyer.id,
            Conversation.seller_user_id == seller.id,
        )
    ).scalar_one_or_none()
    if conversation is None:
        conversation = Conversation(
            listing_id=listing.id,
            buyer_user_id=buyer.id,
            seller_user_id=seller.id,
            status=ConversationStatus.ACTIVE,
            last_message_at=utcnow(),
        )
        session.add(conversation)
        session.flush()
    else:
        conversation.status = ConversationStatus.ACTIVE
        conversation.last_message_at = utcnow()
    return conversation


def get_or_create_message(
    session: Session,
    *,
    conversation: Conversation,
    sender: User,
    body: str,
    message_type: MessageType = MessageType.TEXT,
    status: MessageStatus = MessageStatus.READ,
) -> Message:
    message = session.execute(
        select(Message).where(
            Message.conversation_id == conversation.id,
            Message.sender_user_id == sender.id,
            Message.body == body,
        )
    ).scalar_one_or_none()
    if message is None:
        message = Message(
            conversation_id=conversation.id,
            sender_user_id=sender.id,
            body=body,
            message_type=message_type,
            status=status,
            read_at=utcnow() if status == MessageStatus.READ else None,
        )
        session.add(message)
        session.flush()
    return message


def ensure_message_attachment(session: Session, *, message: Message, file_name: str, storage_key: str) -> None:
    attachment = session.execute(
        select(MessageAttachment).where(
            MessageAttachment.message_id == message.id,
            MessageAttachment.storage_key == storage_key,
        )
    ).scalar_one_or_none()
    if attachment is None:
        session.add(
            MessageAttachment(
                message_id=message.id,
                attachment_type=AttachmentType.IMAGE,
                file_name=file_name,
                storage_key=storage_key,
                mime_type="image/jpeg",
            )
        )


def ensure_notification(
    session: Session,
    *,
    user: User,
    title: str,
    body: str,
    notification_type: str,
    status: NotificationStatus,
) -> None:
    notification = session.execute(
        select(Notification).where(Notification.user_id == user.id, Notification.title == title)
    ).scalar_one_or_none()
    if notification is None:
        session.add(
            Notification(
                user_id=user.id,
                notification_type=notification_type,
                title=title,
                body=body,
                status=status,
                read_at=utcnow() if status == NotificationStatus.READ else None,
            )
        )
        return

    notification.body = body
    notification.status = status
    notification.read_at = utcnow() if status == NotificationStatus.READ else None


def ensure_report(
    session: Session,
    *,
    reporter: User,
    listing: Listing,
    reason_code: str,
    description: str,
) -> None:
    report = session.execute(
        select(Report).where(
            Report.reporter_user_id == reporter.id,
            Report.listing_id == listing.id,
            Report.reason_code == reason_code,
        )
    ).scalar_one_or_none()
    if report is None:
        session.add(
            Report(
                reporter_user_id=reporter.id,
                listing_id=listing.id,
                reason_code=reason_code,
                description=description,
                status=ReportStatus.OPEN,
            )
        )


def get_or_create_promotion_package(
    session: Session,
    *,
    code: str,
    name: str,
    description: str,
    duration_days: int,
    price_amount: Decimal,
    boost_level: int,
) -> PromotionPackage:
    package = session.execute(select(PromotionPackage).where(PromotionPackage.code == code)).scalar_one_or_none()
    if package is None:
        package = PromotionPackage(
            code=code,
            name=name,
            description=description,
            duration_days=duration_days,
            price_amount=price_amount,
            boost_level=boost_level,
        )
        session.add(package)
        session.flush()
    else:
        package.name = name
        package.description = description
        package.duration_days = duration_days
        package.price_amount = price_amount
        package.boost_level = boost_level
        package.is_active = True
    return package


def get_or_create_payment_record(
    session: Session,
    *,
    payer: User,
    listing: Listing,
    provider_reference: str,
    amount: Decimal,
    status: PaymentStatus,
) -> PaymentRecord:
    payment = session.execute(
        select(PaymentRecord).where(PaymentRecord.provider_reference == provider_reference)
    ).scalar_one_or_none()
    if payment is None:
        payment = PaymentRecord(
            payer_user_id=payer.id,
            listing_id=listing.id,
            payment_type=PaymentType.PROMOTION_PURCHASE,
            provider="demo",
            provider_reference=provider_reference,
            amount=amount,
            status=status,
            paid_at=utcnow() if status == PaymentStatus.SUCCESSFUL else None,
            metadata_json={"seeded": True},
        )
        session.add(payment)
        session.flush()
    else:
        payment.payer_user_id = payer.id
        payment.listing_id = listing.id
        payment.amount = amount
        payment.status = status
        payment.paid_at = utcnow() if status == PaymentStatus.SUCCESSFUL else None
    return payment


def ensure_promotion(
    session: Session,
    *,
    listing: Listing,
    package: PromotionPackage,
    payment: PaymentRecord,
    activated_by: User,
) -> None:
    promotion = session.execute(
        select(Promotion).where(Promotion.listing_id == listing.id, Promotion.payment_record_id == payment.id)
    ).scalar_one_or_none()
    starts_at = utcnow() - timedelta(days=1)
    ends_at = starts_at + timedelta(days=package.duration_days)
    if promotion is None:
        session.add(
            Promotion(
                listing_id=listing.id,
                promotion_package_id=package.id,
                payment_record_id=payment.id,
                activated_by_user_id=activated_by.id,
                status=PromotionStatus.ACTIVE,
                duration_days=package.duration_days,
                price_amount=payment.amount,
                currency_code=payment.currency_code,
                starts_at=starts_at,
                ends_at=ends_at,
                activated_at=starts_at,
            )
        )
        return

    promotion.promotion_package_id = package.id
    promotion.activated_by_user_id = activated_by.id
    promotion.status = PromotionStatus.ACTIVE
    promotion.duration_days = package.duration_days
    promotion.price_amount = payment.amount
    promotion.currency_code = payment.currency_code
    promotion.starts_at = starts_at
    promotion.ends_at = ends_at
    promotion.activated_at = starts_at


def ensure_admin_audit_log(
    session: Session,
    *,
    actor: User,
    action: str,
    entity_type: str,
    entity_id: str,
    description: str,
) -> None:
    log = session.execute(
        select(AdminAuditLog).where(
            AdminAuditLog.action == action,
            AdminAuditLog.entity_type == entity_type,
            AdminAuditLog.entity_id == entity_id,
        )
    ).scalar_one_or_none()
    if log is None:
        session.add(
            AdminAuditLog(
                actor_user_id=actor.id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                description=description,
                metadata_json={"seeded": True},
            )
        )


def seed_demo_data() -> None:
    with session_scope() as session:
        admin_role = get_or_create_role(session, RoleCode.ADMIN, "Administrator", "Back office administrator")
        user_role = get_or_create_role(session, RoleCode.USER, "User", "Marketplace customer")
        seller_role = get_or_create_role(session, RoleCode.SELLER, "Seller", "Property owner or agency account")

        admin = get_or_create_user(
            session,
            email=ADMIN_EMAIL,
            username="admin_demo",
            full_name="Admin Demo",
            phone="+15550000001",
            password=ADMIN_PASSWORD,
            locale="en",
            status=UserStatus.ACTIVE,
            verified=True,
        )
        renter = get_or_create_user(
            session,
            email=RENTER_EMAIL,
            username="renter_demo",
            full_name="Renter Demo",
            phone="+15550000002",
            password=RENTER_PASSWORD,
            locale="en",
            status=UserStatus.ACTIVE,
            verified=True,
        )
        rent_seller = get_or_create_user(
            session,
            email=RENT_SELLER_EMAIL,
            username="rent_host_demo",
            full_name="Rent Host Demo",
            phone="+15550000003",
            password=RENT_SELLER_PASSWORD,
            locale="en",
            status=UserStatus.ACTIVE,
            verified=True,
        )
        sale_seller = get_or_create_user(
            session,
            email=SALE_SELLER_EMAIL,
            username="sale_agent_demo",
            full_name="Sale Agent Demo",
            phone="+15550000004",
            password=SALE_SELLER_PASSWORD,
            locale="ru",
            status=UserStatus.ACTIVE,
            verified=True,
        )
        suspended_seller = get_or_create_user(
            session,
            email=SUSPENDED_SELLER_EMAIL,
            username="suspended_owner_demo",
            full_name="Suspended Owner Demo",
            phone="+15550000005",
            password=SUSPENDED_SELLER_PASSWORD,
            locale="en",
            status=UserStatus.SUSPENDED,
            verified=True,
        )

        ensure_user_role(session, admin, admin_role)
        ensure_user_role(session, renter, user_role)
        ensure_user_role(session, rent_seller, user_role)
        ensure_user_role(session, rent_seller, seller_role)
        ensure_user_role(session, sale_seller, user_role)
        ensure_user_role(session, sale_seller, seller_role)
        ensure_user_role(session, suspended_seller, user_role)
        ensure_user_role(session, suspended_seller, seller_role)
        session.flush()

        real_estate = get_or_create_category(
            session,
            slug="real-estate",
            internal_name="Real Estate",
            sort_order=1,
        )
        apartments = get_or_create_category(
            session,
            slug="apartments",
            internal_name="Apartments",
            parent=real_estate,
            sort_order=10,
        )
        houses = get_or_create_category(
            session,
            slug="houses",
            internal_name="Houses",
            parent=real_estate,
            sort_order=20,
        )

        for category, en_name, ru_name in [
            (real_estate, "Real Estate", "Nedvizhimost"),
            (apartments, "Apartments", "Kvartiry"),
            (houses, "Houses", "Doma"),
        ]:
            upsert_category_translation(
                session,
                category=category,
                locale="en",
                name=en_name,
                description=f"{en_name} listings",
            )
            upsert_category_translation(
                session,
                category=category,
                locale="ru",
                name=ru_name,
                description=f"{ru_name} ob" "yavleniya",
            )

        apartment_bathrooms = get_or_create_category_attribute(
            session,
            category=apartments,
            code="bathrooms",
            display_name="Bathrooms",
            data_type=CategoryAttributeType.NUMBER,
            unit=None,
            is_required=True,
            is_filterable=True,
            sort_order=1,
        )
        apartment_heating = get_or_create_category_attribute(
            session,
            category=apartments,
            code="heating_type",
            display_name="Heating type",
            data_type=CategoryAttributeType.SELECT,
            unit=None,
            is_required=True,
            is_filterable=True,
            sort_order=2,
        )
        apartment_pet_friendly = get_or_create_category_attribute(
            session,
            category=apartments,
            code="pet_friendly",
            display_name="Pet friendly",
            data_type=CategoryAttributeType.BOOLEAN,
            unit=None,
            is_required=False,
            is_filterable=True,
            sort_order=3,
        )
        house_bathrooms = get_or_create_category_attribute(
            session,
            category=houses,
            code="bathrooms",
            display_name="Bathrooms",
            data_type=CategoryAttributeType.NUMBER,
            unit=None,
            is_required=True,
            is_filterable=True,
            sort_order=1,
        )
        house_lot_size = get_or_create_category_attribute(
            session,
            category=houses,
            code="lot_size_sqm",
            display_name="Lot size",
            data_type=CategoryAttributeType.NUMBER,
            unit="sqm",
            is_required=False,
            is_filterable=True,
            sort_order=2,
        )
        house_parking = get_or_create_category_attribute(
            session,
            category=houses,
            code="parking",
            display_name="Parking available",
            data_type=CategoryAttributeType.BOOLEAN,
            unit=None,
            is_required=False,
            is_filterable=True,
            sort_order=3,
        )

        for index, heating_type in enumerate(["central", "gas", "electric"], start=1):
            upsert_attribute_option(
                session,
                attribute=apartment_heating,
                option_value=heating_type,
                option_label=heating_type.replace("_", " ").title(),
                sort_order=index,
            )

        rent_apartment_listing = get_or_create_listing(
            session,
            seller=rent_seller,
            category=apartments,
            title="2-room apartment near Ala-Too Square",
            description="Bright furnished apartment with renovated kitchen, balcony, and fast internet. Suitable for long-term rent.",
            purpose=ListingPurpose.RENT,
            property_type=PropertyType.APARTMENT,
            price_amount=Decimal("850.00"),
            item_condition=None,
            status=ListingStatus.PUBLISHED,
            city="Bishkek",
            district="Lenin District",
            address_text="105 Chui Avenue, Bishkek",
            map_label="Ala-Too Square area",
            latitude=Decimal("42.8746210"),
            longitude=Decimal("74.5697620"),
            room_count=2,
            area_sqm=Decimal("68.00"),
            floor=7,
            total_floors=12,
            furnished=True,
            published_at=utcnow() - timedelta(days=3),
        )
        sale_house_listing = get_or_create_listing(
            session,
            seller=sale_seller,
            category=houses,
            title="Family house with garden in Kok-Jar",
            description="Spacious detached house with private yard, updated heating, and covered parking. Ready for immediate sale.",
            purpose=ListingPurpose.SALE,
            property_type=PropertyType.HOUSE,
            price_amount=Decimal("185000.00"),
            item_condition=None,
            status=ListingStatus.PUBLISHED,
            city="Bishkek",
            district="Kok-Jar",
            address_text="14 Kok-Jar Street, Bishkek",
            map_label="Kok-Jar residential area",
            latitude=Decimal("42.8413500"),
            longitude=Decimal("74.6408500"),
            room_count=5,
            area_sqm=Decimal("210.00"),
            floor=2,
            total_floors=2,
            furnished=False,
            published_at=utcnow() - timedelta(days=2),
        )
        reported_apartment_listing = get_or_create_listing(
            session,
            seller=sale_seller,
            category=apartments,
            title="1-room apartment advertised below market",
            description="Compact apartment listed for urgent sale. Reported by a user for suspicious pricing and incomplete disclosure.",
            purpose=ListingPurpose.SALE,
            property_type=PropertyType.APARTMENT,
            price_amount=Decimal("38000.00"),
            item_condition=None,
            status=ListingStatus.PUBLISHED,
            city="Bishkek",
            district="Sverdlov District",
            address_text="22 Toktogul Street, Bishkek",
            map_label="Toktogul / Isanova area",
            latitude=Decimal("42.8799400"),
            longitude=Decimal("74.5901500"),
            room_count=1,
            area_sqm=Decimal("34.00"),
            floor=4,
            total_floors=5,
            furnished=False,
        )
        draft_house_listing = get_or_create_listing(
            session,
            seller=rent_seller,
            category=houses,
            title="Draft townhouse for rent in Asanbay",
            description="Draft property listing waiting for final photos and owner confirmation before publication.",
            purpose=ListingPurpose.RENT,
            property_type=PropertyType.HOUSE,
            price_amount=Decimal("1400.00"),
            item_condition=None,
            status=ListingStatus.DRAFT,
            city="Bishkek",
            district="Asanbay",
            address_text="8 Asanbay Lane, Bishkek",
            map_label="Asanbay area",
            latitude=Decimal("42.8205500"),
            longitude=Decimal("74.6152400"),
            room_count=4,
            area_sqm=Decimal("160.00"),
            floor=2,
            total_floors=2,
            furnished=True,
        )
        suspended_listing = get_or_create_listing(
            session,
            seller=suspended_seller,
            category=apartments,
            title="Suspended seller apartment listing",
            description="This listing belongs to a suspended seller account and should remain hidden from public discovery.",
            purpose=ListingPurpose.RENT,
            property_type=PropertyType.APARTMENT,
            price_amount=Decimal("600.00"),
            item_condition=None,
            status=ListingStatus.INACTIVE,
            city="Bishkek",
            district="Oktyabr District",
            address_text="77 Yunusaliev Avenue, Bishkek",
            map_label="South district area",
            latitude=Decimal("42.8427100"),
            longitude=Decimal("74.6209100"),
            room_count=2,
            area_sqm=Decimal("56.00"),
            floor=5,
            total_floors=9,
            furnished=True,
            moderation_note="Seller account suspended after repeated policy complaints.",
        )

        upsert_listing_media(
            session,
            listing=rent_apartment_listing,
            sort_order=1,
            storage_key="demo/listings/rent-apartment/living-room.jpg",
            is_primary=True,
        )
        upsert_listing_media(
            session,
            listing=rent_apartment_listing,
            sort_order=2,
            storage_key="demo/listings/rent-apartment/bedroom.jpg",
        )
        upsert_listing_media(
            session,
            listing=rent_apartment_listing,
            sort_order=3,
            storage_key="demo/listings/rent-apartment/tour.mp4",
            media_type=MediaType.VIDEO,
            mime_type="video/mp4",
        )
        upsert_listing_media(
            session,
            listing=sale_house_listing,
            sort_order=1,
            storage_key="demo/listings/sale-house/front.jpg",
            is_primary=True,
        )
        upsert_listing_media(
            session,
            listing=sale_house_listing,
            sort_order=2,
            storage_key="demo/listings/sale-house/garden.jpg",
        )
        upsert_listing_media(
            session,
            listing=reported_apartment_listing,
            sort_order=1,
            storage_key="demo/listings/reported-apartment/front.jpg",
            is_primary=True,
        )
        upsert_listing_media(
            session,
            listing=draft_house_listing,
            sort_order=1,
            storage_key="demo/listings/draft-house/front.jpg",
            is_primary=True,
        )
        upsert_listing_media(
            session,
            listing=suspended_listing,
            sort_order=1,
            storage_key="demo/listings/suspended-listing/front.jpg",
            is_primary=True,
        )

        upsert_listing_attribute_value(
            session,
            listing=rent_apartment_listing,
            attribute=apartment_bathrooms,
            numeric_value=Decimal("1"),
        )
        upsert_listing_attribute_value(
            session,
            listing=rent_apartment_listing,
            attribute=apartment_heating,
            option_value="central",
        )
        upsert_listing_attribute_value(
            session,
            listing=rent_apartment_listing,
            attribute=apartment_pet_friendly,
            boolean_value=True,
        )
        upsert_listing_attribute_value(
            session,
            listing=sale_house_listing,
            attribute=house_bathrooms,
            numeric_value=Decimal("2"),
        )
        upsert_listing_attribute_value(
            session,
            listing=sale_house_listing,
            attribute=house_lot_size,
            numeric_value=Decimal("380"),
        )
        upsert_listing_attribute_value(
            session,
            listing=sale_house_listing,
            attribute=house_parking,
            boolean_value=True,
        )
        upsert_listing_attribute_value(
            session,
            listing=reported_apartment_listing,
            attribute=apartment_bathrooms,
            numeric_value=Decimal("1"),
        )
        upsert_listing_attribute_value(
            session,
            listing=reported_apartment_listing,
            attribute=apartment_heating,
            option_value="gas",
        )
        upsert_listing_attribute_value(
            session,
            listing=draft_house_listing,
            attribute=house_bathrooms,
            numeric_value=Decimal("2"),
        )
        upsert_listing_attribute_value(
            session,
            listing=suspended_listing,
            attribute=apartment_bathrooms,
            numeric_value=Decimal("1"),
        )
        upsert_listing_attribute_value(
            session,
            listing=suspended_listing,
            attribute=apartment_heating,
            option_value="central",
        )

        ensure_favorite(session, user=renter, listing=rent_apartment_listing)

        conversation = get_or_create_conversation(
            session,
            listing=rent_apartment_listing,
            buyer=renter,
            seller=rent_seller,
        )
        first_message = get_or_create_message(
            session,
            conversation=conversation,
            sender=renter,
            body="Hello, is the apartment available for move-in next month?",
        )
        get_or_create_message(
            session,
            conversation=conversation,
            sender=rent_seller,
            body="Yes, it is available. I can arrange a viewing this weekend.",
        )
        ensure_message_attachment(
            session,
            message=first_message,
            file_name="income-proof.jpg",
            storage_key="demo/messages/income-proof.jpg",
        )

        ensure_notification(
            session,
            user=rent_seller,
            title="New property inquiry",
            body="Renter Demo sent a message about 2-room apartment near Ala-Too Square.",
            notification_type="message.new",
            status=NotificationStatus.UNREAD,
        )
        ensure_notification(
            session,
            user=renter,
            title="Viewing reply received",
            body="Rent Host Demo replied to your apartment inquiry.",
            notification_type="message.reply",
            status=NotificationStatus.READ,
        )

        ensure_report(
            session,
            reporter=renter,
            listing=reported_apartment_listing,
            reason_code="suspicious_pricing",
            description="The sale price looks far below market and the description feels incomplete.",
        )

        featured_package = get_or_create_promotion_package(
            session,
            code="featured_apartment_7_days",
            name="Featured apartment for 7 days",
            description="Boost apartment visibility in city and category feeds for one week.",
            duration_days=7,
            price_amount=Decimal("24.99"),
            boost_level=10,
        )
        get_or_create_promotion_package(
            session,
            code="top_city_3_days",
            name="Top city placement for 3 days",
            description="Highlights the property at the top of city results.",
            duration_days=3,
            price_amount=Decimal("12.99"),
            boost_level=5,
        )

        paid_promotion = get_or_create_payment_record(
            session,
            payer=rent_seller,
            listing=rent_apartment_listing,
            provider_reference="seed-promo-rent-apartment",
            amount=Decimal("24.99"),
            status=PaymentStatus.SUCCESSFUL,
        )
        ensure_promotion(
            session,
            listing=rent_apartment_listing,
            package=featured_package,
            payment=paid_promotion,
            activated_by=admin,
        )
        session.flush()
        active_promotion = session.execute(
            select(Promotion).where(Promotion.payment_record_id == paid_promotion.id)
        ).scalar_one()
        active_promotion.target_city = "Bishkek"
        active_promotion.target_category_id = apartments.id

        ensure_admin_audit_log(
            session,
            actor=admin,
            action="listing.moderation.publish",
            entity_type="listing",
            entity_id=rent_apartment_listing.public_id,
            description="Seeded publish log for the promoted rental apartment listing.",
        )
        ensure_admin_audit_log(
            session,
            actor=admin,
            action="user.suspend",
            entity_type="user",
            entity_id=suspended_seller.public_id,
            description="Seeded suspension audit entry for a seller with moderation history.",
        )
        session.add(
            UserStatusHistory(
                user_id=suspended_seller.id,
                previous_status=UserStatus.ACTIVE,
                new_status=UserStatus.SUSPENDED,
                changed_by_user_id=admin.id,
                reason="Suspended after repeated misleading property reports and failed identity follow-up.",
            )
        )


def main() -> None:
    seed_demo_data()
    print("Seed completed.")
    print(f"Admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"Renter: {RENTER_EMAIL} / {RENTER_PASSWORD}")
    print(f"Rent seller: {RENT_SELLER_EMAIL} / {RENT_SELLER_PASSWORD}")
    print(f"Sale seller: {SALE_SELLER_EMAIL} / {SALE_SELLER_PASSWORD}")
    print(f"Suspended seller: {SUSPENDED_SELLER_EMAIL} / {SUSPENDED_SELLER_PASSWORD}")


if __name__ == "__main__":
    main()
