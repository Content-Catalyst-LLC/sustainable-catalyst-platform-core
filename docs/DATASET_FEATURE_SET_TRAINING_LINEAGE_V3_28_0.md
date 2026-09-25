# Platform Core v3.28.0 — Dataset, Feature Set & Training Lineage

## Objective

v3.28.0 adds the lineage layer between source data and an AI model version.

The release answers:

- Which exact dataset version trained this model?
- Which feature set was used?
- How were features transformed?
- Which train/evaluation split was used?
- Which random seed and hyperparameters were used?
- Which runtime environment executed the pipeline?
- Which computational job produced the model?
- Which model version did that job create?

## Contract

`sc.core.ai-training-lineage.v1`

Depends on:

- `sc.core.ai-model.v1`
- `sc.core.computational-job.v1`
- `sc.core.execution-environment-provenance.v1`

## First-class objects

- DatasetIdentity
- DatasetArtifact
- DatasetVersion
- DatasetVersionBinding
- FeatureDefinition
- FeatureSet
- TransformationStep
- DatasetSplit
- TrainingLineage
- TrainingLineageBundle

## Dataset identity vs version identity

A dataset has a stable conceptual identity.

Each DatasetVersion captures a reproducible version and can carry:

- content SHA-256;
- schema SHA-256;
- row/column counts;
- parent version;
- runtime environment;
- creation job;
- data/schema/label/split/statistics artifacts.

This is not a second disconnected dataset registry. These objects are the
Core lineage semantics for dataset versions that Workspace, Knowledge Library,
Catalyst Data or external systems may materialize.

## Feature lineage

FeatureSet binds a dataset version to explicit FeatureDefinition objects.

TransformationStep records ordered preprocessing/feature engineering with:
- operation;
- method reference;
- input/output refs;
- parameters;
- code hash;
- runtime environment;
- computational job.

## Training lineage

TrainingLineage binds:

DatasetVersion(s)
→ FeatureSet
→ DatasetSplit(s)
→ TransformationStep(s)
→ random seed
→ hyperparameters
→ runtime environment
→ ComputationalJob
→ AIModelVersion
→ output artifacts

This becomes the direct provenance spine for the AI Engineering track.

## Boundaries

Core records contracts and lineage.

Core does not:
- load/materialize datasets;
- execute preprocessing;
- train models;
- choose training data autonomously.

Workspace and runtime providers execute pipelines. Knowledge Library and
Catalyst Data may supply data. Lab evaluates the resulting models.

## Next

Platform Core v3.29.0 — Inference Run & AI Artifact Provenance.
