import pytest
from pydantic import ValidationError

from app.services.unified_entity_evidence_query_api import (
    CONTRACT_VERSION, CORE_RELEASE, EpistemicState, QueryExecutionDisposition, QueryMode,
    QueryTargetKind, ResultValidationState, UnifiedEntityEvidenceQueryBundle,
    UnifiedQueryResultItem, contract_document, reference_unified_entity_evidence_query_bundle,
)


def ref(): return reference_unified_entity_evidence_query_bundle()

def test_release(): assert CORE_RELEASE=="3.92.0"
def test_contract(): assert CONTRACT_VERSION=="sc.core.unified-entity-evidence-query-api.v1"
def test_reference_valid(): assert UnifiedEntityEvidenceQueryBundle.model_validate(ref().model_dump(mode="python")).release=="3.92.0"
def test_counts():
    b=ref(); assert (len(b.plan_steps),len(b.results),len(b.provenance_refs))==(15,15,15)
def test_remote_reference_preserved():
    x=next(x for x in ref().results if x.target_kind==QueryTargetKind.federation_reference)
    assert x.epistemic_state==EpistemicState.remote_reference and x.validation_state==ResultValidationState.local_validation_required
def test_candidate_preserved():
    x=next(x for x in ref().results if x.epistemic_state==EpistemicState.candidate)
    assert x.validation_state==ResultValidationState.review_required
def test_hypothesis_preserved():
    x=next(x for x in ref().results if x.epistemic_state==EpistemicState.hypothesis)
    assert x.validation_state==ResultValidationState.review_required
def test_complete_with_qualifications(): assert ref().traces[0].final_disposition==QueryExecutionDisposition.complete_with_qualifications
def test_duplicate_scope_capability_rejected():
    d=ref().model_dump(mode="python"); d["scopes"][0]["capability_refs"].append(d["scopes"][0]["capability_refs"][0])
    with pytest.raises(ValidationError): UnifiedEntityEvidenceQueryBundle.model_validate(d)
def test_unknown_scope_capability_rejected():
    d=ref().model_dump(mode="python"); d["scopes"][0]["capability_refs"].append("runtime-capability:missing")
    with pytest.raises(ValidationError): UnifiedEntityEvidenceQueryBundle.model_validate(d)
def test_unknown_query_consumer_rejected():
    d=ref().model_dump(mode="python"); d["queries"][0]["consumer_ref"]="consumer:missing"
    with pytest.raises(ValidationError): UnifiedEntityEvidenceQueryBundle.model_validate(d)
def test_step_contract_mismatch_rejected():
    d=ref().model_dump(mode="python"); d["plan_steps"][0]["output_contract"]="wrong.contract"
    with pytest.raises(ValidationError): UnifiedEntityEvidenceQueryBundle.model_validate(d)
def test_step_capability_outside_scope_rejected():
    d=ref().model_dump(mode="python"); d["scopes"][0]["capability_refs"].remove(d["plan_steps"][0]["capability_ref"])
    with pytest.raises(ValidationError): UnifiedEntityEvidenceQueryBundle.model_validate(d)
def test_duplicate_step_ordinal_rejected():
    d=ref().model_dump(mode="python"); d["plan_steps"][1]["ordinal"]=d["plan_steps"][0]["ordinal"]
    with pytest.raises(ValidationError): UnifiedEntityEvidenceQueryBundle.model_validate(d)
def test_plan_selected_capability_mismatch_rejected():
    d=ref().model_dump(mode="python"); d["plans"][0]["selected_capability_refs"]=d["plans"][0]["selected_capability_refs"][:-1]
    with pytest.raises(ValidationError): UnifiedEntityEvidenceQueryBundle.model_validate(d)
def test_result_contract_mismatch_rejected():
    d=ref().model_dump(mode="python"); d["results"][0]["source_contract"]="wrong.contract"
    with pytest.raises(ValidationError): UnifiedEntityEvidenceQueryBundle.model_validate(d)
def test_result_target_mismatch_rejected():
    d=ref().model_dump(mode="python"); d["results"][0]["target_kind"]="timeline"
    with pytest.raises(ValidationError): UnifiedEntityEvidenceQueryBundle.model_validate(d)
def test_unknown_result_provenance_rejected():
    d=ref().model_dump(mode="python"); d["results"][0]["provenance_refs"]=["query-provenance:missing"]
    with pytest.raises(ValidationError): UnifiedEntityEvidenceQueryBundle.model_validate(d)
def test_result_set_count_mismatch_rejected():
    d=ref().model_dump(mode="python"); d["result_sets"][0]["returned_results"]-=1
    with pytest.raises(ValidationError): UnifiedEntityEvidenceQueryBundle.model_validate(d)
def test_result_set_limit_mismatch_rejected():
    d=ref().model_dump(mode="python"); d["result_sets"][0]["result_limit"]-=1
    with pytest.raises(ValidationError): UnifiedEntityEvidenceQueryBundle.model_validate(d)
def test_remote_without_local_validation_rejected():
    x=next(x for x in ref().results if x.epistemic_state==EpistemicState.remote_reference).model_dump(mode="python")
    x["validation_state"]="governed-reference"
    with pytest.raises(ValidationError): UnifiedQueryResultItem.model_validate(x)
def test_candidate_as_governed_reference_rejected():
    x=next(x for x in ref().results if x.epistemic_state==EpistemicState.candidate).model_dump(mode="python")
    x["validation_state"]="governed-reference"
    with pytest.raises(ValidationError): UnifiedQueryResultItem.model_validate(x)
def test_hypothesis_as_governed_reference_rejected():
    x=next(x for x in ref().results if x.epistemic_state==EpistemicState.hypothesis).model_dump(mode="python")
    x["validation_state"]="governed-reference"
    with pytest.raises(ValidationError): UnifiedQueryResultItem.model_validate(x)

@pytest.mark.parametrize("field",[
    "require_capability_negotiation","preserve_source_contract_identity","preserve_epistemic_state","preserve_provenance",
    "preserve_validation_state","preserve_contradictions","preserve_remote_reference_state","enforce_consumer_scope",
    "label_retrieval_scores_as_relevance_only",
])
def test_policy_requirements(field): assert getattr(ref().policies[0],field) is True

@pytest.mark.parametrize("field",[
    "allow_cross_state_flattening","allow_candidate_promotion","allow_hypothesis_promotion","allow_remote_reference_promotion",
    "allow_local_validation_bypass","allow_truth_score",
])
def test_policy_prohibitions(field): assert getattr(ref().policies[0],field) is False

@pytest.mark.parametrize("field",[
    "single_governed_query_surface","capability_negotiation_required","source_contract_identity_preserved","epistemic_state_preserved",
    "provenance_preserved","validation_state_preserved","contradictions_preserved","remote_references_remain_remote",
    "consumer_scope_enforced","retrieval_scores_are_relevance_only","query_plans_are_reproducible","result_sets_are_explicitly_qualified",
])
def test_contract_principles(field): assert contract_document()["principles"][field] is True

@pytest.mark.parametrize("field",[
    "query_flattens_epistemic_states","query_promotes_candidate_to_fact","query_promotes_hypothesis_to_evidence",
    "query_promotes_remote_reference_to_local_evidence","retrieval_score_is_evidence_strength","retrieval_score_is_probability_of_truth",
    "absence_from_results_proves_nonexistence","query_completeness_is_evidence_completeness","query_result_is_truth_verdict",
    "query_bypasses_local_validation","identity_graph_mutation_performed","relationship_graph_mutation_performed","evidence_graph_mutation_performed",
])
def test_contract_boundaries(field): assert contract_document()["boundaries"][field] is False

@pytest.mark.parametrize("i",range(15))
def test_step_no_promotion(i): assert ref().plan_steps[i].may_promote_epistemic_state is False
@pytest.mark.parametrize("i",range(15))
def test_step_no_mutation(i): assert ref().plan_steps[i].may_mutate_governed_graphs is False
@pytest.mark.parametrize("i",range(15))
def test_result_relevance_only(i): assert ref().results[i].retrieval_score_is_relevance_only is True
@pytest.mark.parametrize("i",range(15))
def test_result_score_not_evidence(i): assert ref().results[i].retrieval_score_is_not_evidence_strength is True
@pytest.mark.parametrize("i",range(15))
def test_result_score_not_truth_probability(i): assert ref().results[i].retrieval_score_is_not_probability_of_truth is True
@pytest.mark.parametrize("i",range(15))
def test_result_no_state_promotion(i): assert ref().results[i].result_does_not_promote_source_state is True
@pytest.mark.parametrize("i",range(15))
def test_result_has_provenance(i): assert len(ref().results[i].provenance_refs)>=1
@pytest.mark.parametrize("i",range(15))
def test_provenance_not_truth_certification(i): assert ref().provenance_refs[i].provenance_is_not_truth_certification is True
@pytest.mark.parametrize("i",range(15))
def test_result_contract_equals_step(i):
    b=ref(); step={x.step_id:x for x in b.plan_steps}[b.results[i].plan_step_ref]; assert b.results[i].source_contract==step.output_contract
@pytest.mark.parametrize("i",range(15))
def test_result_capability_equals_step(i):
    b=ref(); step={x.step_id:x for x in b.plan_steps}[b.results[i].plan_step_ref]; assert b.results[i].source_capability_ref==step.capability_ref

@pytest.mark.parametrize("state",list(QueryMode))
def test_query_modes(state): assert state.value
@pytest.mark.parametrize("state",list(QueryTargetKind))
def test_target_kinds(state): assert state.value
@pytest.mark.parametrize("state",list(EpistemicState))
def test_epistemic_states(state): assert state.value
@pytest.mark.parametrize("state",list(ResultValidationState))
def test_validation_states(state): assert state.value
@pytest.mark.parametrize("state",list(QueryExecutionDisposition))
def test_dispositions(state): assert state.value

def test_plan_preserves_contract(): assert ref().plans[0].preserves_contract_identity is True
def test_plan_preserves_state(): assert ref().plans[0].preserves_epistemic_state is True
def test_plan_preserves_provenance(): assert ref().plans[0].preserves_provenance is True
def test_plan_not_truth(): assert ref().plans[0].plan_is_not_truth_assessment is True
def test_result_set_not_truth(): assert ref().result_sets[0].result_set_is_not_truth_verdict is True
def test_result_set_not_evidence_complete(): assert ref().result_sets[0].query_completeness_is_not_evidence_completeness is True
def test_result_absence_not_nonexistence(): assert ref().result_sets[0].absence_from_results_is_not_nonexistence is True
def test_trace_preserves_state(): assert ref().traces[0].trace_preserves_epistemic_state is True
def test_trace_preserves_provenance(): assert ref().traces[0].trace_preserves_provenance is True
def test_trace_not_truth(): assert ref().traces[0].trace_is_not_truth_assessment is True
def test_trace_no_mutation(): assert ref().traces[0].graph_mutation_performed is False
def test_snapshot_immutable(): assert ref().snapshots[0].immutable is True
def test_snapshot_supersedable(): assert ref().snapshots[0].later_source_state_may_supersede_snapshot is True
def test_snapshot_not_truth_certification(): assert ref().snapshots[0].snapshot_is_not_truth_certification is True
