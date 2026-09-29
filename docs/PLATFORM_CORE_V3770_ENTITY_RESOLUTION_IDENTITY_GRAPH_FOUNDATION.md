# Platform Core v3.77.0 — Entity Resolution & Identity Graph Foundation

## Purpose

v3.77.0 begins the Entity, Evidence & Connection Intelligence block. It defines governed identity objects without allowing automated entity resolution to overwrite source records or silently collapse distinct entities.

## Core object model

- `CanonicalEntityRecord` — governed canonical identity container.
- `EntityAlias` — provenance-bound names, variants, abbreviations, historical names, translations and transliterations.
- `ExternalIdentifierAssertion` — source-bound external identifiers with verification state and provenance.
- `SourceEntityIdentityAssertion` — what a particular source says an entity is.
- `IdentityEvidenceItem` — provenance-bearing non-model identity evidence.
- `EntityResolutionPolicy` — governance requirements for entity resolution.
- `CandidateEntityMatch` — a non-factual candidate equivalence between two entity records.
- `IndependentIdentityReview` — independent review grounded in identity evidence.
- `IdentityMutationAuthorization` — governed merge/split authorization that does not itself mutate the graph.
- `IdentityResolutionAuditRecord` — append-only resolution audit event.
- `EntityIdentityGraphSnapshot` — immutable identity-graph state.

## Invariants

1. Match probability is not identity fact.
2. Same name is not identity fact.
3. Alias equality is not identity proof.
4. A shared identifier requires provenance and review; it cannot bypass governance.
5. A source identity assertion is not canonical identity.
6. A candidate match is not a canonical equivalence edge.
7. Automated resolution cannot silently merge or split entities.
8. Model scores cannot count as identity evidence or authorize identity mutation.
9. An authorized merge/split is a downstream audited handoff, not an in-place graph mutation.
10. The identity graph is distinct from the evidence graph, while remaining linkable to it.

## Reference workflow

The synthetic fixture contains two organization records that share a provenance-bearing synthetic registry identifier. A match model produces a 0.97 candidate probability. Two independent reviewers evaluate two identity evidence items. A merge is authorized, but the immutable snapshot remains pre-mutation and `actual_identity_graph_mutation_performed=false`.

## Roadmap

v3.77.0 establishes the foundation for:

- v3.78.0 Temporal Identity, Alias & Name Variant Intelligence
- v3.79.0 Probabilistic Record Linkage & Entity Matching Objects
- v3.80.0 Cross-Source Entity Reconciliation & Identity Provenance

Database migration: none.
