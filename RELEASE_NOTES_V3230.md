# Platform Core v3.23.0 — Runtime Adapter Contract & Capability Registry

## Added
- `sc.core.runtime-adapter.v1`
- Ten-method runtime adapter lifecycle contract.
- Core capability index.
- Candidate-only capability resolution.
- Julia v0.2.0 reference adapter registration.
- Compatibility translation for the existing analytical-runtime-provider contract.
- Adapter validation and stable SHA-256 fingerprints.
- Public adapter contract discovery endpoint.
- API endpoints for registry inspection, capability index and candidate resolution.
- Ten release tests.

## Architectural boundary
Core owns registration, contract validation, capability indexing and candidate discovery.
Runtime providers own execution mechanics.
Core does not autonomously choose a provider or scientific method and does not execute arbitrary runtime source.

## Next provider build
Catalyst Julia Runtime v0.3.0 — Core Runtime Contract Adapter.
