import math

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import ml_embedding_representation
from app.services.ml_embedding_representation import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    MLEmbeddingObjectRecord,
    MLEmbeddingSpaceRecord,
    MLProjectionMethod,
    MLProjectionPointRecord,
    MLRepresentationClusterRecord,
    MLRepresentationIntelligenceBundle,
    MLSimilarityMetric,
    MLSimilarityNeighborRecord,
    MLSimilarityResultRecord,
    MLVectorProjectionRecord,
    contract_document,
    reference_representation_intelligence_bundle,
)


def test_contract_identity():
    doc = contract_document()
    assert CORE_RELEASE == "3.62.0"
    assert CONTRACT_VERSION == "sc.core.neural-embedding-representation-intelligence.v1"
    assert doc["release"] == "3.62.0"


def test_extends_v361_explainability():
    assert contract_document()["integration"]["extends_explainability_model_interpretation_v3610"] is True


def test_resolves_v361_embedding_refs():
    integration = contract_document()["integration"]
    assert integration["resolves_v361_embedding_representation_refs"] is True
    assert integration["resolves_v361_embedding_space_refs"] is True


def test_governance_semantics():
    governance = contract_document()["governance"]
    for key in (
        "embedding_is_derived_analytical_representation_not_evidence",
        "embedding_similarity_is_not_semantic_fact",
        "nearest_neighbor_is_not_relationship_fact",
        "projection_distance_is_not_original_space_distance",
        "cluster_membership_is_analytical_not_ground_truth",
        "representation_objects_require_source_lineage",
        "learned_representation_does_not_replace_source_evidence",
    ):
        assert governance[key] is True


def test_core_does_not_execute_representation_intelligence():
    boundaries = contract_document()["boundaries"]
    for key in (
        "core_computes_embeddings",
        "core_downloads_representation_models",
        "core_builds_vector_indexes",
        "core_runs_similarity_search",
        "core_projects_vectors",
        "core_clusters_embeddings",
        "core_trains_representation_models",
        "core_promotes_neighbors_to_evidence",
        "core_infers_relationship_facts_from_proximity",
        "core_treats_embedding_similarity_as_semantic_truth",
        "core_certifies_representation_quality",
    ):
        assert boundaries[key] is False


def test_reference_bundle_valid_and_fingerprinted():
    bundle = reference_representation_intelligence_bundle()
    assert len(bundle.fingerprint()) == 64
    assert bundle.representation_models
    assert bundle.embedding_spaces
    assert bundle.embeddings
    assert bundle.similarity_results
    assert bundle.vector_projections
    assert bundle.clusters


def test_fingerprint_stable():
    a = reference_representation_intelligence_bundle()
    b = MLRepresentationIntelligenceBundle.model_validate(a.model_dump(mode="json"))
    assert a.fingerprint() == b.fingerprint()


def invalid(mutator):
    payload = reference_representation_intelligence_bundle().model_dump(mode="json")
    mutator(payload)
    with pytest.raises(ValidationError):
        MLRepresentationIntelligenceBundle.model_validate(payload)


def test_model_spec_ref_must_match_v361_bundle():
    invalid(lambda p: p.__setitem__("model_spec_ref", "ml-model-spec:wrong"))


def test_checkpoint_ref_must_match_v361_bundle():
    invalid(lambda p: p.__setitem__("checkpoint_ref", "ml-checkpoint:wrong"))


def test_v361_fingerprint_must_match():
    invalid(lambda p: p.__setitem__("explainability_fingerprint_sha256", "0" * 64))


def test_representation_model_must_bind_model_spec():
    invalid(lambda p: p["representation_models"][0].__setitem__("model_spec_ref", "ml-model-spec:wrong"))


def test_representation_model_must_bind_checkpoint():
    invalid(lambda p: p["representation_models"][0].__setitem__("checkpoint_ref", "ml-checkpoint:wrong"))


def test_embedding_space_model_ref_must_resolve():
    invalid(lambda p: p["embedding_spaces"][0].__setitem__("representation_model_ref", "representation-model:missing"))


def test_embedding_space_dimensions_match_model():
    invalid(lambda p: p["embedding_spaces"][0].__setitem__("dimensions", 15))


def test_embedding_space_partition_refs_unique():
    payload = reference_representation_intelligence_bundle().embedding_spaces[0].model_dump(mode="json")
    payload["source_partition_refs"].append(payload["source_partition_refs"][0])
    with pytest.raises(ValidationError):
        MLEmbeddingSpaceRecord.model_validate(payload)


def test_embedding_requires_vector_or_artifact():
    with pytest.raises(ValidationError):
        MLEmbeddingObjectRecord(
            embedding_id="embedding:test",
            embedding_space_ref="space:test",
            source_object_ref="sample:test",
            source_object_type="sample",
            dimensions=2,
        )


def test_embedding_vector_length_matches_dimensions():
    with pytest.raises(ValidationError):
        MLEmbeddingObjectRecord(
            embedding_id="embedding:test",
            embedding_space_ref="space:test",
            source_object_ref="sample:test",
            source_object_type="sample",
            dimensions=3,
            vector=[1.0, 0.0],
        )


def test_embedding_l2_norm_matches_vector():
    with pytest.raises(ValidationError):
        MLEmbeddingObjectRecord(
            embedding_id="embedding:test",
            embedding_space_ref="space:test",
            source_object_ref="sample:test",
            source_object_type="sample",
            dimensions=2,
            vector=[1.0, 0.0],
            l2_norm=0.5,
        )


def test_artifact_only_embedding_is_valid():
    record = MLEmbeddingObjectRecord(
        embedding_id="embedding:test",
        embedding_space_ref="space:test",
        source_object_ref="sample:test",
        source_object_type="sample",
        dimensions=128,
        vector_artifact_ref="artifact:test-vector",
        vector_artifact_sha256="a" * 64,
    )
    assert record.vector is None


def test_embedding_space_ref_must_resolve():
    invalid(lambda p: p["embeddings"][0].__setitem__("embedding_space_ref", "space:missing"))


def test_embedding_dimensions_must_match_space():
    invalid(lambda p: p["embeddings"][0].__setitem__("dimensions", 8))


def test_normalized_space_requires_unit_inline_vectors():
    invalid(lambda p: p["embeddings"][0].__setitem__("vector", [0.5] + [0.0] * 15))


def test_source_object_unique_per_embedding_space():
    def mutate(payload):
        payload["embeddings"][1]["source_object_ref"] = payload["embeddings"][0]["source_object_ref"]
    invalid(mutate)


def test_similarity_query_must_resolve():
    invalid(lambda p: p["similarity_results"][0].__setitem__("query_embedding_ref", "embedding:missing"))


def test_similarity_metric_must_match_space():
    invalid(lambda p: p["similarity_results"][0].__setitem__("metric", "euclidean"))


def test_similarity_neighbor_refs_must_resolve():
    invalid(lambda p: p["similarity_results"][0]["neighbors"][0].__setitem__("embedding_ref", "embedding:missing"))


def test_similarity_neighbor_source_ref_matches_embedding():
    invalid(lambda p: p["similarity_results"][0]["neighbors"][0].__setitem__("source_object_ref", "sample:wrong"))


def test_similarity_query_cannot_be_neighbor():
    payload = reference_representation_intelligence_bundle().similarity_results[0].model_dump(mode="json")
    payload["neighbors"][0]["embedding_ref"] = payload["query_embedding_ref"]
    with pytest.raises(ValidationError):
        MLSimilarityResultRecord.model_validate(payload)


def test_similarity_ranks_contiguous():
    payload = reference_representation_intelligence_bundle().similarity_results[0].model_dump(mode="json")
    payload["neighbors"][1]["rank"] = 4
    with pytest.raises(ValidationError):
        MLSimilarityResultRecord.model_validate(payload)


def test_similarity_scores_non_increasing():
    payload = reference_representation_intelligence_bundle().similarity_results[0].model_dump(mode="json")
    payload["neighbors"][1]["similarity_score"] = 0.99
    with pytest.raises(ValidationError):
        MLSimilarityResultRecord.model_validate(payload)


def test_cosine_similarity_bounds():
    with pytest.raises(ValidationError):
        MLSimilarityResultRecord(
            similarity_result_id="sim:test",
            embedding_space_ref="space:test",
            query_embedding_ref="embedding:q",
            metric=MLSimilarityMetric.cosine,
            neighbors=[MLSimilarityNeighborRecord(embedding_ref="embedding:n", source_object_ref="sample:n", rank=1, similarity_score=1.1)],
        )


def test_projection_input_dimensions_match_space():
    invalid(lambda p: p["vector_projections"][0].__setitem__("input_dimensions", 8))


def test_projection_points_resolve():
    invalid(lambda p: p["vector_projections"][0]["points"][0].__setitem__("embedding_ref", "embedding:missing"))


def test_projection_coordinate_dimensions_match():
    payload = reference_representation_intelligence_bundle().vector_projections[0].model_dump(mode="json")
    payload["points"][0]["coordinates"] = [1.0]
    with pytest.raises(ValidationError):
        MLVectorProjectionRecord.model_validate(payload)


def test_projection_embedding_refs_unique():
    payload = reference_representation_intelligence_bundle().vector_projections[0].model_dump(mode="json")
    payload["points"][1]["embedding_ref"] = payload["points"][0]["embedding_ref"]
    with pytest.raises(ValidationError):
        MLVectorProjectionRecord.model_validate(payload)


def test_cluster_members_resolve():
    invalid(lambda p: p["clusters"][0]["member_embedding_refs"].__setitem__(0, "embedding:missing"))


def test_cluster_members_unique():
    payload = reference_representation_intelligence_bundle().clusters[0].model_dump(mode="json")
    payload["member_embedding_refs"].append(payload["member_embedding_refs"][0])
    with pytest.raises(ValidationError):
        MLRepresentationClusterRecord.model_validate(payload)


def test_v361_representation_ref_resolves_to_v362_model():
    invalid(lambda p: p["representation_models"][0].__setitem__("representation_model_id", "representation-model:other"))


def test_v361_embedding_space_ref_resolves_to_v362_space():
    invalid(lambda p: p["embedding_spaces"][0].__setitem__("embedding_space_id", "embedding-space:other"))


def test_v361_query_sample_resolves_to_embedding():
    invalid(lambda p: p["embeddings"][0].__setitem__("source_object_ref", "sample:wrong"))


def test_v361_neighbor_mapping_is_preserved():
    invalid(lambda p: p["similarity_results"][0]["neighbors"][0].__setitem__("source_object_ref", "sample:wrong"))


def test_v361_neighbor_similarity_is_preserved():
    invalid(lambda p: p["similarity_results"][0]["neighbors"][0].__setitem__("similarity_score", 0.93))


def test_v361_cluster_ref_resolves():
    invalid(lambda p: p["clusters"][0].__setitem__("cluster_id", "cluster:other"))


def test_public_contract_route():
    app = FastAPI()
    app.include_router(ml_embedding_representation.public_router)
    response = TestClient(app).get("/public/v1/ml-representations/contract")
    assert response.status_code == 200
    assert response.json()["release"] == "3.62.0"


def test_private_reference_route():
    app = FastAPI()
    app.include_router(ml_embedding_representation.router)
    response = TestClient(app).get("/api/v1/ml-representations/reference")
    assert response.status_code == 200
    assert len(response.json()["bundle_fingerprint_sha256"]) == 64
