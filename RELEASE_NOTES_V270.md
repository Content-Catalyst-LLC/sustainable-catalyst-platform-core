# Platform Core v2.7.0 release notes

## Free Live Data Gateway and Connector Registry

Platform Core v2.7.0 adds the governed data-ingestion foundation for free weather, Earth observation, hazard, economics, and sustainability sources.

## Added

- Migration `0007`
- Free-source acceptance gate
- Source license and attribution registry
- Connector SDK and adapter registry
- Bounded upstream retrieval
- Identifying User-Agent support
- Raw-response SHA-256 hashes
- Bounded raw-response persistence
- Ingestion run records
- Stable observation IDs and deduplication
- Freshness and quality classifications
- Observation provenance endpoint
- Internal live-data routes under `/v1/live`
- Scoped public routes under `/api/v1/live`
- `data:read` public API scope
- Six seeded source records
- Six reference connectors
- Python internal-client methods
- Python and JavaScript public-client methods
- WordPress live-data status shortcode
- Deployment variables and sync script
- JSON schemas and regression tests

## Reference connectors

- MET Norway Locationforecast
- NASA GIBS WMTS
- USGS Earthquake GeoJSON feeds
- World Bank V2 Indicators
- FRED Series Observations
- UN SDG V5 goal and indicator-series catalogs

## Security and reliability

- Paid or credit-card-required sources cannot be active in strict mode.
- Unreviewed sources cannot be ingested in strict mode.
- Production connector URLs must use HTTPS.
- Adapter IDs must be registered server-side.
- Provider credentials are loaded from environment variables only.
- Public APIs exclude internal connector routing and configuration.
- Response and raw-storage byte limits are enforced independently.
- Raw responses are hashed before normalization.
- Public records retain license, attribution, methodology, freshness, and source lineage.

## Compatibility

All v2.0.0–v2.6.0 APIs and data models remain available. Existing product gateway behavior is unchanged.

## Validation

The complete backend regression suite passes with v2.7.0 connector, policy, ingestion, deduplication, provenance, and compatibility coverage.
