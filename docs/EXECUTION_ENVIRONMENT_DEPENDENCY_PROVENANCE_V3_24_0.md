# Platform Core v3.24.0 — Execution Environment & Dependency Provenance

## Objective

v3.24.0 makes the computational environment itself a governed research object.

A result is not reproducible merely because Core knows which runtime produced it. Core must also be able to answer:

- Which exact interpreter/compiler version was used?
- Which packages and libraries were present?
- Which package versions and content hashes were resolved?
- Which project, manifest or lockfiles defined the environment?
- Which OS, architecture, container and runtime flags were active?
- Did the environment drift between two runs?
- Does an observed environment satisfy a declared reproduction requirement?

## Contract

`sc.core.execution-environment-provenance.v1`

Depends on:
- `sc.core.computational-runtime-object.v1`
- `sc.core.runtime-adapter.v1`
- `sc.environment.v1`

## First-class objects

- ExecutionEnvironmentProvenance
- DependencyNode
- DependencyEdge
- LockfileRecord
- EnvironmentRequirement
- RequirementVerification
- EnvironmentComparison

## Julia v0.3.0 promotion

Catalyst Julia Runtime v0.3.0 becomes the reference registered adapter for this layer.

Core records the Julia provider as:
- `adapter:catalyst-julia-runtime`
- provider `0.3.0`
- adapter state `registered`
- Julia runtime `1.13.0`
- environment contract `sc.environment.v1`

The authoritative live Project/Manifest hashes remain provider-supplied.

## Reproducibility boundary

Core records, fingerprints, compares and verifies environments.

Core does not:
- install packages;
- mutate an execution environment;
- invoke a package manager;
- execute Julia/Python/R directly;
- certify that a scientific conclusion is correct.

## Persistence

v3.24.0 is contract-first and comparison/verification-first. It does not add duplicate persistence tables. Environment provenance is designed to bind into the Unified Computational Job Runtime in v3.25.0.
