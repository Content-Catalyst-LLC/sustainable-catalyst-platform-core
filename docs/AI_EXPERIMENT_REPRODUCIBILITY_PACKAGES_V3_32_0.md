# Platform Core v3.32.0 — AI Experiment & Reproducibility Packages

## Objective

v3.32.0 turns the AI Engineering object stack into reproducible experimental packages.

Contract: `sc.core.ai-experiment-reproducibility.v1`

The release connects exact model versions, datasets, prompts, retrieval contexts,
benchmarks, jobs, environments, inference runs and evaluation runs into a
controlled experiment definition and a portable reproduction package.

## First-class objects

- ExperimentalFactor
- ExperimentalCondition
- AIExperimentDefinition
- ExperimentRunBinding
- ReproducibilityRequirement
- ReproducibilityPackageArtifact
- AIExperimentReproducibilityPackage
- ReproductionObservation
- ReproductionAttempt
- ReproducibilityAssessment
- AIExperimentPackageBundle

## Experimental design

Experiments explicitly declare factors, conditions and a baseline. Conditions
bind assignments such as exact model versions, dataset versions, prompt
versions, retrieval contexts, hyperparameters, seeds, environments and
benchmarks.

## Run lineage

ExperimentRunBinding links each condition/replicate to the exact computational
jobs, runtime environments, model versions, inference runs, evaluation runs,
datasets and output artifacts that actually occurred.

## Reproducibility package

AIExperimentReproducibilityPackage freezes:
- experiment fingerprint;
- run bindings;
- source commit;
- strict/non-strict component requirements;
- expected component fingerprints;
- package artifacts/manifests.

This is intended to become the portable handoff format for Research Lab,
Workspace and scholarly publication/reproduction workflows.

## Reproduction

ReproductionAttempt records what was rerun and what was observed for every
declared requirement.

ReproducibilityAssessment records one of:
- exact
- compatible
- diverged
- incomplete

The assessment is a structured provenance object. Core does not certify
scientific validity or infer truth from the label.

## Boundaries

Research Lab executes experiments.
Workspace/runtime providers execute computational jobs.
Platform Core owns identity, lineage, reproducibility requirements and package
exchange contracts.

Core does not select a winning condition.

## AI Engineering sequence

v3.27 Models
→ v3.28 Training lineage
→ v3.29 Inference provenance
→ v3.30 Prompt/context/retrieval
→ v3.31 Evaluation/benchmarks
→ v3.32 Experiments/reproducibility

Next: Platform Core v3.33.0 — AI Error Analysis, Robustness & Failure Taxonomy.
