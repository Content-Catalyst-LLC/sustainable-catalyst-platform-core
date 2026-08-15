# Sustainable Catalyst Public API Python Client v2.11.0

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


## Streaming v2.11.0

The public client exposes a reliability stream URL helper for the Server-Sent Events endpoint. SSE consumers must send the normal scoped Bearer credential. Public streams contain only events explicitly marked public.

## Operational facilities v2.11.0

List public facilities by country/type/bbox, retrieve a public facility, and inspect dated facility observations. Operational, damage, access, service, capacity, and supply dimensions remain distinct.


## Humanitarian access and essential services v2.11.0

Query public humanitarian-condition records and country summaries while preserving service domain, evidence role, facility linkage, source, period, and provenance. Structural baselines are not presented as current operational conditions.
