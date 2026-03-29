# Interaction Model

## Runtime Relationship
```text
Flutter Mobile App ----\
                        \
                         -> FastAPI Backend -> MySQL
                        /                  -> Local media storage
React Admin Panel -----/                   -> Mailhog
```

## Responsibilities
- Mobile handles renter/buyer and seller UX.
- Admin handles operations, reports, visibility controls, payments/promotions oversight, and suspension review.
- Backend owns auth, permissions, listing validation, moderation, messaging, promotions, and audit logging.
- MySQL stores transactional state.
- Media files are stored outside MySQL under the configured storage path.

## Request Flow
1. Mobile or admin sends an HTTP request to the backend.
2. Backend validates auth, status, permissions, and input schema.
3. Backend executes domain logic and persists state.
4. Backend returns JSON or protected media/file responses.
5. Notification and payment-side effects are created by backend workflows, not by clients guessing state.

## Property Listing Interaction
1. Seller creates or edits a property listing in `draft`.
2. Seller fills real-estate fields:
   - purpose
   - property type
   - city / district / address
   - map coordinates
   - rooms / area / floors / price
3. Seller optionally uploads photos and video.
4. Seller publishes directly once validation passes.
5. Listing becomes visible in public discovery immediately.

## Moderation Interaction
1. Renter/buyer or another user reports a listing, user, or conversation.
2. Admin sees the report in the report queue and linked context screens.
3. Admin can hide/archive the listing or suspend the user if needed.
4. Audit logs and status history capture the action and note.

This is intentionally report-driven moderation rather than universal pre-approval.

## Promotion Interaction
1. Seller chooses a promotion package and targeting scope.
2. Backend creates pending promotion and payment records.
3. Mock payment result updates payment state.
4. Only successful payment activates the promotion.

## Local Development Notes
- backend: `http://localhost:8000`
- admin: `http://localhost:5173`
- MySQL: `localhost:3306`
- Mailhog UI: `http://localhost:8025`
- Android emulator should use `10.0.2.2` for backend access
