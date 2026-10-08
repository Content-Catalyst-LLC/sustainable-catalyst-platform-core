import copy
import pytest
from pydantic import ValidationError
from app.services.semantic_synthesis_research_answer import (
    AnswerDisposition, SemanticSynthesisResearchAnswerBundle, SynthesisClaimRole,
    contract_document, reference_semantic_synthesis_research_answer_bundle,
)
from app.routers import semantic_synthesis_research_answer as api

def ref(): return reference_semantic_synthesis_research_answer_bundle()
def invalid(mut):
    p=copy.deepcopy(ref().model_dump(mode="json")); mut(p)
    with pytest.raises(ValidationError): SemanticSynthesisResearchAnswerBundle.model_validate(p)

def test_release_contract():
    b=ref(); assert b.release=='4.19.0'; assert b.predecessor_hypothesis_context.release=='4.18.0'
def test_counts(): assert len(ref().research_answers)==3 and len(ref().synthesis_claims)==7
def test_emissions_answer_unresolved():
    a=next(x for x in ref().research_answers if x.answer_id=='answer:emissions-effect'); assert a.disposition==AnswerDisposition.unresolved; assert len(a.retained_hypothesis_refs)==4; assert a.counterevidence_position_refs
def test_actor_answer_no_merge():
    a=next(x for x in ref().research_answers if x.answer_id=='answer:actor-continuity'); assert a.disposition==AnswerDisposition.unresolved; assert 'identity-merge-not-authorized' in a.qualification_refs
def test_cost_answer_provenance_only():
    a=next(x for x in ref().research_answers if x.answer_id=='answer:cost-corroboration'); assert a.disposition==AnswerDisposition.provenance_resolved_claim_unresolved; assert a.rejected_hypothesis_refs==['hypothesis:cost:independent-corroboration']; assert 'claim-truth-remains-unresolved' in a.qualification_refs
def test_counterevidence_role_present(): assert any(x.role==SynthesisClaimRole.counterevidence for x in ref().synthesis_claims)
def test_original_language_ref_preserved():
    c=next(x for x in ref().synthesis_claims if x.synthesis_claim_id=='synthesis:cost:derived'); assert c.original_language_refs==['zh-original:proposal-cost']
def test_policy_boundaries():
    p=ref().policy; assert p.synthesis_must_preserve_counterevidence; assert p.synthesis_must_preserve_live_competing_explanations; assert not p.answer_disposition_establishes_truth; assert not p.answer_confidence_establishes_probability; assert not p.majority_source_count_establishes_truth
def test_no_auto_mutation():
    p=ref().policy; assert not p.automatic_evidence_promotion_authorized; assert not p.automatic_hypothesis_selection_authorized; assert not p.automatic_context_graph_mutation_authorized; assert not p.automatic_evidence_graph_mutation_authorized; assert not p.automatic_knowledge_graph_mutation_authorized; assert not p.automatic_identity_graph_mutation_authorized
def test_snapshot_exact():
    b=ref(); s=b.snapshots[0]; assert s.answer_fingerprints=={x.answer_id:x.fingerprint() for x in b.research_answers}; assert s.synthesis_claim_fingerprints=={x.synthesis_claim_id:x.fingerprint() for x in b.synthesis_claims}
def test_deterministic(): assert ref().fingerprint()==ref().fingerprint()
def test_contract_counts():
    r=contract_document()['reference']; assert r['research_answers']==3; assert r['synthesis_claims']==7; assert r['unresolved_answers']==2; assert r['provenance_resolved_claim_unresolved_answers']==1; assert r['answers_preserving_counterevidence']==2; assert r['answers_with_live_hypotheses']==3
def test_contract_boundaries():
    b=contract_document()['boundaries']; assert not b['answer_disposition_establishes_truth']; assert not b['answer_confidence_establishes_probability']; assert not b['automatic_hypothesis_selection_performed']
def test_prepares_v420(): assert contract_document()['roadmap_integration']['prepares_v4200_unified_contextual_reasoning_runtime'] is True
def test_api_contract(): assert api.contract()['release']=='4.19.0'
def test_api_reference(): assert api.reference()['ok'] is True
def test_api_answers(): assert api.reference_answers()['count']==3
def test_api_claims(): assert api.reference_synthesis_claims()['count']==7
def test_bad_answer_ref_fails(): invalid(lambda p:p['synthesis_claims'][0].__setitem__('answer_ref','missing'))
def test_bad_hypothesis_ref_fails():
    def m(p): p['synthesis_claims'][1]['hypothesis_refs'][0]='missing'
    invalid(m)
def test_bad_position_ref_fails():
    def m(p): p['synthesis_claims'][0]['evidence_position_refs'][0]='missing'
    invalid(m)
def test_bad_set_ref_fails(): invalid(lambda p:p['research_answers'][0]['explanation_set_refs'].__setitem__(0,'missing'))
def test_answer_wrong_claim_fails(): invalid(lambda p:p['research_answers'][0]['synthesis_claim_refs'].__setitem__(0,'synthesis:actor:candidate'))
def test_rejected_cannot_be_retained():
    def m(p): p['research_answers'][2]['retained_hypothesis_refs'].append('hypothesis:cost:independent-corroboration')
    invalid(m)
def test_rejected_ref_must_be_rejected():
    def m(p): p['research_answers'][0]['rejected_hypothesis_refs']=['hypothesis:emissions:scope-difference']
    invalid(m)
def test_bad_provenance_pred_fails(): invalid(lambda p:p['provenance_records'][0].__setitem__('predecessor_hypothesis_fingerprint_sha256','0'*64))
def test_bad_snapshot_pred_fails(): invalid(lambda p:p['snapshots'][0].__setitem__('predecessor_hypothesis_fingerprint_sha256','0'*64))
def test_bad_snapshot_answer_fingerprint_fails():
    def m(p): k=next(iter(p['snapshots'][0]['answer_fingerprints'])); p['snapshots'][0]['answer_fingerprints'][k]='0'*64
    invalid(m)
def test_database_migration_none(): assert ref().database_migration=='none'
def test_main_mounts_v419_routes():
    from app.main import create_app
    app=create_app(); paths={r.path for r in app.routes}; assert '/v1/research-answers/contract' in paths; assert '/public/v1/research-answers/contract' in paths
