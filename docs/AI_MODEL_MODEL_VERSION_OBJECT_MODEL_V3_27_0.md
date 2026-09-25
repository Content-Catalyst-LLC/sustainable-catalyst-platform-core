# Platform Core v3.27.0 — AI Model & Model-Version Object Model

## Objective

v3.27.0 begins the Sustainable Catalyst AI Engineering track by giving AI and
machine-learning models disciplined identity, versioning, provider metadata,
artifact lineage, dataset lineage and runtime lineage.

This release deliberately does not create a second generic model registry.
`AIModel` specializes and links existing research/predictive model concepts
through `research_model_ref` and `predictive_model_ref`.

## Contract

`sc.core.ai-model.v1`

## First-class objects

- AIModelProvider
- AIModelCapability
- AIModel
- AIModelArtifact
- AIModelVersion
- AIModelVersionBinding
- AIModelVersionComparison

## Stable model identity

`AIModel` represents the conceptual model across versions.

Examples:
- Random Forest urban-heat classifier
- scientific embedding model
- multimodal remote-sensing model
- domain language model
- forecasting model

## Immutable model-version identity

`AIModelVersion` represents a specific reproducible build/version.

It can bind:
- architecture;
- framework/version;
- parameter count;
- precision;
- context window;
- weights/config/tokenizer hashes;
- training/evaluation dataset versions;
- source commit;
- runtime environment;
- training job;
- model artifacts.

## Provider identity

Providers are explicit and typed:
- open source
- local
- self-hosted
- managed API
- remote compute

Provider identity is separate from model identity so the same conceptual model
can be served by different infrastructure without losing lineage.

## Integration with existing Core

AI models do not replace the existing research or predictive model layers.
They specialize them.

Future training and inference releases will bind:
- training jobs to `sc.core.computational-job.v1`;
- inference runs to exact `AIModelVersion`;
- evaluation runs to model versions and evaluation datasets;
- retrieval systems to embedding/reranker model versions.

## Boundaries

Core owns model identity, version identity, lineage, contracts and exchange.

Core does not:
- train models;
- execute inference;
- download weights;
- select a model autonomously;
- certify model quality.

Those execution responsibilities stay in Workspace/runtime providers and the
experimental/evaluation responsibilities stay in Lab.

## Next

Platform Core v3.28.0 — Dataset, Feature Set & Training Lineage.
