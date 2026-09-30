import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import probabilistic_record_linkage as routes
from app.services.probabilistic_record_linkage import (
    CONTRACT_VERSION, CORE_RELEASE, ProbabilisticRecordLinkageBundle,
    RecordLinkageCandidatePair, RecordLinkageFeatureObservation,
    EntityMatchProbabilityRecord, EntityMatchThresholdPolicy,
    PairwiseEntityMatchDecision, MatchDecisionState, contract_document,
    reference_probabilistic_record_linkage_bundle,
)


def ref(): return reference_probabilistic_record_linkage_bundle()
def client():
    app=FastAPI(); app.include_router(routes.router); app.include_router(routes.public_router); return TestClient(app)

def test_release(): assert CORE_RELEASE=="3.79.0"
def test_contract(): assert CONTRACT_VERSION=="sc.core.probabilistic-record-linkage-entity-matching.v1"
def test_extends_v377(): assert "sc.core.entity-resolution-identity-graph-foundation.v1" in contract_document()["extends_contracts"]
def test_extends_v378(): assert "sc.core.temporal-identity-alias-name-variant-intelligence.v1" in contract_document()["extends_contracts"]
def test_three_features(): assert len(ref().feature_definitions)==3
def test_one_block(): assert len(ref().blocking_rules)==1
def test_one_pair(): assert len(ref().candidate_pairs)==1
def test_three_observations(): assert len(ref().feature_observations)==3
def test_one_model(): assert len(ref().model_specifications)==1
def test_one_calibration(): assert len(ref().calibrations)==1
def test_one_probability(): assert len(ref().probability_records)==1
def test_one_threshold(): assert len(ref().threshold_policies)==1
def test_one_decision(): assert len(ref().decisions)==1
def test_two_reviews(): assert len(ref().reviews)==2
def test_one_evaluation(): assert len(ref().evaluations)==1
def test_match_probability(): assert ref().probability_records[0].match_probability==0.97
def test_nonmatch_probability(): assert ref().probability_records[0].nonmatch_probability==0.03
def test_probability_not_fact(): assert ref().probability_records[0].is_identity_fact is False
def test_probability_not_evidence(): assert ref().probability_records[0].is_identity_evidence is False
def test_probability_cannot_merge(): assert ref().probability_records[0].probability_cannot_authorize_merge is True
def test_nonmatch_not_distinct_identity_proof(): assert ref().probability_records[0].nonmatch_probability_is_not_proof_of_distinct_identity is True
def test_feature_agreement_not_evidence(): assert all(x.feature_agreement_is_not_identity_evidence for x in ref().feature_definitions)
def test_block_not_evidence(): assert ref().blocking_rules[0].block_membership_is_not_identity_evidence is True
def test_candidate_not_fact(): assert ref().candidate_pairs[0].candidate_pair_is_not_identity_fact is True
def test_candidate_generation_not_evidence(): assert ref().candidate_pairs[0].candidate_generation_is_not_identity_evidence is True
def test_calibration_not_fact(): assert ref().calibrations[0].calibration_does_not_convert_probability_to_fact is True
def test_threshold_not_fact(): assert ref().threshold_policies[0].threshold_crossing_is_not_identity_fact is True
def test_threshold_cannot_merge(): assert ref().threshold_policies[0].threshold_crossing_cannot_authorize_merge is True
def test_decision_not_canonical(): assert ref().decisions[0].decision_is_not_canonical_identity is True
def test_decision_no_equivalence_edge(): assert ref().decisions[0].decision_does_not_create_equivalence_edge is True
def test_v377_resolution_required(): assert ref().decisions[0].downstream_v377_identity_resolution_required is True
def test_review_probability_context(): assert all(x.probability_is_context_not_identity_evidence for x in ref().reviews)
def test_review_no_merge(): assert all(x.review_does_not_merge_entities for x in ref().reviews)
def test_eval_not_truth(): assert ref().evaluations[0].evaluation_metric_is_not_identity_truth_measure is True
def test_bundle_no_auto_merge(): assert ref().automatic_merge_allowed is False
def test_bundle_no_auto_split(): assert ref().automatic_split_allowed is False
def test_bundle_no_mutation(): assert ref().identity_graph_mutation_performed is False
def test_bundle_probability_not_fact(): assert ref().match_probability_is_not_identity_fact is True
def test_bundle_output_not_evidence(): assert ref().linkage_output_is_not_identity_evidence is True
def test_reference_fingerprint_stable(): assert ref().fingerprint()==ref().fingerprint()
def test_contract_fingerprint_64(): assert len(contract_document()["reference"]["bundle_fingerprint_sha256"])==64

def test_self_pair_rejected():
    d=ref().candidate_pairs[0].model_dump(); d["right_entity_ref"]=d["left_entity_ref"]
    with pytest.raises(ValidationError): RecordLinkageCandidatePair.model_validate(d)
def test_probability_sum_rejected():
    d=ref().probability_records[0].model_dump(); d["nonmatch_probability"]=0.2
    with pytest.raises(ValidationError): EntityMatchProbabilityRecord.model_validate(d)
def test_bad_threshold_order_rejected():
    d=ref().threshold_policies[0].model_dump(); d["review_at_or_above"]=0.95; d["support_candidate_at_or_above"]=0.8
    with pytest.raises(ValidationError): EntityMatchThresholdPolicy.model_validate(d)
def test_supported_decision_requires_candidate_ref():
    d=ref().decisions[0].model_dump(); d["candidate_entity_match_ref"]=None
    with pytest.raises(ValidationError): PairwiseEntityMatchDecision.model_validate(d)
def test_supported_decision_requires_reviews():
    d=ref().decisions[0].model_dump(); d["review_refs"]=[]
    with pytest.raises(ValidationError): PairwiseEntityMatchDecision.model_validate(d)
def test_unknown_pair_entity_rejected():
    b=ref().model_copy(deep=True); b.candidate_pairs[0].left_entity_ref="entity:missing"
    with pytest.raises(ValidationError): ProbabilisticRecordLinkageBundle.model_validate(b.model_dump(mode="json"))
def test_unknown_source_assertion_rejected():
    b=ref().model_copy(deep=True); b.candidate_pairs[0].left_source_identity_assertion_refs=["source-identity:missing"]
    with pytest.raises(ValidationError): ProbabilisticRecordLinkageBundle.model_validate(b.model_dump(mode="json"))
def test_unknown_block_rejected():
    b=ref().model_copy(deep=True); b.candidate_pairs[0].blocking_rule_refs=["blocking:missing"]
    with pytest.raises(ValidationError): ProbabilisticRecordLinkageBundle.model_validate(b.model_dump(mode="json"))
def test_unknown_observation_feature_rejected():
    b=ref().model_copy(deep=True); b.feature_observations[0].feature_ref="feature:missing"
    with pytest.raises(ValidationError): ProbabilisticRecordLinkageBundle.model_validate(b.model_dump(mode="json"))
def test_unknown_observation_pair_rejected():
    b=ref().model_copy(deep=True); b.feature_observations[0].linkage_pair_ref="pair:missing"
    with pytest.raises(ValidationError): ProbabilisticRecordLinkageBundle.model_validate(b.model_dump(mode="json"))
def test_unknown_model_feature_rejected():
    b=ref().model_copy(deep=True); b.model_specifications[0].feature_refs=["feature:missing"]
    with pytest.raises(ValidationError): ProbabilisticRecordLinkageBundle.model_validate(b.model_dump(mode="json"))
def test_unknown_calibration_model_rejected():
    b=ref().model_copy(deep=True); b.calibrations[0].model_ref="model:missing"
    with pytest.raises(ValidationError): ProbabilisticRecordLinkageBundle.model_validate(b.model_dump(mode="json"))
def test_unknown_probability_model_rejected():
    b=ref().model_copy(deep=True); b.probability_records[0].model_ref="model:missing"
    with pytest.raises(ValidationError): ProbabilisticRecordLinkageBundle.model_validate(b.model_dump(mode="json"))
def test_unknown_probability_observation_rejected():
    b=ref().model_copy(deep=True); b.probability_records[0].feature_observation_refs=["observation:missing"]
    with pytest.raises(ValidationError): ProbabilisticRecordLinkageBundle.model_validate(b.model_dump(mode="json"))
def test_unknown_decision_probability_rejected():
    b=ref().model_copy(deep=True); b.decisions[0].probability_record_ref="probability:missing"
    with pytest.raises(ValidationError): ProbabilisticRecordLinkageBundle.model_validate(b.model_dump(mode="json"))
def test_unknown_v377_candidate_rejected():
    b=ref().model_copy(deep=True); b.decisions[0].candidate_entity_match_ref="candidate:missing"
    with pytest.raises(ValidationError): ProbabilisticRecordLinkageBundle.model_validate(b.model_dump(mode="json"))
def test_unknown_review_evidence_rejected():
    b=ref().model_copy(deep=True); b.reviews[0].identity_evidence_refs=["evidence:missing"]
    with pytest.raises(ValidationError): ProbabilisticRecordLinkageBundle.model_validate(b.model_dump(mode="json"))
def test_unknown_evaluation_model_rejected():
    b=ref().model_copy(deep=True); b.evaluations[0].model_ref="model:missing"
    with pytest.raises(ValidationError): ProbabilisticRecordLinkageBundle.model_validate(b.model_dump(mode="json"))

def test_public_contract_route():
    r=client().get("/public/v1/record-linkage/contract"); assert r.status_code==200; assert r.json()["release"]=="3.79.0"
def test_private_contract_route():
    r=client().get("/v1/record-linkage/contract"); assert r.status_code==200; assert r.json()["contract"]==CONTRACT_VERSION
def test_reference_route():
    r=client().get("/v1/record-linkage/reference"); assert r.status_code==200; assert r.json()["ok"] is True
def test_validate_pair_route():
    r=client().post("/v1/record-linkage/validate-pair",json=ref().candidate_pairs[0].model_dump(mode="json")); assert r.status_code==200
def test_validate_probability_route():
    r=client().post("/v1/record-linkage/validate-probability",json=ref().probability_records[0].model_dump(mode="json")); assert r.status_code==200
def test_validate_decision_route():
    r=client().post("/v1/record-linkage/validate-decision",json=ref().decisions[0].model_dump(mode="json")); assert r.status_code==200
def test_validate_bundle_route():
    r=client().post("/v1/record-linkage/validate-bundle",json=ref().model_dump(mode="json")); assert r.status_code==200

def test_contract_no_execution(): assert contract_document()["boundaries"]["core_executes_record_linkage_model"] is False
def test_contract_no_training(): assert contract_document()["boundaries"]["core_trains_record_linkage_model"] is False
def test_contract_no_probability_evidence(): assert contract_document()["boundaries"]["core_treats_probability_as_identity_evidence"] is False
def test_contract_no_auto_merge(): assert contract_document()["boundaries"]["core_auto_merges_entities_from_probability"] is False
def test_contract_no_auto_split(): assert contract_document()["boundaries"]["core_auto_splits_entities_from_nonmatch_probability"] is False
def test_contract_no_equivalence_edge(): assert contract_document()["boundaries"]["core_creates_canonical_equivalence_edge_from_linkage_output"] is False
def test_contract_no_policy_bypass(): assert contract_document()["boundaries"]["core_bypasses_v377_identity_review_policy"] is False
def test_contract_prepares_v380(): assert contract_document()["roadmap_integration"]["prepares_v3800_cross_source_entity_reconciliation"] is True
