# Platform Core v3.92.0 — Unified Entity & Evidence Query API

Contract: `sc.core.unified-entity-evidence-query-api.v1`

Provides one governed query surface over Core entity/evidence capabilities while preserving each result's originating capability/contract, source object reference, epistemic state, validation state, and provenance. Retrieval scores represent relevance only and are not evidence strength or probability of truth. Candidate, hypothesis, unresolved, analytical, and remote-reference states are not promoted by querying. Remote references require local validation. Query execution is non-mutating.

No database migration.
