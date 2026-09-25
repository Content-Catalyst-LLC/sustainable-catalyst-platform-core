# Platform Core v3.28.0 — Dataset, Feature Set & Training Lineage

Added:
- `sc.core.ai-training-lineage.v1`
- stable DatasetIdentity objects
- immutable/content-addressed DatasetVersion objects
- DatasetVersionBinding
- DatasetArtifact
- versioned FeatureSet
- FeatureDefinition
- ordered TransformationStep lineage
- DatasetSplit provenance
- random-seed capture
- hyperparameter capture
- training-job binding
- runtime-environment binding
- AI model-version binding
- TrainingLineageBundle
- public training-lineage contract endpoint
- 18 focused release tests

No database migration is introduced.

Core does not duplicate dataset materialization/storage responsibilities.

Next:
Platform Core v3.29.0 — Inference Run & AI Artifact Provenance.
