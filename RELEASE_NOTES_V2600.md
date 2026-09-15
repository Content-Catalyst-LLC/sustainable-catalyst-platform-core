# Platform Core v2.60.0 — Reproducible Predictive Intelligence Packages

v2.60.0 closes the predictive-intelligence roadmap with a cross-layer reproducibility package that can freeze references from model provenance, backtesting, probabilistic calibration, ensembles/comparisons, monitoring, spatial-temporal analysis, causal-predictive studies, and predictive decision studies.

## Added
- governed reproducible predictive package registry
- cross-layer component manifests with optional SHA-256 digests and frozen snapshots
- artifact registry with media type, size, and integrity metadata
- runtime/environment capture with lockfile and image-digest references
- externally computed verification evidence and human/technical review records
- immutable hash-chained package snapshots
- public-safe package bundle endpoint and Python/JavaScript SDK helpers
- WordPress status shortcode `[sc_platform_core_predictive_package_status]`
- additive migration `0064`

## Boundaries
Platform Core records, validates, packages, hashes, and exposes provenance. It does not execute predictive models, refit models, regenerate forecasts, rerun backtests/calibration/causal analysis, optimize decisions, or automatically reproduce analyses.
