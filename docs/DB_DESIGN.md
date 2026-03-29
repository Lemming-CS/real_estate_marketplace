# Database Design

## Overview
The schema is built for a real-estate marketplace with:
- apartment and house listings
- rent and sale flows
- property media and optional video
- listing-linked conversations
- report-driven moderation
- promotion payments and activation
- suspension history and admin auditability

MySQL is the transactional store. SQLAlchemy models live under `backend/app/db/models/`, and migrations live under `backend/alembic/versions/`.

## Core Principles
- normalize core transactional entities
- keep status fields explicit
- use soft delete only where history/recovery matters
- keep flexible property attributes queryable
- store media outside the database, only metadata and storage keys inside it

## Implemented Tables

### Identity And Access
- `users`
  - important fields: `public_id`, `email`, `username`, `full_name`, `phone`, `bio`, `profile_image_path`, `password_hash`, `locale`, `status`, `deleted_at`
  - constraints: unique `email`, unique `username`, unique `public_id`
  - indexes: `email`, `username`, `status`, `phone`

- `roles`
  - important fields: `code`, `name`, `description`
  - constraints: unique `code`

- `user_roles`
  - important fields: `user_id`, `role_id`
  - constraints: unique `(user_id, role_id)`

- `refresh_tokens`
  - important fields: `user_id`, `token_hash`, `expires_at`, `revoked_at`
  - constraints: unique `token_hash`

- `password_reset_tokens`
  - important fields: `user_id`, `token_hash`, `expires_at`, `used_at`
  - constraints: unique `token_hash`

- `user_status_history`
  - important fields: `user_id`, `previous_status`, `new_status`, `changed_by_user_id`, `reason`
  - purpose: durable suspension/unsuspension note history
  - indexes: `(user_id, created_at)`

### Catalog And Localization
- `categories`
  - important fields: `public_id`, `parent_id`, `slug`, `internal_name`, `is_active`, `sort_order`, `deleted_at`
  - constraints: unique `slug`, unique `public_id`
  - indexes: `parent_id`, `(is_active, sort_order)`

- `category_translations`
  - important fields: `category_id`, `locale`, `name`, `description`
  - constraints: unique `(category_id, locale)`

- `category_attributes`
  - important fields: `category_id`, `code`, `display_name`, `data_type`, `unit`, `is_required`, `is_filterable`, `sort_order`, `config_json`
  - constraints: unique `(category_id, code)`

- `category_attribute_options`
  - important fields: `category_attribute_id`, `option_value`, `option_label`, `sort_order`
  - constraints: unique `(category_attribute_id, option_value)`

### Listings
- `listings`
  - important fields:
    - identity: `public_id`, `seller_id`, `category_id`
    - content: `title`, `description`
    - real-estate: `purpose`, `property_type`, `city`, `district`, `address_text`, `map_label`, `latitude`, `longitude`, `room_count`, `area_sqm`, `floor`, `total_floors`, `furnished`
    - pricing: `price_amount`, `currency_code`, `normalized_price_kgs`
    - moderation: `status`, `moderation_note`, `published_at`, `deleted_at`
    - counters: `view_count`
  - constraints: unique `public_id`
  - indexes:
    - `(seller_id, status, created_at)`
    - `(category_id, status, price_amount)`
    - `(status, published_at)`
    - `(status, city, published_at)`
    - `(status, purpose, property_type, published_at)` via composite purpose/property search indexes
    - `(status, normalized_price_kgs)`
    - `(city, purpose, property_type, normalized_price_kgs)`
    - `(status, area_sqm)`
    - `(status, room_count)`
    - `title`

- `listing_media`
  - important fields: `public_id`, `listing_id`, `media_type`, `storage_key`, `mime_type`, `file_size_bytes`, `sort_order`, `is_primary`, `deleted_at`
  - constraints: unique `(listing_id, sort_order)`
  - supports: images plus optional MP4 property video

- `listing_attribute_values`
  - important fields: `listing_id`, `category_attribute_id`, typed value columns
  - constraints: unique `(listing_id, category_attribute_id)`
  - purpose: category-driven property detail without schema explosion

- `listing_views`
  - important fields: `listing_id`, `user_id`, `guest_token`, `last_viewed_at`
  - constraints:
    - unique `(listing_id, user_id)`
    - unique `(listing_id, guest_token)`
  - purpose: deduplicated 24-hour view tracking for logged-in users and guests
  - indexes: `(listing_id, last_viewed_at)`, `user_id`, `guest_token`

### Engagement And Messaging
- `favorites`
  - important fields: `user_id`, `listing_id`
  - constraints: unique `(user_id, listing_id)`
  - indexes: `listing_id`, `(user_id, created_at)`

- `conversations`
  - important fields: `public_id`, `listing_id`, `buyer_user_id`, `seller_user_id`, `status`, `last_message_at`, `deleted_at`
  - constraints: unique `public_id`, unique `(listing_id, buyer_user_id, seller_user_id)`
  - indexes: `(buyer_user_id, last_message_at)`, `(seller_user_id, last_message_at)`, `(status, last_message_at)`

- `messages`
  - important fields: `public_id`, `conversation_id`, `sender_user_id`, `body`, `message_type`, `status`, `read_at`, `deleted_at`
  - constraints: unique `public_id`
  - indexes: `(conversation_id, created_at)`, `(conversation_id, read_at)`

- `message_attachments`
  - important fields: `public_id`, `message_id`, `attachment_type`, `file_name`, `storage_key`, `mime_type`, `file_size_bytes`
  - constraints: unique `public_id`
  - supports: image and file/document attachments

### Notifications, Reports, And Audit
- `notifications`
  - important fields: `user_id`, `notification_type`, `title`, `body`, `data_json`, `status`, `read_at`
  - indexes: `(user_id, status, created_at)`

- `reports`
  - important fields: `public_id`, `reporter_user_id`, `reported_user_id`, `listing_id`, `conversation_id`, `reason_code`, `description`, `status`, `resolved_by_user_id`, `resolution_note`, `resolved_at`
  - indexes: `(status, created_at)`, `listing_id`, `reported_user_id`, `(reporter_user_id, created_at)`
  - purpose: primary moderation intake

- `admin_audit_logs`
  - important fields: `actor_user_id`, `action`, `entity_type`, `entity_id`, `description`, `before_json`, `after_json`, `metadata_json`
  - indexes: `(actor_user_id, created_at)`, `(entity_type, entity_id)`, `action`

### Payments And Promotions
- `payment_records`
  - important fields: `public_id`, `payer_user_id`, `listing_id`, `payment_type`, `provider`, `provider_reference`, `amount`, `currency_code`, `status`, `failure_reason`, timestamps
  - constraints: unique `public_id`, unique `provider_reference`
  - indexes: `(payer_user_id, status, created_at)`, `provider_reference`

- `promotion_packages`
  - important fields: `public_id`, `code`, `name`, `description`, `duration_days`, `price_amount`, `currency_code`, `boost_level`, `is_active`
  - constraints: unique `public_id`, unique `code`
  - lifecycle: soft-disabled via `is_active`, not deleted

- `promotions`
  - important fields: `public_id`, `listing_id`, `promotion_package_id`, `payment_record_id`, `activated_by_user_id`, `target_city`, `target_category_id`, `duration_days`, `price_amount`, `currency_code`, `status`, `starts_at`, `ends_at`
  - constraints: unique `public_id`, unique `payment_record_id`
  - indexes: `(listing_id, status)`, `(status, starts_at, ends_at)`, `(target_city, status)`, `(target_category_id, status)`

## Status Enums
- `users.status`: `active`, `pending_verification`, `suspended`, `deleted`
- `listings.purpose`: `rent`, `sale`
- `listings.property_type`: `apartment`, `house`
- `listings.status`: `draft`, `pending_review`, `published`, `rejected`, `archived`, `inactive`, `sold`
- `conversations.status`: `active`, `closed`, `blocked`
- `messages.status`: `sent`, `delivered`, `read`, `deleted`
- `reports.status`: `open`, `in_review`, `resolved`, `rejected`
- `payment_records.status`: `pending`, `successful`, `failed`, `cancelled`, `refunded_ready`
- `promotions.status`: `pending_payment`, `active`, `expired`, `cancelled`

## Foreign Keys
- `users` are referenced from roles, listings, favorites, messages, notifications, reports, payments, promotions, and audit logs
- `categories` cascade to translations and attribute definitions
- `listings` are referenced by media, favorites, views, conversations, reports, payments, and promotions
- `conversations` are referenced by messages and reports
- `messages` are referenced by message attachments
- `promotion_packages` are referenced by promotions
- `payment_records` are referenced by promotions

## Soft Delete Strategy
Soft-deleted:
- `users`
- `categories`
- `listings`
- `listing_media`
- `conversations`
- `messages`

Hard-deleted or operationally removed:
- `favorites`
- `refresh_tokens`
- `password_reset_tokens`
- `user_roles`

Append-only or operational history:
- `user_status_history`
- `admin_audit_logs`

## Dynamic Category Attributes Strategy
Chosen strategy:
- category metadata in `category_attributes`
- select options in `category_attribute_options`
- typed listing values in `listing_attribute_values`

Why this is correct for the assignment:
- core real-estate filters belong directly on `listings` because they drive sort/filter/query performance
- some property details can vary by category and future scope
- this keeps filters queryable and the schema explainable

Examples of direct listing fields:
- purpose
- property type
- city/district
- rooms
- area
- coordinates
- price

Examples of attribute-driven fields:
- heating type
- pet policy
- future parking/yard/lot-size/commercial details

## Currency Normalization
Original fields remain:
- `price_amount`
- `currency_code`

Additional field:
- `normalized_price_kgs`

Purpose:
- mixed USD/KGS listings can be sorted and filtered consistently
- UI still displays the original price/currency

Current fixed conversion:
- `1 USD = 87.5 KGS`

## View Counting
`view_count` is stored on the listing row for quick response rendering.

Increment rule:
- only when a non-owner opens listing detail
- deduplicated through `listing_views`
- same user or guest token does not increment again within 24 hours

Guest tracking:
- mobile sends `X-Guest-Token`
- backend does not rely on IP address

## Suspension Notes
Suspension and unsuspension notes are stored in:
- `user_status_history.reason`

Surfaced in:
- admin user detail
- admin audit workflows
- report-driven moderation actions

This makes moderation actions explainable and reviewable after the fact.
