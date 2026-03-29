# Implementation Plan

This document is now a submission-oriented delivery plan: what was built, what sequence made sense, and what remains as future work.

## Delivery Principles
- keep one backend source of truth
- prefer real domain workflows over mock internal shortcuts
- keep mobile and admin as real clients over stable APIs
- model payments/promotions/reports seriously, even if the external provider is mocked
- make the product clearly real-estate specific

## MVP-First Delivery Order
1. monorepo structure, local env, MySQL, backend bootstrap
2. auth, roles, profile, and seeded demo users
3. categories, dynamic attributes, listings, discovery, and media
4. report-driven moderation and admin operations
5. messaging, notifications, and secure attachments
6. promotion packages, payments, and activation flow
7. Flutter real-estate mobile experience
8. submission hardening: tests, docs, seed polish, bootstrap, UX cleanup

## Stage Status

### Stage 0: Repository Foundation
Status: completed

Delivered:
- backend/admin/mobile/docs/infra monorepo structure
- Docker Compose with MySQL and Mailhog
- sample env files
- Makefile commands

Main risk handled:
- avoided over-scaffolding without real integrations

### Stage 1: Identity And Profiles
Status: completed

Delivered:
- registration, login, refresh, logout
- forgot/reset/change password
- current user and profile update
- profile image upload
- account status enforcement

Dependencies:
- Stage 0

### Stage 2: Real-Estate Listings
Status: completed

Delivered:
- apartment/house categories
- rent/sale listing model
- map coordinates and location fields
- property media and optional video support
- favorites, view counters, owner actions, sold status, soft delete
- search/filter/sort/pagination

Dependencies:
- auth and category metadata

### Stage 3: Report-Driven Moderation
Status: completed

Delivered:
- listing/user/conversation reports
- admin reports queue
- hide/archive/suspend flows from reports
- audit logging
- suspension note persistence and admin visibility

Important policy decision:
- admin does not pre-approve every new listing
- reports are the primary moderation intake

### Stage 4: Messaging And Notifications
Status: completed

Delivered:
- listing-linked conversations
- secure messaging permissions
- image/document attachments
- unread states
- notifications for message and commerce events

### Stage 5: Promotions And Payments
Status: completed

Delivered:
- promotion packages
- payment records
- pending/success/failure lifecycle
- promotion activation only after successful payment
- duplicate promotion attempt blocking
- promoted listing visibility

### Stage 6: Mobile Product UX
Status: completed for assignment scope

Delivered:
- browse/search/filter
- property detail with photos, counters, and location map
- create/edit/publish/delete/sold flows
- favorites
- messaging
- notifications
- promotions/payment history
- reporting
- localization (`en`, `ru`)

### Stage 7: Submission Hardening
Status: completed in this repository pass

Delivered:
- broader backend integration assertions
- Flutter validation/state tests
- demo-focused documentation
- bootstrap script
- seed polish and real local property photos
- stale legacy marketplace wording cleanup in user-facing docs and env setup

## Backend / Mobile / Admin Task Split

### Backend
- auth and session domain
- listing validation and persistence
- media storage and secure access
- messaging, notifications, reports
- payments, promotions, audit logging

### Mobile
- browse and owner workflows
- session handling
- map and media UX
- reporting and messaging UX
- localized UI

### Admin
- operational visibility
- user suspension and note review
- listing moderation controls
- reports queue
- payment/promotion/package management
- audit log review

## What Was Mocked Safely
- external email provider
- external payment provider
- push notification delivery

These are mocked safely because:
- the core domain records are still real
- flows are still visible and testable locally
- no core marketplace behavior depends on faked internal booleans

## What Had To Be Real
- database schema and migrations
- auth/session handling
- listing CRUD and search
- report workflow
- admin audit logs
- payment records and promotion activation
- secure message/media access
- Flutter/admin integration with the real backend

## Manual Steps Required From The User
- install Python, Node.js, Flutter, and Docker
- copy env files
- run migrations
- run seed
- start emulator/simulator for Flutter

Fastest local preparation path:
```bash
./scripts/bootstrap_local.sh
cd backend && source .venv/bin/activate && alembic upgrade head && python -m app.db.seed
```

## Remaining Future Work
- stronger geospatial search
- richer video playback UX on mobile
- production object storage
- CI/CD and deployment
- expanded automated mobile integration testing
