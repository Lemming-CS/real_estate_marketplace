# Moderation Flow

## Scope
This document covers category-aware listing moderation for the electronics marketplace backend.

## Listing Lifecycle
1. Seller creates a listing in `draft`.
2. Seller uploads media and fills required dynamic category attributes.
3. Seller submits the listing for review, moving it to `pending_review`.
4. Admin reviews the listing and either:
   - approves it, moving it to `published`
   - rejects it, moving it to `rejected` with a moderation note
5. Seller may archive, deactivate, reactivate, or mark sold depending on the current state.

## Owner Rules
- Only the owner or an admin can modify a listing.
- Suspended, pending-verification, or deleted users cannot create or operate listings.
- Draft, rejected, inactive, and archived listings remain visible to the owner in private endpoints.
- Public feeds and public detail views expose only `published` listings from active sellers.

## Re-Moderation Rules
- Editing core listing content while a listing is `published` or `inactive` moves it back to `pending_review`.
- Uploading, replacing, or deleting media while a listing is `published` or `inactive` also moves it back to `pending_review`.
- Pure ordering changes and primary-image changes do not change moderation status.

## Media Rules
- Listing media is limited to image uploads for MVP.
- Supported MIME types: `image/jpeg`, `image/png`, `image/webp`.
- Max active media items per listing: `10`.
- Max file size per media upload: `10 MB`.
- Storage keys are server-generated under `MEDIA_STORAGE_PATH/listings/<listing_public_id>/...`.
- APIs expose media `public_id` and opaque `asset_key`, not arbitrary client-chosen filesystem paths.

## Admin Audit
- Admin category changes and moderation decisions write to `admin_audit_logs`.
- Logs capture actor, action, entity type, entity id, and before/after JSON snapshots.
