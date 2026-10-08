import copy
import pytest
from pydantic import ValidationError

from app.services.unified_contextual_reasoning_runtime import (
    ReasoningStageKind,
    ReasoningStageState,
    UnifiedContextualReasoningRuntimeBundle,
    contract_document,
    reference_unified_contextual_reasoning_runtime_bundle,
)
from app.routers import unified_contextual_reasoning_runtime as api


def ref(): return reference_unified_contextual_reasoning_runtime_bundle()
def invalid(mut):
    p=copy.deepcopy(ref().model_dump(mode="json")); mut(p)
    with pytest.raises(ValidationError): UnifiedContextualReasoningRuntimeBundle.model_validate(p)


def test_release_contract():
    b=ref(); assert b.release=="4.20.0"; assert b.predecessor_synthesis.release=="4.19.0"

def test_stage_inventory():
    b=ref(); assert len(b.stages)==9; assert [x.release for x in b.stages]==[f"4.{n}.0" for n in range(11,20)]

def test_stage_order_kinds():
    assert [x.kind for x in ref().stages]==[
        ReasoningStageKind.contextual_memory, ReasoningStageKind.retrieval_relevance,
        ReasoningStageKind.claim_comparison, ReasoningStageKind.evidence_context,
        ReasoningStageKind.causal_context, ReasoningStageKind.narrative_framing,
        ReasoningStageKind.source_reconciliation, ReasoningStageKind.competing_explanations,
        ReasoningStageKind.semantic_synthesis,
    ]

def test_stage_chain_contiguous():
    xs=ref().stages; assert xs[0].predecessor_stage_ref is None
    assert all(xs[i].predecessor_stage_ref==xs[i-1].stage_id for i in range(1,len(xs)))

def test_unresolved_stages_preserved():
    assert sum(x.state==ReasoningStageState.unresolved for x in ref().stages)==5

def test_three_end_to_end_traces():
    b=ref(); assert len(b.traces)==3; assert {x.final_answer_ref for x in b.traces}=={x.answer_id for x in b.predecessor_synthesis.research_answers}

def test_trace_uses_complete_stage_order():
    ids=[x.stage_id for x in ref().stages]; assert all(x.stage_refs==ids for x in ref().traces)

def test_trace_preserves_answer_disposition():
    b=ref(); answers={x.answer_id:x for x in b.predecessor_synthesis.research_answers}
    assert all(t.final_disposition==answers[t.final_answer_ref].disposition.value for t in b.traces)

def test_trace_preserves_qualifications():
    b=ref(); answers={x.answer_id:x for x in b.predecessor_synthesis.research_answers}
    assert all(set(answers[t.final_answer_ref].qualification_refs).issubset(t.carried_qualification_refs) for t in b.traces)

def test_trace_preserves_unresolved_questions():
    b=ref(); answers={x.answer_id:x for x in b.predecessor_synthesis.research_answers}
    assert all(set(answers[t.final_answer_ref].unresolved_questions).issubset(t.unresolved_questions) for t in b.traces)

def test_policy_epistemic_boundaries():
    p=ref().policy; assert not p.stage_completion_establishes_truth; assert not p.runtime_completion_establishes_truth; assert not p.runtime_confidence_is_probability; assert not p.synthesis_answer_is_evidence_record

def test_policy_no_auto_mutation():
    p=ref().policy; assert not p.automatic_evidence_promotion_authorized; assert not p.automatic_hypothesis_selection_authorized; assert not p.automatic_canonical_identity_merge_authorized; assert not p.automatic_context_graph_mutation_authorized; assert not p.automatic_evidence_graph_mutation_authorized; assert not p.automatic_knowledge_graph_mutation_authorized; assert not p.automatic_identity_graph_mutation_authorized

def test_original_language_policy():
    p=ref().policy; assert p.original_language_remains_authoritative; assert p.translation_remains_derived; assert p.source_independence_must_be_preserved

def test_snapshot_exact():
    b=ref(); s=b.snapshots[0]
    assert s.stage_fingerprints=={x.stage_id:x.fingerprint() for x in b.stages}
    assert s.trace_fingerprints=={x.trace_id:x.fingerprint() for x in b.traces}

def test_deterministic(): assert ref().fingerprint()==ref().fingerprint()

def test_contract_counts():
    r=contract_document()["reference"]; assert r["reasoning_stages"]==9; assert r["reasoning_traces"]==3; assert r["final_research_answers"]==3; assert r["unresolved_stage_records"]==5; assert r["traces_with_unresolved_questions"]==3

def test_contract_milestone():
    m=contract_document()["milestone"]; assert m["contextual_reasoning_arc_complete"]; assert m["reasoning_arc_from_release"]=="4.11.0"; assert m["reasoning_arc_through_release"]=="4.20.0"; assert m["recommended_core_feature_expansion_pause"]

def test_contract_boundaries():
    b=contract_document()["boundaries"]; assert not b["runtime_completion_establishes_truth"]; assert not b["automatic_hypothesis_selection_performed"]; assert not b["automatic_canonical_identity_merge_performed"]

def test_api_contract(): assert api.contract()["release"]=="4.20.0"
def test_api_reference(): assert api.reference()["ok"] is True
def test_api_stages(): assert api.reference_stages()["count"]==9
def test_api_traces(): assert api.reference_traces()["count"]==3

def test_bad_stage_order_fails():
    def m(p): p["stages"][0],p["stages"][1]=p["stages"][1],p["stages"][0]
    invalid(m)

def test_bad_stage_contract_fails(): invalid(lambda p:p["stages"][3].__setitem__("contract","wrong"))
def test_bad_stage_predecessor_fails(): invalid(lambda p:p["stages"][4].__setitem__("predecessor_stage_ref","missing"))
def test_bad_trace_stage_order_fails(): invalid(lambda p:p["traces"][0]["stage_refs"].reverse())
def test_bad_trace_answer_fails(): invalid(lambda p:p["traces"][0].__setitem__("final_answer_ref","missing"))
def test_bad_trace_question_fails(): invalid(lambda p:p["traces"][0].__setitem__("question","Different question"))
def test_drop_answer_qualification_fails():
    def m(p): p["traces"][0]["carried_qualification_refs"]=[]
    invalid(m)
def test_drop_unresolved_question_fails():
    def m(p): p["traces"][0]["unresolved_questions"]=[]
    invalid(m)
def test_bad_provenance_predecessor_fails(): invalid(lambda p:p["provenance_records"][0].__setitem__("predecessor_synthesis_fingerprint_sha256","0"*64))
def test_bad_snapshot_stage_fingerprint_fails():
    def m(p): k=next(iter(p["snapshots"][0]["stage_fingerprints"])); p["snapshots"][0]["stage_fingerprints"][k]="0"*64
    invalid(m)
def test_database_migration_none(): assert ref().database_migration=="none"
def test_main_mounts_v420_routes():
    from app.main import create_app
    app=create_app(); paths={r.path for r in app.routes}
    assert "/v1/contextual-reasoning/contract" in paths
    assert "/public/v1/contextual-reasoning/contract" in paths
