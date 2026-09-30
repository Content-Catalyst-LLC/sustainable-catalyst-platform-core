# Platform Core v3.86.0 — Contradictory Identity & Relationship Resolution

Contract: `sc.core.contradictory-identity-relationship-resolution.v1`

## Purpose

v3.86 adds a governed resolution layer for contradictory identity and relationship assertions. It preserves every source-bound assertion and its provenance while allowing explicit criteria, independent review, qualification, partial resolution, supersession-for-handoff, and downstream validation routing.

## Non-negotiable boundaries

- Contradiction is not a falsity verdict.
- Majority agreement, source count, recency, and model confidence cannot establish truth.
- Resolution cannot silently prioritize one source.
- A disfavored or superseded assertion remains preserved with provenance and scope.
- An unresolved contradiction does not imply equal evidentiary support.
- Resolution decisions are not identity merges, relationship edges, evidence edges, or truth verdicts.

## Handoffs

Identity conflicts hand back to the v3.77 identity-resolution contract. Relationship-scope resolutions hand back to the v3.82 relationship-validation contract. No graph mutation occurs in v3.86.

Database migration: none.
