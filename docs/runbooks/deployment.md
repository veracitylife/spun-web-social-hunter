# Production Deployment Runbook

## Target

A single VPS can run the first production build with Docker Compose, Postgres, Redis, API, worker, frontend, Nginx, and monitoring profile.

## Preflight

```powershell
docker compose config
```

## Start Local Stack

```powershell
docker compose up --build
```

## Start Production Profile

```powershell
docker compose --profile production up -d --build
```

## Start Monitoring Profile

```powershell
docker compose --profile monitoring up -d
```

## Required Before Public Launch

- Replace local `.env` with Vault-injected runtime configuration.
- Add TLS termination through the host proxy or managed load balancer.
- Configure real auth provider.
- Run database migrations.
- Configure backups for Postgres.
- Add alerting for API health, queue depth, error rate, and disk usage.
