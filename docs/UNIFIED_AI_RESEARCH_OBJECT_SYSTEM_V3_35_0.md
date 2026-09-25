# Platform Core v3.35.0 — Unified AI Research Object System

## Objective

v3.35.0 consolidates the AI Engineering object stack introduced in v3.27–v3.34
into one canonical cross-contract identity, lineage and exchange layer.

Contract: `sc.core.ai-research-object-system.v1`

This release does not replace the underlying contracts. It registers their
objects by reference and connects them in a typed research graph.

## Contracts unified

- `sc.core.ai-model.v1`
- `sc.core.ai-training-lineage.v1`
- `sc.core.ai-inference-provenance.v1`
- `sc.core.prompt-context-retrieval.v1`
- `sc.core.ai-evaluation-benchmark.v1`
- `sc.core.ai-experiment-reproducibility.v1`
- `sc.core.ai-error-robustness.v1`
- `sc.core.ai-calibration-drift-risk.v1`

Runtime/job/environment contracts remain linked execution infrastructure rather
than being duplicated into the AI research object system.

## First-class objects

- AIResearchContractBinding
- AIResearchSystemManifest
- AIResearchObjectRef
- AIResearchObjectEnvelope
- AIResearchRelationship
- AIResearchObjectRegistry
- AIResearchRelationshipGraph
- AIResearchLineageQuery
- AIResearchLineagePath
- AIResearchSnapshot
- AIResearchPackageManifest
- UnifiedAIResearchObjectBundle

## Canonical identity layer

Every registered AI research object retains:
- its original object identity;
- original source contract;
- object kind;
- source product owner;
- optional exact object version;
- canonical SHA-256 fingerprint;
- payload reference.

Core therefore unifies identity without copying source payloads.

## Typed relationship graph

The graph can express relationships including:
- trained-on;
- produced-by;
- generated-by;
- uses-prompt;
- uses-context;
- evaluates;
- includes;
- reproduces;
- reports-error;
- robustness-tested-by;
- calibrated-by;
- drift-observed-by;
- risk-observed-by;
- monitored-by;
- evidence-for;
- executed-as;
- executed-in.

The graph convention is that the source object points toward the object it
depends on. Upstream lineage therefore walks toward dependencies; downstream
lineage walks toward dependents.

## Lineage queries

The release includes deterministic breadth-first lineage traversal with:
- upstream queries;
- downstream queries;
- bidirectional queries;
- relationship-type filtering;
- maximum-depth controls;
- truncation reporting.

This makes queries such as the following possible:

`monitoring snapshot → risk → robustness → evaluation → model → training → dataset`

or in the other direction:

`model version → inference/evaluation/robustness/calibration/drift/monitoring`

## Immutable snapshots

AIResearchSnapshot freezes the exact fingerprints of:
- system manifest;
- object registry;
- relationship graph;
- source Core releases.

This creates a reproducible AI research state without moving ownership of
underlying objects.

## Portable AI research packages

AIResearchPackageManifest selects a reproducible subset of objects and
relationships from a snapshot and identifies one or more package roots.

This is the exchange layer for Research Lab, Workspace, Research Librarian,
Knowledge Library and later publication/reproduction workflows.

## Product boundaries

Knowledge Library keeps ownership of source/document/dataset objects.
Research Librarian keeps ownership of prompt/retrieval research workflows.
Research Lab keeps ownership of experiment/evaluation/robustness analysis.
Workspace/runtime providers keep execution ownership.

Platform Core owns:
- canonical identity;
- cross-contract registration;
- typed lineage;
- snapshots;
- package exchange contracts.

Core does not:
- copy source payloads;
- execute AI jobs;
- choose a best model;
- certify scientific validity;
- autonomously mutate research objects.

## AI Engineering milestone

v3.35.0 closes the first AI Engineering object-system sequence:

v3.27 Model identity
→ v3.28 Training lineage
→ v3.29 Inference provenance
→ v3.30 Prompt/context/retrieval
→ v3.31 Evaluation/benchmarks
→ v3.32 Experiments/reproducibility
→ v3.33 Error analysis/robustness
→ v3.34 Calibration/drift/risk
→ v3.35 Unified AI Research Object System

Next mapped Core build: v3.36.0 — Analytics R Migration / R Runtime 1.0.
