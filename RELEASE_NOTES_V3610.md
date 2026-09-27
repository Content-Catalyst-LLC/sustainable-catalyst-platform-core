# Platform Core v3.61.0 — Explainability & Model Interpretation Objects

- Adds governed feature-attribution, saliency, attention, counterfactual, embedding-space, and model-comparison interpretation objects.
- Binds explanations to v3.60 evaluation/checkpoint/dataset-partition lineage and preserves the v3.60 evaluation bundle fingerprint.
- Adds deterministic explanation-bundle fingerprints and artifact/computation references for reproducibility.
- Encodes method-specific interpretation boundaries: attribution is not causation, attention is not proof, counterfactuals are model-relative, embedding proximity is not semantic fact, and saliency is not evidence.
- Keeps all explainability computation, perturbation, embedding computation, causal inference, model selection, interpretation certification, and evidence promotion outside Platform Core.
- No database migration is introduced by this release.
