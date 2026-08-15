# Platform Core v2.8.1 — Production Integration & Readiness Audit

## Defect closed

Core v2.8.0 treated `/ready` as a database/Core-process check and returned `unified_service_gateway: ready` without proving that a product service in the gateway registry was configured or reachable. This allowed a deployment to appear globally ready while Site Intelligence could still be `core-unconfigured` from the product side.

## v2.8.1 contract

- `/health` is liveness only.
- `/ready` is deployment/release readiness.
- `/integration/readiness` is public-safe and never includes upstream URLs or service tokens.
- `/v1/gateway/health` remains the authenticated operator diagnostic surface.
- Required product services must be configured, enabled, operational, and version-compatible.
- Optional product services remain visible without blocking Core's own registry/evidence/data-fabric operation.
- A required token policy fails before a network request when a token is missing.
- An expected version prefix fails closed on either mismatch or an upstream that does not report its version.
- A required canonical Core URL and required browser CORS origin can be enforced independently.

## Production Site Intelligence boundary

The v2.8.1 Render blueprint marks Site Intelligence as a required product integration, expects the `4.` version family, and leaves the actual URL/token deployment-supplied. Transient third-party data-provider health is not part of this first-party release gate.

## Validation

- Inherited v2.8.0 regression suite: 99/99 passed.
- New v2.8.1 integration/readiness tests: 15/15 passed.
- Total deterministic suite: 114/114 passed.
- Fresh database migration: 0001–0011 applied, no pending migrations.
- Seed contract: 40 governed sources, 39 connector definitions.
- Static checks: Python, PHP, JavaScript, Bash, JSON, Render YAML passed.
- Push-safe secret scan: 0 findings.
