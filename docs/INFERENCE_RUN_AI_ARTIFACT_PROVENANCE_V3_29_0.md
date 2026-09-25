# Platform Core v3.29.0 — Inference Run & AI Artifact Provenance

## Objective

v3.29.0 gives Sustainable Catalyst a governed provenance model for AI inference.

The release answers:

- Which exact model version generated this output?
- Which computational job executed the inference?
- Which runtime environment was used?
- Which provider/model identifier was used?
- Which exact inputs and parameter set were supplied?
- Which execution result produced the output?
- Which artifacts were generated?
- Which source inputs contributed to each artifact?
- What usage and latency were observed?

## Contract

`sc.core.ai-inference-provenance.v1`

Depends on:

- `sc.core.ai-model.v1`
- `sc.core.ai-training-lineage.v1`
- `sc.core.computational-job.v1`
- `sc.core.execution-environment-provenance.v1`

## First-class objects

- AIInferenceInput
- AIInferenceParameterSet
- AIArtifactProvenance
- AIInferenceUsage
- AIInferenceRun
- AIInferenceRunBundle
- AIInferenceComparison

## Inference provenance

An inference run binds:

AIModelVersion
→ ComputationalJob
→ ExecutionResult
→ RuntimeEnvironment
→ Provider
→ Inputs
→ ParameterSet
→ AI artifacts

This provides the forward lineage from an exact model version to generated
predictions, embeddings, rankings, text, images, tables, arrays, reports and
other AI-derived artifacts.

## Artifact provenance

AIArtifactProvenance does not replace Core's generic RuntimeArtifact model.

It specializes AI-output semantics while retaining optional:
- runtime_artifact_ref;
- execution_result_ref;
- content SHA-256;
- source-input refs.

This preserves one common artifact fabric across scientific computation and AI.

## Prompt/RAG preparation

`prompt_version_ref` and `retrieval_context_ref` are present only as optional
references in this release. Their formal object models arrive in v3.30.0.

v3.29.0 therefore establishes the inference spine without prematurely defining
prompt or retrieval semantics.

## Usage

Observed usage may include:
- tokens;
- rows;
- samples;
- images;
- seconds;
- bytes;
- requests;
- latency;
- compute time;
- monetary cost.

Usage is observational metadata and is intentionally excluded from stable
inference-run identity.

## Boundaries

Core records inference identity, provenance and artifact lineage.

Core does not:
- execute inference;
- select models autonomously;
- generate artifacts;
- determine provider pricing;
- certify model quality.

Workspace/runtime providers execute inference. Lab evaluates model behavior.
Core makes the resulting process traceable and reproducible.

## Next

Platform Core v3.30.0 — Prompt, Context & Retrieval Object Model.
