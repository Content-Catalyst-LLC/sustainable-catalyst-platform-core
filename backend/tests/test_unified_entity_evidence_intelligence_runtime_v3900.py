import pytest
from pydantic import ValidationError
from app.services.unified_entity_evidence_intelligence_runtime import (
    CORE_RELEASE, CONTRACT_VERSION, RuntimeStageKind, RuntimeStageStatus, RuntimeDisposition,
    UnifiedEntityEvidenceIntelligenceRuntimeBundle, RuntimeCapabilityBinding, UnifiedRuntimeRequest,
    RuntimeHandoffDecision, reference_unified_entity_evidence_intelligence_runtime_bundle, contract_document,
)

def ref(): return reference_unified_entity_evidence_intelligence_runtime_bundle()
def test_release(): assert CORE_RELEASE=='3.90.0'
def test_contract(): assert CONTRACT_VERSION=='sc.core.unified-entity-evidence-intelligence-runtime.v1'
def test_reference_valid(): assert ref().release=='3.90.0'
def test_counts():
    b=ref(); assert (len(b.capabilities),len(b.policies),len(b.requests),len(b.stage_executions),len(b.handoffs),len(b.findings),len(b.traces),len(b.snapshots))==(13,1,1,13,12,2,1,1)
def test_all_stage_kinds_bound(): assert {x.stage_kind for x in ref().capabilities}==set(RuntimeStageKind)
def test_sequence_contiguous(): assert [x.sequence for x in ref().stage_executions]==list(range(1,14))
def test_final_disposition(): assert ref().traces[0].final_disposition==RuntimeDisposition.qualified_analytical
def test_fingerprint_stable(): assert ref().fingerprint()==ref().fingerprint()
def test_contract_fingerprint(): assert contract_document()['reference']['bundle_fingerprint_sha256']==ref().fingerprint()
def test_no_graph_mutation():
    b=ref(); assert not b.identity_graph_mutation_performed and not b.relationship_graph_mutation_performed and not b.evidence_graph_mutation_performed

def test_unknown_request_capability_rejected():
    d=ref().model_dump(mode='python'); d['requests'][0]['requested_capability_refs'].append('capability:missing')
    with pytest.raises(ValidationError): UnifiedEntityEvidenceIntelligenceRuntimeBundle.model_validate(d)
def test_unknown_stage_capability_rejected():
    d=ref().model_dump(mode='python'); d['stage_executions'][0]['capability_ref']='capability:missing'
    with pytest.raises(ValidationError): UnifiedEntityEvidenceIntelligenceRuntimeBundle.model_validate(d)
def test_noncontiguous_sequence_rejected():
    d=ref().model_dump(mode='python'); d['stage_executions'][5]['sequence']=99
    with pytest.raises(ValidationError): UnifiedEntityEvidenceIntelligenceRuntimeBundle.model_validate(d)
def test_backward_handoff_rejected():
    d=ref().model_dump(mode='python'); d['handoffs'][0]['from_stage_ref']='runtime-stage:synthetic:2'; d['handoffs'][0]['to_stage_ref']='runtime-stage:synthetic:1'
    with pytest.raises(ValidationError): UnifiedEntityEvidenceIntelligenceRuntimeBundle.model_validate(d)
def test_duplicate_request_caps_rejected():
    d=ref().requests[0].model_dump(mode='python'); d['requested_capability_refs']=[d['requested_capability_refs'][0]]*2
    with pytest.raises(ValidationError): UnifiedRuntimeRequest.model_validate(d)
def test_same_stage_handoff_rejected():
    d=ref().handoffs[0].model_dump(mode='python'); d['to_stage_ref']=d['from_stage_ref']
    with pytest.raises(ValidationError): RuntimeHandoffDecision.model_validate(d)
def test_bad_capability_hash_rejected():
    d=ref().capabilities[0].model_dump(mode='python'); d['reference_bundle_fingerprint_sha256']='bad'
    with pytest.raises(ValidationError): RuntimeCapabilityBinding.model_validate(d)

@pytest.mark.parametrize('field',[
    'require_capability_contract_identity','require_provenance_preservation','require_epistemic_state_preservation','require_contradiction_preservation',
    'require_explicit_handoffs','require_explicit_stopping_decisions','require_local_validation_for_remote_references','require_human_review_for_promotion'
])
def test_policy_requirements(field): assert getattr(ref().policies[0],field) is True

@pytest.mark.parametrize('field',[
    'runtime_may_create_global_truth_score','runtime_may_auto_promote_candidates','runtime_may_auto_resolve_contradictions',
    'runtime_may_treat_remote_acceptance_as_evidence','runtime_may_mutate_governed_graphs'
])
def test_policy_prohibitions(field): assert getattr(ref().policies[0],field) is False

@pytest.mark.parametrize('field',[
    'unified_runtime_over_v3770_through_v3890','upstream_contract_identity_preserved','epistemic_state_preserved_across_stages',
    'provenance_preserved_across_stages','contradictions_preserved_across_stages','explicit_handoffs_and_stopping_rules',
    'local_validation_required_for_remote_references','human_review_required_for_promotion','reproducible_runtime_trace'
])
def test_contract_principles(field): assert contract_document()['principles'][field] is True

@pytest.mark.parametrize('field',[
    'runtime_creates_global_truth_score','runtime_auto_promotes_candidates','runtime_auto_resolves_contradictions',
    'analytical_confidence_is_probability_of_truth','completed_runtime_is_truth_certification','remote_acceptance_is_local_evidence',
    'identity_graph_mutation_performed','relationship_graph_mutation_performed','evidence_graph_mutation_performed'
])
def test_contract_boundaries(field): assert contract_document()['boundaries'][field] is False

@pytest.mark.parametrize('i',range(13))
def test_capability_preserves_contract(i): assert ref().capabilities[i].preserves_upstream_contract is True
@pytest.mark.parametrize('i',range(13))
def test_capability_preserves_epistemic_state(i): assert ref().capabilities[i].preserves_epistemic_state is True
@pytest.mark.parametrize('i',range(13))
def test_capability_preserves_provenance(i): assert ref().capabilities[i].preserves_provenance is True
@pytest.mark.parametrize('i',range(13))
def test_capability_no_identity_mutation(i): assert ref().capabilities[i].may_mutate_identity_graph is False
@pytest.mark.parametrize('i',range(13))
def test_capability_no_relationship_mutation(i): assert ref().capabilities[i].may_mutate_relationship_graph is False
@pytest.mark.parametrize('i',range(13))
def test_capability_no_evidence_mutation(i): assert ref().capabilities[i].may_mutate_evidence_graph is False
@pytest.mark.parametrize('i',range(13))
def test_capability_hashes(i): assert len(ref().capabilities[i].reference_bundle_fingerprint_sha256)==64
@pytest.mark.parametrize('i',range(13))
def test_stage_outputs_not_truth(i): assert ref().stage_executions[i].stage_output_is_not_truth_verdict is True
@pytest.mark.parametrize('i',range(13))
def test_stage_no_auto_promotion(i): assert ref().stage_executions[i].stage_does_not_auto_promote_graph_fact is True
@pytest.mark.parametrize('i',range(12))
def test_handoff_required(i): assert ref().handoffs[i].handoff_required is True
@pytest.mark.parametrize('i',range(12))
def test_handoff_no_auto_promotion(i): assert ref().handoffs[i].auto_promotion_allowed is False
@pytest.mark.parametrize('i',range(12))
def test_handoff_not_validation(i): assert ref().handoffs[i].handoff_is_not_validation is True
@pytest.mark.parametrize('i',range(2))
def test_findings_need_review(i): assert ref().findings[i].human_review_required is True
@pytest.mark.parametrize('i',range(2))
def test_findings_not_truth(i): assert ref().findings[i].finding_is_not_truth_verdict is True
@pytest.mark.parametrize('i',range(2))
def test_confidence_not_truth_probability(i): assert ref().findings[i].analytical_confidence_is_not_probability_of_truth is True

def test_trace_not_proof(): assert ref().traces[0].trace_is_not_proof is True
def test_trace_not_certification(): assert ref().traces[0].completed_runtime_is_not_truth_certification is True
def test_snapshot_immutable(): assert ref().snapshots[0].immutable is True
def test_snapshot_upstream_authority(): assert ref().snapshots[0].upstream_objects_remain_authoritative_for_their_own_state is True
def test_snapshot_supersedable(): assert ref().snapshots[0].later_evidence_may_supersede_snapshot is True
def test_snapshot_not_truth(): assert ref().snapshots[0].snapshot_is_not_truth_verdict is True
@pytest.mark.parametrize('state',list(RuntimeStageKind))
def test_stage_kind_enum(state): assert state.value
@pytest.mark.parametrize('state',list(RuntimeStageStatus))
def test_stage_status_enum(state): assert state.value
@pytest.mark.parametrize('state',list(RuntimeDisposition))
def test_disposition_enum(state): assert state.value
