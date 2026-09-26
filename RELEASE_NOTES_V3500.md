# Platform Core v3.50.0 — Fortran Runtime

v3.50.0 introduces a governed GNU Fortran runtime for scientific/HPC workloads.

- Core contract: `sc.core.fortran-runtime.v1`
- Runtime ID: `sc-runtime-fortran`
- Adapter ID: `adapter:sc-runtime-fortran`
- Provider version: `1.0.0`
- Compiler: GNU Fortran 13.3.0
- Ubuntu 24.04 amd64 package: `gfortran-13=13.3.0-6ubuntu2~24.04.1`
- Service: `sc-fortran-runtime`
- Endpoint: `127.0.0.1:18099`

## Bounded v1 operations

- `dot_product`
- `matrix_multiply`
- `trapezoidal_integral`
- `central_difference`
- `rk4_linear_step`
- `heat_step_1d`

The provider generates Fortran 2008 source from validated typed inputs, compiles it with provider-controlled flags, executes the resulting transient binary, records source/compile/run/result artifacts, and removes the executable after execution.

No arbitrary Fortran source, shell execution, runtime package installation, or caller-controlled filesystem path is accepted.

## Product integration

Core-side profiles expose Fortran to Workspace, Research Lab and Workbench. Core can validate an explicit runtime binding but does not autonomously select a numerical method or certify numerical/scientific validity.

## Reproducibility and provenance

The reference environment records Ubuntu 24.04 amd64, GNU Fortran 13.3.0, exact Ubuntu package provenance, compiler flags, provider version, environment paths, security policy and a native dot-product deployment smoke test.

No database migration.

Next mapped build: Platform Core v3.51.0 — C/C++ Runtime.
