# Free Live Data Gateway v2.7.0

Sustainable Catalyst Platform Core v2.7.0 adds a governed ingestion and normalization layer for external public data. It is designed to let Site Intelligence, Research Lab, Workbench, Decision Studio, Knowledge Library, Research Librarian, and WordPress consume shared records without embedding provider-specific code in each product.

## Permanent operating rule

The default production policy is strict:

- The source must be free to access.
- No credit card may be required.
- Automated access must be permitted.
- License and attribution requirements must be recorded.
- Source records that have not passed review cannot be ingested while strict mode is enabled.
- Paid, trial-only, or restricted sources can be documented, but they cannot be activated.

Configure this through:

```dotenv
SC_CORE_LIVE_DATA_ENABLED=true
SC_CORE_LIVE_DATA_INGEST_ENABLED=true
SC_CORE_LIVE_DATA_STRICT_FREE_SOURCES=true
```

## Architecture

```text
Official public provider
        ↓
Connector adapter
        ↓
Free-source acceptance gate
        ↓
Bounded HTTP retrieval
        ↓
Raw response hash and bounded cache record
        ↓
Provider-specific normalization
        ↓
sc-live-observation/1.0-compatible database record
        ↓
Internal and scoped public APIs
        ↓
Sustainable Catalyst products
```

## Migration 0007

Migration `0007` creates:

- `live_data_sources`
- `live_data_connectors`
- `live_data_ingestion_runs`
- `live_data_raw_records`
- `live_data_observations`

The migration also seeds six reviewed sources and six reference connectors.

## Seeded sources

| Source ID | Organization | Access gate |
|---|---|---|
| `met-norway` | Norwegian Meteorological Institute | Approved with attribution |
| `nasa-earthdata` | NASA | Approved with attribution and dataset-specific terms |
| `usgs` | U.S. Geological Survey | Approved with attribution |
| `world-bank` | World Bank Group | Approved with attribution and dataset-specific terms |
| `fred` | Federal Reserve Bank of St. Louis | Metadata approved; individual series terms retained |
| `un-statistics` | United Nations Statistics Division | Metadata approved; dataset and agency terms retained |

## Seeded connectors

### `met-no.locationforecast`

Global coordinate-based forecast ingestion.

Required parameters:

```json
{"lat": 41.8781, "lon": -87.6298}
```

Normalized metrics include:

- `air_temperature`
- `relative_humidity`
- `wind_speed`
- `wind_from_direction`
- `air_pressure_at_sea_level`
- `cloud_area_fraction`
- `dew_point_temperature`

The adapter always sends the configured identifying User-Agent.

### `nasa.gibs-wmts`

Retrieves and parses the NASA GIBS EPSG:4326 WMTS capabilities document. Each map layer becomes a catalog observation with formats, tile matrix sets, time defaults, and resource templates.

No parameters are required.

### `usgs.earthquakes`

Retrieves an official USGS GeoJSON summary feed.

Example:

```json
{"feed": "all_hour"}
```

Allowed feeds in the seeded connector:

- `all_hour`
- `all_day`
- `2.5_day`
- `4.5_week`
- `significant_month`

Each event preserves magnitude, magnitude type, point geometry, depth, event status, tsunami flag, place, detail URL, and provider timestamps.

### `world-bank.indicators`

Retrieves World Bank V2 indicator observations.

Required parameter:

```json
{"indicator": "SP.POP.TOTL"}
```

Optional parameters:

```json
{
  "country": "USA",
  "date": "2015:2025",
  "source": "2",
  "per_page": 1000
}
```

### `fred.series-observations`

Retrieves FRED series observations using a free registered key.

Configure:

```dotenv
SC_CORE_FRED_API_KEY=<free-fred-api-key>
```

Required parameter:

```json
{"series_id": "GDP"}
```

FRED records are internal by default because reuse conditions can vary by underlying series provider. Public exposure should be enabled only after the relevant series terms have been reviewed.

### `un.sdg-catalog`

Retrieves the official UN SDG V5 goal catalog or the series list for an indicator.

Goals:

```json
{"resource": "goals"}
```

Indicator series:

```json
{
  "resource": "series",
  "indicator_code": "1.1.1"
}
```

## Internal API

### Registry and status

```text
GET   /v1/live/sources
GET   /v1/live/sources/{source_id}
POST  /v1/live/sources
PATCH /v1/live/sources/{source_id}

GET   /v1/live/connectors
GET   /v1/live/connectors/health
GET   /v1/live/connectors/{connector_id}
POST  /v1/live/connectors
PATCH /v1/live/connectors/{connector_id}

GET   /v1/live/stats
```

### Ingestion and records

```text
POST /v1/live/connectors/{connector_id}/ingest
GET  /v1/live/runs
GET  /v1/live/runs/{run_id}
GET  /v1/live/observations/latest
GET  /v1/live/timeseries
GET  /v1/live/observations/{observation_id}
GET  /v1/live/provenance/{observation_id}
```

Write routes require `X-SC-API-Key`.

## Public API

The governed public surface requires the new `data:read` scope:

```text
GET /api/v1/live/sources
GET /api/v1/live/connectors
GET /api/v1/live/observations/latest
GET /api/v1/live/timeseries
GET /api/v1/live/provenance/{observation_id}
```

Public responses exclude:

- Connector base URLs
- Adapter identifiers
- Connector configuration
- Raw payload contents
- Credential information
- Non-public observations
- Internal run parameters

## Ingestion example

```bash
curl -X POST \
  "$SC_CORE_URL/v1/live/connectors/usgs.earthquakes/ingest" \
  -H "Content-Type: application/json" \
  -H "X-SC-API-Key: $SC_CORE_WRITE_API_KEY" \
  -d '{
    "parameters": {"feed": "all_hour"},
    "requested_by": "site-intelligence",
    "run_type": "scheduled"
  }'
```

## Observation model

Every normalized record includes:

```json
{
  "id": "sha256-derived-stable-id",
  "connector_id": "usgs.earthquakes",
  "source_id": "usgs",
  "source_record_id": "provider-record-id",
  "domain": "hazards",
  "metric": "earthquake_magnitude",
  "value_number": 3.2,
  "value_text": null,
  "unit": "ml",
  "geometry": {
    "type": "Point",
    "coordinates": [-122.1, 37.4]
  },
  "dimensions": {
    "depth_km": 8.5,
    "place": "Example region"
  },
  "observed_at": "2026-07-14T18:35:00Z",
  "published_at": "2026-07-14T18:38:00Z",
  "retrieved_at": "2026-07-14T18:40:00Z",
  "freshness_status": "near_real_time",
  "quality_status": "source_reported",
  "license_name": "provider terms",
  "attribution": "U.S. Geological Survey",
  "methodology_url": "official-documentation-url",
  "raw_record_hash": "sha256",
  "public": true
}
```

## Raw-response controls

Two independent limits apply:

- `SC_CORE_LIVE_DATA_MAX_RESPONSE_BYTES` limits the upstream response accepted by the connector.
- `SC_CORE_LIVE_DATA_RAW_PAYLOAD_MAX_BYTES` limits the raw body retained inline in PostgreSQL.

When the second limit is exceeded, Core stores:

- The complete content hash
- Original byte size
- Media type
- Retrieval time
- A small preview
- A `truncated` flag

The normalized observations are still retained if the full response passed the connector response limit.

## Deduplication and revisions

Observation IDs are derived from:

```text
connector ID
+ provider source record ID
+ metric
+ observed timestamp
```

Repeated retrieval updates the normalized observation and links it to the newest raw-response record. Each ingestion run and raw-response hash remains available for audit history.

## Scheduling

v2.7.0 deliberately does not add a distributed worker or message broker. Use the included command-line script with cron, Render cron jobs, GitHub Actions, or another scheduler:

```bash
python backend/scripts/sync_live_data.py \
  --connector usgs.earthquakes \
  --parameters '{"feed":"all_hour"}' \
  --requested-by scheduled-usgs-sync
```

Distributed workers, event streaming, replay queues, and geographic subscriptions remain planned for Core v2.9.0.

## Product responsibilities

- **Site Intelligence:** public maps, conditions, events, economics, and sustainability dashboards.
- **Research Lab:** scientific files, raster analysis, telescope data, and reproducible investigations.
- **Workbench:** statistics, transformations, models, forecasts, and validation.
- **Decision Studio:** source-aware briefs, alerts, scenarios, and decision packets.
- **Knowledge Library:** source, license, methodology, and citation records.
- **Research Librarian:** dataset discovery and routing.
- **Platform Core:** source policy, connectors, ingestion, normalization, provenance, and API delivery.

## Deferred from v2.7.0

- PostGIS and raster indexing
- STAC catalog persistence
- NetCDF, Zarr, FITS, and GeoTIFF object storage
- Distributed connector workers
- Server-Sent Events and WebSockets
- Alert rules and geographic subscriptions
- Automatic provider failover
- International law and expanded UN connector pack
- Broad science connector pack
- Broad economics and official-statistics connector pack
