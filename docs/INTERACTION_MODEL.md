# Interaction Model

## Runtime Relationship
```text
Flutter Mobile App ----\
                        \
                         -> FastAPI Backend -> MySQL
                        /
React Admin Panel -----/                  -> Mailhog (local email sink)
```

## Responsibilities
- Mobile handles buyer and seller UX.
- Admin handles moderation and operations UX.
- Backend owns business rules, authorization, and persistence.
- MySQL stores marketplace state.
- Mailhog is a local-only helper for email-oriented flows.

## Request Flow
1. Mobile or admin sends HTTP request to the backend.
2. Backend validates auth, permissions, and request schema.
3. Backend executes application logic and persists state in MySQL.
4. Backend returns JSON responses to the requesting client.
5. Future notification or email adapters are triggered from backend-side events, not client-side assumptions.

## Local Development Notes
- Backend runs on `http://localhost:8000`
- Admin runs on `http://localhost:5173`
- MySQL runs on `localhost:3306`
- Mailhog UI runs on `http://localhost:8025`
- Flutter emulator/device should target the backend URL appropriate to its runtime environment
