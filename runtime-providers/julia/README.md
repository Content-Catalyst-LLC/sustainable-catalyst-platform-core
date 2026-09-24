# Catalyst Julia Runtime v0.3.0 — Core Runtime Contract Adapter

Catalyst Julia Runtime v0.3.0 is the first Julia provider release that natively implements Platform Core's universal runtime adapter contract:

- `sc.core.runtime-adapter.v1`
- `sc.core.computational-runtime-object.v1`
- `sc.execution.v1`
- `sc.environment.v1`

## v0.3.0 objective

Turn the Julia provider from a contract-only reference runtime into a registered native Core runtime adapter without moving Julia execution into Platform Core itself.

## Native adapter lifecycle

The runtime now implements all ten Platform Core adapter lifecycle methods:

1. health
2. version
3. capabilities
4. prepare
5. execute
6. cancel
7. inspect
8. collect_results
9. collect_artifacts
10. diagnose

Runtime adapter discovery is available at:

`GET /v1/core-adapter`

## Governed execution

The existing allow-listed deterministic operations remain:

- `identity`
- `sum`
- `mean`
- `matrix_multiply`

Arbitrary Julia source execution, shell execution and runtime package installation remain disabled.

## Execution model

v0.3.0 adds a lightweight in-memory execution registry for the adapter lifecycle.

- `prepare` creates a governed run record.
- `execute` performs the current synchronous allow-listed operation and produces Core-shaped run/result envelopes.
- `cancel` cancels a prepared non-terminal run; completed runs are not retroactively cancelled.
- `inspect` returns the current run record.
- `collect_results` returns the Core-shaped execution result.
- `collect_artifacts` returns an empty artifact list for the built-in scalar/array/matrix operations.
- `diagnose` exposes runtime/environment identity and run diagnostics.

Persistent universal job/result storage remains a Platform Core / Workspace concern for later runtime-fabric builds.

## Security boundaries

Core still does not execute Julia directly. The Julia provider owns interpreter/process behavior. v0.3.0 does not enable arbitrary source, package installation, shell execution, remote shell, or autonomous scientific-method selection.

## Production endpoint

Default: `127.0.0.1:18093`.

## Required predecessor

Platform Core v3.23.0 — Runtime Adapter Contract & Capability Registry.
