# Platform Core v3.38.0 — Scientific Result & Artifact Registry

## Objective

v3.38.0 creates a common registry for scientific results and research artifacts
produced across Sustainable Catalyst.

Contract: `sc.core.scientific-result-artifact-registry.v1`

The registry does not replace the authoritative source object. It stores stable
identity, content fingerprints, source-contract lineage and typed relationships.

## First-class objects

- ScientificResultRef
- ScientificArtifactRef
- ScientificRegistryRelation
- ScientificResultArtifactRegistry
- ScientificRegistryQuery
- ScientificRegistryQueryResult
- ScientificRegistrySnapshot
- ScientificRegistryPackage

## Result identity

The registry can represent scientific outputs including:
- statistical estimates;
- hypothesis-test results;
- effect sizes;
- model-fit statistics;
- diagnostics;
- matrices;
- simulations;
- forecasts;
- calibration/drift/robustness outputs;
- causal estimates;
- optimization outputs;
- measurements;
- findings.

## Artifact identity

Artifacts can include:
- tables and figures;
- charts and matrices;
- datasets;
- models and checkpoints;
- notebooks and scripts;
- reports and publications;
- images and geospatial products;
- JSON, CSV, Parquet and binary files;
- portable research packages.

Every artifact can carry a content SHA-256 fingerprint, media type, size,
source contract and source-object reference.

## Typed relations

Result/artifact relationships can express:
- derived-from;
- produced-by;
- visualizes;
- tabulates;
- summarizes;
- supports;
- contradicts;
- validates;
- reproduces;
- generated-from;
- depends-on;
- source-for;
- packages.

## v3.37 integration

v3.38 can register the governed statistical objects from v3.37 without copying
their payloads. The reference registration converts estimates and fit statistics
into scientific-result references and creates a portable package artifact with
typed package relationships.

## Query and snapshot layer

Registry queries can filter by:
- scientific result kind;
- artifact kind;
- source contract;
- source object;
- lifecycle state.

Snapshots bind the exact registry fingerprint and selected result/artifact/
relationship identities for reproducible exchange.

## Product boundaries

Platform Core owns:
- cross-domain scientific identity;
- result/artifact fingerprints;
- typed scientific relationships;
- registry snapshots;
- exchange packages.

Research Lab, Workbench, Workspace, Knowledge Library and other products retain
ownership of their source payloads and execution responsibilities.

Core does not execute scientific methods, modify source artifacts, certify
scientific validity, or interpret registered results as truth.

## Next mapped build

Platform Core v3.39.0 — Runtime Data Interchange.
