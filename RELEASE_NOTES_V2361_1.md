# Platform Core v2.36.1.1 — Uncertainty Compute Runtime Integration · Production Schema Compatibility Repair

## Purpose

This patch repairs the v2.36.1 production deployment failure without changing the v2.36.0 uncertainty/sensitivity/ensemble persistence contract. v2.36.1 accidentally replaced existing table identities (`sensitivity_studies.id`, `sensitivity_factors.study_id`, `sensitivity_measures`, `ensembles.id`) with an incompatible visual-entity schema. PostgreSQL correctly rejected a new foreign key targeting a non-existent `sensitivity_studies.visual_entity_id` column.

## Repair

- Restores the exact v2.36.0 ORM and API contracts for uncertainty definitions, sensitivity studies/factors/measures, ensembles/members/statistics.
- Keeps migration 0040 additive.
- Adds only `uncertainty_compute_runs` for persisted compute-runtime provenance.
- `uncertainty_compute_runs.sensitivity_study_id` references `sensitivity_studies.id`.
- `uncertainty_compute_runs.ensemble_id` references `ensembles.id`.
- Preserves deterministic Monte Carlo and Latin Hypercube sampling.
- Preserves Sobol design/index helpers and Morris design/elementary-effect helpers.
- Preserves ensemble weight normalization/statistics and empirical exceedance probability estimation.
- Preserves Lab/Workbench/external runtime handoff manifests.
- Arbitrary research-model execution and automatic truth promotion remain outside Core.

## Verification

The release adds a production-schema compatibility test and is validated against a database first created by the v2.36.0 codebase, then upgraded with v2.36.1.1. Migration 0040 applies with `pending: []` while the v2.36.0 tables remain unchanged.
