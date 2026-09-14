## v2.43.0 — Evidence Integrity & Chain of Custody

Open Forensics custody/integrity layer: tamper-evident custody event chains, custodians, seals, hash verification, continuity assessment, external attestations, and immutable custody snapshots.

Next planned: **v2.44.0 — Claims, Contradictions & Competing Hypotheses**.

# Platform Core Roadmap
## v2.42.0 — Forensic Object Model & Evidence Provenance
Current release. Begins Open Forensics with the governed forensic investigation/object/evidence/provenance foundation.

## Open Forensics sequence
- v2.43.0 — Evidence Integrity & Chain of Custody
- v2.44.0 — Claims, Contradictions & Competing Hypotheses
- v2.45.0 — Forensic Timeline & Event Reconstruction
- v2.46.0 — Forensic Spatial/Temporal Evidence Integration
- v2.47.0 — Media Artifact & Derivative Provenance
- v2.48.0 — Quantitative Reconstruction & Reproduction Handoffs
- v2.49.0 — Testimony, Statements & Documentary Evidence
- v2.50.0 — Forensic Research Graph
- v2.51.0 — Reproducible Investigation Packages

## v2.41.0 — Reproducible Visual Knowledge Layer
Current release. Locks the visual/research stack into reproducible knowledge packages before Open Forensics.


## v2.40.0 — Cross-Product Visual Research Objects
Governed, reference-first cross-product visual research packages with explicit source-product identity, semantic member relations, saved composite views, immutable snapshots, portable bundles, and non-executing runtime handoffs.
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

## v2.26.0 — Distributed Quotas, Admission Control & Workload Governance
Status: implemented. Adds database-shared quota policies and usage buckets, burst budgets, workload priority classes, per-class concurrency leases, idempotent admission decisions, retry guidance, SLO/capacity-aware throttling, hard rejection, public-safe aggregate status, optional certification gating, and migration `0029`. Automatic scaling, infrastructure purchasing, and deployment mutation remain disabled.

## v2.27.0 — Scientific Object Storage & Processing Adapter Fabric
Status: implemented. Adds migration `0030`, governed local scientific-object storage, credential-free provider-managed references, SHA-256 integrity metadata, parent/derived lineage, processing-adapter contracts, an executable deterministic object-manifest adapter, public-safe metadata APIs, SDK/WordPress surfaces, and an optional certification gate. xarray, GDAL, and Astropy remain contract-only until configured workers exist. Arbitrary code execution and automatic external-object fetching remain disabled.

## v2.28.0 — Research Object & Model Foundation
Status: implemented. Adds migration `0031` and graph-native research projects, models, immutable model versions, variables, parameters, scenarios, model-run orchestration records, and results. Research objects inherit the Universal Entity Registry, Knowledge Graph, Evidence Ledger, calculation-trace, and provenance foundations. Core records execution intent and lineage but does not execute models; Lab, Workbench, and explicit external runtimes remain the compute boundary.

## v2.29.0 — Visual Reasoning Object Model
Status: implemented. Adds migration `0032`, graph-native renderer-neutral visual reasoning objects, semantic elements and relations, reasoning layers, governed annotations, Core-entity/scientific-object source bindings, and immutable SHA-256 semantic snapshots. Core owns meaning and lineage, not layout, styling, renderer selection, or automatic causal/truth inference.

## v2.30.0 — Visualization Specification & Renderer Registry
Status: implemented. Adds migration `0033`, immutable revisioned visualization specifications, renderer-family contract definitions, contract-version metadata, governed compatibility rules, deterministic compatibility resolution records, public-safe registry metadata, SDK/WordPress surfaces, and explicit non-execution boundaries. Core selects compatible renderer contracts as metadata only; rendering, layout computation, and output generation remain external.

## v2.31.0 — System Maps
Status: implemented. Adds migration `0034`, explicit boundaries, domains, same-map memberships, saved views, structural validation, and deterministic compilation to v2.30 visualization specifications while keeping layout and causal inference external.



## v2.24.0 R1 — Secret-Scan Example Credential & Promotion Repair
Completed: promotion tooling repair only; runtime remains v2.24.0 and migration head remains `0027`.


## v2.32.0 — Flow Maps
Completed: typed flow channels, relation-bound directed flows, quantitative/uncertainty metadata, node-state observations, saved views, unit-safe balance summaries, structural validation, and external-renderer specification compilation. Core does not convert units, simulate systems, or assert conservation automatically.

## v2.33.0 — Scenario Landscapes
Completed: governed scenario memberships, baseline/reference roles, explicit comparison dimensions, uncertainty-aware externally supplied values, provenance, saved views, direct unit-matched baseline summaries, validation, and renderer-neutral specification compilation. Scenario execution, ranking, optimization, and unit conversion remain external.

## v2.34.0 — Interactive Model Canvas
Completed: model-bound canvas nodes, dependency edges, governed parameter/scenario controls, immutable interaction states, saved views, external-execution handoff contracts, structural validation, and renderer-neutral visualization-specification compilation. Model execution and layout remain external.

## v2.35.0 — Scenario Compute Engine
Completed: governed scenario-compute plans and cases, parameter-bound validation, deterministic input manifests, idempotent execution requests, external Lab/Workbench execution-attempt lineage, and canonical model-run/result bindings. Core orchestrates execution but performs no numerical computation, runner network dispatch, arbitrary-code execution, automatic optimization, or truth promotion. Adds migration `0038`.

## v2.36.0 — Uncertainty, Sensitivity & Ensemble Reasoning
Completed: governed uncertainty definitions, sensitivity-study factors and externally supplied measures, ensemble membership/provenance, externally supplied ensemble statistics, descriptive sensitivity ranking, public-safe metadata APIs, and explicit external-execution boundaries. Adds migration `0039`.


## v2.36.1.1 — Uncertainty Compute Runtime Integration · Production Schema Compatibility Repair

Adds deterministic Monte Carlo/LHS sampling, Sobol/Morris design and post-processing, ensemble normalization/statistics, empirical probability estimation, and governed Lab/Workbench handoff manifests while preserving the deployed v2.36.0 uncertainty schema unchanged. Migration 0040 is additive.

## v2.37.0 — Causal Systems Explorer
Completed. Production migration metadata/tag identity repaired in v2.37.0.2.

## v2.38.0 — Spatial & Temporal Visual Reasoning
Completed.

## v2.39.0 — Research Librarian Visual Explanation
Completed.

## v2.40.0 — Cross-Product Visual Research Objects
Planned.

## v2.41.0 — Reproducible Visual Knowledge Layer
Planned.

### Open Forensics foundation

Open Forensics is a cross-platform capability, not an isolated app. Platform Core owns universal forensic semantics, provenance, evidence relationships, and governance; Library, Research Librarian, Lab, Workbench, Site Intelligence, Decision Studio, and Catalyst Data provide source, analysis, computation, spatial, decision, and data capabilities. The system is general-purpose and must not encode a predetermined conclusion for any investigation.

## v2.42.0 — Forensic Object Model & Evidence Provenance
Planned.

## v2.43.0 — Evidence Integrity & Chain of Custody
Planned.

## v2.44.0 — Claims, Contradictions & Competing Hypotheses
Planned.

## v2.45.0 — Forensic Timeline & Event Reconstruction
Planned.

## v2.46.0 — Forensic Spatial/Temporal Evidence Integration
Planned.

## v2.47.0 — Media Artifact & Derivative Provenance
Planned.

## v2.48.0 — Quantitative Reconstruction & Reproduction Handoffs
Planned.

## v2.49.0 — Testimony, Statements & Documentary Evidence
Planned.

## v2.50.0 — Forensic Research Graph
Planned.

## v2.51.0 — Reproducible Investigation Packages
Planned.

Next planned: **v2.44.0 — Claims, Contradictions & Competing Hypotheses**.

- v2.38.0 Spatial & Temporal Visual Reasoning ✓
- v2.39.0 Research Librarian Visual Explanation ✓
