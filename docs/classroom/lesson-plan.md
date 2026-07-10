# Classroom Guide

## Learning Objectives

- Understand OSINT source attribution.
- Normalize heterogeneous source results into one schema.
- Compare confidence scoring strategies.
- Discuss privacy, consent, retention, and misuse prevention.
- Build report exports without storing unnecessary raw payloads.

## Lab 1: Local Search Flow

1. Start the stack.
2. Run a username search for `socialhunter`.
3. Open the evidence panel.
4. Export JSON and CSV.
5. Identify which findings are fixtures and which are provider placeholders.

## Lab 2: Source Registry

1. Open Sources.
2. Classify each source as ready, stubbed, needs key, or disabled.
3. Add one public-source fixture to `apps/api/social_hunter/data/sources.json`.
4. Re-run the search and verify source attribution.

## Lab 3: Ethics And Guardrails

Discuss why the platform stores normalized findings and compliance flags instead of raw private payloads.

## Lab 4: Provider Integration Design

Use `docs/engine-contract.md` to define a provider integration plan. The provider must return normalized findings and source terms.
