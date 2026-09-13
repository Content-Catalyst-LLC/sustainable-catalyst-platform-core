# Platform Core v2.36.1 — Uncertainty Compute Runtime Integration

v2.36.1 converts the v2.36 uncertainty/sensitivity/ensemble semantic layer into a reproducible compute-capable layer without moving arbitrary model execution into Core.

## Adds
- Migration `0040`.
- Deterministic Monte Carlo and Latin Hypercube sampling.
- Sobol-compatible A/B/AB design generation and first/total index calculation from supplied model outputs.
- Morris trajectories and elementary-effect summaries from supplied outputs.
- Ensemble weight normalization and weighted descriptive statistics.
- Empirical threshold/exceedance probability with Wilson 95% interval.
- Lab/Workbench/external runtime handoff manifests.
- Persisted uncertainty compute run/audit records.
- Public readiness, SDK and WordPress status integration.

## Boundary
Core may now perform bounded statistical design generation and post-processing. Core still does not execute arbitrary model code, dispatch network compute by itself, or automatically promote computed results to truth.
