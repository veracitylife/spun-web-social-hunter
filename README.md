# Social Hunter - Production OSINT Aggregation Platform

Social Hunter is a **production-ready OSINT aggregation platform** for authorized analysts to search for and consolidate information about usernames, emails, domains, and IP addresses from public and approved sources.

Built with modern security, compliance, and operational best practices.

## Quick Start

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Start the stack
docker compose up --build

# 3. Access services
# Web app:      http://localhost:5173
# API:          http://localhost:8000
# Health:       http://localhost:8000/health
# Docs:         http://localhost:8000/docs
```

## Stack

- **Frontend**: React + Vite + TypeScript
- **API**: FastAPI + Pydantic
- **Worker**: Python async task queue
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Cache**: Redis
- **Auth**: JWT + pluggable identity providers (Auth0, Okta, OIDC)
- **Secrets**: HashiCorp Vault
- **Monitoring**: Prometheus
- **Deployment**: Docker Compose + production profiles

## Key Features

### 🔐 Security & Authentication
- JWT-based authentication
- Pluggable identity providers (Auth0, Okta, OIDC, or mock for demo)
- Secure credential injection via HashiCorp Vault
- Support for external API key management

### 📋 Compliance & Audit
- Immutable audit logging for all operations
- Real-time audit event streaming (Redis)
- Compliance denylists (protected classes, minors, internal domains/IPs)
- Target-level compliance checks before search execution
- Audit log retention configuration

### 🚦 Rate Limiting
- Per-user rate limits (plan-based: free, professional, enterprise)
- Per-IP rate limits for anonymous requests
- Per-target cooldowns (prevent rapid re-searches)
- Configurable time windows (minute, hour, day)

### 📊 Data Privacy & Retention
- GDPR-compliant data export endpoints
- Right to be forgotten (full user data deletion)
- Configurable retention policies (30/90/180/365 days or indefinite)
- Automatic cleanup of expired searches and exports
- Privacy-preserving target hashing for audit logs

### 💳 Billing Integration
- Subscription plan model (free, professional, enterprise)
- Plan-based feature gates (search limits, export access, API access)
- Stripe webhook scaffolding (ready for integration)

### 📁 Data Model
- Normalized findings schema (source, confidence, evidence, compliance flags)
- Export formats: JSON, CSV, Markdown
- Source attribution and confidence scoring
- Compliance flag tracking

## Documentation

- **[Product Scope](docs/product-scope.md)** — Allowed/disallowed sources, abuse prevention
- **[Architecture](docs/architecture.md)** — Service boundaries and request flow
- **[API](docs/api.md)** — Endpoint summary
- **[Production Setup](docs/PRODUCTION_SETUP.md)** — Configure auth, vault, compliance
- **[Deployment](docs/runbooks/deployment.md)** — Deployment runbook
- **[Operations](docs/runbooks/operations.md)** — Operational runbook

## Useful Commands

```bash
# Start stack (dev)
docker compose up --build

# Start stack (production with Nginx reverse proxy)
docker compose --profile production up -d --build

# Start stack (with Prometheus monitoring)
docker compose --profile monitoring up -d

# View configuration
docker compose config

# Run database migrations
docker compose exec api alembic upgrade head

# View API documentation
http://localhost:8000/docs

# Check source health
curl http://localhost:8000/api/sources/health
```

## Production Deployment

See **[Production Setup Guide](docs/PRODUCTION_SETUP.md)** for:
- Configuring Auth0 / Okta / OIDC
- Setting up HashiCorp Vault
- Enabling audit logging and retention policies
- Configuring rate limiting and compliance controls
- Running database migrations
- Setting up monitoring and alerting

## Environment Variables

Key production environment variables:

```bash
# Authentication
JWT_SECRET=your-jwt-secret
IDENTITY_PROVIDER=auth0  # auth0, okta, oidc, mock
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your-client-id

# Vault (optional, falls back to environment variables)
VAULT_ENABLED=true
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=your-vault-token

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/social_hunter
REDIS_URL=redis://redis:6379/0

# External APIs (stored in Vault in production)
HIBP_API_KEY=vault-or-env-injected
IPINFO_TOKEN=vault-or-env-injected
HUNTER_API_KEY=vault-or-env-injected
```

See [.env.production](.env.production) for a complete production template.

## API Endpoints

### Search
- `POST /api/search` — Run search immediately
- `POST /api/search/jobs` — Enqueue search job
- `GET /api/search/jobs` — List jobs
- `GET /api/search/jobs/{job_id}` — Get job status

### Sources
- `GET /api/sources` — List available sources
- `GET /api/sources/health` — Check source health/readiness

### Data
- `POST /api/export` — Export search as JSON/CSV/Markdown
- `GET /api/plans` — List subscription plans

### Admin
- `GET /api/admin/launch-checklist` — Deployment readiness
- `GET /api/engine-contract` — Engine integration contract
- `GET /api/admin/audit/logs` — Audit log retrieval
- `POST /api/admin/compliance/check` — Check target compliance
- `GET /api/admin/compliance/denylist` — View denylists
- `POST /api/admin/compliance/denylist/update` — Manage denylists

### User Settings
- `GET /api/settings/retention/policy` — Get retention policy
- `POST /api/settings/retention/policy` — Set retention policy
- `POST /api/settings/retention/export-data` — GDPR data export
- `POST /api/settings/retention/delete-all-data` — Right to be forgotten

### Authentication
- `POST /api/auth/token` — Exchange provider token for JWT
- `GET /api/auth/me` — Get current user
- `POST /api/auth/refresh` — Refresh access token
- `POST /api/auth/logout` — Logout

## Compliance & Legal

Before launch, ensure:
- ✅ Privacy policy published
- ✅ Terms of service reviewed by legal
- ✅ Data retention policy documented
- ✅ Abuse reporting process established
- ✅ Audit logging enabled and tested
- ✅ GDPR/CCPA compliance verified
- ✅ Compliance denylists configured
- ✅ Rate limits and abuse prevention active

## Support & Issues

Refer to:
- **[docs/runbooks/operations.md](docs/runbooks/operations.md)** for operational troubleshooting
- **[docs/runbooks/deployment.md](docs/runbooks/deployment.md)** for deployment issues
- **[docs/PRODUCTION_SETUP.md](docs/PRODUCTION_SETUP.md)** for configuration

## License

See LICENSE file for licensing information.
