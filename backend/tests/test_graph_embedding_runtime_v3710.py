import math

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import graph_embedding_runtime
from app.services.graph_embedding_runtime import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    GraphEmbeddingLifecycleState,
    GraphEmbeddingObject,
    GraphEmbeddingTargetKind,
    GraphSimilarityNeighbor,
    GraphSimilarityQueryRecord,
    contract_document,
    reference_graph_embedding_bundle,
)
from app.services.ml_embedding_representation import MLSimilarityMetric


def test_release_identity():
    assert CORE_RELEASE == "3.71.0"
    assert CONTRACT_VERSION == "sc.core.graph-embedding-runtime.v1"


def test_reference_bundle_validates():
    bundle = reference_graph_embedding_bundle()
    assert len(bundle.embedding_spaces) == 1
    assert len(bundle.embeddings) == 3
    assert len(bundle.similarity_queries) == 1
    assert len(bundle.fingerprint()) == 64


def test_reference_vectors_are_normalized():
    bundle = reference_graph_embedding_bundle()
    for embedding in bundle.embeddings:
        assert embedding.vector is not None
        norm = math.sqrt(sum(x*x for x in embedding.vector))
        assert math.isclose(norm, 1.0, rel_tol=1e-8, abs_tol=1e-8)


def test_embedding_is_neither_graph_fact_nor_evidence_edge():
    for embedding in reference_graph_embedding_bundle().embeddings:
        assert embedding.is_graph_fact is False
        assert embedding.is_evidence_edge is False
        assert embedding.embedding_does_not_establish_relationship is True


def test_similarity_query_is_non_mutating_and_non_evidentiary():
    query = reference_graph_embedding_bundle().similarity_queries[0]
    assert query.similarity_is_not_evidence is True
    assert query.similarity_is_not_identity is True
    assert query.similarity_is_not_relationship_validation is True
    assert query.query_does_not_mutate_graph is True


def test_graph_embedding_requires_vector_or_artifact():
    with pytest.raises(ValidationError):
        GraphEmbeddingObject(
            embedding_id="embedding:test",
            embedding_space_ref="space:test",
            source_snapshot_ref="snapshot:test",
            target_kind=GraphEmbeddingTargetKind.node,
            target_object_ref="node:test",
            dimensions=4,
            generated_by_embedding_run_ref="run:test",
        )


def test_graph_embedding_vector_length_must_match_dimensions():
    with pytest.raises(ValidationError):
        GraphEmbeddingObject(
            embedding_id="embedding:test",
            embedding_space_ref="space:test",
            source_snapshot_ref="snapshot:test",
            target_kind=GraphEmbeddingTargetKind.node,
            target_object_ref="node:test",
            dimensions=4,
            vector=[1.0, 0.0],
            generated_by_embedding_run_ref="run:test",
        )


def test_reviewed_embedding_requires_reviewer():
    with pytest.raises(ValidationError):
        GraphEmbeddingObject(
            embedding_id="embedding:test",
            embedding_space_ref="space:test",
            source_snapshot_ref="snapshot:test",
            target_kind=GraphEmbeddingTargetKind.node,
            target_object_ref="node:test",
            dimensions=2,
            vector=[1.0, 0.0],
            generated_by_embedding_run_ref="run:test",
            lifecycle_state=GraphEmbeddingLifecycleState.reviewed,
        )


def test_similarity_query_rejects_self_neighbor():
    with pytest.raises(ValidationError):
        GraphSimilarityQueryRecord(
            similarity_query_id="query:test",
            embedding_space_ref="space:test",
            query_embedding_ref="embedding:a",
            metric=MLSimilarityMetric.cosine,
            top_k=1,
            neighbors=[GraphSimilarityNeighbor(embedding_ref="embedding:a", target_object_ref="node:a", rank=1, similarity_score=1.0)],
            embedding_run_ref="run:test",
        )


def test_similarity_query_rejects_noncontiguous_ranks():
    with pytest.raises(ValidationError):
        GraphSimilarityQueryRecord(
            similarity_query_id="query:test",
            embedding_space_ref="space:test",
            query_embedding_ref="embedding:a",
            metric=MLSimilarityMetric.cosine,
            top_k=2,
            neighbors=[
                GraphSimilarityNeighbor(embedding_ref="embedding:b", target_object_ref="node:b", rank=1, similarity_score=0.9),
                GraphSimilarityNeighbor(embedding_ref="embedding:c", target_object_ref="node:c", rank=3, similarity_score=0.8),
            ],
            embedding_run_ref="run:test",
        )


def test_similarity_query_rejects_bad_cosine_score():
    with pytest.raises(ValidationError):
        GraphSimilarityQueryRecord(
            similarity_query_id="query:test",
            embedding_space_ref="space:test",
            query_embedding_ref="embedding:a",
            metric=MLSimilarityMetric.cosine,
            top_k=1,
            neighbors=[GraphSimilarityNeighbor(embedding_ref="embedding:b", target_object_ref="node:b", rank=1, similarity_score=1.2)],
            embedding_run_ref="run:test",
        )


def test_bundle_rejects_unknown_embedding_space_for_embedding():
    bundle = reference_graph_embedding_bundle().model_copy(deep=True)
    bundle.embeddings[0].embedding_space_ref = "space:missing"
    with pytest.raises(ValidationError):
        type(bundle).model_validate(bundle.model_dump(mode="json"))


def test_bundle_rejects_unknown_snapshot_node_target():
    bundle = reference_graph_embedding_bundle().model_copy(deep=True)
    bundle.embeddings[0].target_object_ref = "node:missing"
    with pytest.raises(ValidationError):
        type(bundle).model_validate(bundle.model_dump(mode="json"))


def test_bundle_rejects_dimension_mismatch():
    bundle = reference_graph_embedding_bundle().model_copy(deep=True)
    bundle.embedding_spaces[0].dimensions = 9
    with pytest.raises(ValidationError):
        type(bundle).model_validate(bundle.model_dump(mode="json"))


def test_bundle_rejects_similarity_metric_mismatch():
    bundle = reference_graph_embedding_bundle().model_copy(deep=True)
    bundle.similarity_queries[0].metric = MLSimilarityMetric.euclidean
    with pytest.raises(ValidationError):
        type(bundle).model_validate(bundle.model_dump(mode="json"))


def test_bundle_extends_v370_and_v362_contracts():
    assert contract_document()["extends_contracts"] == [
        "sc.core.graph-machine-learning-foundation.v1",
        "sc.core.neural-embedding-representation-intelligence.v1",
    ]


@pytest.mark.parametrize("key", [
    "graph_embedding_is_derived_representation",
    "embedding_similarity_is_not_graph_fact",
    "embedding_similarity_is_not_evidence",
    "embedding_similarity_is_not_identity",
    "embedding_distance_is_not_evidence_strength",
    "embedding_does_not_establish_relationship",
    "embedding_space_is_model_and_snapshot_specific",
    "gnn_prediction_is_not_graph_fact",
])
def test_contract_principles_true(key):
    assert contract_document()["principles"][key] is True


@pytest.mark.parametrize("key", [
    "core_computes_graph_embeddings",
    "core_builds_vector_indexes",
    "core_executes_similarity_search",
    "core_installs_graph_embedding_frameworks",
    "core_treats_similarity_as_relationship_validation",
    "core_treats_nearest_neighbor_as_identity",
    "core_mutates_graph_from_similarity",
    "runtime_may_mutate_evidence_graph",
])
def test_contract_boundaries_false(key):
    assert contract_document()["boundaries"][key] is False


def test_contract_preserves_gnn_roadmap():
    r = contract_document()["roadmap_integration"]
    assert r["prepares_v3720_node_edge_classification_objects"] is True
    assert r["prepares_v3730_link_prediction_candidate_relationship_objects"] is True
    assert r["prepares_v3740_graph_anomaly_detection"] is True
    assert r["prepares_v3750_knowledge_graph_representation_learning"] is True
    assert r["prepares_v3760_evidence_graph_neural_analysis_validation_workflow"] is True


def test_public_contract_route():
    app = FastAPI()
    app.include_router(graph_embedding_runtime.public_router)
    with TestClient(app) as client:
        response = client.get("/public/v1/graph-embeddings/contract")
    assert response.status_code == 200
    assert response.json()["release"] == "3.71.0"
    assert response.json()["principles"]["embedding_similarity_is_not_graph_fact"] is True


def test_private_reference_route():
    app = FastAPI()
    app.include_router(graph_embedding_runtime.router)
    with TestClient(app) as client:
        response = client.get("/api/v1/graph-embeddings/reference")
    assert response.status_code == 200
    body = response.json()
    assert body["release"] == "3.71.0"
    assert len(body["bundle_fingerprint_sha256"]) == 64
