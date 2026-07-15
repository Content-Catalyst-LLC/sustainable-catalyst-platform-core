# Sustainable Catalyst Public API Python Client v2.7.3

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
