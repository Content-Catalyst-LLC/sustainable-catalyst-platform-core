# Platform Core v2.18.0 R1 Certification Migration Lineage & Promotion Repair Audit

## Incident

The v2.18.0 macOS promotion reached the inherited `backend/tests/test_production_certification_v2170.py` suite and failed the upgrade rehearsal.

The test claimed to model a database recorded at migration `0019`, but its fixture inserted every migration from the current `MIGRATIONS` registry except `0020`. Under v2.18.0 that incorrectly pre-recorded `0021` as already applied. The migration engine therefore correctly returned only `['0020']`, while the test expected `['0020', '0021']`.

## Corrective action

The fixture now records only migrations whose version is `<= '0019'`. From that truthful state the current engine must and does discover both `0020` and `0021`.

The v2.18.0 promotion and installer scripts are also corrected to syntax-check their own v2.18.0 installer rather than the prior v2.17.0 installer. The R1 repair contract prevents both regressions.

## Scope

No runtime or schema changes. Migration `0021`, observability/SLO behavior, APIs, SDK version, WordPress plugin version, governed sources and connectors remain unchanged.
