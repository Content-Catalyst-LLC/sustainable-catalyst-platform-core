# Predictive Ensembles & Model Comparison — v2.55.0

Platform Core v2.55.0 adds governed representations for predictive ensembles and comparative model evidence.

## Core-owned records

- ensemble definitions and externally supplied combination-rule provenance
- ensemble membership, roles, externally supplied weights, and runtime references
- externally generated ensemble forecasts, including point and probabilistic representations
- comparison studies and candidate registries spanning models, ensembles, baselines, and external comparators
- externally computed metric evidence with aggregation and uncertainty metadata
- externally computed pairwise comparison evidence
- immutable, hash-chained model-comparison packages

## Execution boundary

Platform Core does **not** optimize ensemble weights, construct or execute ensembles, compute comparison metrics, compute statistical significance, rank candidates, select a winning model, or promote predictions to truth. Lab, Workbench, and other specialist runtimes perform those operations and return evidence/provenance to Core.

## Public contracts

- `sc.predictive.ensemble.v1`
- `sc.predictive.ensemble-forecast.v1`
- `sc.predictive.model-comparison.v1`
- `sc.predictive.model-comparison-package.v1`
