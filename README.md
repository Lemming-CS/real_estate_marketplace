# Real Estate Marketplace Assignment

Production-style full-stack marketplace for:
- renting apartments and houses
- buying apartments and houses

Stack:
- `backend/`: FastAPI + SQLAlchemy + Alembic + MySQL
- `mobile/`: Flutter + Riverpod + GoRouter
- `admin/`: React + Vite + TanStack Query
- `docs/`: architecture, API, DB, moderation, submission notes

<video width="640" height="360" controls>
  <source src="./docs/aitSolutionsClean.mp4" type="video/mp4">
</video>

### 5 minute video overview: 
- [Video Link](./docs/aitSolutionsClean.mp4)

## What Is Implemented
- JWT auth with refresh-token rotation, password reset, profile update, profile image upload
- property categories with localization (`en`, `ru`) and dynamic attribute metadata
- property listings for rent/sale with map coordinates, area, rooms, floor data, media, favorites, view counters, soft delete, sold status, and search/filter/sort
- messaging tied to listings, attachment uploads, secure attachment access, notifications, and conversation reporting
- report-driven moderation, admin listing visibility controls, user suspension with note history, and admin audit logging
- promotion packages, promotion purchase flow, payment records, mock payment lifecycle, and promoted listing visibility
- separate admin panel for dashboard, users, reports, listings, payments, promotions, categories, audit logs, and scoped conversation review
- Flutter mobile app for browse/search/filter, auth, create/edit listing, my listings, favorites, inbox, notifications, promotions/payments history, and reporting

## Assignment Alignment
This submission is intentionally aligned to a real-estate marketplace instead of a generic marketplace:
- listings store city, district, address text, map label, latitude, longitude, rooms, area, floor, and furnishing data
- property media supports photos and optional MP4 video tours
- admin does not manually approve every new listing
- moderation is primarily report-driven
- suspension notes are stored durably and shown in admin detail and audit workflows

## Why Admin Does Not Approve Every Listing
The final workflow is closer to a real marketplace:
- active sellers can publish directly once required validation passes
- admin time is focused on risky cases, not on approving every ordinary listing
- reports from users are the primary intake for moderation
- admins can still hide, archive, reject, or manually review listings when needed



## Architecture Summary
- FastAPI is the single source of truth for business rules and data integrity.
- Flutter and admin are separate clients over stable backend contracts.
- MySQL stores transactional state.
- Media files are stored outside the database under `MEDIA_STORAGE_PATH`.
- Promotions, payments, and activation are modeled as separate domains.
- Moderation actions and user status changes are audited.

Detailed docs:
- [Architecture](./docs/ARCHITECTURE.md)
- [API Contract Overview](./docs/API_CONTRACT_OVERVIEW.md)
- [Moderation Flow](./docs/MODERATION_FLOW.md)
## Repository Structure
```text
.
├── .env.example
├── Makefile
├── docker-compose.yml
├── scripts/
│   └── bootstrap_local.sh
├── backend/
├── mobile/
├── admin/
├── docs/
└── infra/
```

## Exact Step-By-Step Local Setup
Generated locally, not committed:
- `backend/.venv`
- `admin/node_modules`
- `mobile/.dart_tool`
- Flutter platform build artifacts

Each developer creates these on their own machine after cloning the repo.

### 1. Copy env files
```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp admin/.env.example admin/.env
cp mobile/.env.example mobile/.env
```

### 2. Start shared local services manually if needed
```bash
docker compose up -d mysql mailhog
```
### 3. Configure backend
Linux / macOS:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```
Windows PowerShell:
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

### 4. Run migrations and seed demo data
Linux / macOS:
```bash
alembic upgrade head
python -m app.db.seed
```

Windows PowerShell:
```powershell
alembic upgrade head
python -m app.db.seed
```

### 5. Run backend
```
uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

Backend dependency note:
- `pip install -e '.[dev]'` installs both runtime and development dependencies from `backend/pyproject.toml`
- this already includes `cryptography`, so you do not need to install it separately unless your machine-specific Python environment has an extra issue

### 6. Run admin
`node_modules` is local and ignored by Git, so each machine installs it after cloning:
```bash
cd admin
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

### 7. Run Flutter mobile
One-time native bootstrap if platform folders are missing:
```bash
cd mobile
flutter create --platforms=android,ios .
```

Then:
```bash
flutter pub get
./scripts/run_local.sh
```
### If flutter doesnt reach backend check the mobile/.env !!!


Flutter note:
- packages are restored locally from `pubspec.yaml` and `pubspec.lock`
- generated folders like `.dart_tool` and platform build outputs are not committed

### 8. Useful root commands
```bash
make help
make bootstrap-local
make compose-up-infra
make backend-migrate
make backend-seed
make backend-run
make admin-run
make mobile-run
```

## Demo Credentials
| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin.demo@example.com` | `AdminPass123!` |
| Renter / buyer | `renter.demo@example.com` | `RenterPass123!` |
| Rental seller | `rent.host@example.com` | `RentHostPass123!` |
| Sale seller | `sale.agent@example.com` | `SaleAgentPass123!` |
| Suspended seller | `suspended.owner@example.com` | `SuspendedOwner123!` |

## Demo Seed Story
The seeded dataset is intentionally reviewer-friendly:
- published apartment rental listing with real local photos
- published house sale listing with real local photos
- draft listing
- reported listing
- active promotion example
- renter-seller conversation with attachment
- suspended seller with persisted note history

Seed photos are copied from `backend/app/db/seed_photos` into the actual media storage tree during seeding.

## Maps, Media, Moderation, and Payments
### Maps
- listings store exact coordinates
- Flutter uses OpenStreetMap via `flutter_map`
- detail screens show location previews
- create/edit flow supports pin placement

### Property media
- photos are supported across backend, admin review, and mobile
- optional MP4 property video is supported in the backend and mobile upload flow
- media is stored under opaque server-generated storage keys

### Report-driven moderation
- sellers publish directly if valid and active
- reports drive moderator review
- admin can hide/archive listings or suspend users from report workflows
- suspension reasons are stored in `user_status_history` and surfaced in admin detail

### Payments and promotions
- promotion package -> promotion record -> payment record -> activation(by admin)
- payments are modeled separately from promotions
- active promotion state is exposed on listings
- current checkout is mock/sandbox

## API Summary
Main route groups:
- auth and profile
- public categories
- listings, media, favorites, and discovery
- conversations and notifications
- reports
- payments and promotions
- admin dashboard, users, listings, reports, payments, packages, promotions, audit logs, and scoped conversation review

Full summary: [docs/API_CONTRACT_OVERVIEW.md](./docs/API_CONTRACT_OVERVIEW.md)

## Testing Status
Backend coverage includes:
- auth flows
- listing CRUD and permissions
- discovery filters and pagination validation
- favorites, counters, soft delete, and deduplicated view tracking
- messaging permissions and secure attachment access
- payment-to-promotion activation rules
- report-driven moderation and audit persistence

Flutter tests include:
- listing form validation rules
- listing filter query-param/state behavior


## Known Limitations
- Mobile video playback is still lighter than photo UX; upload and indicators exist, but the experience is not yet as polished as image browsing.
- Search is MySQL-backed and city/district/text based. There is no geospatial radius search or clustering.
- Admin conversation review is scoped and secure, but still operationally simple rather than a full trust-and-safety workstation.
- The promotion payment flow uses a mock provider, not a real external gateway.
- Flutter package/import identifiers still use an older internal package name; user-facing product branding is real-estate specific.

## Future Work
- geocoding and map bounding-box search
- richer video preview/playback on mobile
- push notifications and background refresh
- CI pipelines and deployment automation
- S3/MinIO storage adapter for production-style object storage
- stronger admin analytics and moderation dashboards

## Submission Quality Notes
- No secrets are committed; env files are examples only.
- The system is explainable in interview terms because domain boundaries are explicit:
  - listings
  - messaging
  - moderation
  - promotions
  - payments
  - audit logging
  