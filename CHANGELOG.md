# Changelog

## 2.25.0 — 2026-08-16
- Added migration `0028` and five secret-free credential/key lifecycle record families.
- Added provider-neutral secret references and service-consumer/operation policy metadata.
- Added key versioning, SHA-256 fingerprints, expiry, retirement, revocation and compromise states.
- Added operator-triggered overlap-aware rotation and explicit completion lineage.
- Added Core credential bootstrap metadata for write API, webhook signing, dossier signing and federation trust bindings.
- Added credential-use audit events with credential-like context stripping before persistence.
- Added public-safe aggregate credential health, SDK/WordPress status surfaces, and optional production-certification gating.
- Explicitly disabled secret/private-key persistence, automatic secret generation/distribution, and automatic key rotation.

## 2.24.0 R1 — Secret-Scan Example Credential & Promotion Repair
- Repaired the push-safe secret scan false positive on the documented federation placeholder `replace-with-long-random-secret`.
- Replaced brittle inline grep filtering with a deterministic value-aware repository scanner.
- Kept `.env.example` files in scan scope; exact documented placeholders are allowed while live-looking credentials remain blocking.
- Added R1 regression tests, contract validation, repair/resume tooling, and promotion audit documentation.
- Preserved runtime `2.24.0` and migration head `0027`; no capacity-governance or federation behavior changed.

## 2.24.0 — Capacity Forecasting & Resource Governance
- Added migration `0027` and five durable capacity-governance object classes.
- Added generic resource profiles and bounded utilization/demand observations.
- Added bounded-linear forecasts with explicit confidence, horizon, predicted utilization, insufficient-data state, and hours-to-capacity.
- Added runtime observation materialization for active jobs, queued partitions, and connector work backlog.
- Added per-product/resource budgets and advisory soft-limit governance decisions.
- Added public-safe aggregate capacity status and SDK/WordPress surfaces.
- Added optional production-certification capacity readiness gating.
- Explicitly disabled automatic scaling, infrastructure purchase, deployment mutation, and hard admission control.

## 2.23.1 — 2026-08-15

- Repaired current release/version metadata across Core runtime, WordPress, public SDKs, deployment user agent, README, roadmap, and release tooling.
- Promoted `distributed_connector_workers` and `server_sent_live_data_events` from deferred to implemented metadata, matching v2.9.0 runtime and regression coverage.
- Added capability-lineage tests and release validation requiring implemented/deferred capability sets to be unique and disjoint.
- Added static implementation proof checks for connector worker leasing and SSE endpoints.
- Preserved migration head `0026`; no schema migration or federation semantic change.

## 2.19.0
- Incident Response, Change Control & Rollback Coordination.
- Adds migration 0022, hash-linked incident events, high-risk approval gates, operator-confirmed rollback assessment, and aggregate public operational status.

## 2.14.0 — 2026-08-15

- Added Cross-Product Evidence Exchange and migration `0017`.
- Added reference-first, non-destructive exchange packages and receipt history across Sustainable Catalyst products.
- Added idempotency, bounded snapshots, canonical Core URIs and inherited Truth-precedence semantics.
- Prevented public escalation of non-public source records and rejected credential-like exchange metadata.
- Added private exchange stream events, public-safe readiness metadata, SDK helpers, WordPress status and deployment validation.

## 2.13.0 — 2026-08-15

- Added Earth, Ocean, Space & Scientific Service Fabric.
- Added persisted scientific domain routing bindings and migration `0016`.
- Added domain-specific scientific records, assets, time-series and map-layer APIs.
- Added mission/source summaries and automatic routing refresh for scientific ingestion.
- Domain routing is explicitly non-truth-precedence metadata and never rewrites source observations.

# Changelog

## 2.12.0 — 2026-08-14

- Added Country Evidence Federation & Reconciliation.
- Added migration `0015` and persisted reconciliation audits.
- Added non-blending comparability guards for concept, semantic class, unit and geography.
- Added public country federation/reconciliation APIs and SDK helpers.
- Added WordPress country-evidence status surface.

## 2.11.0 — 2026-08-14

- Added Humanitarian Access & Essential Services Fabric and migration `0014`.
- Added source-aware conditions for health, education, food, water, electricity, fuel, displacement, communications, shelter, humanitarian access, and protection.
- Added facility-linked and country-level humanitarian observations without requiring every condition to resolve to a facility.
- Added semantic roles that separate operational conditions, humanitarian indicators, classifications, structural baselines, and contextual reports.
- Added conservative structured materialization from HDX HAPI and future explicitly mapped connectors.
- Explicitly prohibited automatic promotion of ReliefWeb report metadata to operational conditions.
- Explicitly prohibited synthetic severity scores, automatic legal conclusions, and automatic causal attribution.
- Added public APIs, SDK helpers, WordPress status, JSON Schema, deployment controls, validation, and regression coverage.

## 2.10.0 — 2026-08-14

- Added Operational Evidence & Facility Registry for hospitals, clinics, schools, universities, shelters, crossings, essential-service infrastructure and related public-interest facilities.
- Added stable source identifiers, geospatial lookup and provenance-preserving dated facility observations.
- Added operational, damage, access, service, capacity and supply status dimensions without automatic cross-source flattening.
- Added migration `0013`, facility APIs, public query surfaces, stream-event integration, schemas, validation and regression coverage.

# Changelog

## 2.9.0 — 2026-08-14

- Added migration `0012` and the persistent streaming/reliability control plane.
- Added database-backed connector work queue, worker leases, retry/dead-letter policy, and standalone distributed worker process.
- Added Server-Sent Events for internal and scoped public consumers.
- Added threshold/existence alert rules and geographic bounding-box matching.
- Added persistent geographic subscriptions.
- Added stale-source detection using connector freshness windows.
- Added immutable dead-letter records and historical replay into new work items.
- Added explicit provider failover groups and priorities; automatic failover requires an explicit parameter-compatibility declaration.
- Added streaming events for successful connector ingestion and triggered alerts without allowing reliability-event failures to roll back source ingestion.
- Added v2.9.0 Python/JavaScript SDK packages, WordPress reliability status, deployment controls, schemas, and regression tests.
- Preserved v2.8.1 production readiness and kept transient external-provider health non-blocking for release promotion.

## 2.8.1 — 2026-08-14

- Separated `/health` liveness from `/ready` production/deployment readiness.
- Added required/optional service semantics and per-service readiness states.
- Required first-party integrations now block release readiness when unconfigured, disabled, unavailable, circuit-open, missing a required service token, version-unreported, or version-incompatible.
- Added safe upstream-version reporting and expected-version-prefix validation.
- Added canonical public Core URL and required CORS-origin configuration gates.
- Added public-safe `/integration/readiness` without exposing upstream URLs or service tokens.
- Added production Render configuration for the Site Intelligence integration.
- Added WordPress integration-readiness status and v2.8.1 regression tests.
- Preserved the v2.8.0 data fabric and all v2.0.0–v2.8.0 routes and migrations.

## 2.8.0 — 2026-07-14

- Added migration `0011` and the geospatial, time-series, scientific-asset, map-layer, and STAC data fabric.
- Added automatic and idempotent materialization from live observations and scientific records.
- Added GeoJSON feature collections, bounding-box queries, monthly time-series partition keys, and PostgreSQL PostGIS/BRIN indexes when available.
- Added STAC 1.0 catalog, collection, item, and search routes.
- Added FITS, NetCDF, Zarr, GeoParquet, COG, PMTiles, VOTable, GRIB2, WMS, WMTS, SDMX, and TAP/ADQL capability records.
- Added internal and scoped public APIs, SDK methods, WordPress status, schemas, deployment controls, and regression tests.

## 2.7.3 — 2026-07-14

- Added migration `0010` and normalized `economic_data_records`.
- Added twelve governed free official-statistics sources and connectors.
- Added shared SDMX CSV ingestion for IMF, OECD, ECB, BIS, and ILOSTAT.
- Added Eurostat JSON-stat, BEA, BLS, Census, SEC EDGAR, EIA, and FAOSTAT adapters.
- Added internal and scoped public economics APIs, SDK methods, WordPress status, provenance, and tests.
- Preserved the strict no-paid-provider acceptance gate and fail-closed free-registration controls.

## 2.7.2 — 2026-07-14

- Added the Scientific Data Connector Pack with 13 connectors over 12 official free-access sources.
- Added migration `0009` and normalized scientific data records with raw-ingestion provenance.
- Added NASA, NOAA, ECMWF, USGS Water, NCBI, PubChem, GBIF, Materials Project, MAST, HEASARC, IRSA, and ESO adapters.
- Added read-only TAP/ADQL validation, scientific APIs, SDK methods, WordPress status, schema, and deployment configuration.
- Preserved the strict zero-paid-provider and credit-card-free acceptance rules.


## 2.7.1 — 2026-07-14

- Added the International Law and United Nations Connector Pack.
- Added UN Digital Library, SDG Metadata, ReliefWeb, HDX HAPI, UN Population, UN Comtrade, UNHCR, and OHCHR UHRI adapters.
- Added a dedicated international-law record store with authority classification and provenance.
- Added internal and scoped public international-law discovery APIs.
- Added source registry records for the UN Treaty Collection, ICJ, and International Law Commission without enabling unsupported scraping.
- Preserved the strict free-source and no-credit-card gate.
- Added a legal safeguard that does not infer Security Council binding effect from a document symbol alone.

## 2.7.0 — 2026-07-14

### Added

- Free Live Data Gateway and Connector Registry
- Migration `0007`
- Strict free-source and no-credit-card acceptance gate
- Source license, attribution, automated-access, and redistribution records
- Connector adapter SDK and runtime
- Bounded upstream response handling
- Bounded raw-response persistence with SHA-256 hashes
- Ingestion run history and connector operational state
- Stable normalized observations and deduplication
- Freshness, quality, methodology, and provenance fields
- Internal `/v1/live` APIs
- Scoped `/api/v1/live` APIs
- `data:read` public API scope
- MET Norway Locationforecast adapter
- NASA GIBS WMTS adapter
- USGS earthquake GeoJSON adapter
- World Bank V2 Indicators adapter
- FRED Series Observations adapter
- UN SDG V5 catalog adapter
- Python and JavaScript SDK methods
- WordPress Live Data Gateway status shortcode
- Sync command, deployment configuration, JSON schemas, and documentation

### Security

- Active sources must remain free and credit-card-free in strict mode.
- Unreviewed or excluded sources cannot be ingested in strict mode.
- Production connector URLs require HTTPS.
- Public routes hide adapter, base URL, raw payload, credentials, and internal configuration.
- Provider credentials remain environment-backed.

### Compatibility

- Preserves all v2.0.0–v2.6.0 routes, migrations, models, and gateway behavior.


## 2.6.0 — Unified Service Gateway and Integration Foundation

- Added environment-backed product service registry.
- Added bounded internal and public gateway routing.
- Added aggregate downstream health reporting.
- Added request correlation, service-token forwarding, and gateway response metadata.
- Added timeouts, size limits, method allowlists, and per-service circuit breakers.
- Added `gateway:read` to the governed public API plans.
- Added Docker Compose and production environment examples.
- Preserved all v2.0–v2.5 APIs and data models.


## 2.5.0 — 2026-07-10

### Added

- Controlled workflow-definition registry
- Research-to-signature-dossier workflow
- Evidence-assurance-dossier workflow
- Dashboard-publication-dossier workflow
- Workflow runs and ordered product stages
- Required-stage dependency enforcement
- Draft, active, blocked, completed, and cancelled workflow states
- Pending, active, blocked, failed, completed, and skipped step states
- Input and output references for workflow stages
- Append-only workflow transitions
- Transition content hashes
- Workflow completion hashes
- Workflow ledger and webhook records
- Signature dossier registry
- Frozen dossier-record snapshots
- SHA-256 record snapshot hashes
- Support for graph, evidence, calculation, provenance, trust, workflow, and ledger dossier records
- Append-only dossier approvals
- Latest-signer approval-state resolution
- Required approval count
- Canonical finalized dossier snapshots
- SHA-256 dossier hashes
- HMAC-SHA256 Platform Core signatures
- Dossier signing key identifiers
- Dossier signature verification
- Dossier tamper detection
- Superseding dossier lineage
- Public/private dossier record boundaries
- Public Dossier Center
- Public workflow and dossier API routes
- `workflow:read` and `dossier:read` scopes
- Python SDK workflow and dossier methods
- JavaScript SDK workflow and dossier methods
- WordPress Dossier Center shortcode
- WordPress signature dossier shortcode
- WordPress workflow status shortcode
- Migration `0006`
- Workflow and dossier JSON schemas
- End-to-end workflow, signature, tampering, scope, and privacy tests

### Security

- Production finalization fails closed without a dossier-signing secret
- Dossier signing uses a distinct configured secret and key identifier
- Dossier records are immutable snapshots
- Workflow transitions and dossier approvals are append-only
- Public APIs exclude private dossier records
- Public APIs expose only finalized or superseded public dossiers
- Verification uses constant-time HMAC comparison

### Changed

- Platform Core version updated to 2.5.0
- API plans include `workflow:read` and `dossier:read`
- Developer Portal documents workflow and dossier routes
- Seed manifest updated to v2.5.0
- Platform metadata reports workflow and signature-dossier capabilities

### Deferred

- External public-key signature verification
- Qualified or regulated electronic signatures
- User casebooks
- Distributed workflow workers
- Automated product callbacks for every workflow stage
- External source-snapshot object storage adapter

## 2.4.0 — 2026-07-10

- Trust Center, evaluation definitions and runs, findings, incidents, known limitations, attestations, trust status, and trust SDK methods

## 2.3.0 — 2026-07-10

- Unified Public API, developer applications, scoped credentials, quotas, webhooks, Developer Portal, SDKs, and Postman collection

## 2.2.0 — 2026-07-10

- Evidence Ledger, claims, snapshots, evidence, provenance, calculation traces, reviews, and tamper-evident ledger

## 2.1.0 — 2026-07-10

- Governed Knowledge Graph, predicate registry, relationship reviews, traversal, paths, recommendations, and Knowledge Explorer

## 2.0.0 — 2026-07-10

- Universal Entity Registry, stable IDs, aliases, relationship foundation, validation records, and integration clients

## 2.15.0
- Distributed processing, storage-object registry, backpressure, retention and scale diagnostics.
