# Changelog

## 2.4.0 — 2026-07-10

### Added

- Public Trust Center
- Machine-readable public trust status
- Public evaluation-record feed
- Controlled evaluation-definition registry
- Eight seeded evaluation methods
- Immutable evaluation runs
- Immutable check-level results
- Evaluation content hashes
- Automatic trust findings for failed checks
- Finding lifecycle and remediation records
- Public and internal incident records
- Incident lifecycle and aggregate-status effects
- Known limitation registry
- Evidence-backed attestations and revocation
- Trust-domain aggregation
- Evaluation freshness handling
- Ledger-integrity influence on overall status
- Default platform-native evaluation suite
- Context-driven calculator, connector, AI, and accessibility evaluation
- Recorded custom evaluator
- ValidationEvent compatibility records
- Trust Center webhook events
- `trust:read` public API scope
- Unified Public API trust routes
- Python public SDK trust methods
- JavaScript public SDK trust methods
- Internal Python client trust-administration methods
- Developer Portal trust documentation and console routes
- Postman Trust Center requests
- WordPress Trust Center shortcode
- WordPress public trust-status shortcode
- Public trust JSON schemas
- Trust evaluation CLI
- Migration `0005`
- Trust Center regression tests

### Security and integrity

- Evaluation runs and check results reject ORM updates and deletes
- Private incidents, limitations, attestations, findings, and runs are excluded from public status
- Failed evaluation findings are ledgered and emitted as webhook events
- Attestation contents are hashed
- Overall status becomes critical when ledger verification fails
- Missing evaluations remain unknown rather than passing
- Existing API plans receive `trust:read` without replacing custom quota values

### Changed

- Platform Core version updated to 2.4.0
- Health and readiness report Trust Center availability
- Service metadata reports Trust Center capabilities
- Registry statistics include evaluation and trust records
- Seed manifest updated to v2.4.0
- Developer Portal includes Trust Center routes and scope
- Public SDK packages updated to v2.4.0
- Webhook user agent updated to v2.4.0

### Deferred

- Independent third-party assurance workflow
- Scheduled evaluation orchestration service
- Distributed rate-limit backend
- External source-snapshot object storage adapter
- Dedicated graph database adapter
- User workspaces and casebooks

## 2.3.0 — 2026-07-10

- Unified Public API
- Developer applications and scoped hashed API keys
- Rate limits, quotas, request records, webhooks, Developer Portal, SDKs, and Postman collection

## 2.2.0 — 2026-07-10

- Claims, source snapshots, evidence records, calculation traces, provenance, reviews, manifests, and tamper-evident ledger

## 2.1.0 — 2026-07-10

- Controlled Predicate Registry, relationship reviews, graph paths, neighborhoods, recommendations, JSON-LD, and Knowledge Explorer

## 2.0.0 — 2026-07-10

- Universal Entity Registry, stable IDs, aliases, relationship foundation, evidence foundations, and integration clients
