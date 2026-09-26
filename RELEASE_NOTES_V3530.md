# Platform Core v3.53.0 — Go Runtime

v3.53.0 adds Go as the **Concurrent / Distributed** language runtime in the Sustainable Catalyst computational research fabric.

- Core contract: `sc.core.go-runtime.v1`
- Runtime: `sc-runtime-go`
- Adapter: `adapter:sc-runtime-go`
- Provider: `1.0.0`
- Native toolchain: Go 1.22.2
- Service: `sc-go-runtime` on `127.0.0.1:18102`

## Bounded v1 operations

`parallel_sum`, `parallel_map_affine`, `concurrent_histogram`, `parallel_matrix_row_sums`, `parallel_graph_degrees`, and `batch_sha256`.

The provider generates fixed Go programs from validated inputs and uses goroutines, channels, worker pools, and standard-library primitives. Caller-supplied Go source is not accepted. Module downloads are disabled (`GOPROXY=off`, `GOTOOLCHAIN=local`, `GO111MODULE=off`) and CGO is disabled for these v1 kernels.

Core owns runtime identity, adapter registration, environment/security contracts, discovery/binding, provenance, and scientific-artifact exchange. The provider owns bounded compilation/execution. Calling products retain method/algorithm selection. Core does not certify scientific validity.

No database migration.

Next mapped build: Platform Core v3.54.0 — Python Runtime Core Integration.
