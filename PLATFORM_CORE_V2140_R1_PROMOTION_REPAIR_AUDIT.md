# Platform Core v2.14.0 R1 — Promotion Repair Audit

## Failure isolated

The original installer completed the v2.14.0 release contract, 347-file manifest verification, test-file execution and migrations through 0017. It then exited at the inherited streaming/reliability validator because that validator required `settings.version == 2.13.0` even though the current release correctly reported 2.14.0.

## R1 corrections

R1 removes exact-current-release coupling from four inherited validators and replaces it with minimum feature-version gates. This prevents the same defect from recurring on later Core releases while still rejecting a Core version older than the feature being validated.

R1 also adds a promotion-repair contract that verifies every downstream validator target exists, all four inherited gates are forward-compatible, the push/deploy scripts execute the repair contract, the manifest remains release 2.14.0, and migration lineage remains through 0017.

## Scope boundary

No cross-product exchange runtime behavior, public API behavior, database schema, migration, governed source definition, connector definition, WordPress runtime, or SDK API is changed by R1.
