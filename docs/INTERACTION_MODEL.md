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

## Listing Moderation Interaction
1. Mobile creates or edits a listing in draft/private space.
2. Mobile uploads listing media and submits the listing for review.
3. Backend validates category attributes, media presence, ownership, and status transitions.
4. Admin fetches the moderation queue from admin-prefixed endpoints.
5. Admin approves or rejects the listing with a moderation note.
6. Approved listings become visible in public listing endpoints; rejected listings stay private to the owner and admin.

## Local Development Notes
- Backend runs on `http://localhost:8000`
- Admin runs on `http://localhost:5173`
- MySQL runs on `localhost:3306`
- Mailhog UI runs on `http://localhost:8025`
- Flutter emulator/device should target the backend URL appropriate to its runtime environment
