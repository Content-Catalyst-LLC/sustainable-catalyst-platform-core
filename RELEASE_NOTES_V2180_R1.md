# Platform Core v2.18.0 R1 — Certification Migration Lineage & Promotion Repair

R1 is a release/promotion repair for v2.18.0. It does not change the v2.18.0 observability runtime, public API, migration 0021, database schema, evidence semantics, SDK version, WordPress plugin version, source registry, connector registry, or SLO behavior.

## Repair

- Corrects the inherited v2.17 production-certification migration rehearsal so a recorded `0019` state contains only migrations `0001` through `0019`.
- The repaired rehearsal now correctly expects the current migration engine to apply `0020` and `0021` in order.
- Removes the stale v2.17 installer syntax target from v2.18.0 promotion and validates the current v2.18 installer plus the R1 repair/resume wrapper.
- Adds an R1 promotion-repair contract validator.

Core remains version `2.18.0`.
