# Geospatial, Time-Series, and Scientific Data Fabric — v2.8.0

## Purpose

Core v2.8.0 converts the normalized records introduced in v2.7.0–v2.7.3 into reusable geographic, temporal, catalog, asset, and map-layer structures. External products no longer need to reinterpret provider-specific geometry, time-series dimensions, or scientific access links.

## Materialization flow

```text
LiveDataObservation
├── TimeSeriesDefinition
├── TimeSeriesPoint
└── GeospatialFeature when geometry is present

ScientificDataRecord
├── ScientificDataAsset when an access URL is present
├── GeospatialFeature when geometry is present
├── StacCollection and StacItem when geometry is present
└── MapLayer for GeoJSON, WMS, WMTS, COG, or PMTiles assets
```

Materialization occurs automatically after successful ingestion when both of these settings are enabled:

```text
SC_CORE_DATA_FABRIC_ENABLED=true
SC_CORE_DATA_FABRIC_AUTO_MATERIALIZE=true
```

Existing records can be backfilled safely and repeatedly:

```bash
curl -X POST "$SC_CORE_URL/v1/fabric/materialize" \
  -H "X-SC-API-Key: $SC_CORE_WRITE_API_KEY"
```

Stable hashes and uniqueness constraints make the backfill idempotent.

## Spatial storage

SQLite and other non-PostgreSQL databases use portable GeoJSON plus numeric bounding-box columns. PostgreSQL deployments attempt to enable PostGIS and create a GIST expression index over the GeoJSON geometry. Failure to obtain extension privileges does not stop startup; portable GeoJSON remains available. The capability API probes the extension and reports the active mode instead of inferring PostGIS from the database dialect.

```text
SC_CORE_DATA_FABRIC_POSTGIS_AUTO_ENABLE=true
```

The release does not claim native raster processing. COG, PMTiles, NetCDF, Zarr, FITS, VOTable, GeoParquet, and GRIB2 are registered as remote source assets until a later object-storage or processing worker is configured.

## Time-series storage

Each stable connector, metric, and dimension combination creates one time-series definition. Points retain:

- Original observation and raw-record references
- UTC observation time
- Numeric or text value
- Quality and freshness status
- Dimensions
- A `YYYY-MM` partition key
- Stable point hash

PostgreSQL deployments attempt to create a BRIN index on `observed_at`. Native table partition creation is intentionally deferred; the monthly key allows an additive migration later without changing the public contract.

## STAC

Core exposes a STAC 1.0-compatible read catalog:

```text
GET /v1/stac
GET /v1/stac/collections
GET /v1/stac/collections/{collection_id}
GET /v1/stac/collections/{collection_id}/items
GET /v1/stac/collections/{collection_id}/items/{item_id}
GET /v1/stac/search
```

Scoped public equivalents are available under `/api/v1/stac` with `data:read`.

STAC records preserve the Sustainable Catalyst scientific-record ID, source, connector, geometry, time range, mission, instrument, discipline, license, and remote assets.

## GeoJSON and bounding boxes

```text
GET /v1/fabric/features
GET /v1/fabric/features.geojson
```

The `bbox` query uses `min_x,min_y,max_x,max_y`. It performs an indexed bounding-box intersection before returning exact source geometry.

## Map layers

The map-layer registry supports:

- GeoJSON
- Vector tiles
- Raster tiles
- WMS
- WMTS
- COG
- PMTiles
- STAC

Core registers endpoints and source metadata. Site Intelligence or another map client remains responsible for rendering, styling, tile requests, and user interaction.

## Scientific assets

The asset registry records remote access rather than silently copying provider files. Each asset can retain:

- Scientific record and dataset IDs
- Source and connector IDs
- Role and media type
- Normalized format
- Remote URL
- Storage mode
- Size and checksum when provided
- Variables and extents
- License and attribution

## Public API security

Public routes require a scoped developer credential with `data:read`. Raw provider payloads, credentials, private source configuration, and internal ingestion details remain outside the public fabric API.

## Product handoffs

- **Site Intelligence:** GeoJSON, map layers, STAC searches, time controls
- **Research Lab:** STAC items and scientific assets
- **Workbench:** time-series definitions and points
- **Decision Studio:** source-aware derived data references
- **Knowledge Library:** license, attribution, methods, and dataset records
- **Research Librarian:** cross-domain discovery and routing
