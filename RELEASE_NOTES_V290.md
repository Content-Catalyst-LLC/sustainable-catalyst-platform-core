# Sustainable Catalyst Platform Core v2.9.0

## Streaming, Alerts, and Source Reliability

v2.9.0 converts the v2.7.x live-data gateway and v2.8.x production/data-fabric foundation into a persistent reliability plane.

### Added

- Migration `0012`
- Persistent connector work queue
- Worker lease/retry semantics
- Standalone horizontally scalable connector worker
- Server-Sent Events
- Alert rules
- Geographic subscriptions
- Stale-source detection
- Dead-letter records
- Historical replay
- Explicit provider-failover groups
- Automatic failover only for explicitly compatible parameter contracts
- Reliability readiness surface
- Public stream SDK URL helpers
- WordPress reliability status

### Safety and truth boundaries

External provider health remains non-blocking for release promotion. Core does not average, substitute, or silently reinterpret source meaning when a provider fails. Failover is allowed only inside an explicitly declared compatible provider group. Dead-letter replay preserves the original failure record.

### Compatibility

All v2.0.0–v2.8.1 APIs remain available. Migration `0012` is additive.
