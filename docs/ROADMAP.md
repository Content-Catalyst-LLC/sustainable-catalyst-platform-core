# Platform Core Roadmap

## v2.0.0 — Universal Entity Registry
Completed.

## v2.1.0 — Knowledge Graph and Relationship Engine
Completed.

## v2.2.0 — Evidence Ledger and Provenance Records
Completed.

## v2.3.0 — Unified Public API and Developer Portal
Completed.

## v2.4.0 — Trust Center and Evaluation Framework
Completed.

## v2.5.0 — Signature Dossiers and End-to-End Workflows
Completed.

## v2.6.0 — Unified Service Gateway and Integration Foundation
Completed.

## v2.7.0 — Free Live Data Gateway and Connector Registry
Completed: free-source policy, connector SDK, raw records, normalized observations, freshness, provenance, and six reference connectors.

## v2.7.1 — International Law and United Nations Connector Pack
Completed: official-document, SDG metadata, humanitarian, population, trade, displacement, and human-rights records with legal-authority classification.

## v2.7.2 — Scientific Data Connector Pack
Completed: Earth science, climate, hydrology, biomedical, chemical, biodiversity, materials, and astronomy connectors with read-only TAP/ADQL.

## v2.7.3 — Economics and Official Statistics Connector Pack
Completed: IMF, OECD, Eurostat, ECB, BIS, BEA, BLS, Census, SEC EDGAR, EIA, FAOSTAT, and ILOSTAT with normalized economic records.

## v2.8.0 — Geospatial, Time-Series, and Scientific Data Fabric
Completed:

- Portable GeoJSON store with bounding-box fields and queries
- Optional PostgreSQL PostGIS expression index
- Time-series definitions and points with monthly partition keys
- Optional PostgreSQL BRIN timestamp index
- STAC 1.0 catalog, collections, items, and search
- Scientific asset registry
- Map-layer registry
- WMS and WMTS handoffs
- FITS, NetCDF, Zarr, GeoParquet, COG, PMTiles, VOTable, and GRIB2 format registry
- Existing SDMX and read-only TAP/ADQL integration
- Automatic materialization and idempotent backfill
- Internal and scoped public APIs

Deferred to later infrastructure releases:

- Managed scientific object storage
- Native raster processing workers
- Native scientific-file parsers
- Distributed spatial and time-series workers


## v2.8.1 — Production Integration & Readiness Repair
Completed:

- Separates `/health` liveness from `/ready` deployment readiness
- Adds required and optional first-party service semantics
- Distinguishes unconfigured, disabled, operational, degraded, unavailable, circuit-open, configuration-error, version-unreported, and version-mismatch states
- Adds canonical public Core URL and required CORS-origin configuration checks
- Adds service-token requirement checks without exposing tokens
- Adds public-safe `/integration/readiness` and authenticated gateway diagnostics
- Makes Site Intelligence the first required production product integration in the Render blueprint
- Preserves all v2.0.0–v2.8.0 routes, migrations, source registries, connector packs, and data-fabric contracts

## v2.9.0 — Streaming, Alerts, and Source Reliability
Completed:

- Distributed connector workers
- Server-Sent Events
- Alert rules
- Geographic subscriptions
- Stale-source detection
- Dead-letter records
- Historical replay
- Provider failover


## v2.10.0 — Operational Evidence & Facility Registry
Completed: stable operational facilities, source identifiers, geospatial lookup, independent dated status dimensions, provenance history and facility stream events.


## v2.11.0 — Humanitarian Access & Essential Services Fabric
Completed:

- Humanitarian conditions across health, education, food, water, electricity, fuel, displacement, communications, shelter and access
- Facility-linked and country-level evidence
- Operational/current vs structural/context semantic roles
- Structured HDX HAPI materialization
- Report-metadata non-promotion rule
- Zero records means unknown, not normal
- No synthetic severity, legal conclusion or causal attribution
- Public APIs, SDKs, WordPress status, migration `0014`, schemas and validation


## v2.12.0 — Country Evidence Federation & Reconciliation
Completed:

- Country evidence lanes across official/published statistics, operational humanitarian conditions and facility evidence
- Authority-role precedence with explicit preferred-source fallback
- Exact concept, semantic class, unit and geographic-scope compatibility guards
- Material discrepancy detection without automatic averaging
- Different-period and subnational-scope non-conflict rules
- Persisted reconciliation audits
- Public API, SDK, WordPress status, migration `0015`, schema and validation


## v2.13.0 — Earth, Ocean, Space & Scientific Service Fabric
Completed:

- First-class Earth, Ocean and Space domain routing
- Persisted routing bindings for scientific records, time series and map layers
- Domain-specific records, assets, time-series and map-layer APIs
- Mission/source summaries and Ocean-first discoverability
- Routing classification provenance and confidence
- `truth_precedence = none` for all domain bindings
- Automatic binding refresh for new scientific ingestion
- Public API, SDK, WordPress status, migration `0016`, schema and validation


## v2.14.0 — Cross-Product Evidence Exchange
Completed.

## v2.15.0 — Distributed Processing, Storage & Scale
Completed.

## v2.16.0 — Governance, Access & Audit Control Plane
Completed.

## v2.17.0 — Production Certification, Migration Assurance & Recovery Readiness
Completed.

## v2.18.0 — Observability, SLOs & Production Operations
Completed: first-party request telemetry, aggregate service windows, persisted SLOs, deployment markers, retention compaction, public-safe production status, and local-first monitoring with no paid-provider requirement.


## v2.19.0 — Incident Response, Change Control & Rollback Coordination
Completed: governed operational incidents, hash-linked event history, risk-aware change controls, operator-confirmed rollback coordination, and aggregate public operations status.


## v2.20.0 — Continuity, Backup Verification & Disaster Recovery
Completed: backup artifact registry, checksum verification/attestation, disaster-recovery objectives, isolated SQLite restore rehearsals, externally evidenced production restore drills, RPO/RTO evaluation, public-safe continuity status, and optional certification gates.


## v2.21.0 — Multi-Region Resilience & Failover Coordination
Completed: provider-neutral region/service health, replication-aware failover groups, read-only degraded-mode coordination, explicit operator decision lineage, public-safe resilience status, and optional certification gating.


## v2.22.0 — Data Lifecycle, Archival Integrity & Preservation
Status: implemented.

## v2.23.0 — Federated Core & Trusted Node Exchange
Status: implemented.

## v2.23.1 — Capability Metadata, Documentation & Release-Lineage Repair
Status: implemented. No migration. Repairs runtime/documentation/version truth and promotes the v2.9.0 connector-worker and SSE capabilities out of the deferred set. Adds capability-lineage regression gates while preserving migration head `0026` and all v2.23.0 federation semantics.

## v2.24.0 — Capacity Forecasting & Resource Governance
Status: implemented. Adds resource profiles, utilization/demand observations, bounded linear forecasts with confidence and saturation risk, per-product/resource budgets, advisory soft-limit governance, runtime scale/connector observations, aggregate public-safe status, optional certification gating, and migration `0027`. Automatic scaling, purchasing, deployment mutation, and hard admission control remain disabled.

## v2.25.0 — Identity, Credential & Cryptographic Key Lifecycle
Status: implemented. Adds secret-free credential registry metadata, versioned key identifiers/fingerprints, expiry, overlap-aware operator rotation, revocation/compromise handling, service-consumer policy metadata, credential-use audit events, public-safe health, optional certification gating, and migration `0028`. Secret/private-key values remain outside Core persistence and rotation is never autonomous.

Next planned: v2.26.0 — Distributed Quotas, Admission Control & Workload Governance.


## v2.24.0 R1 — Secret-Scan Example Credential & Promotion Repair
Completed: promotion tooling repair only; runtime remains v2.24.0 and migration head remains `0027`.
