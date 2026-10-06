# Platform Core v4.4.0 — Temporal & Spatial Language Grounding

Contract: `sc.core.temporal-spatial-language-grounding.v1`

v4.4.0 extends the v4.1–v4.3 contextual-semantic stack with explicit, provenance-preserving grounding of time and place language.

## Core objects

- `GroundingSourceExcerpt` preserves immutable source text used by grounding examples.
- `TemporalExpression` and `SpatialExpression` preserve exact linguistic surface forms and source spans.
- `TemporalAnchor` and `SpatialAnchor` represent normalized candidate anchors without turning normalization into source fact.
- `GroundingCandidate` and `GroundingCandidateSet` preserve alternatives, rank, confidence, review state, and provenance.
- `TemporalGrounding` and `SpatialGrounding` bind reviewed expressions to anchors while retaining uncertainty and governance boundaries.
- `TemporalRelationGrounding` lifts reported temporal relations from discourse semantics without claiming real-world chronology.
- `TemporalSpatialGroundingInterpretation` and `TemporalSpatialGroundingSnapshot` provide reproducible interpretation/snapshot lineage.

## Reference cases

The v4.4 reference bundle uses a new immutable excerpt:

> In 2025, the ministry opened an office in Brussels. The commission met there the following year.

It demonstrates:

- absolute temporal grounding: `2025` → calendar year 2025;
- relative temporal grounding: `the following year` → derived 2026 anchor while preserving the `+P1Y` derivation from 2025;
- named-place grounding: `Brussels` → a source-place anchor, not a canonical gazetteer identity;
- spatial deixis: `there` → the prior Brussels source-place anchor;
- inherited discourse grounding: v4.2 `after` → reported `revision before rejection` event ordering.

## Governance boundaries

Core does not autonomously geocode named places, treat grounding scores as truth probabilities, flatten relative-time derivation history, treat a source place name as canonical geographic identity, or promote reported temporal order into world truth.

No temporal, spatial, identity, evidence, relationship, or context graph mutation is performed by the v4.4 reference contract.

## Database

No migration.
