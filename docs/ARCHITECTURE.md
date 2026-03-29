# Architecture

## System Overview
The project is a multi-client real-estate marketplace:

```text
Flutter Mobile App ----\
                        \
                         -> FastAPI Backend -> MySQL
                        /                  -> Local file storage
React Admin Panel -----/                   -> Mailhog (local dev)
                                           -> Mock payment adapter
```

Core product scope:
- apartments and houses
- rent and sale listings
- map-aware property locations
- property photos and optional video tour
- messaging between renter/buyer and seller
- report-driven moderation
- promotion packages and mock payment activation

## Why This Architecture Fits The Assignment
- One backend source of truth keeps auth, moderation, promotions, and listing state consistent.
- Mobile and admin are intentionally separate apps, which demonstrates real multi-client integration.
- Property workflows are explicit and interview-defensible:
  - direct seller publication after validation
  - reports as moderation intake
  - admin visibility controls and suspension history
  - promotions activated only after successful payment

## Repository Structure
```text
.
├── README.md
├── Makefile
├── docker-compose.yml
├── scripts/
├── backend/
├── mobile/
├── admin/
├── docs/
└── infra/
```

## Backend Structure
```text
backend/
├── alembic/
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   ├── router.py
│   │   └── routes/
│   ├── core/
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── models/
│   ├── modules/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── categories/
│   │   ├── listings/
│   │   ├── messaging/
│   │   ├── notifications/
│   │   ├── reports/
│   │   ├── commerce/
│   │   └── admin_console/
│   ├── shared/
│   └── main.py
├── tests/
└── pyproject.toml
```

### Backend Separation Of Concerns
- `api/`: HTTP routes, request parsing, dependency wiring
- `modules/*/schemas.py`: Pydantic request/response contracts
- `modules/*/service.py`: business rules and orchestration
- `db/models/`: SQLAlchemy models and relational structure
- `core/`: config, security, auth helpers, exceptions
- `shared/`: pagination, storage helpers, shared response primitives

This keeps business logic out of routers and keeps client-visible contracts explicit.

## Mobile Structure
```text
mobile/lib/
├── app/
├── core/
├── features/
│   ├── auth/
│   ├── home/
│   ├── listings/
│   ├── messaging/
│   ├── notifications/
│   ├── commerce/
│   ├── reports/
│   └── profile/
├── l10n/
└── shared/
```

### Mobile Layers
- repository layer calls backend APIs
- Riverpod providers manage async state and local session state
- screens remain thin and mostly compose data + widgets
- shared widgets cover images, cards, map previews, badges, and shell navigation

This keeps Flutter state manageable without rewriting the app into a more complex architecture than the assignment needs.

## Admin Structure
```text
admin/src/
├── app/
├── core/
│   ├── api/
│   └── auth/
├── features/
│   ├── auth/
│   ├── dashboard/
│   ├── users/
│   ├── listings/
│   ├── reports/
│   ├── payments/
│   ├── promotions/
│   ├── categories/
│   ├── conversations/
│   └── audit/
└── shared/
```

### Admin Design Principles
- admin is an operational tool, not a second public-facing marketplace app
- all privileged actions still go through backend role checks
- conversation review is scoped to abuse/investigation context
- suspension notes and audit logs are visible because operational traceability matters

## Authentication Strategy
- JWT access token for API calls
- opaque refresh token persisted in the database
- hashed password storage on the backend
- Flutter stores the session locally
- admin keeps a separate auth flow and must use the admin panel, not the marketplace mobile app

Account status enforcement:
- `active`
- `pending_verification`
- `suspended`
- `deleted`

Suspended users are blocked from restricted marketplace actions such as creating or operating listings.

## Listing And Publication Strategy
The project intentionally does not require universal pre-publication admin approval.

Default path:
1. seller creates listing in `draft`
2. seller fills required property fields
3. seller publishes directly if valid and active
4. listing appears in public discovery immediately

Admin path:
- hide listing
- archive listing
- reject listing
- manually send to review if needed

This matches a more realistic marketplace workflow and keeps moderation focused on reports and abuse handling.

## Real-Estate Data Modeling
Core listing fields are first-class columns because they drive search and UI:
- purpose
- property type
- city / district / address text / map label
- latitude / longitude
- rooms / area / floor / total floors / furnished
- price amount / currency / normalized KGS price

Flexible property metadata still uses dynamic category attributes for details that can vary by category over time.

## Map Strategy
- exact coordinates are stored in the listing row
- mobile uses OpenStreetMap via `flutter_map`
- admin can inspect coordinates in listing detail context
- backend remains geocoder-agnostic

Current product decision:
- exact address text is owner/admin oriented
- public clients use map-aware location fields and may choose full or approximate location display

## File Storage Strategy
- media is stored outside MySQL under `MEDIA_STORAGE_PATH`
- listing media uses server-generated opaque storage keys
- profile images, listing photos/videos, and message attachments all follow the same principle
- seed photos are copied into the same storage tree as normal uploads

This keeps the storage model production-shaped without needing S3 immediately.

## Notification Strategy
Notifications are persisted as database records and shown in the clients.

Implemented event types include:
- new message
- listing approved/rejected where relevant
- payment successful
- promotion activated
- promotion expired

Push delivery is intentionally deferred; the assignment only needs the domain and in-app visibility to be real.

## Payment Strategy
Payments are modeled separately from promotions.

Flow:
1. seller chooses promotion package and target
2. backend creates `payment_records` and `promotions`
3. payment starts in `pending`
4. mock provider simulation marks payment `successful` or `failed`
5. promotion activates only after successful payment

This is easy to explain in interview terms because activation is not hidden behind a boolean flag.

## Promotion Activation Flow
1. listing must be valid and promotable
2. seller selects package, city/category target, and duration
3. backend calculates total price
4. backend creates:
   - pending payment record
   - pending promotion record
5. successful payment activates the promotion
6. expired promotions are surfaced as expired state and notification

Inactive promotion packages are soft-disabled, not deleted, so historical promotions remain traceable.

## Moderation Flow
Reports are the primary moderation intake.

Admin can act from:
- report queue
- user detail
- listing detail
- scoped conversation review

Available actions:
- dismiss report
- resolve report
- hide/archive listing
- suspend/unsuspend seller

All of these actions create audit logs. Suspension and unsuspension also create `user_status_history` records with notes.

## Audit Logging Strategy
Sensitive admin actions write to `admin_audit_logs` with:
- actor
- action
- entity type
- entity id
- before/after JSON
- request metadata

Suspension notes are also persisted in `user_status_history.reason`, which is surfaced in admin user detail.

## Remaining Architectural Tradeoffs
- Search is still relational/MySQL based rather than geospatial.
- Video support exists, but the mobile playback experience is lighter than photo UX.
- Admin conversation review is intentionally scoped and not a full omniscient inbox.
- Storage is local-file based for local dev instead of S3/MinIO in production.
