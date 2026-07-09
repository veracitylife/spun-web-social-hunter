# Operations Runbook

## Health Checks

```powershell
docker compose ps
curl http://localhost:8000/health
```

## Source Registry

```powershell
curl http://localhost:8000/api/sources
```

## Engine Contract

```powershell
curl http://localhost:8000/api/engine-contract
```

## Rollback

Restore a backed-up file from the closest `backup-files` directory, then rebuild the affected service.

Example:

```powershell
Copy-Item .\apps\api\social_hunter\backup-files\main.py.backup.TIMESTAMP .\apps\api\social_hunter\main.py
docker compose up -d --build api worker
```
