#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

copy_if_missing() {
  local source_path="$1"
  local target_path="$2"

  if [[ -f "${target_path}" ]]; then
    echo "skip ${target_path} (already exists)"
    return
  fi

  cp "${source_path}" "${target_path}"
  echo "created ${target_path}"
}

mkdir -p "${ROOT_DIR}/backend/uploads"

copy_if_missing "${ROOT_DIR}/.env.example" "${ROOT_DIR}/.env"
copy_if_missing "${ROOT_DIR}/backend/.env.example" "${ROOT_DIR}/backend/.env"
copy_if_missing "${ROOT_DIR}/admin/.env.example" "${ROOT_DIR}/admin/.env"
copy_if_missing "${ROOT_DIR}/mobile/.env.example" "${ROOT_DIR}/mobile/.env"

if command -v docker >/dev/null 2>&1; then
  (
    cd "${ROOT_DIR}"
    docker compose up -d mysql mailhog
  )
else
  echo "docker not found, skipping mysql/mailhog startup"
fi

if command -v python3 >/dev/null 2>&1; then
  if [[ ! -d "${ROOT_DIR}/backend/.venv" ]]; then
    python3 -m venv "${ROOT_DIR}/backend/.venv"
  fi
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/backend/.venv/bin/activate"
  python -m pip install --upgrade pip
  (
    cd "${ROOT_DIR}/backend"
    python -m pip install -e '.[dev]'
  )
else
  echo "python3 not found, skipping backend dependency install"
fi

if command -v npm >/dev/null 2>&1; then
  (
    cd "${ROOT_DIR}/admin"
    npm install
  )
else
  echo "npm not found, skipping admin dependency install"
fi

if command -v flutter >/dev/null 2>&1; then
  (
    cd "${ROOT_DIR}/mobile"
    flutter pub get
  )
else
  echo "flutter not found, skipping mobile dependency install"
fi

cat <<'EOF'

Bootstrap complete.
Next commands:
  cd backend && source .venv/bin/activate && alembic upgrade head && python -m app.db.seed
  cd backend && source .venv/bin/activate && uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000
  cd admin && npm run dev -- --host 0.0.0.0 --port 5173
  cd mobile && ./scripts/run_local.sh
EOF
