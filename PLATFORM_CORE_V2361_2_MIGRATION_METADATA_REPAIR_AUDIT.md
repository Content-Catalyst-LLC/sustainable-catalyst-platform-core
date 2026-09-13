# Platform Core v2.36.1.2 Migration Metadata Length Repair Audit

## Incident

Production PostgreSQL stores migration descriptions in `schema_migrations.description VARCHAR(300)`. The v2.36.1.1 `0040` description exceeded that limit, causing the migration ledger insert to fail after SQLAlchemy had already created the additive compute table.

## Repair

- Migration `0040` keeps the same version and schema semantics.
- Its description is reduced to 239 characters.
- The release gate inspects the SQLAlchemy `SchemaMigration.description` length and fails if any migration description exceeds it.
- The Contabo deployer accepts either a pristine pre-0040 database or the safe partial state where `uncertainty_compute_runs` already exists with the expected foreign-key columns while `0040` is absent from `schema_migrations`.

## Invariants

- `sensitivity_studies.id` remains canonical.
- `sensitivity_factors.study_id` remains canonical.
- `sensitivity_measures` remains unchanged.
- `ensembles.id` remains canonical.
- `uncertainty_compute_runs.sensitivity_study_id` references `sensitivity_studies.id`.
- `uncertainty_compute_runs.ensemble_id` references `ensembles.id`.
- No automatic truth promotion is introduced.
