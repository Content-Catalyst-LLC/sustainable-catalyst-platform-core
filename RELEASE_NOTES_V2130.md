# Platform Core v2.13.0 — Earth, Ocean, Space & Scientific Service Fabric

v2.13.0 adds first-class Earth, Ocean and Space discovery/service routes on top of Core's existing scientific connector and data-fabric layers.

## Highlights

- Persisted routing bindings for scientific records, time series and map layers.
- Explicit Earth, Ocean and Space domains with domain-specific subdomains.
- Ocean is independently discoverable rather than hidden under generic Earth-science navigation.
- Domain summaries include routed record, time-series, map-layer, mission and source counts.
- Scientific assets inherit domain access from their source scientific records.
- New scientific ingestion refreshes routing bindings automatically.
- Routing classification carries basis/evidence/confidence but has `truth_precedence = none`.
- Domain routing never rewrites the underlying source observation, provenance, license or quality status.
- Zero routed records means no indexed records, not no science.
- Additive migration `0016`.
- Public API, Python/JavaScript SDK helpers and WordPress status surface.

External provider health remains observable and non-blocking for Core release readiness.
