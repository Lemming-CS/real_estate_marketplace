# Submission Checklist

## Code And Repo
- [ ] `.env` files are not committed
- [ ] migrations are applied locally
- [ ] seed runs successfully
- [ ] backend starts
- [ ] admin starts
- [ ] mobile starts
- [ ] README matches actual product behavior
- [ ] stale legacy marketplace wording is removed from user-facing docs

## Demo Readiness
- [ ] screenshots captured
- [ ] demo accounts verified
- [ ] Russian locale checked
- [ ] promoted listing visible
- [ ] reported listing visible in admin
- [ ] suspended seller note visible in admin detail
- [ ] messaging attachment flow checked
- [ ] map screen checked
- [ ] optional video upload path checked

## Explanation Readiness
- [ ] can explain why admin does not approve every listing
- [ ] can explain report-driven moderation
- [ ] can explain dynamic category attributes
- [ ] can explain payment record vs promotion record separation
- [ ] can explain suspension note persistence and audit logging
- [ ] can explain deduplicated view counting

## Local Commands
- [ ] `./scripts/bootstrap_local.sh`
- [ ] `cd backend && source .venv/bin/activate && alembic upgrade head && python -m app.db.seed`
- [ ] `cd backend && source .venv/bin/activate && pytest`
- [ ] `cd mobile && flutter test`
- [ ] `cd mobile && flutter analyze`
- [ ] `cd admin && npm run build`
