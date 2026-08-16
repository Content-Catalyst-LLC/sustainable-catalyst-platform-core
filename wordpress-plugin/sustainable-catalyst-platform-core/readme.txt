=== Sustainable Catalyst Platform Core ===
Contributors: content-catalyst
Tags: knowledge graph, entity registry, provenance, live data, sustainable catalyst
Requires at least: 6.4
Tested up to: 6.8
Requires PHP: 8.0
Stable tag: 2.24.0
License: MIT

WordPress status, live-data gateway, and entity lookup client for Sustainable Catalyst Platform Core.

== Installation ==

1. Upload and activate the plugin.
2. Go to Settings → Platform Core.
3. Enter the Platform Core backend URL.
4. Use [sc_platform_core_status].
5. Use [sc_platform_core_integration_readiness] for public-safe service readiness.
6. Use [sc_platform_core_live_data_status].
7. Use [sc_platform_core_international_law_status].
8. Use [sc_platform_core_science_status].
9. Use [sc_platform_core_economics_status].
10. Use [sc_platform_core_data_fabric_status].
11. Use [sc_platform_core_reliability_status].
12. Use [sc_platform_core_observability_status].
13. Use [sc_platform_core_entity id="sc:product:workbench"].

The plugin never exposes the Platform Core write key in frontend code.


== 2.20.0 ==
* Adds continuity, backup verification, DR objectives, restore-rehearsal evidence, and [sc_platform_core_continuity_status].

== 2.19.0 ==
* Adds governed incident response, change approval, and operator-confirmed rollback coordination.
* Adds [sc_platform_core_operations_status].
* Automatic rollback and causal attribution are disabled.

== 2.18.0 ==
* Adds local-first Core observability, SLO evaluation, deployment markers, and aggregate public production status.
* Adds [sc_platform_core_observability_status].
* No paid monitoring provider is required.

== 2.11.0 ==
Operational Evidence & Facility Registry: facility readiness/status surface plus inherited streaming, data-fabric, connector, gateway, evidence, graph, and trust infrastructure.

Streaming, Alerts, and Source Reliability.

* Adds persistent connector work queue, worker leases, retries, and dead-letter records.
* Adds Server-Sent Events and standard Last-Event-ID resume support.
* Adds threshold/existence alerts and geographic subscriptions.
* Adds stale-source detection and historical replay.
* Adds explicit provider failover; automatic failover requires declared parameter compatibility.
* Adds [sc_platform_core_reliability_status].
* External provider health remains non-blocking for Core release readiness.

== 2.8.0 ==
* Adds the geospatial, time-series, scientific-asset, map-layer, and STAC status shortcode.
* Displays feature, series, point, asset, map-layer, and STAC totals.
* Supports GeoJSON, STAC, WMS/WMTS handoffs, COG, PMTiles, FITS, NetCDF, Zarr, GeoParquet, SDMX, and TAP/ADQL capability reporting.

== 2.7.3 ==
* Adds economics and official-statistics connectors, normalized economic records, SDMX ingestion, SEC facts, EIA, BEA, BLS, Census, FAOSTAT, and public economics APIs.

== 2.7.2 ==

* Adds the Scientific Data Connector Pack status shortcode.
* Displays configured science connectors and normalized scientific-record totals.
* Supports Earth science, climate, hydrology, biomedical, chemistry, biodiversity, materials, and astronomy discovery.
* Preserves provider identifiers, access links, license, attribution, content hashes, and raw-ingestion provenance.

== 2.7.1 ==

* Adds the International Law and United Nations status shortcode.
* Displays strict free-source policy status, registered sources, configured connectors, observations, and legal-record totals.
* Supports official UN document discovery, SDG metadata, humanitarian, demographic, trade, displacement, and human-rights connectors.
* Preserves legal-authority class, source, license, attribution, freshness, raw-response hash, and provenance status.
* Does not infer the binding effect of a Security Council resolution from its document symbol alone.

== 2.1.0 ==

* Adds reviewed relationship neighborhood shortcode.
* Adds Knowledge Explorer launch shortcode.
* Supports Platform Core v2.1.0 graph APIs and JSON-LD records.


== 2.2.0 ==

* Adds Evidence Ledger integrity and statistics shortcode.
* Adds claim evidence manifest shortcode.
* Adds Evidence Explorer launch shortcode.
* Supports claims, source snapshots, provenance activities, calculation traces, reviews, and ledger verification.


== 2.3.0 ==

* Adds Developer Portal launch shortcode.
* Adds public API plan cards.
* Supports the Unified Public API, scoped credentials, usage controls, SDK assets, and signed webhooks.

== 2.4.0 ==

* Adds Trust Center launch and public trust-status shortcodes.
* Supports evaluation definitions, runs, check results, findings, incidents, limitations, attestations, and machine-readable trust status.

== 2.6.0 ==

* Adds Signature Dossier Center launch shortcode.
* Adds public signature dossier verification cards.
* Adds end-to-end workflow status cards.
* Supports Platform Core v2.6.0 workflow and dossier APIs.

== 2.21.0 ==

* Adds multi-region resilience, replication-aware failover assessment, read-only degraded mode, and [sc_platform_core_resilience_status].

== 2.22.0 ==

* Adds governed data lifecycle, preservation archives, integrity verification, policy/legal holds, non-destructive tombstone lineage, and [sc_platform_core_lifecycle_status].


== 2.24.0 ==

* Adds Capacity Forecasting & Resource Governance status surfaces.
* Exposes aggregate profile/forecast risk without private capacity values.
* Keeps forecasts and soft-limit decisions advisory; Core does not purchase infrastructure, scale deployments, or enforce hard admission control.

== 2.23.1 ==

* Aligns plugin/runtime release metadata with Core v2.23.1 and the repaired capability truth contract.
* No shortcode, route, database, federation, or evidence-semantics change.

== 2.23.0 ==

* Adds Federated Core trusted-node registration, authenticated reference-first exchange manifests, conflict-safe remote references, and [sc_platform_core_federation_status].
* Trust secrets remain runtime-only; automatic truth promotion, ownership transfer, and cross-node delivery are disabled.
