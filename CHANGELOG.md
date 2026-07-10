# Changelog

## 2.3.0 — 2026-07-10

### Added

- Unified `/api/v1` public API
- Consistent public response envelope
- Public request IDs and API-version headers
- Developer applications
- Application approval and suspension states
- Public, standard, and internal API plans
- Scoped API credentials
- One-time plaintext key issuance
- SHA-256-only credential storage
- Credential expiration and revocation
- Per-minute rate limits
- Daily request quotas
- Plan-aware maximum page sizes
- Request usage records
- Salted client IP and user-agent hashing
- Developer identity and usage endpoints
- Public registry, graph, evidence, and ledger routes
- Public-data filtering for claims, evidence, manifests, and ledger entries
- Signed webhook subscriptions
- Wildcard and prefix webhook event matching
- Webhook outbox, deliveries, retry state, and delivery history
- Registry, relationship, claim, snapshot, provenance, trace, evidence, and review events
- Webhook dispatch worker
- Developer Portal
- Interactive public API console
- Public OpenAPI document
- Python public SDK
- JavaScript public SDK
- Postman collection
- WordPress Developer Portal shortcode
- WordPress public API plan shortcode
- Public JSON schemas for plans, applications, subscriptions, and envelopes
- Internal Python client developer-administration methods
- Migration `0004`
- Public API, credential, quota, privacy, portal, and webhook regression tests

### Security

- API keys are returned once and stored only as SHA-256 hashes
- Key and webhook-secret responses use `Cache-Control: no-store`
- Production public API fails closed without a request-log salt
- Production webhook signing fails closed without a master signing secret
- Public ledger routes exclude developer administration records
- Public evidence manifests exclude nonverified evidence and review assignments
- Production webhook URLs require HTTPS and reject private-network destinations
- Request logs retain salted hashes rather than raw client IP and user-agent values

### Changed

- Platform Core version updated to 2.3.0
- Health and metadata report developer-platform readiness
- Seed manifest updated to v2.3.0
- CORS exposes request, API-version, quota, and retry headers
- Existing `/v1` integrations remain unchanged
- Public external integrations use the curated `/api/v1` surface

### Deferred

- Public Trust Center
- Developer self-service billing
- Distributed rate-limit backend
- External source-snapshot object storage adapter
- Dedicated graph database adapter
- User workspaces and casebooks

## 2.2.0 — 2026-07-10

- Claims, source snapshots, evidence records, calculation traces, provenance, reviews, manifests, and tamper-evident ledger

## 2.1.0 — 2026-07-10

- Controlled Predicate Registry, relationship reviews, graph paths, neighborhoods, recommendations, JSON-LD, and Knowledge Explorer

## 2.0.0 — 2026-07-10

- Universal Entity Registry, stable IDs, aliases, relationship foundation, evidence foundations, and integration clients
