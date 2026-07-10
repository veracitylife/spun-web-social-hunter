# Social Hunter

Social Hunter is an educational OSINT aggregation platform scaffold for username, email, domain, and IP lookups. It is built around source attribution, confidence scoring, normalized evidence, exports, and operator auditability.

This build includes the platform around lawful OSINT workflows: UI, API, source registry, connector contracts, provider clients, report exports, data models, deployment files, monitoring profile, and classroom docs.

## Stack

- Frontend: React + Vite
- API: FastAPI
- Worker: Python async worker process
- Queue/cache: Redis
- Database: PostgreSQL
- Reverse proxy: Nginx profile
- Monitoring: Prometheus profile
- Runtime: Docker Compose

## Quick Start

1. Copy safe environment template:

```powershell
Copy-Item .env.example .env
```

2. Map real secrets through OpenClaw Vault references before production use. Do not paste raw keys into tracked files.

3. Start the stack:

```powershell
docker compose up --build
```

4. Open:

- Web app: `http://localhost:5173`
- API health: `http://localhost:8000/health`
- Source registry: `http://localhost:8000/api/sources`
- Engine contract: `http://localhost:8000/api/engine-contract`

## Delivered Platform Pieces

- Search dashboard with username, email, domain, and IP modes
- Reports view with JSON/CSV export flow
- Source registry view
- Admin/launch blocker view
- FastAPI search, queued-job, source registry, source health, plans, launch checklist, export, and engine contract endpoints
- WhatsMyName-style fixture connector
- Public profile HTTP checker engine for approved public URLs
- HIBP, IPinfo, and email-validation provider client skeletons
- PostgreSQL model scaffold and initial SQL migration for searches, findings, source health, exports, and audits
- Rate-limit, auth-context, billing-plan, privacy-hash, and report service scaffolds
- Docker Compose with Postgres, Redis, API, worker, web, Nginx, and Prometheus profiles
- Classroom guide, cost model, legal templates, deployment and operations runbooks

## Useful Commands

```powershell
docker compose config
docker compose up --build
docker compose --profile production up -d --build
docker compose --profile monitoring up -d
```

## Docs

- `docs/product-scope.md`
- `docs/architecture.md`
- `docs/api.md`
- `docs/engine-contract.md`
- `docs/classroom/lesson-plan.md`
- `docs/runbooks/deployment.md`
- `docs/runbooks/operations.md`
- `docs/cost-model.md`
- `docs/handoff.md`
