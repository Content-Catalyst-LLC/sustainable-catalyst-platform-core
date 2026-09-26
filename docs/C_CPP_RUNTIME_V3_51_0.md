# Platform Core v3.51.0 — C/C++ Runtime

Platform Core v3.51.0 adds a governed native-engineering runtime backed by GCC/G++.

- Contract: `sc.core.c-cpp-runtime.v1`
- Runtime: `sc-runtime-cpp`
- Adapter: `adapter:sc-runtime-cpp`
- Provider: `1.0.0`
- C profile: C11
- C++ profile: C++17
- Compiler family: GCC/G++ 13.3.0
- Ubuntu 24.04 amd64 package: `13.3.0-6ubuntu2~24.04.1`
- Service: `sc-cpp-runtime`
- Endpoint: `127.0.0.1:18100`

## Bounded native-engineering operations

`dot_product`, `matrix_multiply`, `linear_interpolation`, `polynomial_evaluate`, `fir_filter`, and `dijkstra_shortest_path`.

Structured requests are validated and converted to provider-generated C11 or C++17 source. The provider compiles with managed compilers, runs a transient native executable, deletes the executable after execution, and preserves generated source, result JSON, compile log, and run log as governed artifacts.

## Product integration

The C/C++ runtime is exposed through the Unified Runtime API to Workspace, Research Lab, and Workbench. Core owns runtime identity, environment/security contracts, capability discovery/binding, provenance, artifacts, and reproducibility. The provider owns bounded compilation and execution. Calling products own scientific/engineering method selection and interpretation.

## Security boundaries

The v1 API does not accept arbitrary caller C/C++ source, shell commands, runtime package installation, or caller-controlled filesystem paths. Network access is disabled by the Core security policy. Core does not certify numerical or scientific validity.

## Reproducibility

The environment records Ubuntu 24.04 amd64, pinned gcc-13/g++-13 package versions, provider version, language profiles, compiler flags, artifact paths, and a native validation suite.

No database migration.
