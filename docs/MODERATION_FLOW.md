# Moderation Flow

## Scope
This document covers report-driven moderation for the real-estate marketplace backend.

## Listing Lifecycle
1. Seller creates a property listing in `draft`.
2. Seller fills the required real-estate fields, uploads media, and provides required category attributes.
3. Active sellers can publish directly when validation passes.
4. Published listings appear in public discovery immediately.
5. Admin does not approve every listing by default. Admin intervenes through reports, visibility controls, and manual moderation actions.
6. Listings can move between `published`, `inactive`, `archived`, `rejected`, and `sold` depending on owner or admin actions.
7. `pending_review` remains available only for exceptional/manual moderation cases.

## Owner Rules
- Only the owner or an admin can modify a listing.
- Suspended, pending-verification, or deleted users cannot create or operate listings.
- Draft, rejected, inactive, archived, and sold listings remain visible to the owner in private endpoints.
- Public feeds and public detail views expose only `published` listings from active sellers.

## Publication Rules
- Publishing requires at least one active media item and at least one image.
- Publishing requires valid real-estate fields such as `purpose`, `property_type`, `address_text`, coordinates, `room_count`, and `area_sqm`.
- Required dynamic category attributes must be present before publication.
- Editing a published property does not automatically push it back into admin review. The seller can continue operating the listing unless an admin intervenes.

## Report-Driven Moderation
- Reports are the main moderation intake for suspicious listings and abusive users.
- Admin report review shows linked listing status, seller status, and current moderation context.
- From the report workflow, admin can:
  - dismiss the report
  - mark the report in review
  - resolve the report
  - hide the listing by moving it to `inactive`
  - archive the listing
  - suspend the seller
- Report-triggered actions also write audit logs and, for user suspension, create durable `user_status_history` entries.

## Media Rules
- Property listings support images and optional MP4 video tours.
- Supported MIME types: `image/jpeg`, `image/png`, `image/webp`, `video/mp4`.
- Max active media items per listing: `20`.
- Max image size: `10 MB`.
- Max video size: `50 MB`.
- Published property listings must retain at least one image.
- Primary media must be an image.
- Storage keys are server-generated under `MEDIA_STORAGE_PATH/listings/<listing_public_id>/...`.
- APIs expose media `public_id` and opaque `asset_key`, not arbitrary client-chosen filesystem paths.

## Location and Privacy
- The backend stores `address_text`, `city`, `district`, `map_label`, `latitude`, and `longitude`.
- The current product decision is:
  - public listing responses expose map-aware location fields
  - exact `address_text` is only returned to owners and admins in listing detail responses
- Future clients can choose approximate-pin rendering without another schema change.

## Admin Audit
- Admin listing actions, report resolutions, user suspension/unsuspension, and category/package changes write to `admin_audit_logs`.
- Logs capture actor, action, entity type, entity id, and before/after JSON snapshots.
- Suspension and unsuspension notes are also persisted in `user_status_history` and surfaced in admin user detail.
