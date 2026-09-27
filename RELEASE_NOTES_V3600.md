# Platform Core v3.60.0 — Neural Evaluation, Calibration & Uncertainty Objects

- Adds first-class governed scalar metric observations and confusion-matrix records.
- Adds calibration bins/curves, confidence distributions, predictive interval summaries, uncertainty estimates, and OOD indicator records.
- Binds every analytical result to v3.58 evaluation/checkpoint lineage and v3.59 dataset-partition provenance.
- Carries deterministic upstream training-lineage and dataset-lineage fingerprints.
- Explicitly keeps metrics, confidence, uncertainty, and OOD outputs separate from evidence/truth claims.
- Keeps all evaluation/calibration/uncertainty/OOD computation and model selection/promotion outside Platform Core.
