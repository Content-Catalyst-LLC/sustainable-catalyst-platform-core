# Platform Core v2.57.0 — Spatial-Temporal Predictive Intelligence

Platform Core v2.57.0 extends Predictive Intelligence with governed spatial-temporal forecast and evidence objects.

## Added

- spatial-temporal study registry bound to projects and optional models/targets/datasets
- governed spatial-unit registry with geometry/bounding-box/source provenance
- externally computed spatial-temporal forecast records with valid-time windows and uncertainty
- observed spatial-temporal evidence records
- externally computed propagation/lag evidence between spatial units
- externally detected hotspot evidence with geometry and thresholds
- externally computed spatial-temporal evaluation evidence
- immutable hash-chained spatial-temporal packages
- internal and public bundle endpoints
- Python/JavaScript public SDK helpers
- WordPress status shortcode `[sc_platform_core_predictive_spatial_temporal_status]`
- additive migration `0061`

## Governance boundary

Platform Core stores, validates, packages, and exposes spatial-temporal predictive evidence. It does **not** perform interpolation, spatial inference, trajectory prediction, propagation modeling, hotspot detection, spatial metric computation, or automatic intervention. Those operations remain in specialist runtimes such as Lab, Workbench, Site Intelligence, or external systems.
