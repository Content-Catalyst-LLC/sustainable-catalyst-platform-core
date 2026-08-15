# Sustainable Catalyst Platform Core v2.18.0

Core v2.18.0 adds **Observability, SLOs & Production Operations**: a local-first operational telemetry and service-level-objective layer that makes Core performance and release behavior auditable without requiring a paid monitoring vendor.

Key v2.18.0 additions:
- non-fatal request duration/status telemetry with query-string exclusion;
- aggregate availability, error-rate and p95 latency windows;
- persisted SLO definitions and met/breached/insufficient-data evaluation;
- seeded Platform Core availability and p95 latency objectives;
- production deployment markers and retention compaction;
- public-safe aggregate status with no raw request IDs or operator metadata;
- additive migration `0021`;
- no evidence/Truth-precedence effect from operational telemetry.

---

# Sustainable Catalyst Platform Core v2.14.0

Core v2.14.0 adds **Cross-Product Evidence Exchange**: a governed, reference-first handoff contract for moving evidence and analytical references between Sustainable Catalyst products without rewriting canonical records or promoting derived artifacts into new Truth sources.

Key v2.14.0 additions:
- persisted exchange packages, canonical subject references, bounded snapshots and receipt history;
- supported product identities for Site Intelligence, Workspace, Lab, Knowledge Library, Decision Studio, Research Librarian, Workbench, Advisory, Catalyst Data, Finance and Narrative Risk;
- idempotent package creation and pull/acknowledgement delivery semantics;
- privacy guardrails preventing non-public subjects from being placed in public packages;
- credential-like snapshot/provenance keys rejected before persistence;
- `truth_precedence = inherit-from-subject` and no automatic authority promotion;
- source records retained after acceptance or derivation;
- private stream events for package creation and receipts;
- additive migration `0017`, public readiness metadata, SDK readiness helpers and WordPress status.

---

# Sustainable Catalyst Platform Core v2.13.0

Core v2.13.0 adds **Earth, Ocean, Space & Scientific Service Fabric** on top of the scientific connector pack and geospatial/time-series/STAC asset fabric. Scientific records, time series and map layers can now be routed into first-class Earth, Ocean and Space discovery domains while retaining their original source and provenance.

Key v2.13.0 additions:
- first-class Earth, Ocean and Space domain front-door contracts;
- persisted scientific-domain bindings with explicit classification basis and confidence;
- Ocean presented independently rather than hidden inside generic Earth science;
- domain-specific records, assets, time-series and map-layer APIs;
- mission and source summaries for domain discovery;
- automatic routing refresh for newly ingested scientific records;
- routing-only semantics with `truth_precedence = none`;
- zero routed records explicitly means no indexed records, not no science;
- migration `0016`, public API/SDK helpers, WordPress status, schema and regression coverage.

---

# Sustainable Catalyst Platform Core v2.12.0

Core v2.12.0 adds **Country Evidence Federation & Reconciliation** on top of the operational facility and humanitarian evidence layers. Country data is organized by evidence authority and semantic role, with explicit comparability guards and no automatic averaging.

Key v2.12.0 additions:
- country evidence federation across official statistics, humanitarian conditions and facility evidence;
- primary-official, sector-official, operational, intergovernmental and harmonized-benchmark authority roles;
- source-selection rationale and preferred-source fallback reporting;
- geographic, semantic, unit and reference-period compatibility checks;
- persisted reconciliation audits;
- public APIs, SDK helpers and WordPress status surface.

---

# Sustainable Catalyst Platform Core v2.11.0

Core v2.11.0 adds **Humanitarian Access & Essential Services Fabric** on top of the v2.10.0 Operational Evidence & Facility Registry. Humanitarian conditions are stored as dated, source-aware observations rather than flattened into a crisis score or inferred legal/causal conclusion.

Key v2.11.0 additions:

- first-class humanitarian condition records for health, education, food, water, electricity, fuel, displacement, communications, shelter, humanitarian access, and protection;
- independent condition kinds for access, interruption, availability, throughput, population affected, displacement, food security, nutrition, supply, damage, capacity, and operational presence;
- optional linkage to v2.10.0 facilities while preserving country/geographic evidence that is not facility-specific;
- explicit semantic roles separating operational conditions, humanitarian indicators, classifications, structural baselines, and contextual reports;
- automatic materialization only for live-data observations with an explicit structured semantic mapping;
- HDX HAPI mappings for displacement, humanitarian needs, operational presence, funding, and food-security records;
- ReliefWeb report metadata is retained as contextual/report evidence and is not automatically promoted into an operational condition;
- structural baselines such as annual electricity-access percentages are explicitly ineligible for the current-conditions layer;
- no synthetic crisis severity, automatic legal conclusion, or automatic causal attribution;
- additive migration `0014`, internal/public APIs, SDK helpers, WordPress status, schema and regression coverage.

## Humanitarian routes

```text
GET  /v1/humanitarian/readiness
POST /v1/humanitarian/conditions
GET  /v1/humanitarian/conditions
GET  /v1/humanitarian/country/{ISO3}/summary
POST /v1/humanitarian/materialize/live-observation/{observation_id}

GET  /api/v1/humanitarian/conditions
GET  /api/v1/humanitarian/country/{ISO3}/summary
```

The zero-record state is explicitly **unknown, not normal**. Provider outages remain observable but do not independently block Core release readiness.

## Inherited v2.10.0 facility model

Stable facilities remain separate from dated operational, damage, access, service, capacity and supply observations. Humanitarian conditions can link to those facilities when a source identifies one, but country-level reporting is not forced into a facility object.

## Existing release line

```text
v2.7.0  Free Live Data Gateway
v2.7.1  International Law and United Nations Connector Pack
v2.7.2  Scientific Data Connector Pack
v2.7.3  Economics and Official Statistics Connector Pack
v2.8.0  Geospatial, Time-Series, and Scientific Data Fabric
v2.8.1  Production Integration & Readiness Repair
v2.9.0  Streaming, Alerts, and Source Reliability
v2.10.0 Operational Evidence & Facility Registry
v2.11.0 Humanitarian Access & Essential Services Fabric
v2.12.0 Country Evidence Federation & Reconciliation
v2.13.0 Earth, Ocean, Space & Scientific Service Fabric
```

---

## v2.8.0 foundation

Core v2.8.0 adds the **Geospatial, Time-Series, and Scientific Data Fabric** on top of the v2.7.3 economics layer, v2.7.2 scientific connectors, v2.7.1 international-law and United Nations connectors, and v2.7.0 Free Live Data Gateway.

The release adds:

- Migration `0011` and seven additive fabric tables
- Automatic materialization of normalized observations into time-series definitions and monthly keyed points
- Automatic materialization of geometries into source-aware GeoJSON features with bounding boxes
- STAC 1.0 catalog, collection, item, and search routes
- Scientific asset records for FITS, NetCDF, Zarr, GeoParquet, COG, PMTiles, VOTable, and GRIB2 handoffs
- Map-layer registry for GeoJSON, WMS, WMTS, COG, PMTiles, raster tiles, and vector tiles
- Portable SQLite GeoJSON operation and PostgreSQL PostGIS expression indexes when available
- PostgreSQL BRIN indexing for time-series timestamps and portable `YYYY-MM` partition keys
- Idempotent backfill of existing v2.7.x observations and scientific records
- Internal and scoped public APIs, Python and JavaScript SDK methods, WordPress status, JSON Schemas, and deployment controls
- No paid API or credit-card-required production dependency

Core remains the shared source-governance, ingestion, normalization, provenance, and delivery layer. Site Intelligence consumes map layers and GeoJSON; Research Lab consumes STAC and scientific assets; Workbench consumes time series; Decision Studio consumes source-aware derived records; Knowledge Library preserves methods and licenses; Research Librarian discovers and routes records.

## Data-fabric routes

```text
GET  /v1/fabric/capabilities
GET  /v1/fabric/stats
POST /v1/fabric/materialize
GET  /v1/fabric/features
GET  /v1/fabric/features.geojson
GET  /v1/fabric/timeseries
GET  /v1/fabric/timeseries/{series_id}/points
GET  /v1/fabric/assets
GET  /v1/fabric/map-layers

GET /v1/stac
GET /v1/stac/collections
GET /v1/stac/collections/{collection_id}
GET /v1/stac/collections/{collection_id}/items
GET /v1/stac/search

GET /api/v1/fabric/capabilities
GET /api/v1/fabric/features
GET /api/v1/fabric/features.geojson
GET /api/v1/fabric/timeseries
GET /api/v1/fabric/timeseries/{series_id}/points
GET /api/v1/fabric/assets
GET /api/v1/fabric/map-layers
GET /api/v1/stac
GET /api/v1/stac/collections
GET /api/v1/stac/search
```

## Existing connector packs

```text
v2.7.0  Free Live Data Gateway
v2.7.1  International Law and United Nations Connector Pack
v2.7.2  Scientific Data Connector Pack
v2.7.3  Economics and Official Statistics Connector Pack
v2.8.0  Geospatial, Time-Series, and Scientific Data Fabric
v2.8.1  Production Integration & Readiness Repair
v2.9.0  Streaming, Alerts, and Source Reliability
v2.10.0 Operational Evidence & Facility Registry
```

See `docs/GEOSPATIAL_TIME_SERIES_SCIENTIFIC_FABRIC_V280.md`, `RELEASE_NOTES_V280.md`, and `deployment/platform-core-v280.env.example`.

---

## Previous release foundation: v2.6.0

**Unified Service Gateway and Integration Foundation**

Platform Core v2.6.0 makes Sustainable Catalyst Core the governed front door for internal and external product APIs while preserving Site Intelligence, Workbench, Decision Studio, Research Librarian, Catalyst Finance, and Narrative Risk as independently deployable domain services.

The release adds:

- Environment-backed service discovery for six product services
- A sanitized service catalog that never exposes service URLs or tokens
- Aggregated downstream health checks
- Correlation IDs propagated through Core and downstream requests
- Server-side service-token injection
- Request-method allowlists and request/response size limits
- Per-service timeouts and circuit breakers
- Authenticated internal proxy routes
- Read-only public developer routes under `/api/v1`
- A shared `gateway:read` public API scope
- Gateway deployment examples for Docker Compose and self-hosting
- Gateway-specific regression tests

Existing v2.0–v2.5 APIs, the Knowledge Graph, Evidence Ledger, Developer Portal, Trust Center, workflows, and signature dossiers remain available.

## Architectural principle

> Core governs access, identity, provenance, routing, and cross-product integration. Domain products retain their specialized calculations, connectors, retrieval logic, and decision workflows.

## Gateway routes

```text
GET  /v1/gateway/services
GET  /v1/gateway/health
*    /v1/gateway/{service_id}/{path}

GET  /api/v1/gateway/services
GET  /api/v1/gateway/health
GET  /api/v1/site-intelligence/{path}
GET  /api/v1/workbench/{path}
GET  /api/v1/decision-studio/{path}
GET  /api/v1/research-librarian/{path}
GET  /api/v1/finance/{path}
GET  /api/v1/narrative-risk/{path}
```

See `docs/UNIFIED_SERVICE_GATEWAY_V260.md` and `deployment/platform-core-v260.env.example`.

---

## Previous release foundation: v2.5.0

**Signature Dossiers and End-to-End Workflows**

Platform Core v2.5.0 connects the Universal Entity Registry, Knowledge Graph, Evidence Ledger, Unified Public API, and Trust Center into complete, auditable workflows that can end in a frozen and signed decision package.

The release adds:

- A controlled workflow-definition registry
- Ordered end-to-end workflow runs
- Product-specific workflow stages
- Dependency enforcement between required stages
- Append-only, hash-recorded workflow transitions
- Workflow completion hashes
- Signature dossier creation and assembly
- Frozen snapshots of included records
- Human approval and change-request records
- Canonical dossier snapshots
- SHA-256 dossier fingerprints
- HMAC-SHA256 Platform Core signatures
- Dossier verification and tamper detection
- Public and private dossier-record boundaries
- Public Dossier Center
- Public API workflow and dossier routes
- Python and JavaScript SDK support
- WordPress workflow and dossier shortcodes
- Migration `0006`

Existing v2.0–v2.4 APIs remain available.

## Architectural principle

> A final decision package should preserve not only the conclusion, but the exact evidence, sources, calculations, relationships, evaluations, disclosures, approvals, and workflow history used at the time it was signed.

## End-to-end workflows

Three workflow definitions are seeded.

### Research to Signature Dossier

```text
Frame the decision
→ Build the Research Librarian route
→ Collect Site Intelligence sources and indicators
→ Run Workbench models and calculations
→ Review claims and evidence
→ Run Trust Center evaluations
→ Assemble the dossier
→ Approve and sign
→ Publish or deliver
```

### Evidence Assurance Dossier

```text
Define assurance scope
→ Collect claims and source snapshots
→ Validate calculations and provenance
→ Run evaluation framework
→ Resolve or accept findings
→ Assemble and sign assurance dossier
```

### Dashboard Publication Dossier

```text
Verify connectors and source freshness
→ Validate indicator lineage
→ Validate calculations and visual outputs
→ Review accessibility
→ Assemble publication dossier
→ Approve and publish
```

## Workflow behavior

A workflow run instantiates the ordered stages from its definition.

Step states:

```text
pending
in_progress
blocked
completed
skipped
failed
```

Run states:

```text
draft
in_progress
blocked
completed
cancelled
```

A required stage cannot start until earlier required stages are complete or explicitly skipped. A blocked or failed stage blocks the workflow. When all required stages finish, Platform Core:

- Marks the workflow complete
- Records its completion time
- Generates a canonical workflow content hash
- Adds an append-only workflow transition
- Adds a ledger entry
- Emits a `workflow.completed` event

Workflow transition rows cannot be updated or deleted through the ORM.

## Signature dossiers

A signature dossier can include frozen snapshots of:

- Entities
- Graph relationships
- Graph neighborhoods
- Claims
- Evidence records
- Evidence manifests
- Source snapshots
- Calculation traces
- Provenance activities
- Evaluation runs and checks
- Trust findings
- Incidents
- Known limitations
- Attestations
- Trust status
- Workflow runs
- Ledger entries

Adding a record captures its current canonical representation and stores a SHA-256 snapshot hash. Later changes to the live record do not alter the dossier record.

## Approval model

Dossier approvals are append-only records with:

- Decision: `approve`, `reject`, or `request_changes`
- Signer
- Role
- Statement
- Evidence references
- Content hash
- Timestamp

Finalization uses the most recent decision from each signer. A current rejection or change request blocks finalization. The number of current approvals must meet `SC_CORE_DOSSIER_REQUIRED_APPROVALS`.

## Dossier finalization

Finalization requires:

- A draft dossier
- At least one dossier record
- A completed linked workflow, when present
- No unresolved rejection or change request
- The configured number of current approvals
- A dossier-signing secret

Platform Core then freezes one canonical snapshot containing:

```text
Dossier identity and purpose
Workflow and complete transition history
Frozen record snapshots and hashes
Approval records and hashes
Signature context and signing time
```

It computes:

```text
dossier_hash = SHA256(canonical dossier snapshot)
platform_signature = HMAC-SHA256(signing secret, dossier_hash)
```

The signature metadata includes:

- Signature algorithm
- Signing key ID
- Signer
- Signing time
- Dossier hash
- Platform signature

This is a Platform Core integrity signature. It is not a qualified electronic signature, legal notarization, or external public-key certificate.

## Verification

Verification recalculates:

- The canonical dossier snapshot hash
- The platform signature
- Every dossier-record snapshot hash
- The correspondence between database record snapshots and the frozen dossier package

A finalized dossier remains valid when its live source records change because verification checks the frozen package. Direct modification of the frozen package or record snapshots causes verification to fail.

## Internal API routes

### Workflow definitions and runs

```text
GET  /v1/workflow-definitions
POST /v1/workflow-runs
GET  /v1/workflow-runs
GET  /v1/workflow-runs/{run_id}
POST /v1/workflow-runs/{run_id}/start
POST /v1/workflow-runs/{run_id}/steps/{step_key}/transition
POST /v1/workflow-runs/{run_id}/cancel
```

### Signature dossiers

```text
POST /v1/dossiers
GET  /v1/dossiers
GET  /v1/dossiers/{dossier_id}
POST /v1/dossiers/{dossier_id}/records
POST /v1/dossiers/{dossier_id}/approvals
POST /v1/dossiers/{dossier_id}/finalize
GET  /v1/dossiers/{dossier_id}/verify
GET  /v1/dossiers/{dossier_id}/export
GET  /v1/workflow-platform/stats
```

Internal writes require `X-SC-API-Key`.

## Unified Public API

New scopes:

```text
workflow:read
dossier:read
```

Public routes:

```text
GET /api/v1/workflow-definitions
GET /api/v1/workflow-runs/{run_id}
GET /api/v1/dossiers
GET /api/v1/dossiers/{dossier_id}
GET /api/v1/dossiers/{dossier_id}/verify
```

Only public workflow runs and public finalized or superseded dossiers are returned. Dossier records marked private are excluded from public responses and public canonical snapshots.

## Dossier Center

Open:

```text
https://YOUR-PLATFORM-CORE.onrender.com/dossier-center
```

The Dossier Center lists public finalized dossiers and displays:

- Purpose and version
- Dossier hash
- Signing key ID
- Signer
- Record and approval counts
- Verification status
- Full public dossier record

## Example workflow

```bash
curl -X POST "https://YOUR-PLATFORM-CORE.onrender.com/v1/workflow-runs" \
  -H "Content-Type: application/json" \
  -H "X-SC-API-Key: YOUR_INTERNAL_WRITE_KEY" \
  -d '{
    "definition_id": "research-to-signature-dossier",
    "title": "Infrastructure Resilience Decision",
    "subject_entity_id": "sc:concept:infrastructure-resilience",
    "requested_by": "decision-studio",
    "owner": "platform-reviewer",
    "context": {},
    "public": true,
    "metadata": {}
  }'
```

Start it:

```bash
curl -X POST \
  "https://YOUR-PLATFORM-CORE.onrender.com/v1/workflow-runs/WORKFLOW_ID/start" \
  -H "Content-Type: application/json" \
  -H "X-SC-API-Key: YOUR_INTERNAL_WRITE_KEY" \
  -d '{"actor":"workflow-orchestrator"}'
```

Complete a stage:

```bash
curl -X POST \
  "https://YOUR-PLATFORM-CORE.onrender.com/v1/workflow-runs/WORKFLOW_ID/steps/frame/transition" \
  -H "Content-Type: application/json" \
  -H "X-SC-API-Key: YOUR_INTERNAL_WRITE_KEY" \
  -d '{
    "status":"in_progress",
    "actor":"decision-studio",
    "payload":{}
  }'
```

Then transition the same stage to `completed` with output references.

## Example dossier

Create:

```bash
curl -X POST "https://YOUR-PLATFORM-CORE.onrender.com/v1/dossiers" \
  -H "Content-Type: application/json" \
  -H "X-SC-API-Key: YOUR_INTERNAL_WRITE_KEY" \
  -d '{
    "workflow_run_id":"WORKFLOW_ID",
    "subject_entity_id":"sc:concept:infrastructure-resilience",
    "title":"Infrastructure Resilience Signature Dossier",
    "purpose":"Preserve the evidence and decision route used for publication.",
    "version":"1.0",
    "visibility":"public",
    "metadata":{},
    "actor":"decision-studio"
  }'
```

Add a frozen evidence manifest:

```bash
curl -X POST \
  "https://YOUR-PLATFORM-CORE.onrender.com/v1/dossiers/DOSSIER_ID/records" \
  -H "Content-Type: application/json" \
  -H "X-SC-API-Key: YOUR_INTERNAL_WRITE_KEY" \
  -d '{
    "section":"Evidence",
    "record_type":"evidence_manifest",
    "record_id":"sc:claim:CLAIM_ID",
    "label":"Claim Evidence Manifest",
    "sort_order":100,
    "public":true,
    "metadata":{},
    "actor":"dossier-assembler"
  }'
```

Approve:

```bash
curl -X POST \
  "https://YOUR-PLATFORM-CORE.onrender.com/v1/dossiers/DOSSIER_ID/approvals" \
  -H "Content-Type: application/json" \
  -H "X-SC-API-Key: YOUR_INTERNAL_WRITE_KEY" \
  -d '{
    "decision":"approve",
    "signer":"reviewer@example.org",
    "role":"Evidence Reviewer",
    "statement":"The frozen records support publication.",
    "evidence_references":[]
  }'
```

Finalize:

```bash
curl -X POST \
  "https://YOUR-PLATFORM-CORE.onrender.com/v1/dossiers/DOSSIER_ID/finalize" \
  -H "Content-Type: application/json" \
  -H "X-SC-API-Key: YOUR_INTERNAL_WRITE_KEY" \
  -d '{
    "signed_by":"Sustainable Catalyst Platform Core",
    "actor":"platform-signing-service"
  }'
```

Verify:

```bash
curl "https://YOUR-PLATFORM-CORE.onrender.com/v1/dossiers/DOSSIER_ID/verify"
```

## Production environment

Keep all v2.4 variables and add:

```text
SC_CORE_WORKFLOW_ENGINE_ENABLED=true
SC_CORE_DOSSIER_CENTER_ENABLED=true
SC_CORE_DOSSIER_SIGNING_SECRET=<long random secret>
SC_CORE_DOSSIER_SIGNING_KEY_ID=sc-platform-core-production
SC_CORE_DOSSIER_REQUIRED_APPROVALS=1
SC_CORE_DOSSIER_MAX_RECORDS=500
```

In production, dossier finalization fails closed when the signing secret is absent.

Do not reuse the internal write key, API-log salt, or webhook-signing secret as the dossier-signing secret.

## Local setup

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/python scripts/migrate.py
.venv/bin/python scripts/seed_registry.py
.venv/bin/python -m uvicorn app.main:app --reload --port 8090
```

## WordPress shortcodes

```text
[sc_dossier_center]
[sc_signature_dossier id="sc:dossier:..."]
[sc_workflow_status id="sc:workflow-run:..."]
```

These join the existing registry, graph, evidence, developer, and trust shortcodes.

## Boundaries

The dossier signature verifies the integrity of the frozen Platform Core package under the configured server secret. It does not establish that every source is true, that every analysis is correct, that a decision is legally valid, or that a human signer possesses a regulated digital-signature credential.

## License

MIT


## v2.7.1 international-law APIs

Core v2.7.1 adds a dedicated legal-record store and official-source connector pack. Internal routes begin with `/v1/international-law`; scoped public routes begin with `/api/v1/international-law` and require `data:read`. See `docs/INTERNATIONAL_LAW_UN_CONNECTORS_V271.md`.

## v2.7.2 scientific-data APIs

Core v2.7.2 adds normalized scientific discovery and provenance. Internal routes begin with `/v1/science`; scoped public routes begin with `/api/v1/science` and require `data:read`. See `docs/SCIENTIFIC_DATA_CONNECTORS_V272.md`.


## v2.7.3 economics and official-statistics APIs

Core v2.8.0 adds provider-neutral official-statistics records and provenance. Internal routes begin with `/v1/economics`; scoped public routes begin with `/api/v1/economics` and require `data:read`. See `docs/ECONOMICS_OFFICIAL_STATISTICS_CONNECTORS_V273.md`.


## v2.16.0 Governance, Access & Audit Control Plane
Central policy decisions, scoped roles, tamper-evident audit events, and retention controls are available under `/v1/governance`. Public API exposure is readiness-only.


## v2.17.0 Production Certification, Migration Assurance & Recovery Readiness

Core now provides a persisted certification plane for migration-head assurance, zero-pending migration checks, governance-audit integrity, first-party readiness policy, and tamper-evident recovery checkpoint metadata. Recovery checkpoints intentionally do **not** embed a database backup; full restore still requires an operator-managed external backup or managed database snapshot. Transient third-party provider health remains non-blocking for release certification.
