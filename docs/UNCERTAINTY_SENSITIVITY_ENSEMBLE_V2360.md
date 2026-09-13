# v2.36.0 Uncertainty, Sensitivity & Ensemble Reasoning

## Purpose

Make uncertainty and multi-run reasoning first-class, governed Platform Core semantics without moving scientific computation into Core.

## Objects

- `UncertaintyDefinitionRecord`
- `SensitivityStudyRecord`
- `SensitivityFactorRecord`
- `SensitivityResultRecord`
- `EnsembleRecord`
- `EnsembleMemberRecord`
- `EnsembleStatisticRecord`

## Execution boundary

Sampling plans and aggregation contracts are metadata. Numerical execution is external. Sensitivity results and ensemble statistics must identify external provenance and cannot claim calculation by Core.

## Visualization

Sensitivity studies use `sensitivity-map`; ensembles use `ensemble-view`. Core compiles chart specifications and resolves Vega-Lite/Plotly renderer contracts without executing the renderer.
