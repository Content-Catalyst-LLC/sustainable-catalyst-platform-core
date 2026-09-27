# Platform Core v3.59.0 — Neural Dataset, Feature & Transformation Provenance

- Adds governed raw-source, dataset-snapshot, partition, transformation-pipeline, feature-representation, and tensor-input objects.
- Extends v3.57 model/feature-schema contracts and v3.58 experiment/training lineage.
- Adds deterministic hashes for source, dataset, split-index, transformation implementation/state, feature, and tensor artifacts.
- Adds a leakage guardrail requiring fitted transform state to derive from a training partition.
- Keeps ingestion, splitting, transformation execution, fitted-state computation, and tensor creation outside Platform Core.
