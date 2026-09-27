# Platform Core v3.63.0 — Neural Inference & Prediction Provenance

v3.63.0 adds governed inference-run and prediction provenance on top of the neural model, data, evaluation, explainability, and representation layers introduced in v3.57.0–v3.62.0.

## Added

- Source-bound inference-input records resolving to v3.59 tensor/data lineage.
- Inference-run records binding inference plan, model version, checkpoint, runtime, environment, job, and inputs.
- Prediction records covering point, class, probability-vector, distribution, ranking, anomaly, forecast, and structured outputs.
- Confidence/uncertainty bindings resolving v3.60 calibration, confidence, interval, uncertainty, and OOD objects.
- Interpretation bindings resolving v3.61 explanations and v3.62 similarity/projection/cluster objects.
- Deterministic inference/prediction provenance bundle fingerprints.
- Public contract endpoint `/public/v1/ml-inference/contract` and governed validation routes.

## Governance

Predictions remain analytical outputs rather than evidence or claims. Core does not run inference, execute models, generate predictions, calibrate results, estimate uncertainty, produce explanations, promote predictions to evidence/claims, or autonomously act on predictions.

## Migration

No database migration is required for v3.63.0.
