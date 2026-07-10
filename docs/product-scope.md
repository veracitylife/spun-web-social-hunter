# Product Scope

## Purpose

Social Hunter helps authorized analysts aggregate public or approved OSINT signals for usernames, email addresses, domains, and IP addresses.

## Allowed Sources

- Public profile URLs that can be checked without authentication.
- Official APIs with valid keys and terms-compliant use.
- User-supplied datasets with documented provenance.
- Breach/intelligence providers where the account plan allows the requested lookup.
- DNS, WHOIS, and IP intelligence APIs with clear licensing.

## Disallowed Sources

- CAPTCHA bypass.
- Login-wall scraping.
- Password reset abuse.
- Session-cookie automation.
- Credential collection.
- Scraping private APIs or mobile APIs without permission.
- Stealth browser fingerprint evasion.
- Storing raw secrets, cookies, auth headers, or credential dumps.

## Abuse Prevention

- Require authenticated users for non-demo searches.
- Rate-limit by user, IP, and target type.
- Add cooldowns for repeated searches against the same target.
- Keep an immutable audit log for search target, user, timestamp, source set, and export actions.
- Add denylisted target patterns for protected classes, minors, and internal-only domains.
- Make exports traceable to the user account that generated them.

## Data Retention

- Store search metadata and normalized findings.
- Store source URLs, timestamps, confidence scores, and provider names.
- Avoid storing sensitive raw payloads unless required and approved.
- Allow report deletion and account-level retention policy.

## Connector Policy

Every connector must declare:

- Source name
- Source type
- Terms/licensing note
- Authentication requirement
- Rate limit
- Data fields returned
- Whether raw payload storage is allowed

## Launch Gate

Do not launch publicly until legal terms, privacy policy, abuse reporting, billing terms, and data retention controls are complete.
