# Platform Core v2.55.0 — Predictive Ensembles & Model Comparison

v2.55.0 extends Predictive Intelligence with governed ensemble definitions and comparative model evidence.

## Delivered

- ensemble definitions with member roles, externally supplied weights, and combination-rule provenance
- externally generated point and probabilistic ensemble forecasts
- comparison studies spanning models, ensembles, baselines, and external candidates
- externally computed comparative metric evidence with uncertainty metadata
- externally computed pairwise comparison evidence
- immutable hash-chained model-comparison packages
- model-bundle ensemble-membership visibility
- public ensemble and comparison bundle reads
- Python and JavaScript SDK bundle access
- WordPress release-console shortcode `[sc_platform_core_predictive_ensembles_status]`
- additive migration 0059
- regression validation now follows the configured release version and current migration head instead of hard-coding the prior v2.54/0058 state

## Governance boundary

Platform Core stores, validates, packages, and exposes ensemble and comparison evidence. It does not optimize weights, construct or execute ensembles, compute metrics or statistical tests, rank candidates, automatically select models, or promote predictions to truth. Those operations remain with specialist runtimes such as Lab and Workbench.
