# Social Hunter

Current version: `0.1.9`


Social Hunter is a managed public-source intelligence SaaS for username, email, domain, IP, business, and phone validation workflows. It is built around source attribution, confidence scoring, normalized evidence, exports, role-based access, billing controls, and operational auditability.

This build includes the customer-facing workspace, member and admin dashboards, provider registry, report exports, persistent settings, payment configuration, compliance gates, usage controls, and deployment assets.

## Stack

- Frontend: React + Vite
- API: FastAPI
- Worker: Python async worker process
- Queue/cache: Redis
- Database: PostgreSQL
- Web routing: Nginx profile
- Monitoring: Prometheus profile
- Runtime: Docker Compose

## Quick Start

1. Copy safe environment template:

```powershell
Copy-Item .env.example .env
```

2. Map real secrets through secure secret references before production use. Do not paste raw keys into tracked files.

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

- Search dashboard with username, email, domain, IP, and phone modes
- Reports view with JSON/CSV export flow
- Source registry view
- Admin settings, compliance, usage, billing, and operations views
- FastAPI search, queued-job, source registry, source health, plans, readiness, compliance, usage control, export, and integration endpoints
- WhatsMyName-style public profile URL connector
- Public profile HTTP checker engine for approved public URLs
- HIBP, IPinfo, Hunter.io, People Data Labs, Twilio Lookup, GitHub, X, search-index, business-data, and domain-intel provider client skeletons
- PostgreSQL models and initial SQL migration for searches, findings, source health, exports, and audits
- Rate-limit, auth-context, billing-plan, privacy-hash, usage-control, and report services
- Docker Compose with Postgres, Redis, API, worker, web, Nginx, and Prometheus profiles
- Cost model, legal templates, deployment notes, and operations runbooks


## Connector Families

- `username_profile`: WhatsMyName-style public profiles, GitHub, Reddit, X, Mastodon/GitLab/Stack Overflow slots
- `email_intel`: Hunter.io, HIBP, mailbox syntax/MX validation
- `phone_intel`: Twilio Lookup v2 validation and carrier/risk intelligence
- `person_enrichment`: People Data Labs and FullContact-style enrichment slots
- `business_contact`: Google Places, Yelp Fusion, OpenCorporates
- `domain_intel`: RDAP/WHOIS, IPinfo, SecurityTrails, BuiltWith/Wappalyzer, DNSDB-style passive DNS
- `web_search`: Brave Search, SerpApi, Bing Web Search, Tavily, Exa, and legacy Google CSE customer slot

Live provider calls are controlled by secure credential references, provider terms, tenant source gates, and admin approval rules. Providers without active credentials return normalized status results instead of exposing raw failures.
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
- `docs/runbooks/deployment.md`
- `docs/runbooks/operations.md`
- `docs/cost-model.md`

## Versioning

Versioning starts at `0.1.1`. Each major contribution or release milestone increments the patch version by `0.0.1`.

## SaaS Routes

- Public landing page: `/`
- Member gateway: `/members/`
- Admin gateway: `/social-hunter-admin`
- PayPal receiving account: `techpronow@gmail.com`
