# Platform Core v3.84.0 — Explainable Connection Paths & Evidence Chains

## Purpose

v3.84.0 adds a governed explanation layer over v3.83 analytical network snapshots. It records *how* two governed entities are connected through provenance-preserving path steps and source-bound evidence material without promoting analytical connectivity into relationship truth.

## Object model

- `ConnectionPathPolicy`
- `ConnectionPathStep`
- `ExplainableConnectionPath`
- `EvidenceChainItem`
- `PathContradictionMarker`
- `EvidenceChain`
- `AlternativeConnectionPathComparison`
- `PathBottleneckRecord`
- `ConnectionPathEvidenceSnapshot`
- `ExplainableConnectionPathsEvidenceChainsBundle`

## Architectural boundaries

A traversable path is an analytical explanation, not a factual or causal conclusion. Shortest path does not mean strongest evidence. Path length does not mean causal distance. Multiple paths do not automatically represent independent corroboration because routes can share sources, transformations, hypotheses, or upstream ancestry. Missing paths do not prove absence of a real-world relationship.

Every path step preserves the epistemic state of the v3.83 network edge projection. Documentary segments, documentary interpretations, and v3.82 relationship-evidence positions remain explicit references. Upstream reconciliation conflicts may be carried into `PathContradictionMarker` records and cannot be silently discarded.

v3.84.0 performs no relationship, evidence, or identity graph mutation. It creates no evidence edge and no canonical relationship fact.

## Public contract

`GET /public/v1/connection-paths/contract`

## Database migration

None.
