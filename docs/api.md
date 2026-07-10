# API Summary

## `GET /health`

Returns API status.

## `POST /api/search`

Runs enabled source connectors immediately. Searches require `consent_confirmed: true`.

Supported `target_type` values:

- `username`
- `email`
- `domain`
- `ip`
- `phone`

Supported `source_groups`:

- `username_profile`: WhatsMyName-style public profile checks, GitHub, Reddit, X, Mastodon/GitLab/Stack Overflow slots
- `email_intel`: Hunter.io, HIBP, email validation/MX provider slot
- `phone_intel`: Twilio Lookup v2 phone validation and carrier/risk intelligence
- `person_enrichment`: People Data Labs and FullContact-style enrichment slots
- `business_contact`: Google Places, Yelp Fusion, OpenCorporates business/entity data
- `domain_intel`: RDAP/WHOIS, IPinfo, SecurityTrails, BuiltWith/Wappalyzer, DNSDB-style passive DNS
- `web_search`: Brave Search, SerpApi, Bing Web Search, Tavily, Exa, and legacy Google CSE customer slot

Live paid/provider calls remain gated behind Vault-backed credential references and terms review. Placeholder connectors return normalized skipped findings until enabled.

## `POST /api/search/jobs`

Creates a classroom/demo job and executes it through the job lifecycle service.

## `GET /api/search/jobs`

Lists demo jobs in memory.

## `GET /api/search/jobs/{job_id}`

Returns one demo job.

## `GET /api/sources`

Returns connector capability registry, including provider status, categories, target types, terms notes, and returned fields.

## `GET /api/sources/health`

Returns source health/readiness summary. Providers that need credentials return `needs_key` until Vault references are mapped.

## `GET /api/plans`

Returns subscription plan model for future Stripe wiring.

## `GET /api/admin/launch-checklist`

Returns launch-readiness checklist.

## `GET /api/engine-contract`

Returns the live normalized-result contract for external engines.

## `POST /api/export`

Returns JSON, CSV, or Markdown report content from a `SearchResponse`.
