# Sustainable Catalyst Public API Python Client v2.20.0

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


## Distributed scale v2.20.0
Use the public scale readiness endpoint to inspect non-sensitive capacity and backpressure state. Job payloads remain operator-only.


## Governance v2.20.0
Use `governance_readiness` / `governanceReadiness()` to inspect the public-safe governance control-plane status. Policy, decision, and audit data are intentionally not exposed through the public API.

## Production certification v2.20.0
Public-safe certification readiness reports migration head, zero-pending state, and recovery-checkpoint capability without exposing certification records.


## Observability v2.20.0
Public-safe aggregate production status is available through the observability status helper. Request IDs, raw request telemetry, SLO definitions, and operator deployment metadata are not exposed by this helper.
