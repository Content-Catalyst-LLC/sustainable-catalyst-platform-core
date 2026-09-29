import pytest
from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers import graph_classification
from app.services.graph_machine_learning import GraphTargetKind,GraphMLTaskKind
from app.services.graph_classification import *

def test_release_identity(): assert CORE_RELEASE=="3.72.0" and CONTRACT_VERSION=="sc.core.graph-node-edge-classification.v1"
def test_reference_bundle():
    b=reference_graph_classification_bundle(); assert len(b.label_spaces)==2 and len(b.tasks)==2 and len(b.predictions)==2 and len(b.fingerprint())==64
def test_node_and_edge_predictions_present(): assert {p.target_kind for p in reference_graph_classification_bundle().predictions}=={GraphTargetKind.node,GraphTargetKind.edge}
def test_predictions_non_evidentiary():
    for p in reference_graph_classification_bundle().predictions:
        assert p.is_graph_fact is False and p.is_evidence is False and p.is_evidence_edge is False and p.requires_separate_validation_before_graph_fact is True
def test_edge_prediction_targets_existing_edge():
    b=reference_graph_classification_bundle(); p=[x for x in b.predictions if x.target_kind==GraphTargetKind.edge][0]; s=b.graph_embedding_bundle.graph_ml_foundation_bundle.snapshots[0]; assert p.target_object_ref in {e.evidence_edge_ref for e in s.evidence_edges}
def test_exclusive_probabilities_sum_one():
    for p in reference_graph_classification_bundle().predictions: assert abs(sum(x.probability for x in p.class_probabilities)-1)<1e-9
def test_calibrated_requires_ref():
    p=reference_graph_classification_bundle().predictions[0].model_dump(); p['calibration_ref']=None
    with pytest.raises(ValidationError): GraphClassificationPrediction.model_validate(p)
def test_reviewed_requires_reviewer():
    p=reference_graph_classification_bundle().predictions[0].model_dump(); p['review_state']='human-reviewed'; p['reviewer_ref']=None
    with pytest.raises(ValidationError): GraphClassificationPrediction.model_validate(p)
def test_task_kind_must_match_target():
    t=reference_graph_classification_bundle().tasks[0].model_dump(); t['graph_ml_task_kind']=GraphMLTaskKind.edge_classification
    with pytest.raises(ValidationError): GraphClassificationTask.model_validate(t)
def test_bad_probability_sum_rejected_by_bundle():
    b=reference_graph_classification_bundle().model_copy(deep=True); b.predictions[0].class_probabilities[0].probability=.5
    with pytest.raises(ValidationError): GraphClassificationBundle.model_validate(b.model_dump(mode='json'))
def test_unknown_label_rejected():
    b=reference_graph_classification_bundle().model_copy(deep=True); b.predictions[0].class_probabilities[0].label_ref='missing'
    with pytest.raises(ValidationError): GraphClassificationBundle.model_validate(b.model_dump(mode='json'))
def test_missing_node_rejected():
    b=reference_graph_classification_bundle().model_copy(deep=True); b.predictions[0].target_object_ref='node:missing'
    with pytest.raises(ValidationError): GraphClassificationBundle.model_validate(b.model_dump(mode='json'))
def test_missing_edge_rejected():
    b=reference_graph_classification_bundle().model_copy(deep=True); b.predictions[1].target_object_ref='edge:missing'
    with pytest.raises(ValidationError): GraphClassificationBundle.model_validate(b.model_dump(mode='json'))
def test_missing_embedding_rejected():
    b=reference_graph_classification_bundle().model_copy(deep=True); b.predictions[0].embedding_refs=['embedding:missing']
    with pytest.raises(ValidationError): GraphClassificationBundle.model_validate(b.model_dump(mode='json'))
def test_public_route():
    a=FastAPI(); a.include_router(graph_classification.public_router)
    with TestClient(a) as c: r=c.get('/public/v1/graph-classification/contract')
    assert r.status_code==200 and r.json()['release']=='3.72.0'
@pytest.mark.parametrize('key',["classification_output_is_derived_model_output","node_classification_is_not_graph_fact","edge_classification_is_not_graph_fact","classification_probability_is_not_evidence_strength","high_probability_does_not_establish_truth","reviewed_classification_remains_distinct_from_evidence","classification_does_not_change_target_identity","gnn_prediction_is_not_graph_fact"])
def test_principles(key): assert contract_document()['principles'][key] is True
@pytest.mark.parametrize('key',["core_trains_graph_classifier","core_runs_graph_classification_inference","core_calibrates_classifier","core_promotes_classification_to_graph_fact","core_mutates_node_or_edge_identity_from_classification","runtime_may_mutate_evidence_graph","runtime_may_promote_classification_to_graph_fact","v372_performs_link_prediction"])
def test_boundaries(key): assert contract_document()['boundaries'][key] is False
def test_extends_contracts(): assert contract_document()['extends_contracts']==['sc.core.graph-machine-learning-foundation.v1','sc.core.graph-embedding-runtime.v1']
def test_roadmap_v373(): assert contract_document()['roadmap_integration']['prepares_v3730_link_prediction_candidate_relationship_objects'] is True
def test_roadmap_v376(): assert contract_document()['roadmap_integration']['prepares_v3760_evidence_graph_neural_analysis_validation_workflow'] is True
