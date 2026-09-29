import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import graph_machine_learning
from app.services.graph_machine_learning import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    GraphEvidenceEdgeBinding,
    GraphFeatureBinding,
    GraphLabelBinding,
    GraphLearningMode,
    GraphLearningSnapshot,
    GraphMLFoundationBundle,
    GraphMLModelFoundation,
    GraphMLRuntimeContract,
    GraphMLTaskKind,
    GraphMLTaskSpecification,
    GraphRunKind,
    GraphTargetKind,
    PredictedRelationship,
    RelationshipPredictionState,
    contract_document,
    reference_graph_ml_foundation_bundle,
)
from app.services.machine_learning_models import MLModelFamily, NeuralArchitectureKind


def test_release_and_contract_identity():
    assert CORE_RELEASE == "3.70.0"
    assert CONTRACT_VERSION == "sc.core.graph-machine-learning-foundation.v1"


def test_reference_bundle_is_valid_and_deterministic():
    a = reference_graph_ml_foundation_bundle()
    b = reference_graph_ml_foundation_bundle()
    assert a.fingerprint() == b.fingerprint()
    assert len(a.fingerprint()) == 64


def test_reference_model_is_gnn_family_and_architecture():
    foundation = reference_graph_ml_foundation_bundle().model_foundations[0]
    assert foundation.model_spec.model_family == MLModelFamily.graph_neural_network
    assert foundation.model_spec.neural_architecture is not None
    assert foundation.model_spec.neural_architecture.architecture_kind == NeuralArchitectureKind.graph_neural_network


def test_reference_snapshot_contains_only_validated_evidence_edges():
    snapshot = reference_graph_ml_foundation_bundle().snapshots[0]
    assert snapshot.immutable_snapshot is True
    assert snapshot.predicted_relationships_are_excluded_from_evidence_edges is True
    assert len(snapshot.evidence_edges) == 1
    edge = snapshot.evidence_edges[0]
    assert edge.validated_before_graph_snapshot is True
    assert edge.generated_by_graph_ml_model is False
    assert edge.prediction_score_is_not_evidence is True


def test_reference_prediction_is_not_graph_fact_or_evidence_edge():
    prediction = reference_graph_ml_foundation_bundle().predicted_relationships[0]
    assert prediction.is_graph_fact is False
    assert prediction.is_evidence_edge is False
    assert prediction.requires_separate_validation_before_evidence_edge is True
    assert prediction.high_score_does_not_establish_truth is True


def test_reference_prediction_is_explicitly_excluded_from_snapshot_evidence_edges():
    bundle = reference_graph_ml_foundation_bundle()
    prediction = bundle.predicted_relationships[0]
    snapshot = bundle.snapshots[0]
    assert prediction.prediction_id in snapshot.excluded_candidate_relationship_refs
    assert prediction.prediction_id not in {x.evidence_edge_ref for x in snapshot.evidence_edges}


def test_reference_runtime_cannot_mutate_evidence_graph():
    runtime = reference_graph_ml_foundation_bundle().runtime_contracts[0]
    assert runtime.core_executes_graph_ml is False
    assert runtime.runtime_may_mutate_evidence_graph is False
    assert runtime.arbitrary_code_allowed_by_core is False


def test_reference_feature_binding_is_provenance_bound():
    binding = reference_graph_ml_foundation_bundle().feature_bindings[0]
    assert len(binding.feature_artifact_sha256) == 64
    assert binding.feature_values_are_not_evidence is True
    assert binding.cross_lingual_exchange_refs


def test_reference_label_binding_does_not_create_graph_facts():
    binding = reference_graph_ml_foundation_bundle().label_bindings[0]
    assert binding.weak_or_heuristic_labels_advisory is True
    assert binding.labels_do_not_create_graph_facts is True
    assert binding.source_evidence_refs


def test_reference_task_is_link_prediction_foundation():
    task = reference_graph_ml_foundation_bundle().tasks[0]
    assert task.task_kind == GraphMLTaskKind.link_prediction
    assert task.learning_mode == GraphLearningMode.transductive
    assert task.target_relationship_types == ["semantic-related"]
    assert task.task_definition_is_not_evidence is True


def test_reference_run_lineage_separates_train_and_infer():
    bundle = reference_graph_ml_foundation_bundle()
    assert {x.run_kind for x in bundle.run_provenance} == {GraphRunKind.train, GraphRunKind.infer}
    prediction = bundle.predicted_relationships[0]
    infer = next(x for x in bundle.run_provenance if x.run_kind == GraphRunKind.infer)
    assert prediction.inference_run_ref == infer.run_id
    assert all(x.run_output_is_not_evidence for x in bundle.run_provenance)


def test_snapshot_rejects_evidence_edge_with_unknown_endpoint():
    bundle = reference_graph_ml_foundation_bundle()
    edge = bundle.snapshots[0].evidence_edges[0].model_copy(update={"target_node_ref": "missing:node"})
    with pytest.raises(ValidationError):
        GraphLearningSnapshot(
            snapshot_id="snapshot:test",
            source_graph_ref="graph:test",
            source_graph_fingerprint_sha256="a" * 64,
            node_refs=["node:a", "node:b"],
            evidence_edges=[edge],
        )


def test_snapshot_rejects_prediction_id_as_evidence_edge():
    bundle = reference_graph_ml_foundation_bundle()
    edge = bundle.snapshots[0].evidence_edges[0]
    with pytest.raises(ValidationError):
        GraphLearningSnapshot(
            snapshot_id="snapshot:test",
            source_graph_ref="graph:test",
            source_graph_fingerprint_sha256="a" * 64,
            node_refs=[edge.source_node_ref, edge.target_node_ref],
            evidence_edges=[edge],
            excluded_candidate_relationship_refs=[edge.evidence_edge_ref],
        )


def test_evidence_edge_rejects_self_reference():
    with pytest.raises(ValidationError):
        GraphEvidenceEdgeBinding(
            evidence_edge_ref="edge:test",
            source_node_ref="node:a",
            target_node_ref="node:a",
            relationship_type="related",
            evidence_refs=["evidence:a"],
            provenance_refs=["provenance:a"],
        )


def test_label_binding_requires_provenance():
    with pytest.raises(ValidationError):
        GraphLabelBinding(
            label_binding_id="label:test",
            snapshot_ref="snapshot:test",
            target_kind=GraphTargetKind.node,
            object_refs=["node:a"],
            label_artifact_ref="artifact:labels",
            label_artifact_sha256="b" * 64,
        )


def test_supervised_link_prediction_requires_labels():
    with pytest.raises(ValidationError):
        GraphMLTaskSpecification(
            task_id="task:test",
            task_kind=GraphMLTaskKind.link_prediction,
            learning_mode=GraphLearningMode.transductive,
            snapshot_ref="snapshot:test",
            model_spec_ref="model:test",
            feature_binding_refs=["features:test"],
            target_relationship_types=["related"],
        )


def test_link_prediction_requires_target_relationship_types():
    with pytest.raises(ValidationError):
        GraphMLTaskSpecification(
            task_id="task:test",
            task_kind=GraphMLTaskKind.link_prediction,
            learning_mode=GraphLearningMode.transductive,
            snapshot_ref="snapshot:test",
            model_spec_ref="model:test",
            feature_binding_refs=["features:test"],
            label_binding_refs=["labels:test"],
        )


def test_prediction_rejects_self_reference():
    with pytest.raises(ValidationError):
        PredictedRelationship(
            prediction_id="prediction:test",
            source_node_ref="node:a",
            target_node_ref="node:a",
            relationship_type_candidate="related",
            inference_run_ref="run:test",
            model_spec_ref="model:test",
        )


def test_reviewed_prediction_requires_reviewer():
    with pytest.raises(ValidationError):
        PredictedRelationship(
            prediction_id="prediction:test",
            source_node_ref="node:a",
            target_node_ref="node:b",
            relationship_type_candidate="related",
            inference_run_ref="run:test",
            model_spec_ref="model:test",
            state=RelationshipPredictionState.under_review,
        )


def test_bundle_rejects_prediction_backed_by_non_inference_run():
    bundle = reference_graph_ml_foundation_bundle().model_copy(deep=True)
    prediction = bundle.predicted_relationships[0]
    train = next(x for x in bundle.run_provenance if x.run_kind == GraphRunKind.train)
    prediction.inference_run_ref = train.run_id
    with pytest.raises(ValidationError):
        GraphMLFoundationBundle.model_validate(bundle.model_dump(mode="json"))


def test_bundle_rejects_prediction_id_colliding_with_evidence_edge():
    bundle = reference_graph_ml_foundation_bundle().model_copy(deep=True)
    bundle.predicted_relationships[0].prediction_id = bundle.snapshots[0].evidence_edges[0].evidence_edge_ref
    bundle.snapshots[0].excluded_candidate_relationship_refs = [bundle.predicted_relationships[0].prediction_id]
    with pytest.raises(ValidationError):
        GraphMLFoundationBundle.model_validate(bundle.model_dump(mode="json"))


def test_bundle_rejects_prediction_with_unknown_node():
    bundle = reference_graph_ml_foundation_bundle().model_copy(deep=True)
    bundle.predicted_relationships[0].target_node_ref = "node:missing"
    with pytest.raises(ValidationError):
        GraphMLFoundationBundle.model_validate(bundle.model_dump(mode="json"))


def test_foundation_rejects_non_gnn_model_family():
    bundle = reference_graph_ml_foundation_bundle()
    foundation = bundle.model_foundations[0].model_copy(deep=True)
    foundation.model_spec.model_family = MLModelFamily.neural_network
    with pytest.raises(ValidationError):
        GraphMLModelFoundation.model_validate(foundation.model_dump(mode="json"))


def test_bundle_rejects_feature_binding_from_other_snapshot():
    bundle = reference_graph_ml_foundation_bundle().model_copy(deep=True)
    bundle.feature_bindings[0].snapshot_ref = "snapshot:missing"
    with pytest.raises(ValidationError):
        GraphMLFoundationBundle.model_validate(bundle.model_dump(mode="json"))


@pytest.mark.parametrize("key", [
    "gnn_prediction_is_not_graph_fact",
    "predicted_relationship_is_not_evidence_edge",
    "high_prediction_score_does_not_establish_truth",
    "predicted_relationship_requires_separate_validation_before_evidence_edge",
    "training_graph_distinguishes_evidence_edges_from_candidate_relationships",
    "graph_snapshot_is_immutable_and_provenance_bound",
    "weak_or_heuristic_labels_remain_advisory",
    "cross_lingual_assertion_remains_non_factual_until_separately_validated",
])
def test_contract_principles_true(key):
    assert contract_document()["principles"][key] is True


@pytest.mark.parametrize("key", [
    "core_trains_graph_models",
    "core_runs_graph_inference",
    "core_computes_graph_embeddings",
    "core_installs_graph_ml_frameworks",
    "core_mutates_evidence_graph_from_prediction",
    "core_promotes_prediction_to_evidence_edge",
    "core_treats_candidate_relationship_as_fact",
    "core_certifies_graph_model_quality",
    "runtime_may_mutate_evidence_graph",
])
def test_contract_boundaries_false(key):
    assert contract_document()["boundaries"][key] is False


def test_contract_starts_second_neural_wave_and_preserves_full_map():
    r = contract_document()["roadmap_integration"]
    assert r["begins_second_neural_wave"] is True
    assert r["prepares_v3710_graph_embedding_objects_runtime_contracts"] is True
    assert r["prepares_v3720_node_edge_classification_objects"] is True
    assert r["prepares_v3730_link_prediction_candidate_relationship_objects"] is True
    assert r["prepares_v3740_graph_anomaly_detection"] is True
    assert r["prepares_v3750_knowledge_graph_representation_learning"] is True
    assert r["prepares_v3760_evidence_graph_neural_analysis_validation_workflow"] is True


def test_contract_extends_neural_registry_and_cross_lingual_exchange():
    assert contract_document()["extends_contracts"] == [
        "sc.core.machine-learning-neural-model-object.v1",
        "sc.core.neural-model-registry-reproducible-packages.v1",
        "sc.core.cross-lingual-semantic-linguistic-exchange.v1",
    ]


def test_reference_fixture_is_explicitly_synthetic():
    c = contract_document()
    assert c["reference"]["reference_fixture_is_synthetic"] is True
    assert reference_graph_ml_foundation_bundle().metadata["purpose"].startswith("Platform Core v3.70")


def test_public_contract_route():
    app = FastAPI()
    app.include_router(graph_machine_learning.public_router)
    with TestClient(app) as client:
        response = client.get("/public/v1/graph-ml/contract")
    assert response.status_code == 200
    assert response.json()["release"] == "3.70.0"
    assert response.json()["principles"]["gnn_prediction_is_not_graph_fact"] is True


def test_private_reference_route():
    app = FastAPI()
    app.include_router(graph_machine_learning.router)
    with TestClient(app) as client:
        response = client.get("/api/v1/graph-ml/reference")
    assert response.status_code == 200
    body = response.json()
    assert body["release"] == "3.70.0"
    assert len(body["bundle_fingerprint_sha256"]) == 64

