# Platform Core v2.22.0 R1 — Resilience Migration Lineage & Promotion Repair Audit

## Observed promotion failure

The v2.22.0 macOS promotion reached the inherited v2.21 multi-region test file and failed because the `0023` rehearsal expected only migration `0024`, while the v2.22.0 migration engine correctly returned `0024` and `0025`.

## Repair boundary

R1 changes test and release-engineering lineage only. No runtime model, router, service, schema, public API, SDK contract, WordPress behavior, or migration definition is changed.

## Forward-compatibility repair

The v2.21 rehearsal now derives all expected migrations after `0023`. The v2.22 rehearsal derives all expected migrations after `0024`. The R1 validator scans active backend tests for single-next-migration equality assertions so the same brittle pattern cannot silently re-enter the promotion line.
