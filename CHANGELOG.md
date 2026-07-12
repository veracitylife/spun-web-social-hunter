# Changelog

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
