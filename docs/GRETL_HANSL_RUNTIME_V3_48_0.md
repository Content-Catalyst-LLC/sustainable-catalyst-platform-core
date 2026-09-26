# Platform Core v3.48.0 — gretl/hansl Runtime

v3.48.0 adds a governed econometrics runtime backed by gretl and hansl.

Core contract: `sc.core.gretl-hansl-runtime.v1`  
Runtime ID: `sc-runtime-gretl`  
Adapter ID: `adapter:sc-runtime-gretl`  
Provider version: `1.0.0`  
Native runtime: gretl 2023c  
Ubuntu 24.04 package: `2023c-2.1build3`

## v1 operations

- OLS
- robust OLS
- binary logit
- binary probit
- descriptive summary
- correlation matrix

The provider creates hansl scripts internally from validated variable names and
finite numeric datasets. Arbitrary hansl source is not accepted.

## Product integration

The runtime is added to the Unified Runtime API for:
- Workspace
- Research Lab

Workbench remains focused on R, Julia and Octave. gretl is treated as a domain
runtime for econometric research rather than a general engineering runtime.

## Security

The provider does not accept:
- arbitrary hansl source;
- shell commands;
- runtime package installation;
- caller-controlled filesystem paths.

Network access is disabled under the runtime security contract.

## Reproducibility

The reference environment records Ubuntu 24.04, gretl/gretl-common package
`2023c-2.1build3`, the provider version, execution paths, and deployment smoke
test.

## Execution boundaries

Platform Core owns runtime identity, adapter registration, environment/security
contracts, runtime discovery/binding, provenance and exchange.

The gretl provider owns bounded native econometric execution.

Research Lab owns model specification, assumption checking, diagnostics,
interpretation and methodological validity.

No database migration.

Next mapped build:
Platform Core v3.49.0 — Haskell Runtime.
