# Platform Core v3.62.0 — Neural Embedding & Representation Intelligence

Platform Core v3.62.0 establishes a canonical, framework-neutral representation layer for learned embeddings and representation-space analysis. It formalizes the embedding references introduced in v3.61.0 rather than creating a parallel representation system.

## Governed representation objects

- representation-model records bound to the governed model specification and checkpoint
- embedding-space records with dimensions, dtype, normalization, similarity metric, corpus/partition lineage, and optional index hashes
- source-bound embedding objects with inline vectors or immutable vector-artifact references
- ranked similarity results with explicit query/neighbor resolution and metric semantics
- vector projections with governed projection method, dimensions, coordinates, computation refs, and artifact hashes
- representation clusters with explicit membership and optional centroid references
- reproducible representation-intelligence bundles that preserve the complete v3.61 explainability fingerprint

## v3.61 integration

v3.61 introduced embedding-space explanation records containing `representation_ref`, `embedding_space_ref`, nearest neighbors, cluster refs, and projection artifacts. v3.62 resolves those references into canonical governed representation objects. The v3.62 reference bundle requires v3.61 representation IDs, embedding-space IDs, query samples, neighbor ranks/scores, and cluster refs to resolve without silently changing meaning.

## Governance semantics

Core records that an embedding is a derived analytical representation rather than source evidence; embedding similarity is not semantic fact; nearest-neighbor proximity is not a relationship fact; low-dimensional projection distance is not the same as distance in the original embedding space; and cluster membership is analytical rather than ground truth.

## Architectural boundary

**Core defines and governs. Workspace computes. Lab experiments. Products consume.**

Core does not compute embeddings, download representation models, build vector indexes, run similarity search, project vectors, cluster embeddings, train representation models, promote neighbors to evidence, infer relationship facts from proximity, or certify representation quality.

Contract: `sc.core.neural-embedding-representation-intelligence.v1`

Public contract endpoint: `GET /public/v1/ml-representations/contract`
