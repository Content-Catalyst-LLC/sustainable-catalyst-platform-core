# Platform Core v3.59.0 — Neural Dataset, Feature & Transformation Provenance

v3.59.0 adds governed data-side lineage for machine-learning and neural workflows:

`raw source → dataset snapshot → partition → transformation pipeline → feature representation → tensor/model input`

The contract binds these objects to the v3.57 model feature schema and training plan, and carries v3.58 experiment/training-run references forward without moving data processing into Core.

## Reproducibility

The model records content hashes for raw sources, dataset snapshots, partition indices, transformation implementations, fitted transform state, feature representations, and tensor artifacts. It also records runtime/environment/job/code/seed references where applicable.

## Leakage guardrail

A transformation step that carries fitted state must identify the partition on which that state was fitted. The v3.59 bundle rejects fitted transform state derived from validation/test partitions; fitted state must resolve to a training partition.

## Boundary

Core records and validates lineage. Workspace computes and materializes data. Lab experiments. Core does not ingest raw data, execute splits, apply transformations, fit transform state, create tensors, or accept arbitrary executable transform payloads.
