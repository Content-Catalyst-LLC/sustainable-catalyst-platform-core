# Platform Core v3.61.0 — Explainability & Model Interpretation Objects

Platform Core v3.61.0 adds framework-neutral, governed objects for preserving model explanations and interpretations under the same provenance discipline as the neural model, training, dataset, and evaluation layers introduced in v3.57.0–v3.60.0.

## Governed explanation objects

- feature attribution records with feature-level values, baselines, assumptions, computation refs, and artifact hashes
- saliency-map records with source/model lineage, coordinate space, shape, normalization, and immutable artifact hashes
- attention-weight explanations with explicit query/key/component provenance
- constrained counterfactual explanations with changed features, feasibility, constraints, output change, and distance metadata
- embedding-space explanations with representation/space refs, neighbors, clusters, projection artifacts, and computation refs
- descriptive model-comparison interpretations with aligned model/evaluation/checkpoint references and metric deltas
- reproducible explainability bundles that bind all explanations to the v3.60 evaluation/calibration/uncertainty bundle

## Governance semantics

Core explicitly records that feature attribution is not causation; attention weight is not explanatory proof; counterfactuals are model-relative rather than real-world causal effects; embedding proximity is not semantic fact; and saliency is not evidence.

## Architectural boundary

**Core defines and governs. Workspace computes. Lab experiments. Products consume.**

Core does not execute explainability algorithms, perturb inputs, generate counterfactuals, compute embeddings, infer causality from attribution, promote explanations to evidence, select a best model from explanation outputs, certify interpretation quality, or claim an explanation is true.

Contract: `sc.core.explainability-model-interpretation.v1`

Public contract endpoint: `GET /public/v1/ml-explainability/contract`
