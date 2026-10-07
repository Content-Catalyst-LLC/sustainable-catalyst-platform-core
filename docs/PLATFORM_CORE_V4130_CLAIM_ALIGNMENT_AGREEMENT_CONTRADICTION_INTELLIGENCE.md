# Platform Core v4.13.0 — Claim Alignment, Agreement & Contradiction Intelligence

## Purpose

v4.13.0 adds a governed comparison layer for claims recovered through the v4 contextual-semantic pipeline. It distinguishes claim alignment from truth adjudication and treats agreement and contradiction as contextual semantic relations whose validity depends on scope, polarity, modality, attribution, language lineage, and unresolved identity.

## Contract

`sc.core.claim-alignment-agreement-contradiction-intelligence.v1`

Predecessor: `sc.core.context-retrieval-relevance-intelligence.v1` (v4.12.0).

## Core objects

- `ClaimSourceContext`
- `ClaimUnit`
- `ClaimComparisonQuery`
- `ClaimAlignmentSignal`
- `ClaimComparisonPair`
- `ClaimRelationAssessment`
- `ClaimComparisonProvenanceRecord`
- `ClaimComparisonSnapshot`
- `ClaimAlignmentAgreementContradictionBundle`

## Relation taxonomy

- agreement
- qualified agreement
- partial agreement
- contradiction
- apparent contradiction
- scope mismatch
- distinct claim
- unresolved

Strict contradiction requires comparable claim scope and modality in addition to polarity conflict. Opposite wording or opposite polarity alone is insufficient.

## Reference fixture

The governed reference bundle includes seven claims and six pairwise comparisons spanning the v4.5 epistemic fixture, v4.6 pragmatic fixture, v4.8 multilingual fixture, and controlled v4.13 comparison sources. It demonstrates strict contradiction, apparent contradiction, qualified agreement, partial agreement, and cross-language contextual agreement.

## Epistemic boundaries

A contradiction assessment does not identify which claim is false. Agreement does not establish evidence validity. Agreement count does not increase truth. Source majority does not establish truth. Alignment is not credibility. Contradiction is not deception. No context-, identity-, evidence-, or knowledge-graph mutation is authorized.

## Database migration

None.
