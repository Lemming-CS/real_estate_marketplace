"""Initial marketplace schema.

Revision ID: 20260326_0001
Revises:
Create Date: 2026-03-26 00:01:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260326_0001"
down_revision = None
branch_labels = None
depends_on = None


USER_STATUS = sa.Enum(
    "active",
    "pending_verification",
    "suspended",
    "deleted",
    name="userstatus",
    native_enum=False,
)
ROLE_CODE = sa.Enum("admin", "user", "seller", name="rolecode", native_enum=False)
CATEGORY_ATTRIBUTE_TYPE = sa.Enum(
    "text",
    "number",
    "boolean",
    "select",
    "json",
    name="categoryattributetype",
    native_enum=False,
)
LISTING_CONDITION = sa.Enum(
    "new",
    "like_new",
    "used_good",
    "used_fair",
    "for_parts",
    name="listingcondition",
    native_enum=False,
)
LISTING_STATUS = sa.Enum(
    "draft",
    "pending_review",
    "published",
    "rejected",
    "archived",
    "inactive",
    "sold",
    name="listingstatus",
    native_enum=False,
)
MEDIA_TYPE = sa.Enum("image", "video", "file", name="mediatype", native_enum=False)
CONVERSATION_STATUS = sa.Enum("active", "closed", "blocked", name="conversationstatus", native_enum=False)
MESSAGE_TYPE = sa.Enum("text", "image", "system", name="messagetype", native_enum=False)
MESSAGE_STATUS = sa.Enum("sent", "delivered", "read", "deleted", name="messagestatus", native_enum=False)
ATTACHMENT_TYPE = sa.Enum("image", "file", name="attachmenttype", native_enum=False)
NOTIFICATION_STATUS = sa.Enum("unread", "read", "archived", name="notificationstatus", native_enum=False)
REPORT_STATUS = sa.Enum("open", "in_review", "resolved", "rejected", name="reportstatus", native_enum=False)
PAYMENT_STATUS = sa.Enum("pending", "paid", "failed", "cancelled", "refunded", name="paymentstatus", native_enum=False)
PAYMENT_TYPE = sa.Enum(
    "listing_purchase",
    "promotion_purchase",
    "manual_adjustment",
    name="paymenttype",
    native_enum=False,
)
PROMOTION_STATUS = sa.Enum(
    "pending_payment",
    "active",
    "expired",
    "cancelled",
    name="promotionstatus",
    native_enum=False,
)


def timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("profile_image_path", sa.String(length=255), nullable=True),
        sa.Column("profile_image_mime_type", sa.String(length=100), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("locale", sa.String(length=8), nullable=False, server_default="en"),
        sa.Column("status", USER_STATUS, nullable=False, server_default="active"),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint("public_id", name="uq_users_public_id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_status", "users", ["status"])
    op.create_index("ix_users_phone", "users", ["phone"])

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", ROLE_CODE, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("internal_name", sa.String(length=150), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint("public_id", name="uq_categories_public_id"),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])
    op.create_index("ix_categories_is_active_sort_order", "categories", ["is_active", "sort_order"])

    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        *timestamp_columns(),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("client_type", sa.String(length=32), nullable=False, server_default="mobile"),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id_revoked_at", "refresh_tokens", ["user_id", "revoked_at"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint("token_hash", name="uq_password_reset_tokens_token_hash"),
    )
    op.create_index("ix_password_reset_tokens_expires_at", "password_reset_tokens", ["expires_at"])

    op.create_table(
        "user_status_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("previous_status", USER_STATUS, nullable=True),
        sa.Column("new_status", USER_STATUS, nullable=False),
        sa.Column("changed_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        *timestamp_columns(),
    )
    op.create_index("ix_user_status_history_user_id_created_at", "user_status_history", ["user_id", "created_at"])

    op.create_table(
        "category_translations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("locale", sa.String(length=8), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint("category_id", "locale", name="uq_category_translations_category_locale"),
    )

    op.create_table(
        "category_attributes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=150), nullable=False),
        sa.Column("data_type", CATEGORY_ATTRIBUTE_TYPE, nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_filterable", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("config_json", sa.JSON(), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint("category_id", "code", name="uq_category_attributes_category_code"),
    )
    op.create_index(
        "ix_category_attributes_category_id_filterable",
        "category_attributes",
        ["category_id", "is_filterable"],
    )

    op.create_table(
        "category_attribute_options",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "category_attribute_id",
            sa.Integer(),
            sa.ForeignKey("category_attributes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("option_value", sa.String(length=100), nullable=False),
        sa.Column("option_label", sa.String(length=150), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *timestamp_columns(),
        sa.UniqueConstraint(
            "category_attribute_id",
            "option_value",
            name="uq_category_attribute_options_attribute_value",
        ),
    )

    op.create_table(
        "listings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("seller_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("price_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("item_condition", LISTING_CONDITION, nullable=False),
        sa.Column("status", LISTING_STATUS, nullable=False, server_default="draft"),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("moderation_note", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint("public_id", name="uq_listings_public_id"),
    )
    op.create_index("ix_listings_seller_id_status_created_at", "listings", ["seller_id", "status", "created_at"])
    op.create_index("ix_listings_category_id_status_price", "listings", ["category_id", "status", "price_amount"])
    op.create_index("ix_listings_status_published_at", "listings", ["status", "published_at"])

    op.create_table(
        "listing_media",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("media_type", MEDIA_TYPE, nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint("listing_id", "sort_order", name="uq_listing_media_listing_sort_order"),
    )
    op.create_index("ix_listing_media_listing_id_is_primary", "listing_media", ["listing_id", "is_primary"])

    op.create_table(
        "listing_attribute_values",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "category_attribute_id",
            sa.Integer(),
            sa.ForeignKey("category_attributes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text_value", sa.String(length=255), nullable=True),
        sa.Column("numeric_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("boolean_value", sa.Boolean(), nullable=True),
        sa.Column("option_value", sa.String(length=100), nullable=True),
        sa.Column("json_value", sa.JSON(), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint(
            "listing_id",
            "category_attribute_id",
            name="uq_listing_attribute_values_listing_attribute",
        ),
    )
    op.create_index(
        "ix_listing_attribute_values_attribute_text",
        "listing_attribute_values",
        ["category_attribute_id", "text_value"],
    )
    op.create_index(
        "ix_listing_attribute_values_attribute_numeric",
        "listing_attribute_values",
        ["category_attribute_id", "numeric_value"],
    )
    op.create_index(
        "ix_listing_attribute_values_attribute_option",
        "listing_attribute_values",
        ["category_attribute_id", "option_value"],
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("buyer_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seller_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", CONVERSATION_STATUS, nullable=False, server_default="active"),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint("public_id", name="uq_conversations_public_id"),
        sa.UniqueConstraint(
            "listing_id",
            "buyer_user_id",
            "seller_user_id",
            name="uq_conversations_listing_buyer_seller",
        ),
    )
    op.create_index("ix_conversations_status_last_message_at", "conversations", ["status", "last_message_at"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sender_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("message_type", MESSAGE_TYPE, nullable=False, server_default="text"),
        sa.Column("status", MESSAGE_STATUS, nullable=False, server_default="sent"),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint("public_id", name="uq_messages_public_id"),
    )
    op.create_index("ix_messages_conversation_id_created_at", "messages", ["conversation_id", "created_at"])
    op.create_index("ix_messages_sender_user_id_created_at", "messages", ["sender_user_id", "created_at"])

    op.create_table(
        "message_attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attachment_type", ATTACHMENT_TYPE, nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        *timestamp_columns(),
    )

    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        *timestamp_columns(),
        sa.UniqueConstraint("user_id", "listing_id", name="uq_favorites_user_listing"),
    )
    op.create_index("ix_favorites_listing_id", "favorites", ["listing_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("notification_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("data_json", sa.JSON(), nullable=True),
        sa.Column("status", NOTIFICATION_STATUS, nullable=False, server_default="unread"),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        *timestamp_columns(),
    )
    op.create_index(
        "ix_notifications_user_id_status_created_at",
        "notifications",
        ["user_id", "status", "created_at"],
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reporter_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reported_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reason_code", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", REPORT_STATUS, nullable=False, server_default="open"),
        sa.Column("resolved_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        *timestamp_columns(),
    )
    op.create_index("ix_reports_status_created_at", "reports", ["status", "created_at"])
    op.create_index("ix_reports_listing_id", "reports", ["listing_id"])

    op.create_table(
        "payment_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("payer_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("payment_type", PAYMENT_TYPE, nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="demo"),
        sa.Column("provider_reference", sa.String(length=150), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("status", PAYMENT_STATUS, nullable=False, server_default="pending"),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint("public_id", name="uq_payment_records_public_id"),
        sa.UniqueConstraint("provider_reference", name="uq_payment_records_provider_reference"),
    )
    op.create_index(
        "ix_payment_records_payer_status_created_at",
        "payment_records",
        ["payer_user_id", "status", "created_at"],
    )
    op.create_index("ix_payment_records_provider_reference", "payment_records", ["provider_reference"])

    op.create_table(
        "promotion_packages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("price_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("boost_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        *timestamp_columns(),
        sa.UniqueConstraint("code", name="uq_promotion_packages_code"),
    )
    op.create_index("ix_promotion_packages_is_active", "promotion_packages", ["is_active"])

    op.create_table(
        "promotions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "promotion_package_id",
            sa.Integer(),
            sa.ForeignKey("promotion_packages.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "payment_record_id",
            sa.Integer(),
            sa.ForeignKey("payment_records.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("activated_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", PROMOTION_STATUS, nullable=False, server_default="pending_payment"),
        sa.Column("starts_at", sa.DateTime(), nullable=True),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
        sa.Column("activated_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint("public_id", name="uq_promotions_public_id"),
        sa.UniqueConstraint("payment_record_id", name="uq_promotions_payment_record_id"),
    )
    op.create_index("ix_promotions_status_starts_at_ends_at", "promotions", ["status", "starts_at", "ends_at"])
    op.create_index("ix_promotions_listing_id_status", "promotions", ["listing_id", "status"])

    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", sa.String(length=120), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("before_json", sa.JSON(), nullable=True),
        sa.Column("after_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *timestamp_columns(),
    )
    op.create_index("ix_admin_audit_logs_actor_created_at", "admin_audit_logs", ["actor_user_id", "created_at"])
    op.create_index("ix_admin_audit_logs_entity", "admin_audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_admin_audit_logs_action", "admin_audit_logs", ["action"])


def downgrade() -> None:
    op.drop_table("admin_audit_logs")
    op.drop_table("promotions")
    op.drop_table("promotion_packages")
    op.drop_table("payment_records")
    op.drop_table("reports")
    op.drop_table("notifications")
    op.drop_table("favorites")
    op.drop_table("message_attachments")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("listing_attribute_values")
    op.drop_table("listing_media")
    op.drop_table("listings")
    op.drop_table("category_attribute_options")
    op.drop_table("category_attributes")
    op.drop_table("category_translations")
    op.drop_table("user_status_history")
    op.drop_table("password_reset_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("user_roles")
    op.drop_table("categories")
    op.drop_table("roles")
    op.drop_table("users")
