# Platform Core v3.85.0 — Multi-Hop Research & Investigation Graph Reasoning

Contract: `sc.core.multi-hop-research-investigation-graph-reasoning.v1`

## Purpose

v3.85 adds a governed reasoning layer above v3.84 explainable paths and evidence chains. It can trace bounded, multi-hop analytical routes across entities, connection paths, evidence chains, documentary interpretations, candidates, hypotheses, and source context while preserving provenance and epistemic state.

## Core objects

- `MultiHopReasoningPolicy`
- `MultiHopReasoningQuery`
- `ReasoningHop`
- `ReasoningBranch`
- `ReasoningInferenceStep`
- `ReasoningContradictionPropagation`
- `SourceIndependenceAssessment`
- `ReasoningStoppingDecision`
- `MultiHopReasoningTrace`
- `MultiHopReasoningSnapshot`

## Epistemic boundaries

A traversable chain is an analytical explanation, not proof. Reaching a target does not establish an endpoint relationship. Hop count is not evidence strength or causal distance. Analytical confidence is not a probability of truth. Multiple paths do not create independent corroboration when they reuse the same provenance. Contradictions propagate as explicit qualifications and do not automatically invalidate a chain or prove the opposite. Candidate and hypothesis objects remain candidates and hypotheses throughout traversal.

## Runtime boundary

v3.85 creates no relationship edge, evidence edge, identity edge, canonical equivalence, or graph mutation. It produces reproducible reasoning traces for separate review and validation.

## Database migration

None.
