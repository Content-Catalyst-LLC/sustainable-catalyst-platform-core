# Platform Core v2.56.0 — Anomaly, Change-Point & Early-Warning Intelligence

Platform Core v2.56.0 extends Predictive Intelligence with governed monitoring objects and provenance for externally computed anomaly detection, change-point analysis, and early-warning signals.

## Added

- monitoring-study registry bound to projects and optional predictive models/targets/time-series datasets
- externally defined detection rules and thresholds
- anomaly evidence records with detector-score and source-observation provenance
- change-point evidence with bounded temporal uncertainty and before/after state metadata
- early-warning signal records with indicator, threshold, and lead-time evidence
- descriptive monitoring episodes that group explicit evidence references
- immutable hash-chained monitoring packages
- internal and public monitoring bundle endpoints
- Python/JavaScript public SDK helpers
- WordPress shortcode `[sc_platform_core_predictive_monitoring_status]`
- additive migration `0060`

## Governance boundary

Platform Core stores, validates, packages, and exposes monitoring evidence. It does **not** run anomaly/change-point algorithms, optimize thresholds, compute early-warning indicators, dispatch alerts, infer causation, or trigger interventions. Those operations remain in specialist runtimes such as Lab, Workbench, Site Intelligence, or external systems.

## Regression compatibility repair

- historical health tests now compare against the active application release instead of pinning v2.55.0
- capability-lineage tests now derive the current migration head from the migration registry instead of pinning `0059`
- this preserves historical capability assertions while allowing additive releases to advance safely
