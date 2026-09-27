from app.services.ml_embedding_representation import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    contract_document,
    reference_representation_intelligence_bundle,
)

contract = contract_document()
bundle = reference_representation_intelligence_bundle()
assert CORE_RELEASE == "3.62.0"
assert CONTRACT_VERSION == "sc.core.neural-embedding-representation-intelligence.v1"
assert contract["integration"]["extends_explainability_model_interpretation_v3610"] is True
assert contract["integration"]["resolves_v361_embedding_space_refs"] is True
assert contract["governance"]["embedding_similarity_is_not_semantic_fact"] is True
assert contract["governance"]["learned_representation_does_not_replace_source_evidence"] is True
assert contract["boundaries"]["core_computes_embeddings"] is False
assert contract["boundaries"]["core_runs_similarity_search"] is False
assert len(bundle.fingerprint()) == 64
print("PASS - Platform Core v3.62.0 Neural Embedding & Representation Intelligence")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"REPRESENTATION_MODEL={bundle.representation_models[0].representation_model_id}")
print(f"EMBEDDING_SPACE={bundle.embedding_spaces[0].embedding_space_id}")
print(f"SIMILARITY_RESULT={bundle.similarity_results[0].similarity_result_id}")
print(f"VECTOR_PROJECTION={bundle.vector_projections[0].projection_id}")
print("CORE_COMPUTES_EMBEDDINGS=false")
print("EMBEDDING_SIMILARITY_IS_SEMANTIC_FACT=false")
