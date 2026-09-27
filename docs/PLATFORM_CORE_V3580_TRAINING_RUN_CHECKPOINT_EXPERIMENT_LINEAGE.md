# Platform Core v3.58.0 — Training Run, Checkpoint & Experiment Lineage

Canonical lineage: `Experiment → Training Run → Epoch → Checkpoint → Evaluation`. Every run binds back to the v3.57 model specification and training plan, dataset versions, runtime binding, execution environment, computational job, code revision/content hash, resolved parameters, and random seed state.

## First-class objects

- `MLSeedState`
- `MLCodeReference`
- `MLTrainingEpochRecord`
- `MLCheckpointRecord`
- `MLEvaluationRecord`
- `MLTrainingRunRecord`
- `MLExperimentRecord`
- `MLTrainingLineageBundle`

## Boundary

**Core records and validates lineage. Workspace computes. Lab experiments. Products consume.** Core does not train models, run inference, write weights, install ML packages, choose checkpoints, promote models, certify quality, or automatically convert evaluation output into evidence.
