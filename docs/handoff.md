# Handoff

## Current State

This repository contains a working educational OSINT aggregation platform scaffold:

- React dashboard in `apps/web`
- FastAPI service in `apps/api`
- Async worker entrypoint in `apps/api/social_hunter/worker.py`
- Public profile checker in `apps/api/social_hunter/engine/public_profile_checker.py`
- Provider client skeletons in `apps/api/social_hunter/integrations` for Hunter.io, People Data Labs, Twilio Lookup, public profiles, search indexes, business data, and domain intelligence
- Local fixture connector data in `apps/api/social_hunter/data/sources.json`
- Source registry in `apps/api/social_hunter/sources.py`
- Job lifecycle service in `apps/api/social_hunter/services/jobs.py`
- Source health service in `apps/api/social_hunter/services/source_health.py`
- Initial SQL migration in `apps/api/migrations/0001_initial.sql`
- PostgreSQL model scaffold in `apps/api/social_hunter/db.py`
- Service scaffolds for auth, billing, privacy hashing, rate limits, and reports
- Docker Compose for Postgres, Redis, API, worker, frontend, Nginx, and Prometheus
- Classroom, architecture, API, deployment, operations, legal, and cost docs

## What Works Now

- Demo username/email/domain/IP/phone searches through normalized connector paths.
- Evidence panel with confidence, source URL, status, and compliance flags.
- Source registry endpoint and UI.
- Source health, plan, launch-checklist, and queued-job endpoints.
- Category filtering and Markdown export in the dashboard.
- Engine contract endpoint and admin view.
- JSON, CSV, and Markdown export endpoint.
- Docker Compose service definitions.

## What Is Intentionally Stubbed

- Paid API calls are client skeletons until Vault-backed API key injection, consent/legitimate-interest checks, source terms review, and rate-limit policy are wired.
- Authentication returns a demo context only.
- PostgreSQL models are present, but migrations and persistence wiring are not complete.
- Billing plans are modeled, but Stripe checkout/subscriptions are not wired.
- PDF rendering is not implemented; Markdown/JSON/CSV exports are implemented.

## Next Build Steps

1. Convert `apps/api/migrations/0001_initial.sql` into Alembic-managed migrations.
2. Persist searches, findings, source health, exports, and audit events.
3. Replace demo auth with a real auth provider.
4. Add Stripe checkout and subscription webhooks.
5. Import a licensed WhatsMyName dataset with `apps/api/social_hunter/scripts/import_whatsmyname.py`.
6. Wire HIBP, IPinfo, Hunter.io, People Data Labs, Twilio Lookup, GitHub, Reddit, X, search-index, business-contact, and domain-intel providers with Vault-provided runtime secrets.
7. Add PDF report rendering from Markdown report output.
8. Add queue-backed job lifecycle: queued, running, completed, failed.
9. Add source health checks and admin retry controls.
10. Add classroom seed data and instructor reset command.

## Rollback

Backups were created under local `backup-files` directories before existing files were changed. Restore the relevant backup, then rebuild the affected service.

Example:

```powershell
Copy-Item .\apps\api\social_hunter\backup-files\main.py.backup.TIMESTAMP .\apps\api\social_hunter\main.py
docker compose up -d --build api worker
```

## Validation Commands

```powershell
docker compose config
docker compose up --build
```

Expected local URLs:

- `http://localhost:5173`
- `http://localhost:8000/health`
- `http://localhost:8000/api/sources`
- `http://localhost:8000/api/engine-contract`
