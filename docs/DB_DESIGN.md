# Database Design

## Overview
The backend uses a MySQL relational schema centered on real-estate listings, messaging, report-driven moderation, and paid listing promotion. The schema is intentionally normalized for core entities, while flexible property metadata uses a hybrid strategy: category-level attribute definitions plus typed listing attribute values.

This matches the actual implementation in `backend/app/db/models/` and the initial Alembic migration in `backend/alembic/versions/20260326_0001_initial_marketplace_schema.py`.

## Core Principles
- Normalize identities, catalog structure, listings, messaging, payments, promotions, and audit data.
- Use foreign keys consistently so cross-table integrity is enforced by MySQL, not application assumptions.
- Use explicit enum/status fields for long-lived workflows.
- Use soft delete only where recovery or historical visibility is useful.
- Keep flexible per-category specs queryable instead of hiding them in a single JSON blob.

## Implemented Tables
### Access and identity
- `users`
  Fields: `public_id`, `email`, `username`, `full_name`, `phone`, `bio`, `profile_image_path`, `profile_image_mime_type`, `password_hash`, `locale`, `status`, `is_email_verified`, `last_login_at`, `deleted_at`, timestamps
  Constraints: unique `public_id`, unique `email`, unique `username`
  Indexes: `email`, `username`, `status`, `phone`
- `roles`
  Fields: `code`, `name`, `description`, timestamps
  Constraints: unique `code`
- `user_roles`
  Fields: `user_id`, `role_id`, timestamps
  Constraints: unique `(user_id, role_id)`
- `refresh_tokens`
  Fields: `user_id`, `token_hash`, `client_type`, `user_agent`, `ip_address`, `expires_at`, `revoked_at`, timestamps
  Constraints: unique `token_hash`
  Indexes: `(user_id, revoked_at)`, `expires_at`
- `password_reset_tokens`
  Fields: `user_id`, `token_hash`, `expires_at`, `used_at`, timestamps
  Constraints: unique `token_hash`
  Indexes: `expires_at`
- `user_status_history`
  Fields: `user_id`, `previous_status`, `new_status`, `changed_by_user_id`, `reason`, timestamps
  Indexes: `(user_id, created_at)`

### Catalog and localization
- `categories`
  Fields: `public_id`, `parent_id`, `slug`, `internal_name`, `is_active`, `sort_order`, `deleted_at`, timestamps
  Constraints: unique `public_id`, unique `slug`
  Indexes: `parent_id`, `(is_active, sort_order)`
- `category_translations`
  Fields: `category_id`, `locale`, `name`, `description`, timestamps
  Constraints: unique `(category_id, locale)`
- `category_attributes`
  Fields: `category_id`, `code`, `display_name`, `data_type`, `unit`, `is_required`, `is_filterable`, `sort_order`, `config_json`, timestamps
  Constraints: unique `(category_id, code)`
  Indexes: `(category_id, is_filterable)`
- `category_attribute_options`
  Fields: `category_attribute_id`, `option_value`, `option_label`, `sort_order`, timestamps
  Constraints: unique `(category_attribute_id, option_value)`

### Listings and discovery
- `listings`
  Fields: `public_id`, `seller_id`, `category_id`, `title`, `description`, `purpose`, `property_type`, `price_amount`, `currency_code`, `item_condition` (nullable legacy field), `status`, `city`, `district`, `address_text`, `map_label`, `latitude`, `longitude`, `room_count`, `area_sqm`, `floor`, `total_floors`, `furnished`, `moderation_note`, `published_at`, `deleted_at`, timestamps
  Constraints: unique `public_id`
  Indexes: `(seller_id, status, created_at)`, `(category_id, status, price_amount)`, `(status, published_at)`, `(status, city, published_at)`, `(status, price_amount)`, `(purpose, property_type, status, published_at)`, `(city, purpose, property_type, price_amount)`, `(status, area_sqm)`, `(status, room_count)`, `title`
- `listing_media`
  Fields: `public_id`, `listing_id`, `media_type`, `storage_key`, `mime_type`, `file_size_bytes`, `sort_order`, `is_primary`, `deleted_at`, timestamps
  Constraints: unique `(listing_id, sort_order)`
  Indexes: `(listing_id, is_primary)`
- `listing_attribute_values`
  Fields: `listing_id`, `category_attribute_id`, `text_value`, `numeric_value`, `boolean_value`, `option_value`, `json_value`, timestamps
  Constraints: unique `(listing_id, category_attribute_id)`
  Indexes: `(category_attribute_id, text_value)`, `(category_attribute_id, numeric_value)`, `(category_attribute_id, option_value)`
- `favorites`
  Fields: `user_id`, `listing_id`, timestamps
  Constraints: unique `(user_id, listing_id)`
  Indexes: `listing_id`, `(user_id, created_at)`

### Messaging
- `conversations`
  Fields: `public_id`, `listing_id`, `buyer_user_id`, `seller_user_id`, `status`, `last_message_at`, `deleted_at`, timestamps
  Constraints: unique `public_id`, unique `(listing_id, buyer_user_id, seller_user_id)`
  Indexes: `(status, last_message_at)`, `(buyer_user_id, last_message_at)`, `(seller_user_id, last_message_at)`
- `messages`
  Fields: `public_id`, `conversation_id`, `sender_user_id`, `body`, `message_type`, `status`, `read_at`, `deleted_at`, timestamps
  Constraints: unique `public_id`
  Indexes: `(conversation_id, created_at)`, `(sender_user_id, created_at)`, `(conversation_id, read_at)`
- `message_attachments`
  Fields: `public_id`, `message_id`, `attachment_type`, `file_name`, `storage_key`, `mime_type`, `file_size_bytes`, timestamps
  Constraints: unique `public_id`
  Indexes: `message_id`

### Notifications, reports, and admin visibility
- `notifications`
  Fields: `user_id`, `notification_type`, `title`, `body`, `data_json`, `status`, `read_at`, timestamps
  Indexes: `(user_id, status, created_at)`
- `reports`
  Fields: `public_id`, `reporter_user_id`, `reported_user_id`, `listing_id`, `conversation_id`, `reason_code`, `description`, `status`, `resolved_by_user_id`, `resolution_note`, `resolved_at`, timestamps
  Indexes: `(status, created_at)`, `listing_id`, `(reporter_user_id, created_at)`, `reported_user_id`
- `admin_audit_logs`
  Fields: `actor_user_id`, `action`, `entity_type`, `entity_id`, `description`, `ip_address`, `user_agent`, `before_json`, `after_json`, `metadata_json`, timestamps
  Indexes: `(actor_user_id, created_at)`, `(entity_type, entity_id)`, `action`

### Payments and promotions
- `payment_records`
  Fields: `public_id`, `payer_user_id`, `listing_id`, `payment_type`, `provider`, `provider_reference`, `amount`, `currency_code`, `status`, `failure_reason`, `metadata_json`, `paid_at`, `failed_at`, `cancelled_at`, `refunded_ready_at`, timestamps
  Constraints: unique `public_id`, unique `provider_reference`
  Indexes: `(payer_user_id, status, created_at)`, `provider_reference`
- `promotion_packages`
  Fields: `public_id`, `code`, `name`, `description`, `duration_days`, `price_amount`, `currency_code`, `boost_level`, `is_active`, timestamps
  Constraints: unique `public_id`, unique `code`
  Indexes: `is_active`
- `promotions`
  Fields: `public_id`, `listing_id`, `promotion_package_id`, `payment_record_id`, `activated_by_user_id`, `target_city`, `target_category_id`, `duration_days`, `price_amount`, `currency_code`, `status`, `starts_at`, `ends_at`, `activated_at`, `cancelled_at`, timestamps
  Constraints: unique `public_id`, unique `payment_record_id`
  Indexes: `(status, starts_at, ends_at)`, `(listing_id, status)`, `(target_city, status)`, `(target_category_id, status)`

## Foreign Key Strategy
- User-linked tables such as `user_roles`, `refresh_tokens`, `favorites`, `notifications`, and `messages` use foreign keys to `users`.
- Catalog-linked tables cascade from `categories` to translations and attribute definitions.
- Listing-linked tables cascade from `listings` to media, attribute values, favorites, and promotions where appropriate.
- Messaging and reporting use nullable foreign keys where the target may later disappear from the active UI but historical records should survive.
- Audit logs keep a nullable `actor_user_id` foreign key so staff history survives account deactivation.

## Status and Enum Modeling
Implemented enums:

- `users.status`: `active`, `pending_verification`, `suspended`, `deleted`
- `roles.code`: `admin`, `user`, `seller`
- `category_attributes.data_type`: `text`, `number`, `boolean`, `select`, `json`
- `listings.purpose`: `rent`, `sale`
- `listings.property_type`: `apartment`, `house`
- `listings.item_condition`: `new`, `like_new`, `used_good`, `used_fair`, `for_parts` (legacy-compatible, nullable for real-estate listings)
- `listings.status`: `draft`, `pending_review`, `published`, `rejected`, `archived`, `inactive`, `sold`
- `conversations.status`: `active`, `closed`, `blocked`
- `messages.message_type`: `text`, `image`, `system`
- `messages.status`: `sent`, `delivered`, `read`, `deleted`
- `message_attachments.attachment_type`: `image`, `file`
- `notifications.status`: `unread`, `read`, `archived`
- `reports.status`: `open`, `in_review`, `resolved`, `rejected`
- `payment_records.payment_type`: `listing_purchase`, `promotion_purchase`, `manual_adjustment`
- `payment_records.status`: `pending`, `successful`, `failed`, `cancelled`, `refunded_ready`
- `promotions.status`: `pending_payment`, `active`, `expired`, `cancelled`

## Soft Delete Strategy
Soft delete is used on entities where recovery or audit visibility is useful:

- `users`
- `categories`
- `listings`
- `listing_media`
- `conversations`
- `messages`

Hard delete is used for join and token tables where the row is operational rather than user-facing:

- `favorites`
- `refresh_tokens`
- `password_reset_tokens`
- `user_roles`

Append-only or operational history tables are not soft-deleted:

- `user_status_history`
- `admin_audit_logs`

## Dynamic Category Attributes Strategy
The implemented strategy is:

- category-level metadata in `category_attributes`
- optional choice lists in `category_attribute_options`
- typed per-listing values in `listing_attribute_values`

This is the right tradeoff for real estate because:

- core search fields such as `purpose`, `property_type`, price, rooms, area, and location belong directly on `listings`
- category-specific property details still vary by category and future growth, for example:
  - apartment-specific heating or pet rules
  - house-specific lot size or parking flags
  - future commercial, room, or land attributes
- new category attributes can be introduced without schema churn on the main listings table
- validation and filtering remain structured instead of relying on a single opaque `specs_json` blob

Why not a single JSON column on `listings`:

- it would weaken filtering by rooms, area, heating type, parking, or pet rules
- admin-managed attribute definitions would become harder to enforce
- schema discipline would drift quickly as more property categories are added

Why not a fully separate table per category:

- that would create schema explosion and excessive migration churn

The chosen model keeps the schema stable while preserving queryability.

## Seed Data Included
The seed command creates:

- 1 admin user
- 1 renter/buyer user
- 2 seller users, one for rental inventory and one for sale inventory
- 1 suspended seller with status-note history
- base roles
- real-estate, apartments, and houses categories with translations
- sample property attributes and select options
- published rental and sale listings
- one draft listing
- one reported listing
- sample listing media and attribute values
- sample video tour media
- a favorite record
- a renter-seller conversation with messages and an attachment
- sample notifications
- sample listing report data
- promotion packages
- a successful promotion payment record
- admin audit log entries and suspension history
