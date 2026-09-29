import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.routers import graph_anomaly_detection
from app.services.graph_anomaly_detection import *

def ref(): return reference_graph_anomaly_detection_bundle()
def test_release_identity(): assert CORE_RELEASE=="3.74.0" and CONTRACT_VERSION=="sc.core.graph-anomaly-detection.v1"
def test_reference_counts(): b=ref(); assert (len(b.tasks),len(b.targets),len(b.scores),len(b.explanations),len(b.reviews))==(1,1,1,1,1)
def test_bundle_fingerprint(): assert len(ref().fingerprint())==64
def test_task_kind(): assert ref().tasks[0].graph_ml_task_kind.value=="anomaly-detection"
def test_target_is_definition_not_finding(): assert ref().targets[0].target_definition_is_not_anomaly_finding
def test_score_non_evidentiary(): s=ref().scores[0]; assert s.is_graph_fact is False and s.is_evidence is False and s.is_wrongdoing_finding is False
def test_score_flag_threshold_consistent(): s=ref().scores[0]; assert s.flagged_as_anomalous==(s.normalized_score>=s.threshold)
def test_bad_flag_rejected():
    d=ref().scores[0].model_dump(); d['flagged_as_anomalous']=False
    with pytest.raises(ValidationError): GraphAnomalyScoreRecord.model_validate(d)
def test_bad_probability_rejected():
    d=ref().scores[0].model_dump(); d['normalized_score']=1.2
    with pytest.raises(ValidationError): GraphAnomalyScoreRecord.model_validate(d)
def test_calibrated_requires_ref():
    d=ref().scores[0].model_dump(); d['calibration_ref']=None
    with pytest.raises(ValidationError): GraphAnomalyScoreRecord.model_validate(d)
def test_human_reviewed_score_requires_reviewer():
    d=ref().scores[0].model_dump(); d['review_state']='human-reviewed'; d['reviewer_ref']=None
    with pytest.raises(ValidationError): GraphAnomalyScoreRecord.model_validate(d)
def test_node_target_resolves(): assert ref().targets[0].object_ref in ref().graph_link_prediction_bundle.graph_classification_bundle.graph_embedding_bundle.graph_ml_foundation_bundle.snapshots[0].node_refs
def test_missing_node_target_rejected():
    b=ref().model_copy(deep=True); b.targets[0].object_ref='node:missing'
    with pytest.raises(ValidationError): GraphAnomalyDetectionBundle.model_validate(b.model_dump(mode='json'))
def test_subgraph_requires_members():
    with pytest.raises(ValidationError): GraphAnomalyTarget(anomaly_target_id='x1',snapshot_ref='s1',target_kind='subgraph')
def test_graph_target_forbids_object_ref():
    with pytest.raises(ValidationError): GraphAnomalyTarget(anomaly_target_id='x1',snapshot_ref='s1',target_kind='graph',object_ref='x')
def test_task_feature_refs_resolve(): assert ref().tasks[0].feature_binding_refs
def test_missing_task_feature_ref_rejected():
    b=ref().model_copy(deep=True); b.tasks[0].feature_binding_refs=['feature:missing']
    with pytest.raises(ValidationError): GraphAnomalyDetectionBundle.model_validate(b.model_dump(mode='json'))
def test_embedding_ref_resolves(): assert ref().scores[0].embedding_refs
def test_missing_embedding_ref_rejected():
    b=ref().model_copy(deep=True); b.scores[0].embedding_refs=['embedding:missing']
    with pytest.raises(ValidationError): GraphAnomalyDetectionBundle.model_validate(b.model_dump(mode='json'))
def test_explanation_is_not_causal_proof(): e=ref().explanations[0]; assert e.explanation_is_not_causal_proof and e.explanation_is_not_evidence
def test_review_not_wrongdoing(): r=ref().reviews[0]; assert r.review_is_not_truth_determination and r.review_is_not_wrongdoing_determination and r.review_does_not_create_evidence_edge
def test_evaluation_metrics_finite(): assert all(x==x for x in ref().evaluations[0].metric_values.values())
def test_runtime_cannot_mutate(): r=ref().runtime_contracts[0]; assert r.runtime_may_mutate_evidence_graph is False and r.runtime_may_assert_wrongdoing is False
def test_public_route():
    a=FastAPI(); a.include_router(graph_anomaly_detection.public_router)
    with TestClient(a) as c: z=c.get('/public/v1/graph-anomalies/contract')
    assert z.status_code==200 and z.json()['release']=='3.74.0'
@pytest.mark.parametrize('key',["anomaly_detection_is_derived_model_output","anomaly_is_not_graph_fact","anomaly_is_not_evidence","anomaly_is_not_wrongdoing","anomaly_score_is_not_evidence_strength","high_anomaly_score_does_not_establish_error","embedding_outlier_does_not_establish_wrongdoing","structural_outlier_does_not_establish_invalid_edge","human_review_does_not_create_evidence_edge","contradicting_context_must_remain_visible","gnn_prediction_is_not_graph_fact"])
def test_principles(key): assert contract_document()['principles'][key] is True
@pytest.mark.parametrize('key',["core_trains_anomaly_detector","core_runs_anomaly_detection_inference","core_labels_wrongdoing_from_anomaly","core_mutates_evidence_graph_from_anomaly","core_deletes_nodes_or_edges_from_anomaly","core_promotes_anomaly_to_evidence","runtime_may_mutate_evidence_graph","runtime_may_assert_wrongdoing","v374_determines_anomaly_truth"])
def test_boundaries(key): assert contract_document()['boundaries'][key] is False
def test_review_requirements_all_true(): assert all(contract_document()['review_requirements'].values())
def test_extends_v373(): assert 'sc.core.graph-link-prediction-candidate-relationship.v1' in contract_document()['extends_contracts']
def test_prepares_v375(): assert contract_document()['roadmap_integration']['prepares_v3750_knowledge_graph_representation_learning'] is True
def test_prepares_v376(): assert contract_document()['roadmap_integration']['prepares_v3760_evidence_graph_neural_analysis_validation_workflow'] is True
