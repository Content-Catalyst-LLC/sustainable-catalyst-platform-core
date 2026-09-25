# Platform Core v3.25.0 — Unified Computational Job Runtime

## Objective

v3.25.0 gives Sustainable Catalyst one governed job abstraction spanning Julia,
Python, R and later domain runtimes.

The release does **not** make Platform Core an execution host. Instead, Core
owns the semantics, identity, lifecycle, provider binding, environment
requirements, lineage, result binding and artifact binding of a computational
job. Workspace and runtime providers remain responsible for actual execution.

## Contract

`sc.core.computational-job.v1`

Depends on:

- `sc.core.computational-runtime-object.v1`
- `sc.core.runtime-adapter.v1`
- `sc.core.execution-environment-provenance.v1`

## Unified lifecycle

`declared → queued → preparing → running → completed | failed | cancelled`

Transitions are explicit and validated. Terminal states cannot be reopened.

## First-class job objects

- ComputationalJob
- JobProviderBinding
- JobAttempt
- JobEvent
- JobArtifactBinding
- RetryPolicy
- JobDispatchEnvelope
- JobValidationReport

## Provider binding

A job must explicitly bind to a runtime adapter. Core does not select a provider
autonomously.

The reference job is pinned to:

- adapter `adapter:catalyst-julia-runtime`
- runtime `catalyst-julia-runtime`
- provider version `0.3.0`
- operation `matrix_multiply`

## Environment requirements

A computational job can bind an `EnvironmentRequirement` from v3.24.0. Before
execution or reproduction, the observed runtime environment can be checked
against that requirement.

## Dispatch envelope

Core can produce a provider-neutral dispatch envelope containing:

- job and request identity;
- adapter/runtime/provider identity;
- operation/source/entrypoint;
- arguments, inputs and parameters;
- expected environment fingerprint;
- resource budget;
- execution policy;
- random seed;
- provenance.

The envelope is for Workspace/runtime-provider execution. Core does not invoke
the interpreter itself.

## Why this matters

This becomes the common execution spine for:

- Julia scientific compute;
- Python AI/ML and data science;
- R statistics/econometrics;
- Stan probabilistic programming;
- Octave engineering/numerical workflows;
- gretl/hansl econometrics;
- later GPU/HPC/remote compute.

It is also the direct prerequisite for the AI Engineering track, because
training, inference and evaluation will all be specialized computational jobs.
