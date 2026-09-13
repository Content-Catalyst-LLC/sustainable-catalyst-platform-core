# Platform Core v2.36.1.1 Production Schema Compatibility Repair Audit

## Incident

The v2.36.1 Contabo deployment stopped during `Base.metadata.create_all()` because `sensitivity_results.visual_entity_id` referenced `sensitivity_studies.visual_entity_id`, but the deployed v2.36.0 `sensitivity_studies` table uses `id` as its primary key. The failed migration occurred before the production Core container was recreated.

## Root cause

The v2.36.1 source unintentionally redefined several existing v2.36.0 persistence models instead of extending them. Fresh-database tests did not expose the problem because all tables were created from the new incompatible model at once.

## Repair constraints

The patch must preserve:

- `sensitivity_studies.id`
- `sensitivity_factors.study_id`
- `sensitivity_measures`
- `ensembles.id`
- `ensemble_members.ensemble_id`
- `ensemble_statistics.ensemble_id`

No destructive migration, table rename, or production-data rewrite is permitted.

## Additive migration 0040

The only new persisted table is `uncertainty_compute_runs`. Its optional links use the existing v2.36.0 identifiers:

- `sensitivity_study_id -> sensitivity_studies.id`
- `ensemble_id -> ensembles.id`

## Upgrade verification

A true compatibility simulation creates a database using the v2.36.0 source, confirms the deployed column layout, then opens the same database using v2.36.1.1 and applies migrations. The check requires migration 0040 and `pending: []` and confirms the new table uses the existing identifiers.

## Runtime boundary

Core performs bounded statistical calculations only. Arbitrary model code remains an explicit Lab/Workbench/external-runtime handoff. Outputs remain estimates/results with provenance; there is no automatic truth promotion.
