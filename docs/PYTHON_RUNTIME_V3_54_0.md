# Platform Core v3.54.0 — Python Runtime Core Integration

## Purpose

Establish Python as a first-class governed Platform Core runtime alongside R, Julia, Stan, Octave, gretl/hansl, Haskell, Fortran, C/C++, Rust, and Go. This release does not make Platform Core execute arbitrary Python and does not redefine the Python implementation language used internally by existing services.

## Canonical identity

- Contract: `sc.core.python-runtime.v1`
- Runtime: `sc-runtime-python`
- Adapter: `adapter:sc-runtime-python`
- Provider: `1.0.0`
- CPython: `3.12.3`
- Service: `sc-python-runtime`
- Endpoint: `127.0.0.1:18103`

## Bounded operations

`descriptive_summary`, `linear_regression`, `matrix_multiply`, `standardize`, `bootstrap_mean_ci`, `token_frequency`.

Each job is an internally generated program executed as `python3.12 -I -S`, with structured JSON input and no caller source. Bootstrap execution requires an explicit deterministic seed.

## Security boundaries

No arbitrary Python source, shell execution, runtime package installation through the API, caller-controlled filesystem paths, or network access for job programs. Core owns contracts, governance, provenance, and registration; the provider executes bounded jobs.

## Product integration

Python is registered for Workspace, Research Lab, and Workbench through the Unified Runtime API. It supplies general/scientific compute, data analysis, statistics/regression, matrix computation, reproducible randomness, and text analysis.

## Reproducibility

The environment package records CPython 3.12.3 on Ubuntu 24.04, provider requirements, isolated execution flags, security policy, result/artifact lineage, and fingerprints. Production deployment captures the concrete Ubuntu package version in runtime health and deployment evidence.
