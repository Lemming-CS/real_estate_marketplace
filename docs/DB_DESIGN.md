# Database Design

## Design Principles
- Normalize core business entities and relationships.
- Keep flexible or provider-specific payloads in JSON only where relational querying is not core.
- Use explicit status enums for long-running workflows.
- Prefer append-only history tables for sensitive transitions.
- Model marketplace operations directly instead of hiding them in generic blobs.

## Entities and Tables
### Identity and access
#### `users`
- Purpose: all human accounts, including buyers, sellers, and admins
- Important fields:
  - `id`
  - `public_id`
  - `email`
  - `password_hash`
  - `full_name`
  - `phone`
  - `status`
  - `locale`
  - `last_login_at`
  - `created_at`
  - `updated_at`
  - `deleted_at`
- Indexes:
  - unique on `email`
  - unique on `public_id`
  - index on `status`
- Constraints:
  - `email` required and globally unique
  - `status` must be valid enum

#### `user_roles`
- Purpose: assign one or more roles to a user
- Important fields:
  - `id`
  - `user_id`
  - `role`
  - `created_at`
- Foreign keys:
  - `user_id -> users.id`
- Indexes:
  - unique on `(user_id, role)`
  - index on `role`

#### `seller_profiles`
- Purpose: seller-specific profile and verification data
- Important fields:
  - `id`
  - `user_id`
  - `display_name`
  - `bio`
  - `city`
  - `verification_status`
  - `approved_at`
  - `rejected_reason`
  - `created_at`
  - `updated_at`
- Foreign keys:
  - `user_id -> users.id`
- Indexes:
  - unique on `user_id`
  - index on `verification_status`

#### `user_addresses`
- Purpose: buyer shipping/contact addresses
- Important fields:
  - `id`
  - `user_id`
  - `label`
  - `recipient_name`
  - `phone`
  - `country_code`
  - `city`
  - `line1`
  - `line2`
  - `postal_code`
  - `is_default`
  - `created_at`
  - `updated_at`
- Foreign keys:
  - `user_id -> users.id`
- Indexes:
  - index on `user_id`

#### `refresh_tokens`
- Purpose: persistent refresh session tracking
- Important fields:
  - `id`
  - `user_id`
  - `token_hash`
  - `client_type`
  - `device_name`
  - `expires_at`
  - `last_used_at`
  - `revoked_at`
  - `created_at`
- Foreign keys:
  - `user_id -> users.id`
- Indexes:
  - unique on `token_hash`
  - index on `(user_id, revoked_at)`
  - index on `expires_at`

### Catalog
#### `categories`
- Purpose: hierarchical product categories
- Important fields:
  - `id`
  - `public_id`
  - `parent_id`
  - `name`
  - `slug`
  - `description`
  - `is_active`
  - `sort_order`
  - `created_at`
  - `updated_at`
- Foreign keys:
  - `parent_id -> categories.id`
- Indexes:
  - unique on `slug`
  - index on `parent_id`
  - index on `(is_active, sort_order)`

#### `brands`
- Purpose: normalized electronics brands
- Important fields:
  - `id`
  - `public_id`
  - `name`
  - `slug`
  - `is_active`
  - `created_at`
- Indexes:
  - unique on `slug`
  - unique on `name`

#### `category_attribute_definitions`
- Purpose: define allowed dynamic attributes per category
- Important fields:
  - `id`
  - `category_id`
  - `code`
  - `label`
  - `data_type`
  - `unit`
  - `is_required`
  - `is_filterable`
  - `is_sortable`
  - `validation_rules_json`
  - `sort_order`
  - `created_at`
- Foreign keys:
  - `category_id -> categories.id`
- Indexes:
  - unique on `(category_id, code)`
  - index on `(category_id, is_filterable)`

#### `category_attribute_options`
- Purpose: valid values for select-type attributes
- Important fields:
  - `id`
  - `attribute_definition_id`
  - `option_key`
  - `label`
  - `sort_order`
- Foreign keys:
  - `attribute_definition_id -> category_attribute_definitions.id`
- Indexes:
  - unique on `(attribute_definition_id, option_key)`

### Media and marketplace
#### `media_assets`
- Purpose: uploaded file metadata
- Important fields:
  - `id`
  - `public_id`
  - `storage_key`
  - `bucket`
  - `mime_type`
  - `file_size_bytes`
  - `checksum_sha256`
  - `uploaded_by_user_id`
  - `created_at`
  - `deleted_at`
- Foreign keys:
  - `uploaded_by_user_id -> users.id`
- Indexes:
  - unique on `public_id`
  - unique on `storage_key`
  - index on `uploaded_by_user_id`

#### `listings`
- Purpose: marketplace listings
- Important fields:
  - `id`
  - `public_id`
  - `seller_id`
  - `category_id`
  - `brand_id`
  - `title`
  - `description`
  - `condition`
  - `price_amount`
  - `currency_code`
  - `stock_quantity`
  - `city`
  - `status`
  - `moderation_status`
  - `published_at`
  - `approved_at`
  - `archived_at`
  - `sold_at`
  - `created_at`
  - `updated_at`
  - `deleted_at`
- Foreign keys:
  - `seller_id -> users.id`
  - `category_id -> categories.id`
  - `brand_id -> brands.id`
- Indexes:
  - unique on `public_id`
  - index on `(status, published_at)`
  - index on `(category_id, status, published_at)`
  - index on `(brand_id, status, published_at)`
  - index on `(seller_id, status, updated_at)`
  - index on `(price_amount, status)`
- Constraints:
  - `price_amount >= 0`
  - `stock_quantity >= 0`

#### `listing_images`
- Purpose: attach ordered listing images to listings
- Important fields:
  - `id`
  - `listing_id`
  - `media_asset_id`
  - `sort_order`
  - `is_primary`
  - `created_at`
- Foreign keys:
  - `listing_id -> listings.id`
  - `media_asset_id -> media_assets.id`
- Indexes:
  - unique on `(listing_id, sort_order)`
  - unique on `(listing_id, media_asset_id)`
  - index on `(listing_id, is_primary)`

#### `listing_attribute_values`
- Purpose: store validated category-specific specs for each listing
- Important fields:
  - `id`
  - `listing_id`
  - `attribute_definition_id`
  - `value_text`
  - `value_number`
  - `value_boolean`
  - `value_option_key`
  - `value_json`
  - `created_at`
  - `updated_at`
- Foreign keys:
  - `listing_id -> listings.id`
  - `attribute_definition_id -> category_attribute_definitions.id`
- Indexes:
  - unique on `(listing_id, attribute_definition_id)`
  - index on `(attribute_definition_id, value_text)`
  - index on `(attribute_definition_id, value_number)`
  - index on `(attribute_definition_id, value_option_key)`
- Constraints:
  - application and DB checks should ensure only the correct value column is used for each attribute type

#### `listing_favorites`
- Purpose: many-to-many relation between users and saved listings
- Important fields:
  - `id`
  - `user_id`
  - `listing_id`
  - `created_at`
- Foreign keys:
  - `user_id -> users.id`
  - `listing_id -> listings.id`
- Indexes:
  - unique on `(user_id, listing_id)`
  - index on `listing_id`

### Commerce and monetization
#### `orders`
- Purpose: purchase record for a listing
- Important fields:
  - `id`
  - `public_id`
  - `listing_id`
  - `buyer_id`
  - `seller_id`
  - `quantity`
  - `unit_price_amount`
  - `total_price_amount`
  - `currency_code`
  - `payment_method`
  - `status`
  - `shipping_address_snapshot_json`
  - `buyer_note`
  - `seller_note`
  - `confirmed_at`
  - `cancelled_at`
  - `completed_at`
  - `created_at`
  - `updated_at`
- Foreign keys:
  - `listing_id -> listings.id`
  - `buyer_id -> users.id`
  - `seller_id -> users.id`
- Indexes:
  - unique on `public_id`
  - index on `(buyer_id, created_at)`
  - index on `(seller_id, status, created_at)`
  - index on `(listing_id, status)`
- Constraints:
  - `quantity > 0`
  - `total_price_amount >= 0`

#### `order_status_history`
- Purpose: append-only order transition log
- Important fields:
  - `id`
  - `order_id`
  - `from_status`
  - `to_status`
  - `changed_by_user_id`
  - `note`
  - `created_at`
- Foreign keys:
  - `order_id -> orders.id`
  - `changed_by_user_id -> users.id`
- Indexes:
  - index on `(order_id, created_at)`

#### `payments`
- Purpose: payment records for orders and promotions
- Important fields:
  - `id`
  - `public_id`
  - `order_id`
  - `listing_promotion_id`
  - `payment_type`
  - `provider`
  - `provider_reference`
  - `amount`
  - `currency_code`
  - `status`
  - `provider_payload_json`
  - `paid_at`
  - `failed_at`
  - `created_at`
  - `updated_at`
- Foreign keys:
  - `order_id -> orders.id`
  - `listing_promotion_id -> listing_promotions.id`
- Indexes:
  - unique on `public_id`
  - index on `provider_reference`
  - index on `(order_id, status)`
  - index on `(listing_promotion_id, status)`
- Constraints:
  - exactly one of `order_id` or `listing_promotion_id` should be set
  - `amount >= 0`

#### `promotion_plans`
- Purpose: admin-managed marketplace boost plans
- Important fields:
  - `id`
  - `code`
  - `name`
  - `description`
  - `duration_days`
  - `price_amount`
  - `currency_code`
  - `priority_score`
  - `is_active`
  - `created_at`
  - `updated_at`
- Indexes:
  - unique on `code`
  - index on `is_active`

#### `listing_promotions`
- Purpose: purchased or scheduled promotion for a listing
- Important fields:
  - `id`
  - `listing_id`
  - `promotion_plan_id`
  - `status`
  - `start_at`
  - `end_at`
  - `created_by_user_id`
  - `activated_by_user_id`
  - `cancelled_by_user_id`
  - `created_at`
  - `updated_at`
- Foreign keys:
  - `listing_id -> listings.id`
  - `promotion_plan_id -> promotion_plans.id`
  - `created_by_user_id -> users.id`
  - `activated_by_user_id -> users.id`
  - `cancelled_by_user_id -> users.id`
- Indexes:
  - index on `(listing_id, status)`
  - index on `(status, start_at, end_at)`

### Operations and governance
#### `notifications`
- Purpose: in-app notifications for users
- Important fields:
  - `id`
  - `user_id`
  - `type`
  - `title`
  - `body`
  - `payload_json`
  - `read_at`
  - `created_at`
- Foreign keys:
  - `user_id -> users.id`
- Indexes:
  - index on `(user_id, read_at, created_at)`

#### `moderation_cases`
- Purpose: moderation container for listing reviews or escalations
- Important fields:
  - `id`
  - `listing_id`
  - `status`
  - `reason_code`
  - `reason_note`
  - `opened_by_user_id`
  - `assigned_admin_user_id`
  - `resolved_at`
  - `snapshot_json`
  - `created_at`
  - `updated_at`
- Foreign keys:
  - `listing_id -> listings.id`
  - `opened_by_user_id -> users.id`
  - `assigned_admin_user_id -> users.id`
- Indexes:
  - index on `(status, created_at)`
  - index on `listing_id`

#### `moderation_actions`
- Purpose: append-only record of moderation decisions
- Important fields:
  - `id`
  - `moderation_case_id`
  - `admin_user_id`
  - `action_type`
  - `note`
  - `before_snapshot_json`
  - `after_snapshot_json`
  - `created_at`
- Foreign keys:
  - `moderation_case_id -> moderation_cases.id`
  - `admin_user_id -> users.id`
- Indexes:
  - index on `(moderation_case_id, created_at)`

#### `audit_logs`
- Purpose: immutable operational and security audit trail
- Important fields:
  - `id`
  - `actor_user_id`
  - `actor_role`
  - `action`
  - `entity_type`
  - `entity_id`
  - `before_json`
  - `after_json`
  - `metadata_json`
  - `request_id`
  - `ip_address`
  - `user_agent`
  - `created_at`
- Foreign keys:
  - `actor_user_id -> users.id`
- Indexes:
  - index on `(entity_type, entity_id, created_at)`
  - index on `(actor_user_id, created_at)`
  - index on `action`

## Soft-Delete Strategy
- Use `deleted_at` on recoverable business entities such as `users`, `media_assets`, and `listings`.
- Do not soft-delete append-only history tables such as `order_status_history`, `moderation_actions`, or `audit_logs`.
- For join tables like `listing_favorites`, hard delete is acceptable.
- Because MySQL does not offer the same partial unique index ergonomics as PostgreSQL, unique fields like `users.email` should remain globally unique even after soft delete.
- Repository queries must consistently filter out soft-deleted rows unless explicitly requested for admin recovery or audit purposes.

## Status Enums
Recommended enums:

- `users.status`: `active`, `blocked`, `pending_verification`
- `seller_profiles.verification_status`: `pending`, `approved`, `rejected`
- `listings.status`: `draft`, `pending_review`, `published`, `rejected`, `archived`, `sold`
- `orders.status`: `pending_confirmation`, `confirmed`, `awaiting_payment`, `paid`, `ready_for_delivery`, `shipped`, `delivered`, `cancelled`
- `payments.status`: `pending`, `paid`, `failed`, `cancelled`, `refunded`
- `listing_promotions.status`: `pending_payment`, `scheduled`, `active`, `expired`, `cancelled`
- `moderation_cases.status`: `open`, `approved`, `rejected`, `escalated`, `closed`

Enums should be versioned carefully because they affect mobile UI state, admin actions, and seed/demo scenarios.

## What Should Be Normalized vs JSON
### Normalize
- users, roles, seller profiles
- categories, brands, attribute definitions, option lists
- listings and prices
- listing-to-image relations
- orders, payments, promotions
- moderation and audit entity references

### JSON is acceptable for
- `validation_rules_json` in attribute definitions
- `shipping_address_snapshot_json` in orders
- `provider_payload_json` in payments
- `payload_json` in notifications
- moderation snapshots
- audit before/after metadata

The rule is to normalize anything that will be joined, filtered, permission-checked, or audited as a core business object.

## Dynamic Category Attributes Strategy
Electronics categories vary too much for a single flat listings table. A phone, laptop, and TV do not share the same spec fields, but filtering still matters.

Chosen strategy:

- keep attribute definitions normalized in `category_attribute_definitions`
- keep allowed options normalized in `category_attribute_options`
- keep listing values in a typed `listing_attribute_values` table

Why this is the right compromise:

- avoids schema migrations every time a category gains a new attribute
- supports validation and admin-managed metadata
- keeps filterable attributes queryable with indexes
- avoids an opaque `specs_json` blob becoming the center of catalog logic

Tradeoff:

- query construction is more complex than a single JSON column

Mitigation:

- filter building will live in a dedicated repository/query service
- if scale later demands it, a denormalized search projection can be added without rewriting the core schema
