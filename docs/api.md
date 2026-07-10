# API Summary

## `GET /health`

Returns API status.

## `POST /api/search`

Runs enabled source connectors immediately.

## `POST /api/search/jobs`

Creates a classroom/demo job and executes it through the job lifecycle service.

## `GET /api/search/jobs`

Lists demo jobs in memory.

## `GET /api/search/jobs/{job_id}`

Returns one demo job.

## `GET /api/sources`

Returns connector capability registry.

## `GET /api/sources/health`

Returns source health/readiness summary.

## `GET /api/plans`

Returns subscription plan model for future Stripe wiring.

## `GET /api/admin/launch-checklist`

Returns launch-readiness checklist.

## `GET /api/engine-contract`

Returns the live normalized-result contract for external engines.

## `POST /api/export`

Returns JSON, CSV, or Markdown report content from a `SearchResponse`.
