SHELL := /bin/bash

.PHONY: help env-init bootstrap-local compose-up compose-up-infra compose-down compose-logs backend-install backend-migrate backend-seed backend-run backend-test admin-install admin-run admin-lint admin-build mobile-bootstrap mobile-get mobile-run mobile-analyze

help:
	@echo "Available targets:"
	@echo "  env-init          Copy sample env files into place if missing"
	@echo "  bootstrap-local   Prepare env files, dependencies, and shared local services"
	@echo "  compose-up        Start mysql, mailhog, backend, and admin via Docker Compose"
	@echo "  compose-up-infra  Start only mysql and mailhog via Docker Compose"
	@echo "  compose-down      Stop Docker Compose services"
	@echo "  compose-logs      Tail Docker Compose logs"
	@echo "  backend-install   Install backend dependencies into the active Python environment"
	@echo "  backend-migrate   Apply Alembic migrations"
	@echo "  backend-seed      Seed demo marketplace data"
	@echo "  backend-run       Start the FastAPI dev server locally"
	@echo "  backend-test      Run backend tests"
	@echo "  admin-install     Install admin dependencies"
	@echo "  admin-run         Start the admin dev server locally"
	@echo "  admin-lint        Run admin lint checks"
	@echo "  admin-build       Build the admin app"
	@echo "  mobile-bootstrap  Generate Flutter platform folders if missing"
	@echo "  mobile-get        Fetch Flutter packages"
	@echo "  mobile-run        Start the Flutter app using values from mobile/.env"
	@echo "  mobile-analyze    Run Flutter static analysis"

env-init:
	@test -f .env || cp .env.example .env
	@test -f backend/.env || cp backend/.env.example backend/.env
	@test -f admin/.env || cp admin/.env.example admin/.env
	@test -f mobile/.env || cp mobile/.env.example mobile/.env

bootstrap-local:
	./scripts/bootstrap_local.sh

compose-up:
	docker compose up -d mysql mailhog backend admin

compose-up-infra:
	docker compose up -d mysql mailhog

compose-down:
	docker compose down

compose-logs:
	docker compose logs -f

backend-install:
	cd backend && python3 -m pip install -e '.[dev]'

backend-migrate:
	cd backend && alembic upgrade head

backend-seed:
	cd backend && python -m app.db.seed

backend-run:
	cd backend && uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000

backend-test:
	cd backend && pytest

admin-install:
	cd admin && npm install

admin-run:
	cd admin && npm run dev -- --host 0.0.0.0 --port 5173

admin-lint:
	cd admin && npm run lint

admin-build:
	cd admin && npm run build

mobile-bootstrap:
	cd mobile && flutter create --platforms=android,ios .

mobile-get:
	cd mobile && flutter pub get

mobile-run:
	cd mobile && ./scripts/run_local.sh

mobile-analyze:
	cd mobile && flutter analyze
