# Platform Core v3.1.0 — Analytical Runtime Provider Contract

## Scope
Introduces the runtime-neutral contract that lets Platform Core describe, govern, trace, and package specialist analytical computation without executing that computation inside Core.

## First provider
- Provider: `catalystanalyticsr`
- Provider version: `2.0.1`
- Runtime: `r`
- Execution host: `workspace`
- Invocation mode: `workspace-managed`

## New governed records
Analytical runtime providers, capabilities, execution requests, runtime environments, execution results, artifacts, statistical diagnostics, and reproduction references.

## Boundary
Core does not execute R/Python/Julia, autonomously select providers, infer statistical significance, certify scientific validity, or determine truth. Workspace/specialist runtimes perform computation and return declared results/provenance.

## Migration
`0103`

## Backend endpoint
`GET /v1/analytics/runtime-providers/readiness`

`GET /v1/analytics/runtime-providers/providers/catalystanalyticsr`
