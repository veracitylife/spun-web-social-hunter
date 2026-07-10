# Architecture

## Service Boundaries

- `apps/web`: analyst dashboard and report surface.
- `apps/api`: FastAPI HTTP API, source registry, export endpoint, job lifecycle, connector orchestration.
- `apps/api/social_hunter/connectors`: normalized source adapters.
- `apps/api/social_hunter/engine`: approved public-profile HTTP checker.
- `apps/api/social_hunter/integrations`: paid-provider client skeletons.
- `apps/api/social_hunter/services`: auth context, billing plans, jobs, privacy hashes, rate limits, reports, source health.
- `apps/api/social_hunter/db.py`: planned SQLAlchemy persistence models.
- `apps/api/migrations/0001_initial.sql`: initial SQL schema scaffold.
- `docs/engine-contract.md`: integration contract for separately built normalized-result engines.

## Connector Families

The connector registry is organized by capability instead of by one-off provider:

- `username_profile`: public account/profile checks.
- `email_intel`: email discovery, validation, and breach exposure checks.
- `phone_intel`: validation and carrier/risk intelligence for known phone numbers.
- `person_enrichment`: licensed person/company enrichment with consent or legitimate-interest gates.
- `business_contact`: business/entity contact data from public or licensed providers.
- `domain_intel`: RDAP/WHOIS, DNS, passive DNS, infrastructure, and technology profile sources.
- `web_search`: search-index providers for public web evidence.

Every provider adapter must return normalized `Finding` records and must not return raw secrets, cookies, or private payloads.

## Request Flow

1. Analyst submits target with authorization confirmation.
2. API validates target and either runs immediately or creates a job.
3. Connector registry runs enabled source adapters.
4. Findings are normalized into one schema.
5. UI displays findings with source URL, confidence, evidence, and compliance flags.
6. Export endpoint returns JSON, CSV, or Markdown report content.

## Production Remaining Work

- Replace in-memory job store with Redis/Celery or persisted queue records.
- Add Alembic or another migration runner.
- Wire SQLAlchemy repositories into API and worker paths.
- Replace demo auth with production identity.
- Wire Stripe checkout/subscription webhooks.
- Inject provider credentials through OpenClaw Vault-backed runtime config.\n- Promote provider placeholders to live connectors only after terms, consent, rate-limit, and storage review.
