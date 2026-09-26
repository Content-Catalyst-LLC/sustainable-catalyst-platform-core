# Platform Core v3.49.0 — Haskell Runtime

v3.49.0 adds a governed Haskell runtime to the Sustainable Catalyst computational research fabric.

Core contract: `sc.core.haskell-runtime.v1`  
Runtime ID: `sc-runtime-haskell`  
Adapter ID: `adapter:sc-runtime-haskell`  
Provider version: `1.0.0`  
Native runtime: GHC 9.4.7  
Ubuntu 24.04 package: `9.4.7-3`  
Provider endpoint: `127.0.0.1:18098`

## v1 bounded operations

- `gcd`
- `lcm`
- `rational_reduce`
- `factorial`
- `fibonacci`
- `binomial_coefficient`
- `integer_power`
- `graph_reachable`

The provider generates Haskell source internally from validated typed integer inputs and executes it with `runghc`. It does not accept caller-supplied Haskell source, shell commands, runtime package-install requests, or caller-controlled filesystem paths.

## Product integration

Haskell is registered in the Unified Runtime API for Workspace, Research Lab and Workbench. Its primary declared capabilities are exact arithmetic, discrete mathematics, functional computation and graph reasoning.

Core can validate an explicit runtime binding and build a governed invocation envelope. Core does not decide that Haskell is the scientifically or mathematically appropriate method for a research question.

## v3.48 forward repair

The v3.49 apply step carries the production-proven gretl fixes into `main`: pipefail-safe Ubuntu package candidate extraction and valid `open "dataset.csv"` hansl generation. The immutable v3.48 tag is not rewritten.

## Security and reproducibility

The Haskell runtime records a dedicated reproducible environment and security policy. Network access is disabled by policy; package installation, shell execution and arbitrary source execution are denied. Generated source, result JSON and the native execution log are retained as governed artifacts.

## Native verification

Deployment requires a real GHC/runghc smoke test reducing `42/56` exactly to `3/4` before Platform Core is promoted.

No database migration.

Next mapped build: **Platform Core v3.50.0 — Fortran Runtime**.
