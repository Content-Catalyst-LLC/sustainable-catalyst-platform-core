# Platform Core v4.1.0 — Context Object & Semantic Frame Foundation

## Purpose

v4.1.0 establishes the first governed contextual-semantics layer above the v4.0 Sustainable Catalyst Computational Research Core. It defines persistent context objects, semantic mentions, semantic frames, participant roles, interpretation provenance, ambiguity preservation, and immutable/supersedable semantic snapshots.

## Architectural rule

Core records semantic interpretation; it does not silently convert interpretation into evidence, entity identity, relationship fact, or truth.

Original-language source material remains primary. Translation, transliteration, embeddings, semantic mappings, and model-assisted interpretations remain derived representations with provenance.

## Governed objects

- `SourceContextBinding` — binds semantic context to a canonical source representation and source provenance.
- `ContextObject` — persistent sentence/paragraph/section/document/conversation/session/cross-document context boundary.
- `SemanticMention` — source-grounded mention with exact span and preserved unresolved-reference state.
- `SemanticFrame` — predicate/event/state/relation interpretation anchored to source text.
- `SemanticParticipant` — role binding between frames and mentions or proposition contexts.
- `SemanticInterpretation` — one governed interpretation package; Core does not select a globally preferred interpretation.
- `ContextSemanticProvenanceRecord` — method, producer, model/tool, review, and source lineage for semantic derivations.
- `ContextSemanticSnapshot` — immutable, supersedable context snapshot that does not certify truth or mutate graphs.

## Epistemic boundaries

v4.1.0 explicitly does **not**:

- execute a semantic parser;
- resolve pronouns or coreference;
- infer discourse/rhetorical relations;
- choose the best interpretation;
- treat a semantic frame as source truth;
- treat a mention as canonical entity identity;
- promote epistemic state through context selection; or
- mutate identity, relationship, evidence, or future context graphs.

Model-assisted and graph-assisted interpretations are advisory and require declared model provenance.

## Reference case

The bundled reference sentence pair intentionally includes the unresolved mention **“It”** in:

> The commission rejected the proposal after the ministry revised its estimate. It nevertheless remained politically viable.

v4.1.0 records the mention and viability frame but does not decide what “It” refers to. That resolution is reserved for the planned v4.3.0 Coreference, Reference & Referential Identity Intelligence release.

## Roadmap hooks

v4.1.0 prepares the governed object layer for:

- v4.2.0 — Discourse Structure & Rhetorical Semantics
- v4.3.0 — Coreference, Reference & Referential Identity Intelligence
- v4.4.0 — Temporal & Spatial Language Grounding
- v4.5.0 — Epistemic, Modal, Negation & Certainty Semantics
- v4.6.0 — Pragmatic Meaning, Speech Act & Communicative Intent
- v4.7.0 — Cross-Document Context Graph
- v4.8.0 — Multilingual Context & Semantic Alignment
- v4.9.0 — Contextual Semantic Evaluation & Benchmark Framework

## API

- `GET /public/v1/context-semantics/contract`
- `GET /v1/context-semantics/contract`
- `GET /v1/context-semantics/reference`
- `POST /v1/context-semantics/validate-context`
- `POST /v1/context-semantics/validate-frame`
- `POST /v1/context-semantics/validate-interpretation`
- `POST /v1/context-semantics/validate-bundle`

## Persistence

Database migration: **none**.
