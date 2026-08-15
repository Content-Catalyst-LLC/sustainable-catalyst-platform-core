# Sustainable Catalyst Platform Core v2.8.1

## Production Integration & Readiness Repair

Core v2.8.1 repairs a production-readiness ambiguity in the v2.8.0 service gateway. Earlier releases could report `/ready` with `unified_service_gateway: ready` after only confirming the Core database, even when product services in the gateway registry were unconfigured.

v2.8.1 makes the distinction explicit:

- `/health` is **liveness**: Core is running and can answer requests.
- `/ready` is **deployment truth**: Core plus every first-party service marked required must satisfy readiness.
- `/integration/readiness` is a **public-safe integration view** that never exposes service URLs or service tokens.
- `/v1/gateway/health` remains the authenticated operator-level downstream health surface.

### Service states

Each registered product service now reports a distinct state:

- `unconfigured`
- `disabled`
- `operational`
- `degraded`
- `unavailable`
- `circuit_open`
- `configuration_error`
- `version_unreported`
- `version_mismatch`

Required services block release readiness unless operational. Optional services remain visible without falsely blocking Core's own registry, evidence, connector, and data-fabric capabilities.

### Production configuration

The v2.8.1 deployment template adds:

- `SC_CORE_PUBLIC_BASE_URL`
- `SC_CORE_PUBLIC_BASE_URL_REQUIRED`
- `SC_CORE_REQUIRED_CORS_ORIGIN`
- per-service `REQUIRED`
- per-service `TOKEN_REQUIRED`
- per-service `EXPECTED_VERSION_PREFIX`

The Render blueprint marks Site Intelligence as the first required production product integration. Its URL and optional service token remain deployment-supplied secrets/configuration rather than committed repository values.

### Compatibility

v2.8.1 is additive. It adds no database migration and preserves all v2.0.0–v2.8.0 entity, graph, evidence, public API, trust, workflow, connector, economics, scientific, geospatial, time-series, STAC, map-layer, SDK, and WordPress contracts.

Third-party provider availability remains outside the first-party release gate.

## Validation

- 114 deterministic tests passed: 99 inherited v2.8.0 regressions plus 15 v2.8.1 production-integration/readiness tests.
- Fresh SQLite migration applies 0001 through 0011 with no pending migration.
- 40 governed source records and 39 connector definitions remain seeded.
- Python, PHP, JavaScript, Bash, JSON, Render YAML, SDK ZIP integrity, and push-safe secret scanning pass.
