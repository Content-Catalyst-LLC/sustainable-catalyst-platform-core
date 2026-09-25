# Platform Core v3.40.0 — Cross-Runtime Research Workflow

## Objective

v3.40.0 composes the governed runtime, statistical, interchange and scientific
artifact layers into one reproducible cross-runtime research workflow contract.

Contract: `sc.core.cross-runtime-research-workflow.v1`

The workflow model describes execution intent and lineage across multiple
runtimes without turning Platform Core into a scheduler or execution engine.

## First-class objects

- WorkflowRuntimeBinding
- WorkflowInputBinding
- WorkflowOutputBinding
- CrossRuntimeWorkflowStep
- WorkflowDependency
- RuntimeHandoff
- CrossRuntimeWorkflowDefinition
- WorkflowReadinessReport
- WorkflowExecutionEvent
- WorkflowVerification
- CrossRuntimeWorkflowRun
- CrossRuntimeWorkflowPackage

## Workflow graph

A workflow is a directed acyclic graph of research steps. Dependencies are
typed as hard, soft, data, evidence or provenance relationships.

Core validates:
- unique step/runtime/dependency/handoff identities;
- known dependency endpoints;
- acyclic workflow structure;
- runtime-binding consistency;
- handoff/runtime consistency;
- matching dependency edges for cross-runtime handoffs.

A deterministic topological order is available for orchestration systems.

## Runtime bindings

Each computational step can bind:
- runtime identity/version;
- runtime adapter;
- execution environment;
- required operations;
- computational-job identity;
- analysis/model/evaluation object references.

Runtime selection remains explicit. Core does not choose a runtime
autonomously.

## Runtime handoffs

`RuntimeHandoff` binds a workflow dependency to the v3.39 interchange layer:

source step
→ source runtime
→ logical data identity
→ interchange transfer
→ verification
→ target artifact
→ target runtime
→ target step

A target step remains blocked until its hard/data dependencies have completed
and any required runtime handoff is verified.

## Readiness model

`workflow_readiness()` evaluates which uncompleted steps are ready without
executing or scheduling them.

For the reference workflow:

1. R regression is initially ready.
2. After R completes, Julia remains blocked until the R→Julia handoff is
   verified.
3. After the verified handoff, the Julia matrix step becomes ready.
4. After R and Julia complete, scientific registration becomes ready.

This provides deterministic orchestration semantics while preserving Workspace
or another execution host as the scheduler.

## Reference workflow

The v3.40 reference workflow is:

R statistical analysis
`sc-runtime-r@1.0.0`
→ verified v3.39 JSON interchange
→ Julia matrix computation
`catalyst-julia-runtime@0.3.0`
→ v3.38 scientific result/artifact registration.

The reference package includes:
- two runtime bindings;
- three workflow steps;
- three dependencies;
- one verified cross-runtime handoff;
- execution events;
- exact step/handoff fingerprints;
- workflow-level verification;
- scientific-registry/interchange references.

It is a contract proof, not evidence that the reference jobs were run during
local packaging.

## Workflow verification

A completed workflow requires passed or warning-level verification.

Verification can bind:
- exact step fingerprints;
- exact handoff fingerprints;
- completed step identities;
- verified handoffs;
- final scientific artifacts;
- final research results.

This supports later reproduction and audit layers.

## Scientific registry bridge

A complete cross-runtime workflow package can be projected into a v3.38
`ScientificArtifactRef`, preserving:
- package fingerprint;
- workflow identity;
- workflow run identity;
- workflow state;
- participating runtime identities.

## Product boundaries

Platform Core owns:
- workflow contracts;
- typed dependencies;
- runtime bindings;
- handoff lineage;
- readiness semantics;
- event provenance;
- verification objects;
- portable workflow packages.

Workspace or another execution host owns:
- queueing;
- scheduling;
- retries;
- worker allocation;
- actual runtime execution;
- data movement/conversion execution.

Core does not execute runtime steps, schedule jobs, autonomously choose
runtimes/formats, or certify scientific validity.

## Next mapped build

Platform Core v3.41.0 — Reproducible Environment Packages.
