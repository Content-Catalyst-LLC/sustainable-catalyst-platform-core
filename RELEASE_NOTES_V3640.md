# Platform Core v3.64.0 — Neural Model Registry & Reproducible Model Packages

## Summary

v3.64.0 completes the initial Platform Core neural-intelligence foundation by making governed models registry-addressable and packageable as reproducible research objects.

## Added

- Governed model registry entries bound to model specification, model version, training run, checkpoint, inference plan, evaluations, and representation models.
- Immutable model artifact records with SHA-256 integrity.
- Runtime/environment requirement records with lockfile identity.
- First-class intended-use and limitation records.
- Deterministic reproducibility manifests spanning v3.57–v3.63 lineage fingerprints.
- Portable reproducible model packages that bind model artifacts, runtime requirements, schemas, evaluation, calibration/uncertainty, explainability/representation, intended use, and limitations.
- Public contract endpoint: `/public/v1/ml-model-registry/contract`.
- Private reference endpoint: `/api/v1/ml-model-registry/reference`.

## Governance boundaries

- Registration does not certify model quality.
- Packaging does not guarantee identical reproduction.
- Model packages are not evidence.
- Intended-use metadata does not authorize autonomous action.
- Platform Core does not train models, run inference, execute packages, install dependencies, download artifacts, select a best model, certify quality, or certify reproducibility.

## Database

No database migration is required.
