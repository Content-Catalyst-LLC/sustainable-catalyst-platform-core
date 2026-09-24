# Platform Core integration notes — Catalyst Julia Runtime v0.3.0

## Contract transition

Platform Core v3.23.0 registered Catalyst Julia Runtime v0.2.0 as a `contract-only` reference adapter.

Julia v0.3.0 is the provider-side implementation of that contract. Its native descriptor reports:

- adapter id: `adapter:catalyst-julia-runtime`
- adapter contract: `sc.core.runtime-adapter.v1`
- object contract: `sc.core.computational-runtime-object.v1`
- provider version: `0.3.0`
- status: `registered`
- transport: `http`
- invocation: `governed-service`

## Compatibility

The v0.1/v0.2 endpoints remain intact:
- `/health`
- `/version`
- `/capabilities`
- `/v1/environment`
- `/v1/environment/fingerprint`
- `/v1/jobs/validate`
- `/v1/jobs/run`

The new adapter endpoints are additive under `/v1/core-adapter`.

## Next Core step

After Julia v0.3.0 is deployed and verified, Platform Core should advance to v3.24.0 — Execution Environment & Dependency Provenance, and update its built-in Julia registry entry from v0.2.0 `contract-only` to v0.3.0 `registered`.
