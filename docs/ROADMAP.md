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
