# Platform Core v2.36.1.1 — Uncertainty Compute Runtime Integration

v2.36.1.1 preserves the deployed v2.36.0 schema and adds bounded, reproducible statistical computation to the v2.36 uncertainty/sensitivity/ensemble semantic layer.

## Core-native bounded computation

- deterministic Monte Carlo sampling;
- deterministic Latin Hypercube sampling;
- Sobol-compatible A/B/AB design generation;
- Sobol first-order and total-effect post-processing from supplied model outputs;
- Morris trajectory generation and elementary-effect post-processing;
- explicit/equal ensemble weight normalization;
- weighted mean, variance, standard deviation, min/max and weighted quantiles;
- empirical threshold/exceedance probabilities with Wilson 95% intervals;
- persisted compute-run provenance and deterministic manifest hashes.

## Runtime integration

Core emits governed handoff manifests for Lab, Workbench, or an explicit external runtime. Handoffs carry model/scenario references, design manifests, requested outputs, callback contracts, and a deterministic SHA-256 digest.

Core does **not** dispatch arbitrary model code itself and does **not** execute arbitrary code. Numerical model execution remains a Lab/Workbench/external-runtime responsibility.

## Epistemic boundary

Computed statistics are results, not automatically truth. v2.36.1.1 does not automatically promote a probability, sensitivity index, ensemble statistic, or simulation result into a verified finding or truth claim.


## Production schema compatibility

The repair deliberately retains the v2.36.0 persistence identities: `sensitivity_studies.id`, `sensitivity_factors.study_id`, `sensitivity_measures`, `ensembles.id`, `ensemble_members.ensemble_id`, and `ensemble_statistics.ensemble_id`. Migration 0040 adds `uncertainty_compute_runs` without rewriting those tables.
