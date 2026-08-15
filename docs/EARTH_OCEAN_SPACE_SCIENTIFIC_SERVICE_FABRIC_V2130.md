# Earth, Ocean, Space & Scientific Service Fabric — v2.13.0

Core v2.13.0 adds a scientific routing plane over the existing v2.7.2 scientific connector pack and v2.8.0 geospatial/time-series/STAC/scientific-asset fabric. It does not create new scientific observations and does not alter source provenance.

## Domain front doors

- **Earth** — terrestrial, atmospheric, climate, hydrologic, cryosphere, ecosystem, geophysical, hazard and Earth-observation records.
- **Ocean** — oceanographic surface, water-column, seafloor, coastal, marine-ecosystem, pollution and marine-hazard records.
- **Space** — Earth-orbit, lunar, planetary, solar-system, astronomy, astrophysics, exoplanet and technosignature records.

Ocean is intentionally exposed as its own first-class domain rather than being hidden under a generic Earth-science route.

## Truth boundary

Scientific domain bindings are **routing metadata only**. A binding records why a source record is discoverable through Earth, Ocean or Space. It never changes the underlying observation, publisher, license, source, quality status, or provenance and carries `truth_precedence = none`.

A zero-record domain means **no routed records are currently present**, not that no science or observations exist.

## Routes

```text
GET  /v1/scientific-fabric/readiness
POST /v1/scientific-fabric/materialize
GET  /v1/scientific-fabric/domains
GET  /v1/scientific-fabric/domains/{earth|ocean|space}
GET  /v1/scientific-fabric/domains/{domain}/records
GET  /v1/scientific-fabric/domains/{domain}/assets
GET  /v1/scientific-fabric/domains/{domain}/timeseries
GET  /v1/scientific-fabric/domains/{domain}/map-layers
```

Scoped public equivalents are available under `/api/v1/scientific-fabric/...`.

## Materialization

Existing scientific records, time-series definitions and map layers can be backfilled through `/v1/scientific-fabric/materialize`. Newly ingested scientific records refresh their domain bindings automatically when the service fabric is enabled.
