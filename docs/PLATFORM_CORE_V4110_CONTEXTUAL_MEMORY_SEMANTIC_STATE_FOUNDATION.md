# Platform Core v4.11.0 — Contextual Memory & Semantic State Foundation

Platform Core v4.11.0 extends the v4.10 Unified Semantic & Contextual Intelligence Runtime with governed, durable semantic-state identities that can be carried across document, runtime-session, investigation, and research-project scopes.

## Foundation

The release adds:

- explicit `ContextualMemoryScope` objects;
- stable `SemanticMemoryEntry` identities;
- immutable `SemanticStateRevision` history with exact predecessor lineage;
- governed review and supersession states;
- `MemoryCarryForward` records that retain predecessor qualifications;
- non-mutating `ContextualMemoryLink` objects;
- replayable memory provenance;
- reproducible `ContextualMemoryCheckpoint` objects; and
- immutable, supersedable `ContextualMemorySnapshot` objects.

## Reference state

The governed reference bundle carries six contextual states forward from v4.10:

1. unresolved referential alternatives for **“It”**;
2. Brussels source-place grounding with canonical geography deferred;
3. explicit ministry-source uncertainty;
4. candidate ministry/agency cross-document actor continuity;
5. culturally conditioned divergence across **治理 / governance / gobernanza**; and
6. the qualified-complete v4.10 runtime summary.

The actor-continuity memory includes two immutable revisions. The initial candidate revision is superseded, but retained. A reviewed successor remains unresolved and explicitly does not authorize canonical actor identity merging.

## Persistence boundary

v4.11 defines the semantics required for durable contextual memory. It does **not** make a storage engine authoritative and it does not require a new database migration. A later persistence adapter may store these objects, but storage, repetition, scope inheritance, and checkpointing do not increase the truth, authority, evidence validity, or identity status of the remembered interpretation.

No context graph, identity graph, evidence graph, or knowledge graph mutation is authorized by this contract.

## API

Private API prefix: `/v1/context-memory`

Public contract: `/public/v1/context-memory/contract`

Reference endpoints expose the bundle, scopes, memories, revision history, and project checkpoint. Validation endpoints accept revisions, checkpoints, and complete bundles.

## Roadmap

v4.11 prepares the Core for v4.12 Context Retrieval & Relevance Intelligence, v4.13 Claim Alignment / Agreement / Contradiction Intelligence, and the later unified contextual-reasoning runtime.
