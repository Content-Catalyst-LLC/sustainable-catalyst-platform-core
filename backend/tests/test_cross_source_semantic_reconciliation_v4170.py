from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.routers import cross_source_semantic_reconciliation as api
from app.services.cross_source_semantic_reconciliation import (
    CrossSourceSemanticReconciliationBundle,
    ReconciliationAnchorKind,
    ReconciliationConflictKind,
    ReconciliationRelation,
    ReconciliationReviewState,
    contract_document,
    reference_cross_source_semantic_reconciliation_bundle,
)


def ref(): return reference_cross_source_semantic_reconciliation_bundle()
def payload(): return ref().model_dump(mode="json")
def invalid(mutator):
    p = deepcopy(payload()); mutator(p)
    with pytest.raises((ValidationError, ValueError)):
        CrossSourceSemanticReconciliationBundle.model_validate(p)


def test_release_identity():
    assert tuple(map(int, Settings().version.split('.'))) >= (4,17,0)
    assert ref().release == '4.17.0'
    assert ref().contract == 'sc.core.cross-source-semantic-reconciliation-engine.v1'
    assert ref().predecessor_contract == 'sc.core.narrative-framing-perspective-intelligence.v1'


def test_predecessor_exact():
    assert ref().predecessor_framing_context.release == '4.16.0'
    assert ref().predecessor_framing_context.contract == ref().predecessor_contract


def test_reference_inventory():
    assert len(ref().anchors) == 16
    assert len(ref().candidates) == 10
    assert len(ref().conflicts) == 6
    assert len(ref().decisions) == 10
    assert len(ref().clusters) == 6
    assert len(ref().provenance_records) == 1
    assert len(ref().snapshots) == 1


def test_anchor_kinds_cover_claim_actor_term_time_place():
    kinds = {x.kind for x in ref().anchors}
    assert {ReconciliationAnchorKind.claim, ReconciliationAnchorKind.actor_reference, ReconciliationAnchorKind.terminology, ReconciliationAnchorKind.temporal_scope, ReconciliationAnchorKind.spatial_reference}.issubset(kinds)


def test_claim_conflict_preserved():
    c = next(x for x in ref().candidates if x.candidate_id == 'candidate:emissions-report-audit')
    assert c.proposed_relation == ReconciliationRelation.same_semantic_target_conflicting
    assert c.candidate_establishes_truth is False
    assert c.candidate_establishes_equivalence is False


def test_scope_overlap_preserved():
    c = next(x for x in ref().candidates if x.candidate_id == 'candidate:emissions-audit-review')
    assert c.proposed_relation == ReconciliationRelation.scope_overlap
    assert 'direct-vs-total-emissions-scope' in c.unresolved_refs


def test_modality_temporal_difference_preserved():
    c = next(x for x in ref().candidates if x.candidate_id == 'candidate:emissions-report-agency')
    assert c.proposed_relation == ReconciliationRelation.modality_temporal_related


def test_translation_derivative_not_independent():
    c = next(x for x in ref().candidates if x.candidate_id == 'candidate:cost-zh-en-derived')
    right = next(x for x in ref().anchors if x.anchor_id == c.right_anchor_ref)
    assert c.proposed_relation == ReconciliationRelation.translation_derived_correspondence
    assert right.derived_representation is True
    assert 'translation-derived-not-independent' in c.qualification_refs


def test_cross_source_cost_near_equivalence_is_not_identity():
    c = next(x for x in ref().candidates if x.candidate_id == 'candidate:cost-report-zh')
    assert c.proposed_relation == ReconciliationRelation.near_equivalent
    assert c.candidate_establishes_identity is False


def test_actor_continuity_remains_unresolved():
    d = next(x for x in ref().decisions if x.decision_id == 'decision:actor-ministry-agency')
    assert d.state == ReconciliationReviewState.unresolved
    assert d.identity_merge_authorized is False


def test_cultural_semantic_divergence_preserved():
    f = next(x for x in ref().conflicts if x.conflict_id == 'conflict:governance-cultural-semantics')
    assert f.kind == ReconciliationConflictKind.cultural_semantic_divergence
    assert f.resolved is False


def test_source_independence_constraint_is_explicitly_resolved_without_truth_claim():
    f = next(x for x in ref().conflicts if x.conflict_id == 'conflict:translation-source-independence')
    assert f.kind == ReconciliationConflictKind.source_independence_constraint
    assert f.resolved is True
    assert f.conflict_is_not_truth_adjudication


def test_spatial_deictic_grounding_not_canonical_geography():
    c = next(x for x in ref().candidates if x.candidate_id == 'candidate:spatial-brussels-there')
    assert c.proposed_relation == ReconciliationRelation.deictic_grounding
    assert c.candidate_establishes_identity is False


def test_temporal_alignment_remains_candidate():
    d = next(x for x in ref().decisions if x.decision_id == 'decision:temporal-report-audit')
    assert d.selected_relation == ReconciliationRelation.temporal_alignment_candidate
    assert d.state == ReconciliationReviewState.unresolved


def test_clusters_are_navigation_not_canonicalization():
    assert all(x.cluster_is_navigation_object_not_canonical_entity for x in ref().clusters)
    assert all(not x.cluster_establishes_equivalence for x in ref().clusters)
    assert all(not x.cluster_establishes_truth for x in ref().clusters)


def test_derived_member_tracked_in_cost_cluster():
    c = next(x for x in ref().clusters if x.cluster_id == 'cluster:proposal-cost')
    assert c.derived_member_refs == ['anchor:claim:en-derived-cost-possible']


def test_emissions_cluster_keeps_three_conflicts():
    c = next(x for x in ref().clusters if x.cluster_id == 'cluster:emissions-policy-measure')
    assert len(c.conflict_refs) == 3


def test_policy_boundaries():
    p = ref().policy
    assert p.reconciliation_is_alignment_not_canonicalization
    assert p.same_surface_form_is_not_same_entity
    assert p.source_agreement_is_not_truth
    assert p.temporal_overlap_is_not_same_event
    assert p.original_language_remains_authoritative
    assert p.translation_remains_derived
    assert p.derived_representation_is_not_independent_source
    assert not p.reconciliation_score_establishes_truth
    assert not p.reconciliation_score_establishes_identity
    assert not p.reconciliation_score_establishes_equivalence


def test_policy_no_graph_mutation():
    p = ref().policy
    assert not p.automatic_canonical_entity_merge_authorized
    assert not p.automatic_context_graph_mutation_authorized
    assert not p.automatic_evidence_graph_mutation_authorized
    assert not p.automatic_knowledge_graph_mutation_authorized
    assert not p.automatic_identity_graph_mutation_authorized


def test_snapshot_exact_anchors(): assert ref().snapshots[0].anchor_fingerprints == {x.anchor_id:x.fingerprint() for x in ref().anchors}
def test_snapshot_exact_candidates(): assert ref().snapshots[0].candidate_fingerprints == {x.candidate_id:x.fingerprint() for x in ref().candidates}
def test_snapshot_exact_conflicts(): assert ref().snapshots[0].conflict_fingerprints == {x.conflict_id:x.fingerprint() for x in ref().conflicts}
def test_snapshot_exact_decisions(): assert ref().snapshots[0].decision_fingerprints == {x.decision_id:x.fingerprint() for x in ref().decisions}
def test_snapshot_exact_clusters(): assert ref().snapshots[0].cluster_fingerprints == {x.cluster_id:x.fingerprint() for x in ref().clusters}
def test_bundle_deterministic(): assert ref().fingerprint() == ref().fingerprint()


def test_contract_counts():
    r = contract_document()['reference']
    assert r['anchors'] == 16
    assert r['correspondence_candidates'] == 10
    assert r['conflicts'] == 6
    assert r['review_decisions'] == 10
    assert r['semantic_clusters'] == 6
    assert r['unresolved_decisions'] == 3
    assert r['derived_anchors'] == 1
    assert r['resolved_source_independence_conflicts'] == 1


def test_contract_boundaries():
    b = contract_document()['boundaries']
    assert not b['reconciliation_score_establishes_truth']
    assert not b['reconciliation_score_establishes_identity']
    assert not b['reconciliation_score_establishes_equivalence']
    assert not b['automatic_canonical_entity_merge_performed']


def test_contract_prepares_next_line():
    r = contract_document()['roadmap_integration']
    assert r['prepares_v4180_contextual_hypothesis_competing_explanations'] is True
    assert r['prepares_v4190_semantic_synthesis_research_answer'] is True
    assert r['prepares_v4200_unified_contextual_reasoning_runtime'] is True


def test_api_contract(): assert api.contract()['release'] == '4.17.0'
def test_api_reference(): assert api.reference()['ok'] is True
def test_api_anchors(): assert api.reference_anchors()['count'] == 16
def test_api_candidates(): assert api.reference_candidates()['count'] == 10
def test_api_conflicts(): assert api.reference_conflicts()['count'] == 6
def test_api_decisions(): assert api.reference_decisions()['count'] == 10
def test_api_clusters(): assert api.reference_clusters()['count'] == 6


def test_bad_anchor_source_fails(): invalid(lambda p: p['anchors'][0].__setitem__('source_ref','missing'))
def test_bad_claim_language_fails(): invalid(lambda p: p['anchors'][0].__setitem__('language_tag','zh'))
def test_derived_claim_cannot_be_marked_original():
    def mutate(p):
        a = next(x for x in p['anchors'] if x['anchor_id']=='anchor:claim:en-derived-cost-possible')
        a['derived_representation'] = False
    invalid(mutate)

def test_bad_candidate_anchor_fails(): invalid(lambda p: p['candidates'][0].__setitem__('left_anchor_ref','missing'))
def test_same_anchor_candidate_fails(): invalid(lambda p: p['candidates'][0].__setitem__('right_anchor_ref',p['candidates'][0]['left_anchor_ref']))
def test_duplicate_candidate_dimensions_fail(): invalid(lambda p: p['candidates'][0]['dimensions'].append(p['candidates'][0]['dimensions'][0]))
def test_translation_relation_requires_derived_member():
    def mutate(p):
        c=next(x for x in p['candidates'] if x['candidate_id']=='candidate:cost-zh-en-derived')
        c['right_anchor_ref']='anchor:claim:report-cost-possible'
    invalid(mutate)

def test_actor_relation_requires_actor_anchors():
    def mutate(p):
        c=next(x for x in p['candidates'] if x['candidate_id']=='candidate:actor-ministry-agency')
        c['left_anchor_ref']='anchor:claim:report-emissions-negative'
    invalid(mutate)

def test_deictic_relation_requires_spatial_anchors():
    def mutate(p):
        c=next(x for x in p['candidates'] if x['candidate_id']=='candidate:spatial-brussels-there')
        c['left_anchor_ref']='anchor:actor:ministry'
    invalid(mutate)

def test_bad_conflict_candidate_fails(): invalid(lambda p: p['conflicts'][0]['candidate_refs'].__setitem__(0,'missing'))
def test_bad_conflict_anchor_fails(): invalid(lambda p: p['conflicts'][0]['affected_anchor_refs'].__setitem__(0,'missing'))
def test_resolved_conflict_requires_note():
    def mutate(p):
        c=next(x for x in p['conflicts'] if x['conflict_id']=='conflict:translation-source-independence')
        c['resolution_note']=None
    invalid(mutate)

def test_bad_decision_candidate_fails(): invalid(lambda p: p['decisions'][0].__setitem__('candidate_ref','missing'))
def test_decision_relation_must_match_candidate(): invalid(lambda p: p['decisions'][0].__setitem__('selected_relation','near-equivalent'))
def test_unresolved_decision_requires_reviewer(): invalid(lambda p: p['decisions'][0].__setitem__('reviewer_ref',None))
def test_conflicting_candidate_cannot_be_accepted(): invalid(lambda p: p['decisions'][0].__setitem__('state','accepted'))
def test_bad_cluster_anchor_fails(): invalid(lambda p: p['clusters'][0]['member_anchor_refs'].__setitem__(0,'missing'))
def test_bad_cluster_decision_fails(): invalid(lambda p: p['clusters'][0]['decision_refs'].__setitem__(0,'missing'))
def test_bad_cluster_conflict_fails(): invalid(lambda p: p['clusters'][0]['conflict_refs'].__setitem__(0,'missing'))
def test_derived_cluster_member_must_be_derived():
    def mutate(p):
        c=next(x for x in p['clusters'] if x['cluster_id']=='cluster:proposal-cost')
        c['derived_member_refs']=['anchor:claim:report-cost-possible']
    invalid(mutate)

def test_bad_provenance_predecessor_fails(): invalid(lambda p: p['provenance_records'][0].__setitem__('predecessor_framing_fingerprint_sha256','0'*64))
def test_bad_snapshot_predecessor_fails(): invalid(lambda p: p['snapshots'][0].__setitem__('predecessor_framing_fingerprint_sha256','0'*64))
def test_bad_snapshot_anchor_fingerprint_fails(): invalid(lambda p: p['snapshots'][0]['anchor_fingerprints'].__setitem__(next(iter(p['snapshots'][0]['anchor_fingerprints'])),'0'*64))
def test_database_migration_none(): assert ref().database_migration == 'none'


def test_main_mounts_v417_routes():
    from app.main import create_app
    app = create_app()
    paths = {r.path for r in app.routes}
    assert '/v1/source-reconciliation/contract' in paths
    assert '/public/v1/source-reconciliation/contract' in paths
