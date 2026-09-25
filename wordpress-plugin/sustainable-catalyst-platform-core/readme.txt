== 3.3.0 ==
* Adds Statistical Reasoning Object Model status and Analytics R 2.2 diagnostics visibility.

== 3.2.0 ==
Analytical Result & Provenance Integration status surface with first-class result lineage, estimates, uncertainty objects, and immutable snapshots.

== 3.0.0 ==
Unified Research, Scientific Computing & Investigation Runtime status surface and Core 3.0.0 compatibility.

== 2.96.0 ==
Unified Research Runtime Contract status surface and Core 2.96.0 compatibility.

== 2.95.0 ==
Scholarly Interoperability & Research Packaging status surface and Core 2.95.0 compatibility.

== 2.92.0 ==
Research Project State, Versioning & Reproducibility status surface and Core 2.92.0 compatibility.

== 2.89.0 ==
Research Quality, Bias & Methodological Audit Engine status surface and Core 2.89.0 compatibility.

== 2.88.0 ==
Unified Findings, Claims & Inference Engine status surface and Core 2.88.0 compatibility.

== 2.85.0 ==
Research Portfolio & Institutional Knowledge Governance status surface and Core 2.85.0 compatibility.

== 2.55.0 ==
Predictive Model Object Model & Forecast Provenance status surface and Core 2.55.0 compatibility.

== 2.51.0 ==
Reproducible Investigation Packages status surface and Core 2.51.0 compatibility.

== 2.47.0 ==
Media Artifact & Derivative Provenance status surface and Core 2.47.0 compatibility.

== 2.46.0 ==
Forensic Spatial/Temporal Evidence Integration status surface and Core 2.46.0 compatibility.

=== Sustainable Catalyst Platform Core ===
Contributors: content-catalyst
Tags: knowledge graph, entity registry, provenance, live data, sustainable catalyst
Requires at least: 6.4
Tested up to: 6.8
Requires PHP: 8.0
Stable tag: 3.41.0
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




== 2.29.0 ==
* Adds Visual Reasoning Object Model status via `[sc_platform_core_visual_reasoning_status]`.
* Reports governed visual objects, semantic elements/relations, layers, annotations, and reproducible semantic snapshots.
* Core remains renderer-neutral; visualization specification, renderer selection, and layout execution are deferred to v2.30.0.

== 2.28.0 ==
* Adds Research Object & Model Foundation status and `[sc_platform_core_research_object_status]`.
* Tracks graph-native projects, models, model versions, variables, parameters, scenarios, model runs, and results.
* Core does not execute models; Lab, Workbench, and explicit external executors remain the compute boundary.

== 2.27.0 ==
* Adds Scientific Object Storage & Processing Adapter Fabric status via `[sc_platform_core_scientific_object_storage_status]`.
* Reports stored objects, processing adapters, and local-store readiness without exposing object bytes publicly.

== 2.26.0 ==
* Adds distributed quotas, admission control, and workload-governance status.
* Reports workload classes, quota policies, and active leases while keeping automatic scaling outside Core.

== 2.25.0 ==
* Adds secret-free credential registry and cryptographic-key lifecycle status.
* Tracks versions, expiry, overlap-aware rotation, revocation, compromise state, and credential-use audit metadata.
* Secret/private-key values remain outside WordPress and Core persistence.

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


== 2.30.0 ==
* Adds Visualization Specification & Renderer Registry status via `[sc_platform_core_visualization_registry_status]`.
* Reports immutable visualization specifications, renderer contracts, compatibility rules, and resolution records.
* Core performs compatibility resolution only; renderer execution, layout execution, and render-output generation remain external.
* Retains the v2.29.0.1 backend-URL diagnostics for visual reasoning status.


== 2.31.0 ==
* Adds governed System Maps status via `[sc_platform_core_system_maps_status]`.
* Adds explicit boundaries, domains, memberships, saved views, structural validation, and specification compilation.
* Core does not perform layout or causal inference.


== 2.32.0 ==
* Adds governed Flow Maps status via `[sc_platform_core_flow_maps_status]`.
* Adds typed channels, relation-bound directed flows, quantitative/uncertainty metadata, node states, saved views, unit-safe balance summaries, validation, and visualization specification compilation.
* Core does not convert units, simulate systems, infer conservation, or promote flow-map structure to truth.


== 2.33.0 ==
* Adds governed Scenario Landscapes status via `[sc_platform_core_scenario_landscapes_status]`.
* Binds existing research scenarios into baseline/alternative/reference/stress/sensitivity comparison roles.
* Adds explicit dimensions, externally supplied values, uncertainty bounds, provenance, saved views, direct baseline-relative numeric summaries, and visualization-specification compilation.
* Core does not execute scenarios, rank alternatives, optimize decisions, convert units, or promote scenario outputs to truth.


== 2.34.0 ==
Adds Interactive Model Canvas status for governed model-bound nodes, controls, immutable interaction states, and external execution handoffs.


== 2.35.0 ==
* Adds governed Scenario Compute Engine status via `[sc_platform_core_scenario_compute_status]`.
* Adds reproducible compute plans, scenario cases, parameter-bound validation, deterministic input manifests, idempotent execution requests, attempt tracking, and research run/result bindings.
* Core orchestrates compute but does not dispatch network execution, execute arbitrary code, or perform numerical model execution.


== 2.36.0 ==
* Adds governed uncertainty definitions, sensitivity studies, and ensemble reasoning status via `[sc_platform_core_uncertainty_reasoning_status]`.
* Core stores externally supplied sensitivity measures and ensemble statistics; sampling, sensitivity algorithms, ensemble aggregation, and numerical execution remain external.

== 2.36.1.1 ==
Production schema compatibility repair for Uncertainty Compute Runtime Integration. Preserves v2.36.0 uncertainty tables and adds compute readiness/status.

== 2.37.0.2 ==
* Adds Causal Systems Explorer status integration and runtime readiness.

== 2.38.0 ==
* Adds Spatial & Temporal Visual Reasoning and shortcode [sc_platform_core_spatial_temporal_status].


== 2.39.0 ==
* Adds Research Librarian Visual Explanation and shortcode [sc_platform_core_research_visual_explanation_status].
* Adds governed citation-aware explanation graphs, evidence bindings, views, snapshots, and renderer-neutral visual explanation contracts.
* Source retrieval, prose generation, citation selection, source ranking, layout, rendering, and truth promotion remain outside Core.

== 2.40.0 ==
* Adds Cross-Product Visual Research Objects and shortcode `[sc_platform_core_cross_product_visual_research_status]`.
* Preserves source-product identity, explicit references, semantic relations, portable packages, saved views, and immutable snapshots.
* Remote fetching, specialist execution, truth merging, layout, rendering, and automatic truth promotion remain outside Core.


== 2.41.0 ==
* Adds Reproducible Visual Knowledge Layer status via `[sc_platform_core_reproducible_visual_knowledge_status]`.
* Adds versioned/hashed input manifests, runtime environment capture, external-only replay plans, integrity fingerprints, verification evidence, immutable snapshots, and portable reproducibility packages.
* Core documents and verifies reproducibility state but does not execute specialist runtimes, arbitrary code, or claim output equivalence without external evidence.

== 2.45.0 ==
Adds Open Forensics: governed forensic investigations, typed objects, evidence provenance/source bindings, hashes, semantic relations, and immutable snapshots.


== 2.45.0 ==
Adds Open Forensics claims, contradictions, competing hypotheses, evidence-position assessments, descriptive comparison matrices, and immutable reasoning snapshots.

== 2.76.0 ==
Research Notebook & Analytical Narrative status surface and Core 2.76.0 compatibility.


== 2.77.0 ==
Finding, Claim & Evidence Intelligence status surface and Core 2.77.0 compatibility. Adds [sc_platform_core_research_intelligence_status].


== 2.78.0 ==
Hypothesis & Competing Explanation Engine status surface and Core 2.78.0 compatibility. Adds [sc_platform_core_hypothesis_engine_status].

== 2.79.0 ==
Research Argument & Evidentiary Synthesis Engine status surface and Core 2.79.0 compatibility. Adds governed argument graphs, researcher-authored synthesis registries, counterarguments, unresolved tensions, descriptive coverage, revisions, and immutable snapshots without Core-side generation, evidence scoring, ranking, or truth inference.

== 2.80.0 ==
Research Decision Trace & Conclusion Governance status surface and Core 2.80.0 compatibility. Adds researcher-authored conclusions, evidence bindings, caveats, dissent, decision traces, reviews, revisions, descriptive governance summaries, and immutable snapshots without Core-side conclusion selection, scoring, ranking, certification, truth inference, or publication.


== 2.81.0 ==
Reproducible Research Publication & Scholarly Output Engine status surface and Core 2.81.0 compatibility. Adds structured publications, manuscript sections, bibliographic references and claim-linked citations, figures/tables, supplementary materials, external identifier records, structural readiness diagnostics, research-to-publication lineage, export manifests, revisions, and immutable snapshots without Core-side manuscript/conclusion generation, citation fabrication, quality judgment, DOI issuance, or external publication. Adds [sc_platform_core_research_publication_status].


== 2.82.0 ==
Peer Review, Replication & Rebuttal Intelligence status surface and Core 2.82.0 compatibility. Adds governed peer reviews, comments and responses, replication studies/attempts/comparisons, rebuttals and evidence-linked rebuttal points, revisions, descriptive summaries, declared lineage, and immutable snapshots without Core-side review generation, quality scoring, replication-success inference, rebuttal resolution, publication decisions, or truth inference. Adds [sc_platform_core_peer_review_status].


== 2.83.0 ==
Cross-Study Evidence Synthesis & Meta-Research status surface and Core 2.83.0 compatibility. Adds governed synthesis protocols, declared study inclusion, outcome harmonization, source-reported/external effect records, external meta-analysis result provenance, meta-research assessments, cross-study relations, evidence gaps, revisions, lineage, and immutable snapshots. Core does not search literature, decide inclusion, compute/pool effects, score studies, infer bias/causality/truth, rank evidence, or generate synthesis conclusions. Adds [sc_platform_core_evidence_synthesis_status].


== 2.84.0 ==
Research Program & Longitudinal Knowledge Graph status surface and Core 2.84.0 compatibility. Adds governed research programs, cross-project memberships, objectives, milestones, declared longitudinal graph nodes/edges, time-indexed knowledge states, research-evolution events, revisions, lineage, and immutable snapshots. Core does not prioritize research, allocate funding, rank projects, auto-link graphs, forecast program success, infer causality, resolve evidence gaps, or infer truth. Adds [sc_platform_core_research_program_status].


== 2.86.0 ==
Scientific Study & Investigation Protocol Model status surface and Core 2.86.0 compatibility. Adds universal governed protocols for experimental, observational, engineering, forensic, literature-review, systematic-review, mixed-method, simulation, and case-study research with objectives, scope units, measures, source/data plans, acquisition, methods, assumptions, validation, planned outputs, deviations, revisions, lineage, and immutable snapshots. Adds [sc_platform_core_research_protocol_status].

== 2.87.0 ==
Computation, Analysis & Execution Lineage status surface and Core 2.87.0 compatibility.
