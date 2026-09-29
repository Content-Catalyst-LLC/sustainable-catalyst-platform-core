import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import graph_link_prediction
from app.services.graph_link_prediction import *


def ref(): return reference_graph_link_prediction_bundle()

def test_release_identity():
    assert CORE_RELEASE == "3.73.0"
    assert CONTRACT_VERSION == "sc.core.graph-link-prediction-candidate-relationship.v1"

def test_reference_bundle_counts():
    b=ref(); assert len(b.candidate_pairs)==1 and len(b.predictions)==1 and len(b.candidate_relationships)==1 and len(b.promotion_gates)==1

def test_bundle_fingerprint(): assert len(ref().fingerprint()) == 64

def test_candidate_pair_non_relationship():
    p=ref().candidate_pairs[0]; assert p.candidate_pair_is_not_relationship and p.candidate_pair_is_not_evidence

def test_prediction_is_not_fact_or_evidence():
    p=ref().predictions[0]; assert p.is_graph_fact is False and p.is_evidence is False and p.is_evidence_edge is False

def test_candidate_is_not_fact_or_evidence_edge():
    c=ref().candidate_relationships[0]; assert c.is_graph_fact is False and c.is_evidence is False and c.is_evidence_edge is False

def test_candidate_requires_separate_evidence_validation(): assert ref().candidate_relationships[0].separate_evidence_validation_required_for_promotion is True

def test_supported_candidate_only_eligible_for_validation():
    c=ref().candidate_relationships[0]; assert c.state==CandidateRelationshipState.supported_for_validation and c.validation_state==CandidateValidationState.eligible_for_evidence_validation

def test_review_not_truth_or_evidence_edge():
    r=ref().review_records[0]; assert r.review_is_not_truth_determination and r.review_does_not_create_evidence_edge

def test_promotion_gate_forbids_model_only_promotion():
    g=ref().promotion_gates[0]; assert g.model_probability_can_satisfy_gate is False and g.embedding_similarity_can_satisfy_gate is False and g.classification_output_can_satisfy_gate is False

def test_promotion_gate_forbids_v373_edge_creation(): assert ref().promotion_gates[0].v373_may_create_evidence_edge is False

def test_candidate_pair_endpoints_exist():
    b=ref(); p=b.candidate_pairs[0]; s=b.graph_classification_bundle.graph_embedding_bundle.graph_ml_foundation_bundle.snapshots[0]; assert p.source_node_ref in s.node_refs and p.target_node_ref in s.node_refs

def test_candidate_pair_self_reference_rejected():
    p=ref().candidate_pairs[0].model_dump(); p['target_node_ref']=p['source_node_ref']
    with pytest.raises(ValidationError): LinkPredictionCandidatePair.model_validate(p)

def test_task_kind_is_link_prediction(): assert ref().tasks[0].graph_ml_task_kind.value=='link-prediction'

def test_probability_mass_sums_one():
    p=ref().predictions[0]; assert abs(sum(x.probability for x in p.relationship_type_probabilities)+p.no_relationship_probability-1.0)<1e-9

def test_bad_probability_mass_rejected():
    p=ref().predictions[0].model_dump(); p['no_relationship_probability']=.50
    with pytest.raises(ValidationError): LinkPredictionRecord.model_validate(p)

def test_predicted_type_must_be_max():
    p=ref().predictions[0].model_dump(); p['predicted_relationship_type']='translation-related'
    with pytest.raises(ValidationError): LinkPredictionRecord.model_validate(p)

def test_calibrated_prediction_requires_calibration_ref():
    p=ref().predictions[0].model_dump(); p['calibration_ref']=None
    with pytest.raises(ValidationError): LinkPredictionRecord.model_validate(p)

def test_reviewed_prediction_requires_reviewer():
    p=ref().predictions[0].model_dump(); p['review_state']='human-reviewed'; p['reviewer_ref']=None
    with pytest.raises(ValidationError): LinkPredictionRecord.model_validate(p)

def test_missing_pair_ref_rejected_by_bundle():
    b=ref().model_copy(deep=True); b.predictions[0].candidate_pair_ref='pair:missing'
    with pytest.raises(ValidationError): GraphLinkPredictionBundle.model_validate(b.model_dump(mode='json'))

def test_missing_embedding_ref_rejected_by_bundle():
    b=ref().model_copy(deep=True); b.candidate_pairs[0].embedding_refs=['embedding:missing']
    with pytest.raises(ValidationError): GraphLinkPredictionBundle.model_validate(b.model_dump(mode='json'))

def test_candidate_endpoint_mismatch_rejected():
    b=ref().model_copy(deep=True); b.candidate_relationships[0].target_node_ref=b.graph_classification_bundle.graph_embedding_bundle.graph_ml_foundation_bundle.snapshots[0].node_refs[1]
    with pytest.raises(ValidationError): GraphLinkPredictionBundle.model_validate(b.model_dump(mode='json'))

def test_candidate_type_mismatch_rejected():
    b=ref().model_copy(deep=True); b.candidate_relationships[0].relationship_type_candidate='translation-related'
    with pytest.raises(ValidationError): GraphLinkPredictionBundle.model_validate(b.model_dump(mode='json'))

def test_review_requires_candidate_ref():
    b=ref().model_copy(deep=True); b.review_records[0].candidate_relationship_ref='candidate:missing'
    with pytest.raises(ValidationError): GraphLinkPredictionBundle.model_validate(b.model_dump(mode='json'))

def test_supported_review_state_pairing():
    r=ref().review_records[0].model_dump(); r['validation_state_after_review']='evidence-review-required'
    with pytest.raises(ValidationError): CandidateRelationshipReviewRecord.model_validate(r)

def test_rejected_candidate_state_pairing():
    c=ref().candidate_relationships[0].model_dump(); c['state']='rejected'; c['validation_state']='unvalidated'
    with pytest.raises(ValidationError): CandidateRelationship.model_validate(c)

def test_evaluation_metrics_are_finite(): assert all(x==x for x in ref().evaluations[0].metric_values.values())

def test_public_route():
    a=FastAPI(); a.include_router(graph_link_prediction.public_router)
    with TestClient(a) as c: r=c.get('/public/v1/link-prediction/contract')
    assert r.status_code==200 and r.json()['release']=='3.73.0'

@pytest.mark.parametrize('key',[
    'link_prediction_is_derived_model_output','predicted_link_is_not_graph_fact','predicted_link_is_not_evidence',
    'candidate_relationship_is_not_graph_fact','candidate_relationship_is_not_evidence_edge','human_review_does_not_create_evidence_edge',
    'high_probability_does_not_establish_relationship','embedding_similarity_does_not_establish_relationship',
    'classification_output_does_not_establish_relationship','contradicting_evidence_must_remain_visible','gnn_prediction_is_not_graph_fact'])
def test_principles(key): assert contract_document()['principles'][key] is True

@pytest.mark.parametrize('key',[
    'core_generates_candidate_pairs','core_trains_link_predictor','core_runs_link_prediction_inference',
    'core_promotes_candidate_to_evidence_edge','core_mutates_evidence_graph_from_link_prediction','runtime_may_mutate_evidence_graph',
    'runtime_may_promote_candidate_to_evidence_edge','v373_creates_evidence_edges_from_predictions','v373_determines_relationship_truth'])
def test_boundaries(key): assert contract_document()['boundaries'][key] is False

def test_promotion_requirements_all_true(): assert all(contract_document()['promotion_requirements'].values())
def test_extends_classification_contract(): assert 'sc.core.graph-node-edge-classification.v1' in contract_document()['extends_contracts']
def test_roadmap_v374(): assert contract_document()['roadmap_integration']['prepares_v3740_graph_anomaly_detection'] is True
def test_roadmap_v376(): assert contract_document()['roadmap_integration']['prepares_v3760_evidence_graph_neural_analysis_validation_workflow'] is True
