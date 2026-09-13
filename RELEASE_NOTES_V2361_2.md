# Platform Core v2.36.1.2 — Migration Metadata Length Repair

v2.36.1.2 is a production deployment repair for the v2.36.1.1 Uncertainty Compute Runtime Integration.

The v2.36.1.1 backend reached migration `0040`, created the additive `uncertainty_compute_runs` table, and then PostgreSQL rejected the migration-ledger insert because the human-readable migration description exceeded the existing `schema_migrations.description VARCHAR(300)` contract.

This release:

- shortens the `0040` migration description to 239 characters;
- adds an automated gate requiring every migration description to fit the production storage column;
- preserves the v2.36.0 uncertainty/sensitivity/ensemble persistence contract;
- preserves all v2.36.1.1 uncertainty-compute behavior;
- supports recovery when `uncertainty_compute_runs` was already created but `0040` was not recorded;
- keeps arbitrary model execution external to Platform Core and preserves the no-automatic-truth-promotion boundary.

No scientific or statistical algorithm is removed or changed by this patch.
