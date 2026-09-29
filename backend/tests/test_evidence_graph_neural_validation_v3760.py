import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.services.evidence_graph_neural_validation import *
from app.routers import evidence_graph_neural_validation

def ref(): return reference_evidence_graph_neural_validation_bundle()
def test_release(): assert CORE_RELEASE=="3.76.0"
def test_contract(): assert CONTRACT_VERSION=="sc.core.evidence-graph-neural-analysis-validation.v1"
def test_roundtrip(): b=ref(); assert EvidenceGraphNeuralValidationBundle.model_validate(b.model_dump(mode="json")).fingerprint()==b.fingerprint()
def test_fingerprint_deterministic(): assert ref().fingerprint()==ref().fingerprint()
def test_signal_count(): assert len(ref().neural_signals)==4
def test_signal_sources_non_evidence(): assert all(not x.is_evidence and not x.is_graph_fact and not x.may_satisfy_evidence_gate for x in ref().neural_signals)
def test_evidence_items_independent(): assert all(x.independent_of_model_output for x in ref().evidence_items)
def test_policy_blocks_model_probability(): assert ref().policies[0].model_probability_can_satisfy_gate is False
def test_policy_blocks_anomaly(): assert ref().policies[0].anomaly_score_can_satisfy_gate is False
def test_policy_blocks_embedding(): assert ref().policies[0].embedding_similarity_can_satisfy_gate is False
def test_policy_blocks_classification(): assert ref().policies[0].classification_output_can_satisfy_gate is False
def test_policy_blocks_kg_score(): assert ref().policies[0].kg_triple_score_can_satisfy_gate is False
def test_case_candidate_still_not_fact(): assert ref().validation_cases[0].candidate_still_not_graph_fact is True
def test_case_separates_model_from_evidence(): assert ref().validation_cases[0].neural_signals_do_not_count_as_evidence is True
def test_two_independent_reviewers(): assert len({x.reviewer_ref for x in ref().assessments})==2
def test_reviewers_independent(): assert all(x.reviewer_independent_of_model_run for x in ref().assessments)
def test_review_does_not_create_edge(): assert all(x.assessment_does_not_itself_create_edge for x in ref().assessments)
def test_authorization_is_not_mutation(): assert ref().promotion_authorizations[0].actual_evidence_graph_mutation_performed is False
def test_authorization_models_not_counted(): assert ref().promotion_authorizations[0].model_outputs_counted_as_evidence is False
def test_authorization_models_cannot_authorize(): assert ref().promotion_authorizations[0].model_outputs_can_authorize_promotion is False
def test_authorized_has_proposed_edge(): assert ref().promotion_authorizations[0].proposed_evidence_edge_ref
def test_authorized_requires_downstream_creation(): assert ref().promotion_authorizations[0].authorization_requires_downstream_edge_creation is True
def test_audit_append_only(): assert all(x.append_only_audit_event for x in ref().audit_records)
def test_bad_signal_source_rejected():
    b=ref().model_copy(deep=True); b.neural_signals[0].source_object_ref='missing:prediction'
    with pytest.raises(ValidationError): EvidenceGraphNeuralValidationBundle.model_validate(b.model_dump(mode='json'))
def test_bad_candidate_rejected():
    b=ref().model_copy(deep=True); b.validation_cases[0].candidate_relationship_ref='missing:candidate'
    with pytest.raises(ValidationError): EvidenceGraphNeuralValidationBundle.model_validate(b.model_dump(mode='json'))
def test_case_identity_mismatch_rejected():
    b=ref().model_copy(deep=True); b.validation_cases[0].relationship_type_candidate='wrong-type'
    with pytest.raises(ValidationError): EvidenceGraphNeuralValidationBundle.model_validate(b.model_dump(mode='json'))
def test_authorized_without_proposed_edge_rejected():
    d=ref().promotion_authorizations[0].model_dump(); d['proposed_evidence_edge_ref']=None
    with pytest.raises(ValidationError): EvidenceEdgePromotionAuthorization.model_validate(d)
def test_authorized_without_gates_rejected():
    d=ref().promotion_authorizations[0].model_dump(); d['evidence_provenance_verified']=False
    with pytest.raises(ValidationError): EvidenceEdgePromotionAuthorization.model_validate(d)
def test_authorized_insufficient_support_rejected():
    b=ref().model_copy(deep=True); b.promotion_authorizations[0].supporting_evidence_item_refs=b.promotion_authorizations[0].supporting_evidence_item_refs[:1]
    with pytest.raises(ValidationError): EvidenceGraphNeuralValidationBundle.model_validate(b.model_dump(mode='json'))
def test_authorized_insufficient_reviewers_rejected():
    b=ref().model_copy(deep=True); b.promotion_authorizations[0].reviewer_assessment_refs=b.promotion_authorizations[0].reviewer_assessment_refs[:1]
    with pytest.raises(ValidationError): EvidenceGraphNeuralValidationBundle.model_validate(b.model_dump(mode='json'))
def test_support_review_needs_evidence():
    d=ref().assessments[0].model_dump(); d['supporting_evidence_item_refs']=[]
    with pytest.raises(ValidationError): IndependentEvidenceAssessmentRecord.model_validate(d)
def test_case_self_ref_rejected():
    d=ref().validation_cases[0].model_dump(); d['target_node_ref']=d['source_node_ref']
    with pytest.raises(ValidationError): EvidenceGraphNeuralValidationCase.model_validate(d)
def test_public_route():
    a=FastAPI(); a.include_router(evidence_graph_neural_validation.public_router)
    with TestClient(a) as c: z=c.get('/public/v1/evidence-graph-neural-validation/contract')
    assert z.status_code==200 and z.json()['release']=='3.76.0'
@pytest.mark.parametrize('key',["gnn_prediction_is_not_graph_fact","neural_signal_is_not_evidence","anomaly_is_not_evidence","embedding_similarity_is_not_evidence","classification_output_is_not_evidence","kg_triple_score_is_not_evidence","model_output_cannot_satisfy_evidence_gate","promotion_requires_independent_evidence","promotion_requires_evidence_provenance","contradictory_evidence_must_be_reviewable","authorization_is_not_graph_mutation"])
def test_principles(key): assert contract_document()['principles'][key] is True
@pytest.mark.parametrize('key',["core_treats_model_output_as_evidence","core_allows_model_score_to_satisfy_promotion_gate","core_auto_promotes_candidate_relationship","core_mutates_evidence_graph_during_neural_validation","runtime_may_promote_candidate_to_evidence_edge","authorization_itself_creates_evidence_edge"])
def test_boundaries(key): assert contract_document()['boundaries'][key] is False
def test_completes_gnn_wave(): assert contract_document()['roadmap_integration']['completes_graph_neural_wave_v3700_through_v3760'] is True
def test_reconnects_evidence_architecture(): assert contract_document()['roadmap_integration']['reconnects_graph_ml_to_evidence_validation_architecture'] is True
def test_schema_generation(): assert EvidenceGraphNeuralValidationBundle.model_json_schema()['title']=='EvidenceGraphNeuralValidationBundle'
