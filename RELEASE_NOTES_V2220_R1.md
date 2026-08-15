# Platform Core v2.22.0 R1 — Resilience Migration Lineage & Promotion Repair

R1 is a release/promotion repair for v2.22.0. It does not change the v2.22.0 data-lifecycle runtime, migration 0025, database schema, evidence semantics, SDK version, WordPress plugin version, source registry, connector registry, or preservation behavior.

## Repair

- Repairs the inherited v2.21 multi-region migration rehearsal so a recorded `0023` state expects every migration after `0023`, rather than hard-coding only `0024`.
- Hardens the v2.22 lifecycle migration rehearsal so a recorded `0024` state likewise follows the current migration head, preventing the same defect at v2.23 and later.
- Adds an R1 contract scan that rejects active single-next-migration assertions in migration rehearsal tests.
- Adds the R1 repair/resume path to both installer and promotion syntax/preflight validation.

Core remains version `2.22.0` and migration head remains `0025`.
