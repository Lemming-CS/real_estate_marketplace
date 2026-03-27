# Real Estate Marketplace Assignment

## Project Overview
This repository is a monorepo-style foundation for a production-minded real-estate marketplace with:

- `backend/`: FastAPI service and business logic
- `mobile/`: Flutter buyer/seller app
- `admin/`: React admin panel (JSX)
- `docs/`: architecture, API, DB, and delivery plans
- `infra/`: local infrastructure notes and placeholders

The marketplace domain is now real estate, focused on apartment and house listings for rent and sale. The existing marketplace architecture was preserved and incrementally realigned so auth, messaging, reports, promotions, payments, and admin tooling still work against a stronger property-specific listing model.

## Current Status
The repository now contains a working backend/admin foundation with auth, profiles, listings, discovery, messaging, reports, promotions, payments, and admin operations aligned to a real-estate marketplace. Flutter mobile is still scaffolded for the next phase.

## Architecture Summary
- Backend is the source of truth for auth, property listings, report-driven moderation, promotions, payments, messaging, and audit logging.
- Mobile and admin are separate clients over explicit backend contracts.
- MySQL is the transactional data store.
- Docker Compose is used for local infrastructure and optional containerized backend/admin development.
- Environment-specific values live in env files or runtime variables, never in application code.

Detailed architecture and planning docs:

- [Architecture](/home/lemming/Projects/marketplace-assignment/docs/ARCHITECTURE.md)
- [Implementation Plan](/home/lemming/Projects/marketplace-assignment/docs/IMPLEMENTATION_PLAN.md)
- [API Contract Overview](/home/lemming/Projects/marketplace-assignment/docs/API_CONTRACT_OVERVIEW.md)
- [Database Design](/home/lemming/Projects/marketplace-assignment/docs/DB_DESIGN.md)
- [Interaction Model](/home/lemming/Projects/marketplace-assignment/docs/INTERACTION_MODEL.md)

## Repo Structure
```text
.
├── README.md
├── Makefile
├── docker-compose.yml
├── backend/
├── mobile/
├── admin/
├── docs/
└── infra/
```

## Exact Local Setup Commands
### 1. Create env files
```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp admin/.env.example admin/.env
cp mobile/.env.example mobile/.env
```

### 2. Start shared local services
```bash
docker compose up -d mysql mailhog
```

Mailhog UI will be available at `http://localhost:8025` by default.

### 3. Start backend locally
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

Backend health check:

```bash
curl http://localhost:8000/api/v1/health
```

Then apply the schema and seed demo data:

```bash
cd backend
alembic upgrade head
python -m app.db.seed
```

### 4. Start admin locally
```bash
cd admin
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Admin UI will be available at `http://localhost:5173`.

### 5. Start mobile locally
One-time project bootstrap to generate native platform folders:

```bash
cd mobile
flutter create --platforms=android,ios .
```

Then run the starter app:

```bash
cd mobile
flutter pub get
./scripts/run_local.sh
```

The mobile app reads `APP_NAME` and `API_BASE_URL` from `mobile/.env` and passes them into Flutter with `--dart-define`.

### 6. Optional: run backend and admin in Docker
```bash
docker compose up --build backend admin
```

## Common Commands
The repository includes a root [Makefile](/home/lemming/Projects/marketplace-assignment/Makefile):

```bash
make help
make env-init
make compose-up
make backend-migrate
make backend-seed
make backend-run
make admin-run
make mobile-run
```

## How Backend, Mobile, and Admin Interact
1. The Flutter mobile app calls the FastAPI backend for auth, listings, favorites, orders, and seller actions.
2. The admin panel calls the same backend through separate admin-prefixed routes for moderation, support, and audit workflows.
3. The backend persists marketplace state in MySQL and exposes a stable HTTP API to both clients.
4. Local email-style flows can be inspected through Mailhog during development.

The full interaction model lives in [docs/INTERACTION_MODEL.md](/home/lemming/Projects/marketplace-assignment/docs/INTERACTION_MODEL.md).

## Planned Demo Accounts
These are the intended seed accounts once auth and seed data are implemented:

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin.demo@example.com` | `AdminPass123!` |
| Renter / buyer | `renter.demo@example.com` | `RenterPass123!` |
| Rental seller | `rent.host@example.com` | `RentHostPass123!` |
| Sale seller | `sale.agent@example.com` | `SaleAgentPass123!` |
| Suspended seller | `suspended.owner@example.com` | `SuspendedOwner123!` |

## Payments and Promotion Assumptions
- Payments are modeled as a real domain.
- MVP checkout can start with `cash_on_delivery`, `manual_transfer`, or sandbox/demo settlement.
- Promotions must activate through backend flow, not direct database edits.
- Property listings currently use direct publication by active sellers after validation; admin moderation is primarily report-driven.
- Exact property coordinates are stored. Current backend responses expose map-aware location fields; future clients can choose whether to display full or approximate pins.

## Localization Plan
- Initial target locales: `en` and `ru`
- API contracts stay language-neutral through stable machine-readable enums
- Client-facing strings are externalized from the start

## Known Limitations
- Flutter native platform folders are generated during local bootstrap rather than committed now.
- Search remains MySQL-backed for MVP before any external geospatial/search engine is considered.
- Public property location privacy is currently a product-level tradeoff: exact coordinates are stored and returned, while exact address text is only returned to owners/admin in detail flows.

## Future Work
- Seller/mobile property creation UX with map pin placement
- Approximate-location privacy controls
- Geocoding and map-based bounding-box search
- MinIO-backed media storage
- CI pipelines and deployment infrastructure

## How This Project Maps To The Assignment
- Flutter app for end users: `mobile/`
- FastAPI backend: `backend/`
- MySQL database: `docker-compose.yml` plus future migrations in `backend/alembic/`
- Separate admin panel: `admin/`
- Clean architecture and production-minded structure: enforced through repo layout and docs-first contracts
