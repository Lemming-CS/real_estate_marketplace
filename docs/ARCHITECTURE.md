# Architecture

## System Architecture
The platform is intentionally designed as a multi-client system with one backend source of truth.

```text
Flutter Mobile App  ----\
                         \
                          -> FastAPI Backend -> MySQL
                         /                   -> Object Storage (MinIO locally, S3-compatible later)
React Admin Panel  -----/                    -> Notification adapters
                                             -> Payment provider adapter
```

Key decisions:

- business rules live in the backend, not duplicated in clients
- mobile and admin remain thin clients over explicit API contracts
- MySQL stores transactional state; media stays outside the database
- admin functionality is separate from customer functionality
- integrations with storage, notifications, and payments sit behind interfaces

## Recommended Folder Structure
### Repository root
```text
.
├── README.md
├── docker-compose.yml
├── admin/
├── backend/
├── docs/
└── infra/
```

### Backend
```text
backend/
├── alembic/
│   ├── versions/
│   └── env.py
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── models/
│   ├── shared/
│   │   ├── schemas/
│   │   ├── pagination/
│   │   └── utils/
│   ├── modules/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── catalog/
│   │   ├── listings/
│   │   ├── media/
│   │   ├── orders/
│   │   ├── payments/
│   │   ├── promotions/
│   │   ├── notifications/
│   │   ├── moderation/
│   │   └── audit/
│   └── main.py
├── scripts/
├── tests/
│   ├── integration/
│   ├── unit/
│   └── fixtures/
├── pyproject.toml
└── .env.example
```

Each backend module should follow the same internal shape:

```text
modules/listings/
├── domain/
├── application/
├── infrastructure/
└── presentation/
```

### Mobile
```text
mobile/
├── lib/
│   ├── app/
│   │   ├── router/
│   │   ├── theme/
│   │   └── bootstrap/
│   ├── core/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── storage/
│   │   └── widgets/
│   ├── shared/
│   │   ├── models/
│   │   ├── utils/
│   │   └── constants/
│   ├── features/
│   │   ├── auth/
│   │   ├── home/
│   │   ├── catalog/
│   │   ├── listings/
│   │   ├── favorites/
│   │   ├── orders/
│   │   ├── promotions/
│   │   └── profile/
│   └── l10n/
├── test/
├── integration_test/
└── pubspec.yaml
```

### Admin
```text
admin/
├── src/
│   ├── app/
│   │   ├── router/
│   │   ├── providers/
│   │   └── layout/
│   ├── core/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── permissions/
│   │   └── utils/
│   ├── shared/
│   │   ├── components/
│   │   ├── table/
│   │   └── forms/
│   ├── features/
│   │   ├── dashboard/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── listings/
│   │   ├── moderation/
│   │   ├── orders/
│   │   ├── promotions/
│   │   └── audit/
│   └── main.jsx
├── public/
├── tests/
├── package.json
└── .env.example
```

### Docs
```text
docs/
├── ARCHITECTURE.md
├── IMPLEMENTATION_PLAN.md
├── API_CONTRACT_OVERVIEW.md
├── DB_DESIGN.md
└── decisions/
```

### Infra
```text
infra/
├── compose/
├── mysql/
├── minio/
├── nginx/
└── scripts/
```

## Separation of Concerns
- Backend owns validation, authorization, persistence, moderation rules, payment state, and audit logging.
- Mobile owns presentation, local session storage, offline-friendly UI behavior, and user interaction flows.
- Admin owns operational visibility and privileged workflows, but it does not bypass backend business rules.
- Database stores normalized transactional state, not presentation logic.
- Infrastructure code provisions supporting services, but does not contain domain rules.
- Documentation stays versioned in the repository and acts as the operating contract for future prompts.

## Backend Layers
### Domain layer
- entities, value objects, enums, and business invariants
- no FastAPI, ORM, or external provider details
- examples: `Listing`, `PromotionPlan`, `Order`, `ModerationDecision`

### Application layer
- use cases and orchestration
- transaction boundaries and cross-module coordination
- examples: `CreateListing`, `SubmitListingForReview`, `ActivatePromotion`, `PlaceOrder`

### Infrastructure layer
- SQLAlchemy repositories
- storage adapters
- payment provider adapters
- notification adapters
- password hashing and token persistence

### Presentation layer
- FastAPI routers
- request/response schemas
- auth dependencies
- HTTP exception mapping

The practical rule is simple: routers call use cases, use cases depend on interfaces, interfaces are implemented by infrastructure.

## Mobile Layers
### Presentation
- screens, widgets, controllers, and route guards
- state managed with Riverpod

### Domain
- entities, repository contracts, and use cases
- no Dio or Flutter widget code

### Data
- DTOs, mappers, API clients, repository implementations, and local storage adapters

### Core
- shared auth/session handling
- app-wide error handling
- network client setup
- localization bootstrap

This keeps Flutter features testable and prevents API concerns from leaking directly into widgets.

## Admin Architecture
The admin panel should be treated as an internal operations product, not a thin page of ad hoc screens.

- feature-first React structure
- typed API client shared across admin features
- route-level role and permission guards
- reusable data table, filters, and action modal patterns
- optimistic UI only where operationally safe
- audit-sensitive actions require explicit confirmation and reason input where appropriate

Recommended admin roles:

- `admin_super`
- `admin_moderator`
- `admin_support`

Permissions should be backend-enforced even if the UI also hides unauthorized actions.

## Authentication Strategy
- Single identity domain with `users` plus role assignments.
- Access tokens are short-lived JWTs.
- Refresh tokens are opaque, stored hashed in the database, and rotated on use.
- Mobile stores tokens in secure device storage.
- Admin stores access tokens in memory and should use an HTTP-only refresh cookie where practical.
- Seller access is not a separate login system; seller capability is a role/profile on the same identity.
- Sensitive admin actions require backend role checks, not just client-side route guards.

Baseline auth flows:

1. Register or login.
2. Receive access token and refresh token.
3. Access token is used for API calls.
4. Refresh token rotates through a dedicated endpoint.
5. Logout revokes the refresh token session.

## File Storage Strategy
- Media files are stored in object storage, not as database blobs.
- MySQL stores metadata such as storage key, checksum, MIME type, dimensions, and uploader.
- Listing images attach through a `media_assets` relation so files remain traceable and reusable.
- Local development should use MinIO for S3-compatible behavior.
- MVP upload path should be backend-managed multipart upload for simpler control and validation.
- The storage service must be abstracted so S3-compatible production storage can replace local MinIO without changing domain code.

## Notification Strategy
- In-app notifications are real and stored in MySQL from the first MVP.
- Notification creation is event-driven from backend use cases such as listing approval, order confirmation, and promotion activation.
- External delivery channels are adapters, not business logic.
- Push delivery can be deferred, but the notification domain itself should not be skipped.
- If push is added later, Firebase Cloud Messaging is the expected mobile path.

## Payment Strategy
- Payments are a first-class module with records, statuses, provider references, and event history.
- The backend must never treat payment success as a boolean flag passed from the client.
- MVP should support practical marketplace methods:
  - `cash_on_delivery` for orders
  - `manual_transfer` for orders or promotions
  - `demo_gateway` or sandbox provider for promotion purchases
- Provider adapters allow later addition of Stripe or another gateway without rewriting order or promotion logic.

The important tradeoff is this: the domain must be real even if the first provider is a controlled sandbox.

## Promotion Activation Flow
1. Seller selects a promotion plan for a listing.
2. Backend verifies listing eligibility and creates a `listing_promotions` record in `pending_payment`.
3. Backend creates a linked payment record.
4. Payment becomes `paid` through sandbox/manual confirmation flow.
5. Promotion moves to `scheduled` or `active` based on start time.
6. Listing query ranking includes promotion priority only while the promotion is active.
7. Admin can cancel or override a promotion, but every override is audited.

Important rule: promotion activation happens through application logic, never through direct field edits in admin tables.

## Moderation Flow
1. Seller creates or edits a listing in `draft`.
2. Seller submits listing for review.
3. Listing becomes `pending_review`.
4. Admin reviews content, images, price sanity, and policy compliance.
5. Admin action results in:
   - `published`
   - `rejected`
   - `needs_changes` if implemented as a separate state
6. Approved listings become visible in public discovery endpoints.
7. Certain risky edits to published listings should push them back into review.

Moderation is intentionally explicit because electronics marketplaces are vulnerable to counterfeit, misleading specs, and stolen device listings.

## Audit Logging Strategy
Audit logging is mandatory for admin and other sensitive workflows.

What should be logged:

- admin login and logout
- listing moderation decisions
- user blocking or role changes
- promotion overrides
- order status changes by admins
- payment status overrides

Each audit record should capture:

- actor user id
- actor role
- action name
- entity type
- entity id
- request id
- before snapshot when relevant
- after snapshot when relevant
- IP and user agent where available
- timestamp

Audit logs are append-only at the application level and should never be editable through the admin UI.
