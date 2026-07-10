# Production Setup Guide

## Overview

This document guides you through enabling production-ready features:
- User authentication (Auth0, Okta, OIDC)
- Audit logging
- Rate limiting
- Vault credential injection
- Compliance controls
- Data retention policies

## 1. Authentication Setup

### Auth0 Configuration

1. Create an Auth0 tenant at https://auth0.com
2. Create an Application (type: Regular Web Application)
3. Set environment variables:
   ```bash
   IDENTITY_PROVIDER=auth0
   AUTH0_DOMAIN=your-tenant.auth0.com
   AUTH0_CLIENT_ID=your_client_id
   AUTH0_CLIENT_SECRET=your_client_secret  # Inject via Vault
   ```
4. Implement Auth0 token verification in `services/auth.py::_auth0_verify()`

### Alternative: Okta

1. Create an Okta organization at https://developer.okta.com
2. Set environment variables:
   ```bash
   IDENTITY_PROVIDER=okta
   OKTA_DOMAIN=your-tenant.okta.com
   ```

### Alternative: Generic OIDC

1. Configure any OIDC-compliant provider
2. Set environment variables:
   ```bash
   IDENTITY_PROVIDER=oidc
   OIDC_ISSUER=https://your-provider.com
   ```

## 2. Vault Credential Injection

### Setup HashiCorp Vault

1. Install Vault: https://www.vaultproject.io/downloads
2. Start Vault in dev mode (not for production):
   ```bash
   vault server -dev
   ```
3. Store secrets:
   ```bash
   vault kv put secret/social-hunter/hibp_api_key value=your-hibp-key
   vault kv put secret/social-hunter/ipinfo_token value=your-ipinfo-token
   vault kv put secret/social-hunter/hunter_api_key value=your-hunter-key
   ```
4. Enable Vault in environment:
   ```bash
   VAULT_ENABLED=true
   VAULT_ADDR=http://localhost:8200  # or your Vault server
   VAULT_TOKEN=your-vault-token
   ```

### Fallback: Environment Variables

If Vault is not available, secrets are read from environment:
   ```bash
   HIBP_API_KEY=your-hibp-key
   IPINFO_TOKEN=your-ipinfo-token
   HUNTER_API_KEY=your-hunter-key
   ```

## 3. Database Persistence

### Run Alembic Migrations

1. Create initial migration:
   ```bash
   cd apps/api
   alembic revision --autogenerate -m "initial schema"
   ```
2. Apply migrations:
   ```bash
   alembic upgrade head
   ```

### Wire Repositories

The `db_models.py` file contains SQLAlchemy ORM models. Wire them into services:

- `AuditService`: Replace `self.in_memory_log` with database queries
- `RateLimitService`: Replace `self.buckets` with Redis (or database)
- `RetentionService`: Implement `cleanup_expired_searches()`, `delete_user_data()`

## 4. Rate Limiting

### Using Redis (Recommended)

```python
from redis import Redis
from social_hunter.services.rate_limit import RateLimitService, RateLimitConfig

redis_client = Redis.from_url(os.getenv("REDIS_URL"))
config = RateLimitConfig()
rate_limit_service = RateLimitService(config, redis_client)
```

### Configure Plan-Based Limits

Modify `RateLimitConfig` to adjust per-plan limits:
```python
config = RateLimitConfig(
    searches_per_minute_free=5,
    searches_per_hour_free=100,
    searches_per_day_free=500,
    searches_per_minute_professional=20,
    searches_per_hour_professional=500,
    searches_per_day_professional=5000,
)
```

## 5. Audit Logging

### Enable Database Persistence

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from social_hunter.services.audit import AuditService
from social_hunter.db_models import Base

engine = create_async_engine(os.getenv("DATABASE_URL"))
async_session = AsyncSession(engine)
audit_service = AuditService(db_session=async_session)
```

### View Audit Logs

Access the admin endpoint:
```bash
curl http://localhost:8000/api/admin/audit/logs
```

## 6. Compliance Controls

### Add Custom Denylists

```bash
curl -X POST http://localhost:8000/api/admin/compliance/denylist/update \
  -H "Content-Type: application/json" \
  -d '{"action": "add", "category": "email_patterns", "value": ".*@internal\\.company\\.local"}'
```

### Check Compliance

```bash
curl -X POST http://localhost:8000/api/admin/compliance/check \
  -H "Content-Type: application/json" \
  -d '{"target_type": "email", "target": "test@internal.company.local"}'
```

## 7. Data Retention Policies

### Set User Retention Policy

```bash
curl -X POST http://localhost:8000/api/settings/retention/policy?user_id=user123 \
  -H "Content-Type: application/json" \
  -d '{"policy": "90_days"}'
```

### Export User Data (GDPR)

```bash
curl http://localhost:8000/api/settings/retention/export-data?user_id=user123
```

### Delete User Data (Right to be Forgotten)

```bash
curl -X POST http://localhost:8000/api/settings/retention/delete-all-data?user_id=user123
```

## 8. Environment Variables Summary

```bash
# Authentication
JWT_SECRET=your-jwt-secret-key
IDENTITY_PROVIDER=auth0  # auth0, okta, oidc, mock
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret  # Inject via Vault

# Vault
VAULT_ENABLED=true
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=your-vault-token  # Inject via Vault
VAULT_NAMESPACE=social-hunter

# External APIs
HIBP_API_KEY=your-hibp-key  # Or inject via Vault
IPINFO_TOKEN=your-ipinfo-token
HUNTER_API_KEY=your-hunter-key

# Billing
STRIPE_API_KEY=your-stripe-key  # Inject via Vault
STRIPE_WEBHOOK_SECRET=your-webhook-secret

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/social_hunter
REDIS_URL=redis://localhost:6379/0
```

## 9. Monitoring & Observability

### Prometheus Metrics

Start Prometheus with the production profile:
```bash
docker compose --profile production --profile monitoring up -d
```

Access at http://localhost:9090

### TODO: Instrument Services

Add Prometheus metrics to services:
- `searches_total` (counter)
- `search_duration_seconds` (histogram)
- `rate_limit_exceeded_total` (counter)
- `compliance_checks_failed_total` (counter)
- `audit_events_total` (counter)

## 10. Deployment Checklist

- [ ] Enable HTTPS (TLS certificates)
- [ ] Set strong JWT_SECRET
- [ ] Configure Auth0 / Okta / OIDC provider
- [ ] Set up HashiCorp Vault
- [ ] Store all API keys in Vault
- [ ] Run database migrations
- [ ] Test rate limiting
- [ ] Enable audit logging
- [ ] Set up compliance denylists
- [ ] Configure data retention policies
- [ ] Set up monitoring/alerting
- [ ] Document operational runbooks
- [ ] Conduct security review
- [ ] Load test with production data
