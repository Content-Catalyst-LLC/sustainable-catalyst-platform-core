import copy
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.routers import contextual_hypothesis_competing_explanations as api
from app.services.contextual_hypothesis_competing_explanations import (
    ContextualHypothesisCompetingExplanationBundle,
    DiscriminatingDimension,
    EvidencePositionKind,
    ExplanationRelation,
    HypothesisKind,
    HypothesisReviewState,
    contract_document,
    reference_contextual_hypothesis_competing_explanation_bundle,
)


def ref(): return reference_contextual_hypothesis_competing_explanation_bundle()
def invalid(mutator):
    payload=ref().model_dump(mode='json')
    mutator(payload)
    with pytest.raises(ValidationError): ContextualHypothesisCompetingExplanationBundle.model_validate(payload)


def test_app_version_forward(): assert tuple(map(int, Settings().version.split('.'))) >= (4,18,0)
def test_release_and_contract(): assert ref().release == '4.18.0' and ref().contract == 'sc.core.contextual-hypothesis-competing-explanation-objects.v1'
def test_predecessor_exact(): assert ref().predecessor_reconciliation.release == '4.17.0'
def test_reference_hypothesis_count(): assert len(ref().hypotheses) == 10
def test_reference_evidence_position_count(): assert len(ref().evidence_positions) == 12
def test_reference_comparison_count(): assert len(ref().comparisons) == 7
def test_reference_explanation_set_count(): assert len(ref().explanation_sets) == 4

def test_emissions_scope_hypothesis_retained():
    h=next(x for x in ref().hypotheses if x.hypothesis_id=='hypothesis:emissions:scope-difference')
    assert h.kind == HypothesisKind.measurement_scope
    assert h.state == HypothesisReviewState.retained
    assert h.explanatory_fit_score == 0.86
    assert h.fit_score_is_not_probability_or_truth

def test_emissions_temporal_hypothesis_unresolved():
    h=next(x for x in ref().hypotheses if x.hypothesis_id=='hypothesis:emissions:temporal-change')
    assert h.state == HypothesisReviewState.unresolved
    assert 'same-period:reference-corpus' in h.unresolved_refs

def test_measurement_process_stays_candidate_without_protocol_evidence():
    h=next(x for x in ref().hypotheses if x.hypothesis_id=='hypothesis:emissions:measurement-process')
    assert h.state == HypothesisReviewState.candidate
    assert 'no-measurement-protocol-evidence-in-reference-corpus' in h.qualification_refs

def test_causal_effect_hypothesis_constrained():
    h=next(x for x in ref().hypotheses if x.hypothesis_id=='hypothesis:emissions:real-intervention-effect')
    assert h.kind == HypothesisKind.causal_mechanism
    assert h.state == HypothesisReviewState.constrained
    assert h.mechanism_refs == ['mechanism:measure-to-emissions:reference']
    assert 'causal-identification-not-established' in h.qualification_refs

def test_actor_hypotheses_both_live():
    states={x.hypothesis_id:x.state for x in ref().hypotheses if x.target_cluster_ref=='cluster:actor-ministry-agency'}
    assert states == {
        'hypothesis:actor:same-institution-label-variation': HypothesisReviewState.unresolved,
        'hypothesis:actor:distinct-related-institutions': HypothesisReviewState.unresolved,
    }

def test_governance_hypotheses_can_be_complementary():
    c=next(x for x in ref().comparisons if x.comparison_id=='comparison:governance:equivalence-vs-divergence')
    assert c.relation == ExplanationRelation.complementary
    assert DiscriminatingDimension.terminology in c.discriminating_dimensions

def test_translation_derivation_retained():
    h=next(x for x in ref().hypotheses if x.hypothesis_id=='hypothesis:cost:translation-derivation')
    assert h.state == HypothesisReviewState.retained

def test_independent_corroboration_rejected_by_lineage():
    h=next(x for x in ref().hypotheses if x.hypothesis_id=='hypothesis:cost:independent-corroboration')
    assert h.state == HypothesisReviewState.rejected
    assert 'rejected-by-governed-translation-lineage' in h.qualification_refs

def test_derived_translation_never_counts_as_independent_support():
    p=next(x for x in ref().evidence_positions if x.position_id=='position:cost-translation:support')
    assert p.position == EvidencePositionKind.non_independent
    assert p.counts_as_independent_support is False

def test_independent_corroboration_has_challenge_position():
    p=next(x for x in ref().evidence_positions if x.position_id=='position:cost-independent:challenge')
    assert p.position == EvidencePositionKind.challenges
    assert p.counts_as_independent_support is False

def test_emissions_set_has_no_winner():
    s=next(x for x in ref().explanation_sets if x.explanation_set_id=='explanation-set:emissions-discrepancy')
    assert s.set_establishes_winner is False
    assert len(s.hypothesis_refs) == 4
    assert len(s.unresolved_questions) == 4

def test_cost_set_can_reject_specific_explanation_without_truth_verdict():
    s=next(x for x in ref().explanation_sets if x.explanation_set_id=='explanation-set:cost-source-independence')
    assert s.rejected_hypothesis_refs == ['hypothesis:cost:independent-corroboration']
    assert s.retained_hypothesis_refs == ['hypothesis:cost:translation-derivation']
    assert s.set_establishes_truth is False

def test_policy_boundaries():
    p=ref().policy
    assert p.hypotheses_are_explanatory_objects_not_truth_claims
    assert p.competing_explanations_may_coexist
    assert p.derived_translation_cannot_count_as_independent_support
    assert p.causal_identification_status_must_carry_forward
    assert p.identity_uncertainty_must_carry_forward
    assert not p.explanatory_fit_score_establishes_truth
    assert not p.explanatory_fit_score_is_probability
    assert not p.support_count_establishes_truth
    assert not p.challenge_count_establishes_falsity
    assert not p.retained_hypothesis_is_selected_winner

def test_policy_no_auto_mutation_or_promotion():
    p=ref().policy
    assert not p.automatic_hypothesis_promotion_authorized
    assert not p.automatic_context_graph_mutation_authorized
    assert not p.automatic_evidence_graph_mutation_authorized
    assert not p.automatic_knowledge_graph_mutation_authorized
    assert not p.automatic_identity_graph_mutation_authorized

def test_snapshot_exact_hypotheses(): assert ref().snapshots[0].hypothesis_fingerprints == {x.hypothesis_id:x.fingerprint() for x in ref().hypotheses}
def test_snapshot_exact_positions(): assert ref().snapshots[0].evidence_position_fingerprints == {x.position_id:x.fingerprint() for x in ref().evidence_positions}
def test_snapshot_exact_comparisons(): assert ref().snapshots[0].comparison_fingerprints == {x.comparison_id:x.fingerprint() for x in ref().comparisons}
def test_snapshot_exact_sets(): assert ref().snapshots[0].explanation_set_fingerprints == {x.explanation_set_id:x.fingerprint() for x in ref().explanation_sets}
def test_bundle_deterministic(): assert ref().fingerprint() == ref().fingerprint()

def test_contract_counts():
    r=contract_document()['reference']
    assert r['hypotheses'] == 10
    assert r['evidence_positions'] == 12
    assert r['comparisons'] == 7
    assert r['explanation_sets'] == 4
    assert r['retained_hypotheses'] == 4
    assert r['unresolved_hypotheses'] == 3
    assert r['constrained_hypotheses'] == 1
    assert r['rejected_hypotheses'] == 1
    assert r['non_independent_positions'] == 1
    assert r['sets_with_no_winner'] == 4

def test_contract_boundaries():
    b=contract_document()['boundaries']
    assert not b['explanatory_fit_score_establishes_truth']
    assert not b['explanatory_fit_score_is_probability']
    assert not b['support_count_establishes_truth']
    assert not b['challenge_count_establishes_falsity']
    assert not b['retained_hypothesis_is_selected_winner']
    assert not b['automatic_hypothesis_promotion_performed']

def test_contract_prepares_next_line():
    r=contract_document()['roadmap_integration']
    assert r['prepares_v4190_semantic_synthesis_research_answer'] is True
    assert r['prepares_v4200_unified_contextual_reasoning_runtime'] is True

def test_api_contract(): assert api.contract()['release'] == '4.18.0'
def test_api_reference(): assert api.reference()['ok'] is True
def test_api_hypotheses(): assert api.reference_hypotheses()['count'] == 10
def test_api_positions(): assert api.reference_evidence_positions()['count'] == 12
def test_api_comparisons(): assert api.reference_comparisons()['count'] == 7
def test_api_sets(): assert api.reference_explanation_sets()['count'] == 4

def test_bad_target_cluster_fails(): invalid(lambda p: p['hypotheses'][0].__setitem__('target_cluster_ref','missing'))
def test_bad_source_anchor_fails(): invalid(lambda p: p['hypotheses'][0]['source_anchor_refs'].__setitem__(0,'missing'))
def test_bad_conflict_ref_fails(): invalid(lambda p: p['hypotheses'][0]['conflict_refs'].__setitem__(0,'missing'))
def test_bad_decision_ref_fails(): invalid(lambda p: p['hypotheses'][0]['decision_refs'].__setitem__(0,'missing'))
def test_bad_mechanism_ref_fails():
    def mutate(p):
        h=next(x for x in p['hypotheses'] if x['hypothesis_id']=='hypothesis:emissions:real-intervention-effect')
        h['mechanism_refs']=['missing']
    invalid(mutate)
def test_causal_hypothesis_requires_mechanism():
    def mutate(p):
        h=next(x for x in p['hypotheses'] if x['hypothesis_id']=='hypothesis:emissions:real-intervention-effect')
        h['mechanism_refs']=[]
    invalid(mutate)
def test_reviewed_state_requires_reviewer():
    def mutate(p):
        h=next(x for x in p['hypotheses'] if x['hypothesis_id']=='hypothesis:emissions:scope-difference')
        h['reviewer_ref']=None
    invalid(mutate)
def test_rejected_requires_qualification():
    def mutate(p):
        h=next(x for x in p['hypotheses'] if x['hypothesis_id']=='hypothesis:cost:independent-corroboration')
        h['qualification_refs']=[]
    invalid(mutate)
def test_position_bad_hypothesis_fails(): invalid(lambda p: p['evidence_positions'][0].__setitem__('hypothesis_ref','missing'))
def test_position_bad_anchor_fails(): invalid(lambda p: p['evidence_positions'][0]['anchor_refs'].__setitem__(0,'missing'))
def test_derived_anchor_cannot_count_independent_support():
    def mutate(p):
        pos=next(x for x in p['evidence_positions'] if x['position_id']=='position:cost-translation:support')
        pos['position']='supports'; pos['counts_as_independent_support']=True
    invalid(mutate)
def test_non_support_cannot_count_independent():
    def mutate(p):
        pos=next(x for x in p['evidence_positions'] if x['position_id']=='position:cost-independent:challenge')
        pos['counts_as_independent_support']=True
    invalid(mutate)
def test_comparison_bad_hypothesis_fails(): invalid(lambda p: p['comparisons'][0].__setitem__('left_hypothesis_ref','missing'))
def test_comparison_same_hypothesis_fails(): invalid(lambda p: p['comparisons'][0].__setitem__('right_hypothesis_ref',p['comparisons'][0]['left_hypothesis_ref']))
def test_comparison_cross_cluster_fails():
    def mutate(p): p['comparisons'][0]['right_hypothesis_ref']='hypothesis:actor:same-institution-label-variation'
    invalid(mutate)
def test_set_bad_hypothesis_fails(): invalid(lambda p: p['explanation_sets'][0]['hypothesis_refs'].__setitem__(0,'missing'))
def test_set_bad_position_fails(): invalid(lambda p: p['explanation_sets'][0]['evidence_position_refs'].__setitem__(0,'missing'))
def test_set_bad_comparison_fails(): invalid(lambda p: p['explanation_sets'][0]['comparison_refs'].__setitem__(0,'missing'))
def test_set_rejected_cannot_be_retained():
    def mutate(p): p['explanation_sets'][3]['retained_hypothesis_refs'].append('hypothesis:cost:independent-corroboration')
    invalid(mutate)
def test_set_rejected_refs_must_really_be_rejected():
    def mutate(p): p['explanation_sets'][0]['rejected_hypothesis_refs']=['hypothesis:emissions:scope-difference']
    invalid(mutate)
def test_bad_provenance_predecessor_fails(): invalid(lambda p: p['provenance_records'][0].__setitem__('predecessor_reconciliation_fingerprint_sha256','0'*64))
def test_bad_snapshot_predecessor_fails(): invalid(lambda p: p['snapshots'][0].__setitem__('predecessor_reconciliation_fingerprint_sha256','0'*64))
def test_bad_snapshot_hypothesis_fingerprint_fails(): invalid(lambda p: p['snapshots'][0]['hypothesis_fingerprints'].__setitem__(next(iter(p['snapshots'][0]['hypothesis_fingerprints'])),'0'*64))
def test_database_migration_none(): assert ref().database_migration == 'none'

def test_main_mounts_v418_routes():
    from app.main import create_app
    app=create_app()
    paths={r.path for r in app.routes}
    assert '/v1/context-hypotheses/contract' in paths
    assert '/public/v1/context-hypotheses/contract' in paths
