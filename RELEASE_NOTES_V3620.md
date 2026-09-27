# Platform Core v3.62.0 — Neural Embedding & Representation Intelligence

Platform Core v3.62.0 adds the governed representation layer for learned embeddings, similarity analysis, projections, and representation clusters.

## Added

- canonical representation-model objects bound to model specification and checkpoint lineage
- canonical embedding-space objects with dimensions, dtype, normalization, similarity metric, partition refs, and optional index hashes
- source-bound embedding objects supporting inline vectors or immutable artifact-backed vectors
- ranked similarity-result objects with query/neighbor resolution and deterministic fingerprints
- governed vector-projection objects for PCA/UMAP/t-SNE/PaCMAP/custom projection outputs
- governed representation-cluster objects
- explicit resolution of v3.61 embedding explanation `representation_ref`, `embedding_space_ref`, query sample, neighbors, scores, cluster, and projection lineage
- public contract endpoint at `/public/v1/ml-representations/contract`

## Governance

v3.62.0 explicitly records that embeddings are derived analytical representations rather than evidence; similarity is not semantic truth; nearest neighbors are not relationship facts; projection geometry is not original-space geometry; and clusters are not ground truth.

## Boundaries

Core does not compute embeddings, train/download representation models, build vector indexes, execute similarity search, project vectors, cluster embeddings, infer relationship facts from proximity, promote neighbors to evidence, or certify representation quality.

No database migration is introduced in this release.
