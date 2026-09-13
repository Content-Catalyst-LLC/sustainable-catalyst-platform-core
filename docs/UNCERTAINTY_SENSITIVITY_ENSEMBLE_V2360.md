# Uncertainty, Sensitivity & Ensemble Reasoning — v2.36.0

Platform Core v2.36.0 governs the semantics, provenance, and inspectability of uncertainty analysis while leaving numerical execution to Lab, Workbench, or external runtimes.

## Object families
1. `UncertaintyDefinitionRecord`
2. `SensitivityStudyRecord`
3. `SensitivityFactorRecord`
4. `SensitivityMeasureRecord`
5. `EnsembleRecord`
6. `EnsembleMemberRecord`
7. `EnsembleStatisticRecord`

## Boundaries
Core does not sample distributions, execute sensitivity algorithms, normalize ensemble weights, calculate ensemble statistics, execute models, automatically generate probabilities, or promote model output to truth.
