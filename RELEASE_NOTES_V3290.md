# Platform Core v3.29.0 — Inference Run & AI Artifact Provenance

Added:
- `sc.core.ai-inference-provenance.v1`
- AIInferenceInput
- AIInferenceParameterSet
- AIArtifactProvenance
- AIInferenceUsage
- AIInferenceRun
- AIInferenceRunBundle
- AIInferenceComparison
- exact AI model-version binding
- computational-job binding
- execution-result binding
- runtime-environment binding
- provider identity binding
- inference-input fingerprints
- parameter-set fingerprints
- AI artifact content hashes
- source-input → artifact lineage
- usage/latency metadata
- optional prompt/retrieval refs for v3.30 integration
- public inference-provenance contract endpoint
- 22 focused release tests

No database migration is introduced.

Next:
Platform Core v3.30.0 — Prompt, Context & Retrieval Object Model.
