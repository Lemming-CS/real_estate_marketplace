# Real Estate Marketplace Mobile

Flutter client for the real-estate marketplace assignment.

Key user flows already implemented:
- registration, login, password reset
- browse apartments and houses for rent or sale
- property detail with map/location, counters, photos, and optional video indicator
- create, edit, publish, sell, and delete own property listings
- favorites, conversations, notifications, and promotion/payment history

Run locally:
```bash
flutter pub get
./scripts/run_local.sh
```
If app doesn't reach backend check the .env file

The app reads `APP_NAME` and `API_BASE_URL` from `mobile/.env`.
