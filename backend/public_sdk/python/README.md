# Sustainable Catalyst Public API Python Client v2.44.0

```python
from sc_platform_core_public import PublicApiClient

client = PublicApiClient(
    "https://YOUR-PLATFORM-CORE.onrender.com",
    "scpk_your_key",
)

print(client.status())
print(client.trust_status())
print(client.workflow_definitions())
print(client.dossiers())
print(client.verify_dossier("sc:dossier:..."))
```

## Live data gateway v2.7.0

```python
sources = client.live_sources()
connectors = client.live_connectors(domain="hazards")
events = client.live_observations(connector_id="usgs.earthquakes")
series = client.live_timeseries("SP.POP.TOTL", source_id="world-bank")
lineage = client.live_provenance(events[0]["id"])
```

These methods require the `data:read` scope.


## International law and UN records v2.7.1

Use the international-law record, detail, and authority-taxonomy client methods to consume official-source records without exposing connector configuration or raw payloads.

## Scientific data v2.7.2

Use `scientific_records`, `scientific_record`, and `scientific_record_types` (camelCase in JavaScript) to discover normalized public scientific records through the scoped API.


## Economics and official statistics v2.7.3

```python
records = client.economic_records(indicator_code="GDP", geography_code="USA", limit=25)
record = client.economic_record(records[0]["id"])
types = client.economic_record_types()
```


## Data fabric v2.8.1

```python
capabilities = client.fabric_capabilities()
features = client.geospatial_features(bbox="-88,41,-87,42")
series = client.time_series(metric="temperature")
points = client.time_series_points(series[0]["id"])
assets = client.scientific_assets(format="fits")
layers = client.map_layers(layer_type="cog")
stac = client.stac_search(collections="mast:JWST")
```


## Streaming v2.13.0

The public client exposes a reliability stream URL helper for the Server-Sent Events endpoint. SSE consumers must send the normal scoped Bearer credential. Public streams contain only events explicitly marked public.

## Operational facilities v2.13.0

List public facilities by country/type/bbox, retrieve a public facility, and inspect dated facility observations. Operational, damage, access, service, capacity, and supply dimensions remain distinct.


## Humanitarian access and essential services v2.13.0

Query public humanitarian-condition records and country summaries while preserving service domain, evidence role, facility linkage, source, period, and provenance. Structural baselines are not presented as current operational conditions.

## Country evidence federation v2.13.0

Use `country_evidence_federation(country_code)` for the country evidence lanes and `country_evidence_reconcile(country_code, concept)` for non-blending source selection with explicit comparability and fallback rationale.


## Earth, Ocean, Space scientific fabric v2.13.0
Discover routed scientific domains and retrieve domain-specific records, assets, time series, and map layers. Domain routing is navigation metadata only and has no factual Truth precedence.


## Cross-product evidence exchange v2.14.0

The public SDK exposes exchange readiness/capability metadata only. Exchange package contents remain an authenticated internal Core surface.


## Distributed scale v2.15.0
Use the public scale readiness endpoint to inspect non-sensitive capacity and backpressure state. Job payloads remain operator-only.


## Governance v2.16.0
Use `governance_readiness` / `governanceReadiness()` to inspect the public-safe governance control-plane status. Policy, decision, and audit data are intentionally not exposed through the public API.

## Production certification v2.17.0
Public-safe certification readiness reports migration head, zero-pending state, and recovery-checkpoint capability without exposing certification records.


## Observability v2.18.0
Public-safe aggregate production status is available through the observability status helper. Request IDs, raw request telemetry, SLO definitions, and operator deployment metadata are not exposed by this helper.


## Federated Core v2.23.0
Use `federation_status()` / `federationStatus()` for aggregate public-safe trusted-node exchange readiness. Node identities, trust details, manifests, signatures, and remote-reference contents are not exposed through this helper.

## v2.24.0
Adds `capacity_status()` for aggregate Capacity Forecasting & Resource Governance status.

## v2.25.0

Adds `credential_lifecycle_status()` for public-safe aggregate credential/key lifecycle health. Secret references, key identifiers, fingerprints, and secret/private-key material are not returned by the public status contract.


## v2.27.0 — Scientific object metadata

Use `scientific_object_storage_readiness()`, `scientific_stored_objects(...)`, `scientific_stored_object(id)`, and `scientific_processing_adapters()` for public-safe storage and adapter metadata. Raw object bytes and execution remain internal.


## v2.28.0 — Research objects

The client exposes `research_object_readiness()`, `research_objects()`, `research_object()`, and `research_project_bundle()` for public, graph-native research metadata. Model execution remains outside Core.


## v2.29.0 — Visual reasoning

The public client exposes renderer-neutral visual reasoning readiness, public visual-object listing/detail, and semantic bundles. Core returns semantic elements, relations, layers, annotations, and snapshot metadata; it does not return a renderer choice or execute layout.


## v2.30.0 — Visualization specification & renderer registry

Use `visualization_readiness()`, `visualization_renderers()`, and `visualization_specifications()` to inspect public-safe renderer contracts and governed visualization specifications. Core resolves compatibility metadata only; it does not execute renderers or layouts.


## v2.31.0 — System Maps
Adds `system_maps_readiness`, `system_maps`, `system_map`, and `system_map_bundle` public metadata helpers.


## v2.33.0 — Flow Maps
Adds public Flow Maps readiness, listing, detail, bundle, and unit-safe balance-summary helpers. Core does not convert units or execute simulations.


## v2.33.0 — Scenario Landscapes

Adds `scenario_landscapes_readiness`, `scenario_landscapes`, `scenario_landscape`, `scenario_landscape_bundle`, and `scenario_landscape_comparison` public metadata helpers. Scenario execution, ranking, optimization, and unit conversion remain outside Core.


## v2.35.0 — Scenario Compute Engine
Adds public readiness/list/detail/bundle helpers for governed interactive model canvases. Model execution remains external to Core.


## v2.36.0 — Uncertainty, Sensitivity & Ensemble Reasoning
Adds public metadata helpers for governed uncertainty definitions, sensitivity-study summaries, and ensemble summaries. Sampling, model execution, sensitivity algorithms, and ensemble aggregation remain external to Platform Core.


## v2.38.0 — Uncertainty Compute Runtime Integration repair
Adds public compute readiness helpers while preserving v2.36.0 uncertainty APIs.

## v2.38.0 — Causal Systems Explorer
Public readiness, graph discovery, and public causal-system bundle helpers.

## v2.38.0 — Causal Migration Metadata Repair

Runtime/API surface unchanged from v2.37.0; release metadata and promotion/deployment integrity repaired.


## v2.44.0 — Research Librarian Visual Explanation
Adds public readiness, explanation listing, and public visual-explanation bundle helpers.

## v2.44.0 — Open Forensics
Adds public readiness, investigation listing, and investigation-bundle helpers for the Forensic Object Model & Evidence Provenance layer.


## v2.44.0 — Claims, Contradictions & Competing Hypotheses
Adds public read helpers for forensic claim maps, competing-hypothesis matrices, and reasoning bundles. Matrices are descriptive only; Core does not rank hypotheses or assign probabilities.
