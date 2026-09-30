# Platform Core v3.89.0 — Federated Evidence Graph Exchange Contract

Contract: `sc.core.federated-evidence-graph-exchange.v1`

This release adds a reference-first federation contract for exchanging governed evidence-graph object descriptors and reproducible investigation-package references between Core nodes. Remote epistemic state, source provenance, contradictions, hashes, and as-of context remain explicit.

## Boundaries

- Node trust does not establish content truth.
- Signature validity verifies the exchanged bytes/manifest relationship, not claim truth.
- Federation consensus does not establish truth.
- Schema compatibility does not establish semantic equivalence.
- Remote acceptance does not create local evidence.
- Remote references do not create local graph edges.
- Local validation is required before any promotion.
- No identity, relationship, or evidence graph mutation is performed by this contract.

No database migration is introduced.
