# Platform Core v3.79.0 — Probabilistic Record Linkage & Entity Matching Objects

Contract: `sc.core.probabilistic-record-linkage-entity-matching.v1`.

This release governs probabilistic record-linkage inputs and outputs while leaving identity resolution and merge authorization to the v3.77 evidence/review workflow. It models linkage features, blocking rules, candidate pairs, pairwise comparisons, model/calibration lineage, probability records, threshold policies, review decisions, and evaluation summaries.

## Non-negotiable boundaries

- Match probability is not identity fact.
- Nonmatch probability is not proof of distinct identity.
- Feature agreement and block membership are not identity evidence.
- Calibration does not convert probability into fact.
- Threshold crossing cannot authorize merge.
- Linkage output cannot create a canonical equivalence edge.
- Platform Core defines contracts; compute runtimes execute linkage models.
- Identity graph mutation remains a separate downstream audited action.

Database migration: none.
