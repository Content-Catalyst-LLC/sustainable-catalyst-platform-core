# Platform Core v3.63.0 — Neural Inference & Prediction Provenance

## Purpose

v3.63.0 establishes governed provenance for model inference and prediction outputs. It connects a prediction to the exact governed input, inference plan, model specification, model version, checkpoint, runtime binding, environment, computational job, calibration/uncertainty objects, explainability objects, and representation objects that contextualize it.

## Lineage

`governed input → model/checkpoint → inference run → prediction → confidence/uncertainty → interpretation`

## First-class objects

- `MLInferenceInputBindingRecord`
- `MLInferenceRunRecord`
- `MLClassScoreRecord`
- `MLPredictionRecord`
- `MLPredictionConfidenceBindingRecord`
- `MLPredictionInterpretationBindingRecord`
- `MLInferencePredictionProvenanceBundle`

## Governance boundary

A prediction is a derived analytical output. It is not a source observation, evidence object, factual assertion, or research claim. Confidence and uncertainty metadata do not convert it into truth. Explainability and representation objects provide model-relative interpretation only.

Platform Core records contracts and provenance. Workspace/Lab/runtime providers execute inference, prediction, calibration, uncertainty estimation, OOD detection, and explanation computation.
