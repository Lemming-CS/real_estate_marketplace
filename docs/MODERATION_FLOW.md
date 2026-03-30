# Moderation Flow

## Summary
This project uses report-driven moderation, not universal pre-publication approval.

That is intentional and aligned with a more realistic real-estate marketplace:
- active sellers can publish valid listings directly
- admins focus on abuse, fraud, suspicious content, and user conduct
- reports are the main moderation queue

## Listing Lifecycle
1. Seller creates property in `draft`.
2. Seller fills required real-estate fields.
3. Seller can publish directly if:
   - account is active
   - listing passes validation
4. Published listing appears in discovery immediately.
5. Admin may later:
   - hide it (`inactive`)
   - archive it
   - reject it
   - move it to `pending_review` only in exceptional/manual cases
6. Seller may also archive, reactivate, mark sold, or delete according to business rules.

## Why Admin Does Not Manually Approve Every Listing
- It would slow normal property supply unnecessarily.
- Real marketplaces usually rely on post-publication moderation plus user reports.
- The assignment is easier to defend when moderation effort is concentrated on suspicious cases.
- The codebase already models reporting, audit logs, suspension history, and scoped admin review, so report-driven moderation is the stronger story.

## Seller Validation Rules
Publishing requires:
- title
- description
- purpose (`rent` or `sale`)
- property type (`apartment` or `house`)
- city
- address text
- latitude / longitude
- room count
- area
- valid category attribute values where required

Property media is optional.
- Photos are strongly encouraged for demo quality.
- Optional MP4 video tours are supported.
- If media exists, it must pass MIME and size validation.

## Report Intake
Users can report:
- listings
- users
- conversations

Report payload includes:
- target ids
- reason code
- optional description

Reports are stored in `reports` and surfaced in:
- admin reports queue
- user detail context
- listing moderation context
- scoped conversation review context

## Admin Actions From Reports
From a report workflow, admin can:
- mark the report in review
- dismiss the report
- resolve the report
- hide the listing
- archive the listing
- suspend the seller/user

## Listing Visibility Rules
Public feeds and public detail show only:
- `published` listings
- from active sellers
- not soft-deleted

Owners can still see their own:
- `draft`
- `inactive`
- `archived`
- `rejected`
- `sold`

Deleted listings are soft-deleted and excluded from normal views.

## Suspension Notes And Auditability
Suspension notes are stored durably in:
- `user_status_history.reason`

Admin action logs are stored in:
- `admin_audit_logs`

Admin user detail shows:
- latest status note
- status history


## Conversation Review
Admins should not casually browse all private chats.

Implemented principle:
- admin conversation review is scoped to abuse/review context
- attachments remain protected
- admin access is allowed only through explicit review flows

This keeps messaging oversight investigation-aware instead of turning the admin panel into an unrestricted staff inbox.

## Media And Safety Rules
Listing media:
- images: `jpeg`, `png`, `webp`
- optional video: `mp4`

Message attachments:
- images
- documents such as PDF

All storage keys are server-generated.
No attachment or media is public by default.

## Payment And Promotion Moderation Notes
- promotion packages can be activated/deactivated by admin
- packages are soft-disabled, not deleted
- historical payments and promotions remain linked
- listing promotion activation still depends on successful payment, not admin override
