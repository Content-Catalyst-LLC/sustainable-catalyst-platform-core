# Changelog

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
