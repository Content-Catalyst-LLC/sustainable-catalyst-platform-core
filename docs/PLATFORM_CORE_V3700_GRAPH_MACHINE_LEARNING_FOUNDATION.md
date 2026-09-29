# Platform Core v3.70.0 — Graph Machine Learning Foundation

v3.70.0 begins the second neural wave by defining framework-neutral, provenance-bearing contracts for graph machine learning while preserving the separation between evidence and model inference.

## Foundation objects

- `GraphLearningSnapshot` freezes the node/edge universe used by a graph-ML task and binds it to a source graph fingerprint.
- `GraphEvidenceEdgeBinding` records only pre-validated evidence edges and their evidence/provenance references.
- `GraphFeatureBinding` and `GraphLabelBinding` preserve feature, transformation, supervision, and artifact lineage.
- `GraphMLTaskSpecification` declares node/edge/graph tasks, learning mode, leakage controls, and target relationship types.
- `GraphMLRuntimeContract` keeps graph computation outside Core and prevents graph runtimes from mutating the evidence graph.
- `GraphMLModelFoundation` reuses the existing v3.57 ML/neural model specification with the graph-neural-network family and architecture.
- `GraphMLRunProvenance` separates train/evaluate/infer/embed runs and preserves input/output lineage.
- `PredictedRelationship` is a non-factual inference envelope. It cannot be an evidence edge and requires separate validation before any promotion workflow.

## Non-negotiable evidence boundary

`GNN prediction != graph fact`.

A high score, probability, embedding similarity, link-prediction result, or model review state does not establish a factual relationship. Model output remains separate from the evidence graph. Later v3.73 and v3.76 releases may add richer candidate and validation workflows, but may not weaken this invariant.

## Architecture

Core defines and validates graph-ML objects. Workspace computes. Research Lab experiments. Downstream products consume. Core does not install graph frameworks, train models, run inference, compute embeddings, or mutate evidence graphs from model output.

## Roadmap

- v3.71.0 — Graph Embedding Objects & Runtime Contracts
- v3.72.0 — Node & Edge Classification Objects
- v3.73.0 — Link Prediction & Candidate Relationship Objects
- v3.74.0 — Graph Anomaly Detection
- v3.75.0 — Knowledge Graph Representation Learning
- v3.76.0 — Evidence Graph Neural Analysis & Validation Workflow

No database migration.
