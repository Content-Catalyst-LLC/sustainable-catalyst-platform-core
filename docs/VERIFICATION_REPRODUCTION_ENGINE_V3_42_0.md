# Platform Core v3.42.0 — Verification & Reproduction Engine

## Objective

v3.42.0 adds the governed verification layer that turns reproducible
environments and cross-runtime workflows into auditable reproduction attempts.

Contract: `sc.core.verification-reproduction-engine.v1`

The engine specifies what should be reproduced, which evidence is required,
how outputs are compared, and whether the reproduction evidence satisfies the
declared criteria. Workspace or another execution host still performs the
actual execution.

## First-class objects

- VerificationCriterion
- ReproductionTarget
- ReproductionPlan
- VerificationEvidence
- CriterionVerificationResult
- ReproductionAttempt
- ReproductionVerificationReport
- ReproductionComparison
- ReproductionPackage

## Reproduction targets

A target can represent:
- an environment;
- a runtime job;
- a cross-runtime workflow;
- a statistical analysis;
- a scientific artifact;
- a complete research package.

Every target binds its source contract, source object and exact source
fingerprint.

## Verification criteria

The initial engine supports governed criteria for:
- exact content hashes;
- schema equivalence;
- runtime versions;
- dependency versions;
- row/column counts;
- numeric tolerance;
- categorical equivalence;
- statistical equivalence;
- workflow completion;
- artifact presence;
- result presence;
- externally implemented custom checks.

Criteria are either required or advisory.

## Evidence

Every criterion can be bound to explicit evidence. Evidence preserves:
- criterion identity;
- evidence kind;
- source reference;
- observed value;
- optional content hash;
- provenance.

Core does not declare a reproduction equivalent merely because an execution
completed.

## Verification report

`assemble_verification_report()` evaluates evidence against the plan.

Required criteria must pass for the report to pass. Advisory failures yield a
warning rather than silently converting the reproduction into success.

Missing required evidence fails the report.

## Reproduction comparison

The comparison layer combines:
- criterion verification;
- expected artifacts;
- produced artifacts;
- expected results;
- produced results.

Statuses are:
- equivalent;
- equivalent-with-warnings;
- non-equivalent;
- indeterminate.

These are reproduction-comparison states, not declarations of scientific truth
or validity.

## Reference proof

The reference package reproduces the R→Julia workflow assembled in v3.40 using
the environment package defined in v3.41.

It verifies:
- environment package hash;
- R runtime version;
- Julia runtime version;
- workflow completion;
- regression slope within tolerance;
- final scientific artifact presence.

The reference report passes all required criteria and the comparison is
`equivalent`.

This is a contract proof generated for release validation, not evidence that a
new live research reproduction was executed during local packaging.

## Scientific registry bridge

A complete reproduction package can be projected into the v3.38 Scientific
Artifact Registry. The reproduction-package fingerprint becomes the artifact
content hash.

## Product boundaries

Platform Core owns:
- reproduction targets;
- plans and criteria;
- evidence contracts;
- criterion evaluation;
- verification reports;
- reproduction comparisons;
- portable reproduction packages;
- lineage and exchange.

Workspace or another execution host owns:
- rebuilding the environment;
- launching jobs;
- executing workflow steps;
- collecting runtime outputs;
- executing external/custom comparators;
- acquiring evidence from live runs.

Core does not launch reproduction jobs, rebuild environments, rerun runtime
steps, declare equivalence without evidence, or certify scientific validity.

## Next mapped build

Platform Core v3.43.0 — Runtime Security, Isolation & Governance.
