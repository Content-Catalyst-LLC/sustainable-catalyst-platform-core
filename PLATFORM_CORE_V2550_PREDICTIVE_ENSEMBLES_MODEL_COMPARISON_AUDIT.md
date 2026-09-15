# Platform Core v2.55.0 — Predictive Ensembles & Model Comparison Audit

## Release invariants

1. Migration 0059 is additive and follows 0058.
2. Ensemble and comparison tables are created idempotently by the migration runner.
3. Ensemble definitions, members, externally generated forecasts, comparison candidates, metric evidence, pairwise evidence, and hash-chained packages are persisted.
4. Model, ensemble, and comparison references are project-bounded where applicable.
5. Public reads require public visibility.
6. Core refuses fields that ask it to optimize weights, execute ensembles, compute comparison metrics/significance, rank candidates, select a model, or promote truth.
7. v2.52–v2.54 predictive contracts remain intact.

8. Regression recovery/readiness tests derive the active release and migration head dynamically, preventing a valid additive release from failing solely because older tests pin the previous release number.
