# Platform Core v2.6.0 release notes

This release turns Platform Core into the unified service gateway without merging the product codebases.

## Added

- Service registry for Site Intelligence, Workbench, Decision Studio, Research Librarian, Catalyst Finance, and Narrative Risk
- Public and internal gateway routes
- Aggregated service health
- End-to-end request IDs
- Internal service-token injection
- Header filtering and path validation
- Bounded payload sizes
- Per-service method allowlists
- Circuit breaking and cooldown
- Docker network example and environment template
- Gateway regression tests

## Compatibility

All v2.0.0–v2.5.0 routes remain intact. No database schema migration is required for this release.
