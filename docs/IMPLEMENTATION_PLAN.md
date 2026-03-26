# Implementation Plan

## Planning Principles
- Build the real backbone first: auth, database, catalog metadata, listings, moderation.
- Keep one backend source of truth for all clients.
- Prefer a smaller but complete vertical slice over broad disconnected scaffolding.
- Mock only external providers, not core platform behavior.
- Keep each stage demonstrable.

## MVP-First Order
1. Repository scaffolding, coding standards, and local infrastructure baseline
2. Identity, roles, and catalog foundation
3. Listings, media upload, and moderation pipeline
4. Mobile buyer/seller core experience
5. Admin operations panel
6. Orders, promotion purchase flow, and notifications
7. Hardening, localization, testing, and demo preparation

## Stage 0: Foundation and Scaffolding
### Goals
- Turn the empty folders into a usable multi-app repository.
- Establish conventions before feature work begins.
- Expand local development setup beyond MySQL when needed.

### Dependencies
- Approval of the architecture and implementation direction in these docs.

### Backend tasks
- Create FastAPI project skeleton with clean architecture module layout.
- Add config loading, app bootstrap, health endpoint, and database session setup.
- Add Alembic configuration and first empty migration baseline.
- Add linting, formatting, typing, and test configuration.

### Mobile tasks
- Create Flutter app shell with routing, theme, localization bootstrap, and environment config.
- Add Riverpod, Dio, and secure storage foundations.

### Admin tasks
- Create React admin shell (JSX) with routing, auth placeholders, API client foundation, and base layout.

### Deliverables
- Running backend health endpoint
- Buildable mobile app shell
- Buildable admin app shell
- Shared environment file examples
- CI-ready lint/test commands

### Risks
- Over-scaffolding without delivering a real vertical slice
- Inconsistent conventions across backend, mobile, and admin

## Stage 1: Identity, Roles, and Catalog Foundation
### Goals
- Make authentication, authorization, and seller capability real.
- Create stable catalog metadata needed by listings.

### Dependencies
- Stage 0 completed

### Backend tasks
- Implement `users`, `user_roles`, `seller_profiles`, `refresh_tokens`, and `user_addresses`.
- Implement register, login, refresh, logout, and profile endpoints.
- Seed categories, brands, and category attribute definitions.
- Implement role-based access checks for buyer, seller, and admin actions.

### Mobile tasks
- Build auth screens and token/session bootstrap.
- Build profile screen and seller onboarding flow.
- Consume category and brand endpoints for selection screens.

### Admin tasks
- Build admin login flow and role-protected route shell.
- Add category and brand management screens only if needed for assignment flexibility.
- Otherwise treat catalog metadata as seeded and admin-readable in MVP.

### Deliverables
- Real auth flow with refresh rotation
- Seeded electronics catalog metadata
- Seller onboarding path
- Demo accounts

### Risks
- Role model drift if buyer/seller/admin responsibilities are not kept explicit
- Category metadata churn if attribute strategy is not locked early

## Stage 2: Listings, Media, and Moderation Pipeline
### Goals
- Deliver the marketplace core: listings that can be created, reviewed, and published.

### Dependencies
- Stage 1 completed

### Backend tasks
- Implement listings, listing images, media assets, attribute values, favorites, and moderation tables.
- Implement image upload flow backed by storage abstraction.
- Implement listing draft, submit, approve, reject, archive, and sold transitions.
- Implement public listing search with pagination and core filters.
- Implement owner listing management endpoints.

### Mobile tasks
- Build listing creation and edit flow with image upload.
- Build home, category browse, listing detail, and favorites screens.
- Show moderation status and rejection reasons on seller-owned listings.

### Admin tasks
- Build listing moderation queue.
- Build listing detail moderation screen with approve/reject actions and reason capture.
- Build basic user review screen for investigating suspicious sellers if needed.

### Deliverables
- Seller can create listing and submit it for review
- Admin can approve or reject
- Buyer can discover approved listings only
- Image upload works end to end

### Risks
- Dynamic attribute implementation can become messy if not standardized
- Media lifecycle can cause orphaned assets if attachment flow is weak
- Search queries may degrade if indexes are not chosen early

## Stage 3: Mobile Core Experience Completion
### Goals
- Turn the API foundation into a coherent buyer/seller app.

### Dependencies
- Stage 2 completed

### Backend tasks
- Fill missing support endpoints for seller dashboards, notification feed, and richer listing detail.
- Stabilize response shapes and validation errors based on mobile integration feedback.

### Mobile tasks
- Refine buyer journey from login to browse to favorite to order initiation.
- Refine seller journey from onboarding to listing management to promotion purchase.
- Implement error states, empty states, pull-to-refresh, and token refresh handling.
- Add localization plumbing for at least two locales.

### Admin tasks
- Minimal changes only where mobile integration reveals operational gaps.

### Deliverables
- Demo-ready mobile app that supports core buyer and seller flows
- Stable API contract proven by real client integration

### Risks
- Mobile state management can become inconsistent if DTOs and domain models are mixed
- Unclear UX decisions may cause rework late in implementation

## Stage 4: Admin Operations Panel
### Goals
- Make the back office credible and operationally useful.

### Dependencies
- Stages 1 and 2 completed

### Backend tasks
- Add admin-focused list/filter endpoints for users, listings, orders, promotions, and audits.
- Add dashboard summary endpoints.
- Add admin-only mutation endpoints for moderation, blocking, and promotion override.

### Mobile tasks
- No major new scope beyond bug fixes required by admin-backed operations.

### Admin tasks
- Implement dashboard summary views.
- Implement user management list and detail view.
- Implement order management screen.
- Implement promotion review/override screen.
- Implement audit log viewer.

### Deliverables
- Separate admin panel with real operational workflows
- Moderation, user actions, and promotion actions all auditable

### Risks
- Admin panel can sprawl into a second product if workflows are not tightly scoped
- Permission boundaries can get weak if admin UI starts assuming trust over backend checks

## Stage 5: Orders, Promotions, and Notifications
### Goals
- Close the marketplace loop from discovery to transaction to visibility boosting.

### Dependencies
- Stage 2 completed
- Stage 3 strongly recommended

### Backend tasks
- Implement order placement and order lifecycle.
- Implement payment records and sandbox/manual settlement paths.
- Implement promotion plan purchase and activation.
- Emit in-app notifications for approval, order, and promotion events.
- Add order status history and payment event logging.

### Mobile tasks
- Build order creation, order history, and order detail flows.
- Build seller order management actions that fit allowed permissions.
- Build promotion purchase and listing boost selection flow.
- Surface in-app notifications.

### Admin tasks
- Add order review and escalation tools.
- Add promotion monitoring and override actions.
- Add payment review page if assignment scope benefits from it.

### Deliverables
- Buyer can place order
- Seller can manage order state
- Seller can purchase and activate promotion through a controlled flow
- Notifications are visible in-app

### Risks
- Payment semantics can become inconsistent if the domain supports too many methods too early
- Orders may need policy clarifications around stock reservation, cancellation, and delivery

## Stage 6: Hardening, Localization, and Demo Readiness
### Goals
- Make the system reviewable as a serious assignment submission.

### Dependencies
- Previous stages completed

### Backend tasks
- Add broader integration tests for auth, listings, moderation, orders, and promotions.
- Add request logging, error mapping, and basic performance review of listing queries.
- Finalize seed scripts and demo fixtures.

### Mobile tasks
- Finish localization pass.
- Improve polish, form validation, accessibility basics, and failure handling.
- Add widget and integration tests for critical flows.

### Admin tasks
- Add validation, loading states, and operational guardrails around sensitive actions.
- Add smoke tests for critical admin workflows.

### Deliverables
- Stable demo environment
- Clear seeded story for reviewer walkthrough
- Reduced risk of obvious runtime failures

### Risks
- Late-stage polish can mask missing core behavior if started too early
- Seed data and docs can drift from actual implementation if not refreshed together

## What Must Be Real vs What Can Be Mocked
### Must be real
- FastAPI backend with actual route handlers and database persistence
- MySQL schema, migrations, and relational data
- Mobile app consuming the backend API
- Admin panel consuming the backend API
- Authentication, authorization, and session handling
- Listing creation, moderation, publication, and search
- Image upload pipeline with real file persistence
- Order persistence and status changes
- Audit logs for sensitive admin actions

### Can be mocked safely if clearly documented
- External card gateway, replaced by sandbox/manual payment provider
- Push notification delivery provider, as long as in-app notification records are real
- Email delivery provider, as long as events are generated and observable locally
- Cloud object storage provider, as long as local S3-compatible storage is used
- Shipping carrier integration

The rule is strict: external vendors may be mocked, but core marketplace workflows may not.

## Manual Steps Required From User
- Confirm whether a live payment gateway is mandatory or a sandbox/manual provider is acceptable.
- Confirm the target locales for MVP. Current recommendation is `en` and `ru`.
- Confirm whether seller verification must include document upload in MVP or can stay profile-based.
- Provide any assignment rubric, mandatory features, or forbidden libraries that are not yet in the repo.
- Approve the admin stack direction. Current recommendation is React (JSX) + Vite.
- Provide brand name, app name, and any required design direction if this is part of evaluation.
- If deployment is required later, provide target environment and credentials or hosting constraints.
