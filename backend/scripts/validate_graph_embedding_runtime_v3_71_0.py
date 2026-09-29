from app.services.graph_embedding_runtime import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    contract_document,
    reference_graph_embedding_bundle,
)

bundle = reference_graph_embedding_bundle()
contract = contract_document()

assert CORE_RELEASE == "3.71.0"
assert CONTRACT_VERSION == "sc.core.graph-embedding-runtime.v1"
assert contract["principles"]["embedding_similarity_is_not_graph_fact"] is True
assert contract["principles"]["embedding_similarity_is_not_evidence"] is True
assert contract["principles"]["embedding_does_not_establish_relationship"] is True
assert contract["principles"]["gnn_prediction_is_not_graph_fact"] is True
assert contract["boundaries"]["core_computes_graph_embeddings"] is False
assert contract["boundaries"]["core_mutates_graph_from_similarity"] is False
assert contract["roadmap_integration"]["prepares_v3720_node_edge_classification_objects"] is True
assert all(x.is_graph_fact is False and x.is_evidence_edge is False for x in bundle.embeddings)
assert all(x.query_does_not_mutate_graph is True for x in bundle.similarity_queries)

print("PASS - Platform Core v3.71.0 Graph Embedding Objects & Runtime Contracts")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"EMBEDDING_SPACES={len(bundle.embedding_spaces)}")
print(f"EMBEDDINGS={len(bundle.embeddings)}")
print(f"SIMILARITY_QUERIES={len(bundle.similarity_queries)}")
print(f"DIMENSIONS={bundle.embedding_spaces[0].dimensions}")
print("EMBEDDING_SIMILARITY_IS_GRAPH_FACT=false")
print("EMBEDDING_SIMILARITY_IS_EVIDENCE=false")
print("EMBEDDING_ESTABLISHES_RELATIONSHIP=false")
