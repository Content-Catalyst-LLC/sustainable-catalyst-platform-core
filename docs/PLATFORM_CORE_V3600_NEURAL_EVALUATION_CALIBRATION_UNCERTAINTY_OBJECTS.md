# Platform Core v3.60.0 — Neural Evaluation, Calibration & Uncertainty Objects

v3.60.0 turns neural/model evaluation outputs into governed, reproducible research objects while keeping all evaluation computation outside Platform Core.

## Lineage

`v3.58 Evaluation → v3.59 Dataset Partition → Metric / Calibration / Confidence / Interval / Uncertainty / OOD Object`

Every v3.60 result binds to the evaluation and partition that produced it and carries the upstream training-lineage and dataset-lineage fingerprints.

## Objects

- `MLMetricObservation`
- `MLConfusionMatrixRecord`
- `MLCalibrationBinRecord` / `MLCalibrationRecord`
- `MLConfidenceDistributionRecord`
- `MLPredictionIntervalSummary`
- `MLUncertaintyEstimateRecord`
- `MLOutOfDistributionIndicatorRecord`
- `MLEvaluationCalibrationUncertaintyBundle`

## Governance rule

Metrics and model-derived scores are analytical results. They are not evidence and do not become truth claims merely because they are calibrated, confident, or low-uncertainty. OOD indicators likewise remain model-derived analytical signals.

## Execution boundary

Core does not compute metrics, calibrate models, generate predictions, estimate uncertainty, run OOD detectors, choose thresholds, rank/select the best model, certify model quality, or promote a model. Workspace/Lab runtimes perform computation; Core preserves governed contracts and provenance.
