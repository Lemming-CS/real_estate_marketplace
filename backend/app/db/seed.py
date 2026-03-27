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
    ListingStatus,
    MediaType,
    MessageStatus,
    MessageType,
    NotificationStatus,
    PaymentStatus,
    PaymentType,
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
)
from app.db.session import session_scope

ADMIN_EMAIL = "admin.demo@example.com"
ADMIN_PASSWORD = "AdminPass123!"
BUYER_EMAIL = "buyer.demo@example.com"
BUYER_PASSWORD = "BuyerPass123!"
SELLER_EMAIL = "seller.demo@example.com"
SELLER_PASSWORD = "SellerPass123!"


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
    price_amount: Decimal,
    item_condition: ListingCondition,
    status: ListingStatus,
    city: str,
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
            price_amount=price_amount,
            item_condition=item_condition,
            status=status,
            city=city,
            moderation_note=moderation_note,
            published_at=published_at,
        )
        session.add(listing)
        session.flush()
    else:
        listing.seller_id = seller.id
        listing.category_id = category.id
        listing.description = description
        listing.price_amount = price_amount
        listing.item_condition = item_condition
        listing.status = status
        listing.city = city
        listing.moderation_note = moderation_note
        listing.published_at = published_at
    return listing


def upsert_listing_media(
    session: Session,
    *,
    listing: Listing,
    sort_order: int,
    storage_key: str,
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
                media_type=MediaType.IMAGE,
                storage_key=storage_key,
                mime_type=mime_type,
                sort_order=sort_order,
                is_primary=is_primary,
            )
        )
        return

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
            paid_at=utcnow() if status == PaymentStatus.PAID else None,
            metadata_json={"seeded": True},
        )
        session.add(payment)
        session.flush()
    else:
        payment.payer_user_id = payer.id
        payment.listing_id = listing.id
        payment.amount = amount
        payment.status = status
        payment.paid_at = utcnow() if status == PaymentStatus.PAID else None
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
                starts_at=starts_at,
                ends_at=ends_at,
                activated_at=starts_at,
            )
        )
        return

    promotion.promotion_package_id = package.id
    promotion.activated_by_user_id = activated_by.id
    promotion.status = PromotionStatus.ACTIVE
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
        seller_role = get_or_create_role(session, RoleCode.SELLER, "Seller", "Seller with listing access")

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
        buyer = get_or_create_user(
            session,
            email=BUYER_EMAIL,
            username="buyer_demo",
            full_name="Buyer Demo",
            phone="+15550000002",
            password=BUYER_PASSWORD,
            locale="en",
            status=UserStatus.ACTIVE,
            verified=True,
        )
        seller = get_or_create_user(
            session,
            email=SELLER_EMAIL,
            username="seller_demo",
            full_name="Seller Demo",
            phone="+15550000003",
            password=SELLER_PASSWORD,
            locale="en",
            status=UserStatus.ACTIVE,
            verified=True,
        )

        ensure_user_role(session, admin, admin_role)
        ensure_user_role(session, buyer, user_role)
        ensure_user_role(session, seller, user_role)
        ensure_user_role(session, seller, seller_role)
        session.flush()

        electronics = get_or_create_category(
            session,
            slug="electronics",
            internal_name="Electronics",
            sort_order=1,
        )
        smartphones = get_or_create_category(
            session,
            slug="smartphones",
            internal_name="Smartphones",
            parent=electronics,
            sort_order=10,
        )
        laptops = get_or_create_category(
            session,
            slug="laptops",
            internal_name="Laptops",
            parent=electronics,
            sort_order=20,
        )

        for category, en_name, ru_name in [
            (electronics, "Electronics", "Elektronika"),
            (smartphones, "Smartphones", "Smartfony"),
            (laptops, "Laptops", "Noutbuki"),
        ]:
            upsert_category_translation(
                session,
                category=category,
                locale="en",
                name=en_name,
                description=f"{en_name} category",
            )
            upsert_category_translation(
                session,
                category=category,
                locale="ru",
                name=ru_name,
                description=f"{ru_name} kategoriya",
            )

        phone_brand = get_or_create_category_attribute(
            session,
            category=smartphones,
            code="brand",
            display_name="Brand",
            data_type=CategoryAttributeType.SELECT,
            unit=None,
            is_required=True,
            is_filterable=True,
            sort_order=1,
        )
        phone_storage = get_or_create_category_attribute(
            session,
            category=smartphones,
            code="storage_gb",
            display_name="Storage",
            data_type=CategoryAttributeType.NUMBER,
            unit="GB",
            is_required=True,
            is_filterable=True,
            sort_order=2,
        )
        laptop_ram = get_or_create_category_attribute(
            session,
            category=laptops,
            code="ram_gb",
            display_name="RAM",
            data_type=CategoryAttributeType.NUMBER,
            unit="GB",
            is_required=True,
            is_filterable=True,
            sort_order=1,
        )
        laptop_screen = get_or_create_category_attribute(
            session,
            category=laptops,
            code="screen_inches",
            display_name="Screen size",
            data_type=CategoryAttributeType.NUMBER,
            unit="in",
            is_required=True,
            is_filterable=True,
            sort_order=2,
        )

        for index, brand in enumerate(["Apple", "Samsung", "Google"], start=1):
            upsert_attribute_option(
                session,
                attribute=phone_brand,
                option_value=brand.lower(),
                option_label=brand,
                sort_order=index,
            )

        iphone_listing = get_or_create_listing(
            session,
            seller=seller,
            category=smartphones,
            title="iPhone 14 Pro 256GB",
            description="Clean condition, battery health at 91%, box included.",
            price_amount=Decimal("899.00"),
            item_condition=ListingCondition.LIKE_NEW,
            status=ListingStatus.PUBLISHED,
            city="Bishkek",
            published_at=utcnow() - timedelta(days=3),
        )
        thinkpad_listing = get_or_create_listing(
            session,
            seller=seller,
            category=laptops,
            title="Lenovo ThinkPad X1 Carbon Gen 9",
            description="Business laptop with 16GB RAM and 512GB SSD.",
            price_amount=Decimal("1190.00"),
            item_condition=ListingCondition.USED_GOOD,
            status=ListingStatus.PUBLISHED,
            city="Bishkek",
            published_at=utcnow() - timedelta(days=2),
        )
        samsung_listing = get_or_create_listing(
            session,
            seller=seller,
            category=smartphones,
            title="Samsung Galaxy S24 128GB",
            description="Freshly listed device with warranty card and original charger.",
            price_amount=Decimal("720.00"),
            item_condition=ListingCondition.NEW,
            status=ListingStatus.PENDING_REVIEW,
            city="Bishkek",
            moderation_note=None,
        )
        draft_laptop_listing = get_or_create_listing(
            session,
            seller=seller,
            category=laptops,
            title="Dell XPS 15 Draft Listing",
            description="Draft listing prepared for a high-spec laptop with RTX graphics.",
            price_amount=Decimal("1450.00"),
            item_condition=ListingCondition.LIKE_NEW,
            status=ListingStatus.DRAFT,
            city="Bishkek",
        )

        upsert_listing_media(
            session,
            listing=iphone_listing,
            sort_order=1,
            storage_key="demo/listings/iphone-14-pro/front.jpg",
            is_primary=True,
        )
        upsert_listing_media(
            session,
            listing=iphone_listing,
            sort_order=2,
            storage_key="demo/listings/iphone-14-pro/back.jpg",
        )
        upsert_listing_media(
            session,
            listing=thinkpad_listing,
            sort_order=1,
            storage_key="demo/listings/thinkpad-x1/open.jpg",
            is_primary=True,
        )
        upsert_listing_media(
            session,
            listing=samsung_listing,
            sort_order=1,
            storage_key="demo/listings/galaxy-s24/front.jpg",
            is_primary=True,
        )
        upsert_listing_media(
            session,
            listing=draft_laptop_listing,
            sort_order=1,
            storage_key="demo/listings/dell-xps-15/open.jpg",
            is_primary=True,
        )

        upsert_listing_attribute_value(
            session,
            listing=iphone_listing,
            attribute=phone_brand,
            option_value="apple",
        )
        upsert_listing_attribute_value(
            session,
            listing=iphone_listing,
            attribute=phone_storage,
            numeric_value=Decimal("256"),
        )
        upsert_listing_attribute_value(
            session,
            listing=thinkpad_listing,
            attribute=laptop_ram,
            numeric_value=Decimal("16"),
        )
        upsert_listing_attribute_value(
            session,
            listing=thinkpad_listing,
            attribute=laptop_screen,
            numeric_value=Decimal("14"),
        )
        upsert_listing_attribute_value(
            session,
            listing=samsung_listing,
            attribute=phone_brand,
            option_value="samsung",
        )
        upsert_listing_attribute_value(
            session,
            listing=samsung_listing,
            attribute=phone_storage,
            numeric_value=Decimal("128"),
        )
        upsert_listing_attribute_value(
            session,
            listing=draft_laptop_listing,
            attribute=laptop_ram,
            numeric_value=Decimal("32"),
        )
        upsert_listing_attribute_value(
            session,
            listing=draft_laptop_listing,
            attribute=laptop_screen,
            numeric_value=Decimal("15.6"),
        )

        ensure_favorite(session, user=buyer, listing=iphone_listing)

        conversation = get_or_create_conversation(
            session,
            listing=iphone_listing,
            buyer=buyer,
            seller=seller,
        )
        first_message = get_or_create_message(
            session,
            conversation=conversation,
            sender=buyer,
            body="Hi, is the iPhone still available?",
        )
        get_or_create_message(
            session,
            conversation=conversation,
            sender=seller,
            body="Yes, it is available. I can meet tomorrow after 6 PM.",
        )
        ensure_message_attachment(
            session,
            message=first_message,
            file_name="device-reference.jpg",
            storage_key="demo/messages/device-reference.jpg",
        )

        ensure_notification(
            session,
            user=seller,
            title="New buyer message",
            body="Buyer Demo sent a message about iPhone 14 Pro 256GB.",
            notification_type="message.received",
            status=NotificationStatus.UNREAD,
        )
        ensure_notification(
            session,
            user=buyer,
            title="Listing still available",
            body="Seller Demo replied to your inquiry.",
            notification_type="message.reply",
            status=NotificationStatus.READ,
        )

        ensure_report(
            session,
            reporter=buyer,
            listing=thinkpad_listing,
            reason_code="price_suspicious",
            description="Please verify whether the listing price is intentionally low.",
        )

        featured_package = get_or_create_promotion_package(
            session,
            code="featured_7_days",
            name="Featured for 7 days",
            description="Boost listing visibility in category feeds for one week.",
            duration_days=7,
            price_amount=Decimal("19.99"),
            boost_level=10,
        )
        get_or_create_promotion_package(
            session,
            code="urgent_3_days",
            name="Urgent badge for 3 days",
            description="Highlights the listing with an urgent badge.",
            duration_days=3,
            price_amount=Decimal("9.99"),
            boost_level=5,
        )

        paid_promotion = get_or_create_payment_record(
            session,
            payer=seller,
            listing=iphone_listing,
            provider_reference="seed-promo-iphone-14-pro",
            amount=Decimal("19.99"),
            status=PaymentStatus.PAID,
        )
        ensure_promotion(
            session,
            listing=iphone_listing,
            package=featured_package,
            payment=paid_promotion,
            activated_by=admin,
        )

        ensure_admin_audit_log(
            session,
            actor=admin,
            action="listing.approved",
            entity_type="listing",
            entity_id=iphone_listing.public_id,
            description="Seeded approval log for the promoted iPhone listing.",
        )
        ensure_admin_audit_log(
            session,
            actor=admin,
            action="listing.submitted_for_review",
            entity_type="listing",
            entity_id=samsung_listing.public_id,
            description="Seeded moderation queue entry for the Samsung listing.",
        )


def main() -> None:
    seed_demo_data()
    print("Seed completed.")
    print(f"Admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"Buyer: {BUYER_EMAIL} / {BUYER_PASSWORD}")
    print(f"Seller: {SELLER_EMAIL} / {SELLER_PASSWORD}")


if __name__ == "__main__":
    main()
