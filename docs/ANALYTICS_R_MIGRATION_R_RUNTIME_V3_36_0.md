# Platform Core v3.36.0 — Analytics R Migration / R Runtime 1.0

## Objective

v3.36.0 moves the former Catalyst Analytics R execution role into the shared
Platform Core runtime fabric as a first-class language runtime.

Canonical runtime identity: `sc-runtime-r`
Provider version: `1.0.0`
Adapter identity: `adapter:sc-runtime-r`
Core contract: `sc.core.r-runtime-migration.v1`

The historical `catalyst-analytics-r@2.0.1` identity remains resolvable as a
compatibility alias. This is a non-destructive migration.

## Runtime architecture

Platform Core owns:
- canonical runtime identity;
- adapter registration;
- capability discovery;
- computational job contracts;
- environment/provenance bindings;
- legacy Analytics R compatibility metadata.

`sc-runtime-r` owns:
- the R interpreter;
- allowlisted statistical execution;
- runtime diagnostics;
- result collection.

Research Lab is the primary statistical-analysis surface.
Workbench exposes interactive analytical use.
Workspace can orchestrate reproducible R jobs.

## R Runtime 1.0 allowlist

The initial provider intentionally uses base R / `stats` operations so production
deployment does not depend on ad-hoc package installation:

- descriptive_summary
- quantile_summary
- correlation_matrix
- linear_regression
- t_test
- one_way_anova

Additional econometric, psychometric and statistical package capabilities can
be added through later governed environment/package releases rather than
allowing package installation from job payloads.

## Security boundary

R Runtime 1.0 does not accept arbitrary R source code.

Job payloads cannot:
- invoke `system()`;
- execute shell commands;
- install packages;
- evaluate user-supplied formulas through `eval(parse(...))`.

Linear-model formulas are generated with R `reformulate()` from validated
column names.

## Migration semantics

Legacy Analytics R capability names map to canonical runtime operations.
Examples:

`linear_model` / `lm` / `ols` → `linear_regression`

`correlation` / `cor` → `correlation_matrix`

`anova` / `aov` / `oneway` → `one_way_anova`

Core does not run both legacy and canonical execution paths in parallel.

## Runtime deployment

The provider is installed under:

`/opt/sustainable-catalyst/r-runtime`

Systemd service:

`sc-r-runtime.service`

Loopback endpoint:

`http://127.0.0.1:18094`

The deployment script installs Ubuntu `r-base-core` when `Rscript` is absent,
creates a Python virtual environment for the governed FastAPI adapter, runs
static/provider tests, runs a native R smoke test, starts systemd, and performs
a live prepare/execute/inspect/results/artifacts/diagnose verification.

## Runtime registry

v3.36 adds a registered `sc-runtime-r` descriptor to the existing
`sc.core.runtime-adapter.v1` registry. Capability resolution remains
candidate-discovery-only. Platform Core does not autonomously choose a runtime
or a statistical method.

## Relationship to v3.35

v3.35 completed the Unified AI Research Object System. v3.36 begins the runtime
fabric continuation by consolidating R execution into the same governed runtime
architecture already used for Julia.

Next mapped build:
Platform Core v3.37.0 — Statistical Analysis Object Model.
