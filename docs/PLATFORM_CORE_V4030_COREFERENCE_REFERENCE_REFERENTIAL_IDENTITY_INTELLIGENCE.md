# Platform Core v4.3.0 — Coreference, Reference & Referential Identity Intelligence

Contract: `sc.core.coreference-reference-referential-identity-intelligence.v1`

## Purpose

v4.3.0 extends the v4.1 Context Object & Semantic Frame Foundation and v4.2 Discourse Structure & Rhetorical Semantics with a governed layer for resolving what linguistic references point to without collapsing reference resolution into canonical entity identity.

The release introduces first-class reference expressions, persistent referent anchors, ranked candidate sets, reviewed coreference links and chains, and explicit handoffs to the existing entity-resolution/identity graph contracts.

## Governing distinction

Core v4.3 distinguishes three separate questions:

1. **What text span is the reference expression?** — for example, `It`.
2. **What discourse referent does the expression point to?** — for example, the previously mentioned proposal.
3. **What canonical real-world entity, if any, does that referent identify?** — delegated to governed identity evidence and review.

A successful answer to question 2 does not automatically answer question 3.

## Reference case

The inherited text is:

> The commission rejected the proposal after the ministry revised its estimate. It nevertheless remained politically viable.

v4.1 preserved `It` as an unresolved reference and v4.2 added discourse/concession structure without resolving it. v4.3 adds a reviewed resolution overlay:

- `proposal` — rank 1, confidence 0.82, accepted by governed manual review;
- `estimate` — rank 2, confidence 0.12, preserved as a reviewed alternative;
- `rejection event` — rank 3, confidence 0.06, preserved as a reviewed alternative.

The original v4.1 `mention:it-unresolved` object is not rewritten. The resolution exists as a new v4.3 interpretation layer with provenance.

The generic source mentions `commission` and `ministry` remain **deferred** for canonical identity binding. Source wording alone is insufficient to determine which real-world institutions they refer to.

## New governed objects

- `ReferenceExpression`
- `ReferentAnchor`
- `ReferentCandidate`
- `ReferentCandidateSet`
- `CoreferenceLink`
- `CoreferenceChain`
- `ReferentialIdentityBinding`
- `ReferenceResolutionProvenanceRecord`
- `ReferentialInterpretation`
- `ReferentialIdentitySnapshot`
- `CoreferenceReferentialIdentityBundle`

## Safety and epistemic boundaries

- Core does not autonomously select referents.
- Resolution scores do not establish identity or truth.
- Coreference links do not establish canonical entity identity.
- Accepted v4.3 resolutions do not rewrite v4.1/v4.2 source objects.
- Generic names/descriptions do not establish canonical identity.
- Referential identity bindings cannot merge entities.
- Identity, relationship, evidence, and context graphs are not mutated by this contract.
- Canonical identity binding remains subject to upstream identity evidence and governed review.

## API

- `GET /v1/referential-identity/contract`
- `GET /public/v1/referential-identity/contract`
- `GET /v1/referential-identity/reference`
- `POST /v1/referential-identity/validate-reference-expression`
- `POST /v1/referential-identity/validate-candidate`
- `POST /v1/referential-identity/validate-candidate-set`
- `POST /v1/referential-identity/validate-coreference-link`
- `POST /v1/referential-identity/validate-coreference-chain`
- `POST /v1/referential-identity/validate-identity-binding`
- `POST /v1/referential-identity/validate-interpretation`
- `POST /v1/referential-identity/validate-bundle`

## Roadmap handoff

v4.3 establishes the referential layer required by:

- v4.4 Temporal & Spatial Language Grounding;
- v4.5 Epistemic, Modal, Negation & Certainty Semantics;
- v4.6 Pragmatic Meaning, Speech Act & Communicative Intent;
- v4.7 Cross-Document Context Graph;
- v4.8 Multilingual Context & Semantic Alignment;
- v4.9 Contextual Semantic Evaluation & Benchmark Framework.

## Database

No new database migration.
