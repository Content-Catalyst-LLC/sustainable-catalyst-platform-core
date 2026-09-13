# Platform Core v2.36.0 — Uncertainty, Sensitivity & Ensemble Reasoning

Release date: 2026-09-13

Migration `0039` adds governed uncertainty definitions, sensitivity studies/factors/measures, ensembles/members/statistics, provenance, and public-safe metadata.

Core records the semantics and lineage of uncertainty analysis. Sampling, sensitivity algorithms, ensemble aggregation, and model execution are performed by Lab, Workbench, or an approved external runtime and supplied back to Core.

## Primary capabilities
- aleatory, epistemic, mixed, measurement, model, scenario, and unknown uncertainty;
- deterministic/interval/uniform/normal/lognormal/triangular/beta/empirical/custom distribution metadata;
- bounds, confidence level, assumptions, source, and provenance;
- sensitivity methods including local, OAT, Morris, Sobol, Monte Carlo, correlation, elasticity, and custom contracts;
- descriptive sensitivity ranking from externally supplied measures;
- ensemble membership by scenario, Scenario Compute request, or model run;
- externally supplied ensemble statistics and interval/quantile metadata;
- no automatic probability generation or truth promotion.
