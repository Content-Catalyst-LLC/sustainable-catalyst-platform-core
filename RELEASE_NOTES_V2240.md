# Release Notes — Platform Core v2.24.0

**Release:** Capacity Forecasting & Resource Governance  
**Migration head:** `0027`  
**Base:** v2.23.1 capability-truth repair / v2.23.0 federated trusted-node exchange

v2.24.0 adds a provider-neutral capacity governance plane. Operators and Sustainable Catalyst products can register bounded resource profiles, record utilization/demand observations, generate persisted bounded forecasts, define resource budgets, and record advisory capacity decisions.

The release includes runtime observations for existing Core processing and connector queues, public-safe aggregate status, an optional production-certification capacity gate, SDK helpers, WordPress status, JSON Schemas, validation tooling, and regression coverage.

No automatic scaling, infrastructure purchase, deployment mutation, autonomous resource allocation, or hard admission control is introduced.

## Validation
- 304/304 backend tests pass across 34 modules.
- Migration `0001` through `0027` applies from a clean database with zero pending migrations.
- Capacity, federation, preservation, governance, certification, scale, observability, incident, continuity, resilience, operational-facility, humanitarian, country-evidence, scientific-service, cross-product, streaming, and production-integration validators reach their PASS contracts.
- Connector-worker smoke returns `queue-empty` on the clean validation database.
