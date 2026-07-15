# Sustainable Catalyst Platform Core v2.8.0

## Geospatial, Time-Series, and Scientific Data Fabric

Core v2.8.0 adds a shared data fabric over the free live-data, UN/legal, scientific, and economics connector packs.

### Added

- Migration `0011`
- `geospatial_features`
- `time_series_definitions`
- `time_series_points`
- `scientific_data_assets`
- `map_layers`
- `stac_collections`
- `stac_items`
- Automatic observation and scientific-record materialization
- Idempotent full backfill
- GeoJSON FeatureCollection output and bounding-box filters
- STAC 1.0 catalog, collection, item, and search APIs
- Scientific format capability registry
- Map-layer registry
- PostgreSQL PostGIS activation and expression-index setup when available, with an explicit portable GeoJSON fallback
- PostgreSQL BRIN time index and portable monthly partition keys
- Public `data:read` routes
- Python and JavaScript SDK methods
- WordPress data-fabric status shortcode
- JSON Schemas and deployment settings

### Storage boundary

The release registers remote scientific assets and map endpoints. It does not download or redistribute large provider files by default, and it does not claim native parsing or raster processing for FITS, NetCDF, Zarr, GeoParquet, COG, PMTiles, VOTable, or GRIB2.

### Compatibility

Migrations are additive. Existing Core v2.0.0–v2.7.3 tables, records, routes, credentials, workflows, dossiers, Trust Center records, sources, connectors, and normalized records remain intact.


### Validation

- 99 tests passed across three stable regression groups
- Migrations `0001` through `0011` passed on a fresh database
- 40 governed free sources and 39 connector definitions preserved
- Python, PHP, JavaScript, Bash, JSON Schema, Postman, secret-scan, manifest, and archive checks passed

### PostGIS reporting

Core does not infer that PostGIS is active merely because the database uses PostgreSQL. Capability and statistics responses probe the extension and report one of `native_postgis`, `portable_geojson_postgresql`, or `portable_geojson`.
