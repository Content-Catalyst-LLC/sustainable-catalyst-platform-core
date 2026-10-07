# Platform Core v4.7.0 — Cross-Document Context Graph

Platform Core v4.7.0 introduces a persistent, inspectable context graph that can connect governed semantic objects across multiple documents without flattening source-specific meaning, provenance, uncertainty, or review state.

## Scope

The v4.7 contract adds first-class document bindings, typed context nodes, typed context edges, cross-document context threads, graph provenance, reviewed graph interpretations, and immutable/supersedable graph snapshots. Nodes can reference governed v4.1–v4.6 objects including semantic mentions, referents, temporal/spatial anchors, propositions, epistemic assessments, speech acts, and communicative intents.

## Reference graph

The reference graph spans three predecessor documents:

1. the v4.1 contextual-semantics reference document,
2. the v4.4 temporal/spatial grounding reference document, and
3. the v4.6 pragmatic public-hearing reference document.

It preserves exact predecessor object references for `mention:ministry`, `mention:proposal`, the Brussels source-place anchor, the 2025/2026 temporal anchors, the agency speaker participant, the warning speech act, and the alert communicative intent.

Two cross-document continuity hypotheses are intentionally left unresolved:

- `mention:ministry` ↔ `participant:agency-speaker` as a candidate actor-continuity relation;
- `mention:proposal` ↔ `content:measure-may-reduce-emissions` as a candidate topic-continuity relation.

Neither hypothesis establishes canonical identity, entity merge, claim equivalence, evidence validity, or source authority.

## Architectural boundaries

The Context Graph is a contextual index, not a truth store. Graph density is not confidence. Accepted edges certify reviewed contextual structure only. Canonical identity still requires the governed identity authority; evidence validity still requires the evidence workflow. v4.7 does not automatically mutate the identity graph, evidence graph, or knowledge graph and does not rewrite predecessor semantic objects.

## API

- `GET /public/v1/context-graph/contract`
- `GET /v1/context-graph/contract`
- `GET /v1/context-graph/reference`
- `POST /v1/context-graph/validate-edge`
- `POST /v1/context-graph/validate-thread`
- `POST /v1/context-graph/validate-interpretation`
- `POST /v1/context-graph/validate-bundle`

Database migration: **none**.
