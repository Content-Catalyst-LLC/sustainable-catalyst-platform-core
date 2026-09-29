# Platform Core v3.71.0 — Graph Embedding Objects & Runtime Contracts

v3.71 extends the v3.70 Graph Machine Learning Foundation and v3.62 neural embedding contract with graph-specific embedding spaces, node/edge/graph embedding objects, external runtime contracts, vector-index lineage, and similarity-query provenance.

## Core invariants
- Embeddings are derived representations, not graph facts.
- Similarity is not evidence, identity, or relationship validation.
- Distance is not evidence strength.
- Every embedding is bound to a graph snapshot, model/runtime lineage, dimensionality and normalization contract.
- Core validates and exchanges embedding objects; Workspace or another governed runtime computes them.
- Similarity queries and embedding runtimes may not mutate the evidence graph.

## Roadmap
v3.71 prepares v3.72 node/edge classification, v3.73 link prediction/candidate relationships, v3.74 graph anomaly detection, v3.75 knowledge-graph representation learning, and v3.76 evidence-graph neural validation workflow.
