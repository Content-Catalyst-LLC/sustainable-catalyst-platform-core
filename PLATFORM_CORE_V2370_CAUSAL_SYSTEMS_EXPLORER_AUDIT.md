# Platform Core v2.37.0 — Causal Systems Explorer Audit

## Baseline
- Direct predecessor: Platform Core v2.36.1.2 (deployed and verified).
- Migration 0040 remains the repaired 239-character uncertainty-compute ledger entry.
- Migration 0041 is additive and its description is 282 characters, within the production `schema_migrations.description VARCHAR(300)` contract.
- The v2.36.1.2 migration-description guard and partial-0040 recovery regression tests remain active.

## Causal capability
- Governed causal graphs, variables, directed relationships, interventions, identification records, effect estimates, diagnostics, and provenance.
- Deterministic DAG validation, ancestry/descendancy and directed-path reasoning.
- Conservative adjustment-set candidates are explicitly labeled candidate-only.
- Explicit assumptions are required before an identification record may claim `identified` status.
- Effect estimates require attributable execution or provenance.
- Lab, Workbench, and explicit external runtimes remain available for statistical/causal estimation handoffs.

## Safety and epistemic boundary
- No silent conversion of association to causation.
- No automatic causal identification.
- No automatic effect estimation.
- No arbitrary research-model execution by Core.
- No automatic promotion of computational results to truth.

## Validation
- 91/91 release-critical tests passed in bounded groups.
- True v2.36.1.2 -> v2.37.0 database upgrade simulation passed with migration 0041 as head and `pending=[]`.
- Repaired uncertainty persistence contracts remained intact during the upgrade simulation.
- Release contract, secret scan, Python compilation, PHP lint, JavaScript syntax, and shell syntax passed before source freeze.
