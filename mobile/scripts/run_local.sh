#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_DIR/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing mobile/.env. Copy mobile/.env.example to mobile/.env first."
  exit 1
fi

if [[ ! -d "$PROJECT_DIR/android" && ! -d "$PROJECT_DIR/ios" ]]; then
  flutter create --platforms=android,ios "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"
flutter pub get

APP_NAME="$(grep '^APP_NAME=' "$ENV_FILE" | cut -d '=' -f 2-)"
API_BASE_URL="$(grep '^API_BASE_URL=' "$ENV_FILE" | cut -d '=' -f 2-)"

flutter run \
  --dart-define=APP_NAME="$APP_NAME" \
  --dart-define=API_BASE_URL="$API_BASE_URL"

