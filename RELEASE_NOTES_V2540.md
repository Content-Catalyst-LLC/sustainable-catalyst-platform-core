# Platform Core v2.54.0 — Probabilistic Forecasting & Calibration

v2.54.0 extends the predictive-intelligence object model with governed probabilistic forecast representations and calibration evidence.

## Delivered

- binary-event, categorical, quantile, interval, parametric-distribution, empirical-sample, and ensemble-distribution forecast records
- calibration studies and reliability/coverage evidence bins
- externally fitted calibration mappings with provenance
- externally computed proper-scoring, calibration, coverage, sharpness, and distribution-diagnostic evidence
- immutable hash-chained calibration packages
- model-bundle and public calibration-bundle reads
- Python and JavaScript SDK access to calibration bundles
- WordPress release-console shortcode `[sc_platform_core_predictive_calibration_status]`
- additive migration 0058

## Governance boundary

Platform Core stores, validates, packages, and exposes probabilistic evidence. It does not fit calibration mappings, apply recalibration, execute probabilistic inference, compute scoring rules or calibration metrics, rank models, or promote predictions to truth. Those operations remain with specialist runtimes such as Lab and Workbench.
