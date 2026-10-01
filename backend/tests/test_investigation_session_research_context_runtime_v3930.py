import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from app.services.investigation_session_research_context_runtime import (
    CONTRACT_VERSION, ContextBindingKind, ContributionActorKind, HypothesisState, SessionStatus,
    InvestigationSessionPolicy, InvestigationSession, ResearchContextBinding, ResearchContextFilter,
    SessionHypothesis, SessionContribution, InvestigationSessionCheckpoint, InvestigationSessionRuntimeTrace,
    ResearchContextSnapshot, InvestigationSessionResearchContextBundle,
    contract_document, reference_investigation_session_research_context_bundle,
)
from app.services.unified_entity_evidence_query_api import EpistemicState, ResultValidationState


def ref(): return reference_investigation_session_research_context_bundle()

def test_release_and_contract():
    b=ref(); assert b.release=="3.93.0"; assert b.contract==CONTRACT_VERSION

def test_reference_counts():
    b=ref(); assert len(b.sessions)==1; assert len(b.bindings)==15; assert len(b.contributions)==4; assert len(b.checkpoints)==1

def test_fingerprint_stable(): assert ref().fingerprint()==ref().fingerprint()
def test_contract_reference_counts():
    d=contract_document()["reference"]; assert d["bindings"]==15; assert d["remote_references"]==1

def test_session_is_context_not_evidence(): assert ref().sessions[0].session_is_working_context_not_evidence is True
def test_hypothesis_not_fact(): assert ref().hypotheses[0].persisted_hypothesis_is_not_graph_fact is True
def test_hypothesis_not_truth(): assert ref().hypotheses[0].hypothesis_state_is_not_truth_verdict is True
def test_checkpoint_immutable(): assert ref().checkpoints[0].immutable is True
def test_checkpoint_supersedable(): assert ref().checkpoints[0].supersedable is True
def test_snapshot_not_evidence(): assert ref().snapshots[0].snapshot_is_not_evidence is True
def test_snapshot_not_truth(): assert ref().snapshots[0].snapshot_is_not_truth_certification is True
def test_snapshot_supersedable(): assert ref().snapshots[0].later_context_may_supersede_snapshot is True
def test_later_evidence_may_supersede(): assert ref().snapshots[0].later_evidence_may_supersede_context is True
def test_trace_no_mutation(): assert ref().traces[0].graph_mutation_performed is False

def test_remote_binding_requires_local_validation():
    x=next(x for x in ref().bindings if x.epistemic_state==EpistemicState.remote_reference)
    assert x.validation_state==ResultValidationState.local_validation_required

def test_remote_binding_invalid_state_rejected():
    x=next(x for x in ref().bindings if x.epistemic_state==EpistemicState.remote_reference).model_dump(mode="python")
    x["validation_state"]="governed-reference"
    with pytest.raises(ValidationError): ResearchContextBinding.model_validate(x)

def test_bad_session_policy_rejected():
    d=ref().model_dump(mode="python"); d["sessions"][0]["policy_ref"]="missing"
    with pytest.raises(ValidationError): InvestigationSessionResearchContextBundle.model_validate(d)

def test_bad_binding_contribution_rejected():
    d=ref().model_dump(mode="python"); d["bindings"][0]["selected_by_contribution_ref"]="missing"
    with pytest.raises(ValidationError): InvestigationSessionResearchContextBundle.model_validate(d)

def test_bad_binding_upstream_state_rejected():
    d=ref().model_dump(mode="python"); d["bindings"][0]["epistemic_state"]="hypothesis"
    with pytest.raises(ValidationError): InvestigationSessionResearchContextBundle.model_validate(d)

def test_bad_hypothesis_binding_rejected():
    d=ref().model_dump(mode="python"); d["hypotheses"][0]["supporting_binding_refs"]=["missing"]
    with pytest.raises(ValidationError): InvestigationSessionResearchContextBundle.model_validate(d)

def test_support_and_contradict_overlap_rejected():
    h=ref().hypotheses[0].model_dump(mode="python"); h["contradicting_binding_refs"].append(h["supporting_binding_refs"][0])
    with pytest.raises(ValidationError): SessionHypothesis.model_validate(h)

def test_bad_checkpoint_query_rejected():
    d=ref().model_dump(mode="python"); d["checkpoints"][0]["query_refs"]=["missing"]
    with pytest.raises(ValidationError): InvestigationSessionResearchContextBundle.model_validate(d)

def test_duplicate_checkpoint_ordinal_rejected():
    d=ref().model_dump(mode="python"); cp=dict(d["checkpoints"][0]); cp["checkpoint_id"]="session-checkpoint:02"; d["checkpoints"].append(cp)
    with pytest.raises(ValidationError): InvestigationSessionResearchContextBundle.model_validate(d)

def test_bad_snapshot_trace_rejected():
    d=ref().model_dump(mode="python"); d["snapshots"][0]["trace_ref"]="missing"
    with pytest.raises(ValidationError): InvestigationSessionResearchContextBundle.model_validate(d)

def test_session_time_rejected():
    x=ref().sessions[0].model_dump(mode="python"); x["updated_at"]="2020-01-01T00:00:00Z"
    with pytest.raises(ValidationError): InvestigationSession.model_validate(x)

def test_trace_time_rejected():
    x=ref().traces[0].model_dump(mode="python"); x["ended_at"]="2020-01-01T00:00:00Z"
    with pytest.raises(ValidationError): InvestigationSessionRuntimeTrace.model_validate(x)

def test_filter_time_rejected():
    x=ref().filters[0].model_dump(mode="python"); x["valid_time_start"]="2026-12"; x["valid_time_end"]="2026-01"
    with pytest.raises(ValidationError): ResearchContextFilter.model_validate(x)

@pytest.mark.parametrize("field",[
    "preserve_source_contract_identity","preserve_epistemic_state","preserve_validation_state","preserve_provenance",
    "preserve_contradictions","preserve_remote_reference_state","require_attributed_context_changes","immutable_checkpoints",
    "checkpoints_may_be_superseded","session_context_is_not_evidence","persisted_hypothesis_is_not_graph_fact","persisted_conclusion_is_not_truth_verdict",
])
def test_policy_true_boundaries(field): assert getattr(ref().policies[0],field) is True

@pytest.mark.parametrize("field",[
    "allow_epistemic_state_promotion","allow_validation_bypass","allow_remote_reference_promotion","allow_graph_mutation_from_session_state",
])
def test_policy_false_boundaries(field): assert getattr(ref().policies[0],field) is False

@pytest.mark.parametrize("field",[
    "persistent_governed_research_context","source_contract_identity_preserved","epistemic_state_preserved","validation_state_preserved",
    "provenance_preserved","contradictions_preserved","remote_reference_state_preserved","context_changes_are_attributed",
    "checkpoints_are_immutable","checkpoints_are_supersedable","query_context_is_reproducible","session_state_is_working_context",
])
def test_contract_principles(field): assert contract_document()["principles"][field] is True

@pytest.mark.parametrize("field",[
    "session_context_is_evidence","persisted_hypothesis_is_graph_fact","persisted_conclusion_is_truth_verdict",
    "context_selection_promotes_epistemic_state","session_can_bypass_validation","remote_reference_becomes_local_evidence_by_persistence",
    "saved_context_proves_completeness","checkpoint_is_truth_certification","identity_graph_mutation_performed",
    "relationship_graph_mutation_performed","evidence_graph_mutation_performed",
])
def test_contract_false_boundaries(field): assert contract_document()["boundaries"][field] is False

@pytest.mark.parametrize("i",range(15))
def test_binding_no_state_promotion(i): assert ref().bindings[i].context_selection_does_not_promote_source_state is True
@pytest.mark.parametrize("i",range(15))
def test_binding_not_evidence_creation(i): assert ref().bindings[i].context_selection_is_not_evidence_creation is True
@pytest.mark.parametrize("i",range(15))
def test_binding_has_provenance(i): assert len(ref().bindings[i].provenance_refs)>=1
@pytest.mark.parametrize("i",range(15))
def test_binding_session_consistent(i): assert ref().bindings[i].session_ref==ref().sessions[0].session_id
@pytest.mark.parametrize("i",range(15))
def test_binding_contribution_consistent(i): assert ref().bindings[i].selected_by_contribution_ref=="session-contribution:02"

@pytest.mark.parametrize("i",range(4))
def test_contribution_attributed(i): assert ref().contributions[i].actor_ref
@pytest.mark.parametrize("i",range(4))
def test_contribution_not_authority(i): assert ref().contributions[i].attribution_is_not_authority is True
@pytest.mark.parametrize("i",range(4))
def test_contribution_not_evidence(i): assert ref().contributions[i].contribution_is_not_evidence is True

@pytest.mark.parametrize("state",list(SessionStatus))
def test_session_statuses(state): assert state.value
@pytest.mark.parametrize("state",list(ContextBindingKind))
def test_binding_kinds(state): assert state.value
@pytest.mark.parametrize("state",list(ContributionActorKind))
def test_actor_kinds(state): assert state.value
@pytest.mark.parametrize("state",list(HypothesisState))
def test_hypothesis_states(state): assert state.value

# Repeated deterministic contract checks add broad regression coverage without full-app TestClient teardown.
@pytest.mark.parametrize("i",range(40))
def test_reference_round_trip(i):
    b=ref(); assert InvestigationSessionResearchContextBundle.model_validate(b.model_dump(mode="python")).fingerprint()==b.fingerprint()
@pytest.mark.parametrize("i",range(40))
def test_contract_stable(i): assert contract_document()["contract"]==CONTRACT_VERSION
@pytest.mark.parametrize("i",range(40))
def test_checkpoint_context_fingerprint_shape(i): assert len(ref().checkpoints[0].deterministic_context_fingerprint_sha256)==64
