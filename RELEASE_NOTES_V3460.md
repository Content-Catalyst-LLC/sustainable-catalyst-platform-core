# Platform Core v3.46.0 — Stan Runtime

## Objective

v3.46.0 introduces Stan as the first dedicated domain runtime in the post-v3.45
runtime fabric.

Core contract: `sc.core.stan-runtime.v1`  
Runtime ID: `sc-runtime-stan`  
Adapter ID: `adapter:sc-runtime-stan`  
Provider version: `1.0.0`  
Pinned native runtime: `CmdStan 2.36.0`

## Runtime operations

The v1 provider exposes:

- `compile_model`
- `sample`
- `optimize`
- `variational`
- `diagnose`

The runtime is intended for Bayesian and probabilistic modeling. Core does not
choose a model, choose priors, interpret convergence, or certify the validity
of an inference.

## Security boundary

The provider accepts Stan domain-model source but does not expose a shell or
arbitrary process execution.

v1 forbids:

- `#include` directives;
- external C++ extensions;
- runtime package installation through the API;
- caller-controlled filesystem paths;
- shell execution;
- multi-chain parallel execution inside one provider invocation.

One chain per invocation keeps the runtime boundary simple. Workspace can later
orchestrate multiple independent chains as governed jobs.

## Reproducible environment

The Core reference environment records:

- Ubuntu 24.04 amd64;
- Stan provider `1.0.0`;
- CmdStan `2.36.0`;
- build-essential and Git;
- `cmdstanpy`;
- CmdStan installation manifest;
- provider Python lock/requirements asset;
- provider-managed artifact/model directories.

The execution host builds that environment. Core records the environment
contract and its lineage.

## Runtime security policy

The Stan policy permits only the registered Stan runtime/adapter and the five
v1 operations.

Network access is disabled during execution. Package installation is disabled.
Filesystem writes are limited to governed workspace/runtime artifact prefixes.
Approved research artifacts, posterior samples and diagnostics may be emitted.

## Unified Runtime API integration

v3.46 extends the v3.44 runtime catalog:

- R
- Julia
- Stan

Workspace and Research Lab are Core-side Stan clients. Workbench remains an
R/Julia client in this release.

A Research Lab request for capability `bayesian-inference` and operation
`sample` can discover or explicitly bind `sc-runtime-stan`. Core validates the
binding and constructs the invocation envelope; Workspace/the execution host
dispatches it.

## Native provider

The Stan provider is deployed as a local systemd service on port 18095. The
deployment installs pinned CmdStan when needed and performs a bounded native
sampling smoke test before Platform Core is promoted.

## Boundaries

Platform Core owns runtime identity, adapter registration, environment and
security contracts, product-facing discovery/binding, provenance and exchange.

The Stan provider owns bounded CmdStan compilation/execution.

Workspace or another execution host owns job orchestration.

Research Lab owns model-building, inference workflow, diagnostics review and
scientific interpretation.

## Next mapped build

Platform Core v3.47.0 — Octave Runtime.
