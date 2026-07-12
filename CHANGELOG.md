# Changelog

## 0.1.9 - 2026-07-13

- Replaced the public platform-controls block with sales-focused value copy.
- Added a public questions-and-answers section for prospects.
- Removed setup-oriented password reset and contact wording from public-facing surfaces.
- Kept the six operational controls in the app while moving their details into protected admin/member areas.

## 0.1.8 - 2026-07-13

- Added live role verification before rendering member or admin dashboard UI.
- Added member-only and admin-only verification endpoints.
- Changed member dashboard APIs to require member role instead of accepting any valid session.
- Ensured member tokens cannot load admin configuration views or admin-only API data.

## 0.1.7 - 2026-07-13

- Reframed the public landing page from internal recommendations into included SaaS platform controls.
- Added admin-managed compliance settings for tenant controls, consent records, source attribution, geography, use case, and reviewer role policy.
- Added admin-managed usage controls for queued jobs, concurrency limits, cost alerts, billing notifications, and automatic pause behavior.
- Added audit records for completed searches, queued jobs, exports, compliance changes, and usage-control changes.
- Removed customer-visible demo, launch, scaffold, and handoff language from the main SaaS UI and README.

## 0.1.6 - 2026-07-12

- Finished member dashboard account and billing surfaces with live account summary, plan details, source health, recent jobs, and PayPal checkout wiring.
- Finished admin dashboard overview, users/tenant management, and mail settings pages against live backend endpoints.
- Wired member signup requests to backend signup and PayPal checkout flows instead of a static form.

## 0.1.5 - 2026-07-12

- Added an admin proxy connection tester that checks each imported proxy against a configurable public target URL.
- Added per-proxy result reporting with redacted proxy display, status, latency, HTTP status, and safe error messages.
- Added backend protections that block proxy tests against localhost, private, link-local, multicast, and reserved target hosts.

## 0.1.4 - 2026-07-12

- Added provider catalog mapping every source/API to its backend connector function and required Vault references.
- Wired admin API-key, source-gate, proxy import, proxy validation, proxy route, contact mail, and audit pages to backend endpoints.
- Added proxy route rules for allowlisted provider API egress without bypass or evasion features.

## 0.1.2 - 2026-07-12

- Added email-based password reset panels to both the member and admin gateways.
- Added admin password reset API endpoint and audit event.
- Wired reset forms to the live API reset endpoints with success and error states.

## 0.1.1 - 2026-07-12

- Added SaaS public landing page with pricing, benefits, contact, and recommendations.
- Added member gateway and member dashboard routes.
- Added admin gateway and admin configuration dashboard routes.
- Added PayPal-oriented plan and checkout scaffolding for techpronow@gmail.com.
- Added backend scaffold endpoints for member/admin auth, signup, password reset, contact submissions, admin settings, API key tests, proxy tests, and audit events.
- Established milestone versioning rule: each major contribution increments patch version by 0.0.1.
