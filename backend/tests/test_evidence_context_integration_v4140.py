from copy import deepcopy
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.routers import evidence_context_integration as api
from app.services.evidence_context_integration import (
    EvidenceContextIntegrationBundle,
    EvidenceContextRelationKind,
    EvidenceIndependenceState,
    EvidenceIntegrationOutcome,
    EvidenceContextReviewState,
    contract_document,
    reference_evidence_context_integration_bundle,
)

def ref(): return reference_evidence_context_integration_bundle()
def payload(): return ref().model_dump(mode="json")
def invalid(mutator):
    p=deepcopy(payload()); mutator(p)
    with pytest.raises((ValidationError, ValueError)): EvidenceContextIntegrationBundle.model_validate(p)

def test_release_identity():
    assert tuple(int(x) for x in Settings().version.split('.')) >= (4,14,0)
    assert ref().release == '4.14.0'
    assert ref().contract == 'sc.core.evidence-context-integration-layer.v1'
    assert ref().predecessor_contract == 'sc.core.claim-alignment-agreement-contradiction-intelligence.v1'

def test_v413_predecessor_exact():
    assert ref().predecessor_claim_comparison.release == '4.13.0'
    assert ref().predecessor_claim_comparison.contract == ref().predecessor_contract

def test_reference_inventory():
    assert len(ref().evidence_anchors) == 7
    assert len(ref().links) == 12
    assert len(ref().assessments) == 6
    assert len(ref().provenance_records) == 1
    assert len(ref().snapshots) == 1

def test_every_claim_has_anchor():
    assert {a.claim_ref for a in ref().evidence_anchors} == {c.claim_id for c in ref().predecessor_claim_comparison.claims}

def test_every_relation_has_two_links():
    by={}
    for x in ref().links: by.setdefault(x.relation_assessment_ref,[]).append(x)
    assert len(by)==6 and all(len(v)==2 for v in by.values())

def test_strict_contradiction_stays_unresolved():
    pred=next(x for x in ref().predecessor_claim_comparison.assessments if x.relation_kind.value=='contradiction')
    a=next(x for x in ref().assessments if x.claim_relation_assessment_ref==pred.assessment_id)
    assert a.outcome == EvidenceIntegrationOutcome.unresolved_evidence_conflict
    assert a.state == EvidenceContextReviewState.unresolved

def test_translation_derivative_not_independent():
    a=next(x for x in ref().evidence_anchors if x.claim_ref=='claim:v48:en-proposal-may-reduce-costs')
    assert a.independence_state == EvidenceIndependenceState.same_source_derived
    links=[x for x in ref().links if x.evidence_anchor_ref==a.anchor_id]
    assert links and all(not x.independent_corroboration for x in links)
    assert all(x.contextual_relation == EvidenceContextRelationKind.derived_representation for x in links)

def test_original_language_anchor_independent():
    a=next(x for x in ref().evidence_anchors if x.claim_ref=='claim:v48:zh-proposal-may-lower-costs')
    assert a.independence_state == EvidenceIndependenceState.independent

def test_policy_upstream_review_authority(): assert ref().policy.upstream_evidence_review_status_is_authoritative is True
def test_policy_distinguishes_claim_from_evidence(): assert ref().policy.semantic_claim_is_distinct_from_evidence_record is True
def test_policy_read_only(): assert ref().policy.read_only_bridge_by_default is True
def test_policy_no_truth_from_count(): assert ref().policy.supporting_evidence_count_establishes_truth is False
def test_policy_no_validity_from_link(): assert ref().policy.evidence_link_establishes_evidence_validity is False
def test_policy_no_false_claim_from_contradiction(): assert ref().policy.contradiction_link_identifies_false_claim is False
def test_policy_no_review_override(): assert ref().policy.semantic_layer_may_override_upstream_review_status is False
def test_policy_no_materialization(): assert ref().policy.automatic_evidence_materialization_authorized is False
def test_policy_no_truth_promotion(): assert ref().policy.claim_truth_promotion_authorized is False
def test_policy_no_graph_mutation():
    p=ref().policy
    assert not p.context_graph_mutation_authorized and not p.identity_graph_mutation_authorized and not p.evidence_graph_mutation_authorized and not p.knowledge_graph_mutation_authorized

def test_links_preserve_claim_qualifications():
    claims={x.claim_id:x for x in ref().predecessor_claim_comparison.claims}
    for x in ref().links: assert set(claims[x.claim_ref].qualification_refs).issubset(x.qualification_refs)

def test_links_preserve_claim_unresolved():
    claims={x.claim_id:x for x in ref().predecessor_claim_comparison.claims}
    for x in ref().links: assert set(claims[x.claim_ref].unresolved_refs).issubset(x.unresolved_refs)

def test_all_reviewed_links_have_reviewer():
    assert all(x.reviewer_ref for x in ref().links if x.state == EvidenceContextReviewState.reviewed)

def test_assessment_link_sets_exact():
    by={}
    for x in ref().links: by.setdefault(x.relation_assessment_ref,set()).add(x.link_id)
    for a in ref().assessments: assert set(a.evidence_link_refs)==by[a.claim_relation_assessment_ref]

def test_snapshot_predecessor_fingerprint(): assert ref().snapshots[0].predecessor_claim_comparison_fingerprint_sha256 == ref().predecessor_claim_comparison.fingerprint()
def test_snapshot_anchor_fingerprints(): assert ref().snapshots[0].anchor_fingerprints == {x.anchor_id:x.fingerprint() for x in ref().evidence_anchors}
def test_snapshot_link_fingerprints(): assert ref().snapshots[0].link_fingerprints == {x.link_id:x.fingerprint() for x in ref().links}
def test_snapshot_assessment_fingerprints(): assert ref().snapshots[0].assessment_fingerprints == {x.assessment_id:x.fingerprint() for x in ref().assessments}
def test_snapshot_deterministic(): assert ref().snapshots[0].fingerprint() == ref().snapshots[0].fingerprint()
def test_bundle_deterministic(): assert ref().fingerprint() == ref().fingerprint()
def test_contract_counts():
    c=contract_document(); assert c['reference']['evidence_anchors']==7 and c['reference']['evidence_context_links']==12 and c['reference']['evidence_context_assessments']==6

def test_contract_one_strict_conflict_unresolved(): assert contract_document()['reference']['strict_contradictions_left_unresolved']==1
def test_contract_boundaries():
    b=contract_document()['boundaries']; assert not b['evidence_graph_mutation_performed'] and not b['claim_truth_promotion_authorized']
def test_contract_prepares_reasoning_line(): assert contract_document()['roadmap_integration']['prepares_v4150_contextual_causal_language_mechanism_intelligence'] is True
def test_api_direct_contract(): assert api.contract()['release']=='4.14.0'
def test_api_direct_reference(): assert api.reference()['ok'] is True
def test_api_direct_anchors(): assert api.reference_anchors()['count']==7
def test_api_direct_links(): assert api.reference_links()['count']==12
def test_api_direct_assessments(): assert api.reference_assessments()['count']==6

def test_bad_anchor_claim_fails(): invalid(lambda p: p['evidence_anchors'][0].__setitem__('claim_ref','missing'))
def test_bad_anchor_source_fails(): invalid(lambda p: p['evidence_anchors'][0].__setitem__('source_context_ref','missing'))
def test_bad_derived_without_parent_fails():
    def m(p): p['evidence_anchors'][-1]['derived_from_evidence_record_ref']=None
    invalid(m)
def test_bad_link_anchor_fails(): invalid(lambda p: p['links'][0].__setitem__('evidence_anchor_ref','missing'))
def test_bad_link_claim_fails(): invalid(lambda p: p['links'][0].__setitem__('claim_ref','missing'))
def test_bad_independent_corroboration_for_translation_fails():
    idx=next(i for i,x in enumerate(payload()['links']) if x['claim_ref']=='claim:v48:en-proposal-may-reduce-costs')
    invalid(lambda p: p['links'][idx].__setitem__('independent_corroboration',True))
def test_bad_assessment_relation_fails(): invalid(lambda p: p['assessments'][0].__setitem__('claim_relation_assessment_ref','missing'))
def test_bad_assessment_links_fails(): invalid(lambda p: p['assessments'][0].__setitem__('evidence_link_refs',[p['links'][0]['link_id']]))
def test_strict_contradiction_cannot_auto_resolve():
    pred=next(x for x in ref().predecessor_claim_comparison.assessments if x.relation_kind.value=='contradiction')
    idx=next(i for i,x in enumerate(payload()['assessments']) if x['claim_relation_assessment_ref']==pred.assessment_id)
    invalid(lambda p: p['assessments'][idx].__setitem__('outcome','supports-comparison-context'))
def test_bad_snapshot_predecessor_fails(): invalid(lambda p: p['snapshots'][0].__setitem__('predecessor_claim_comparison_fingerprint_sha256','0'*64))
def test_bad_snapshot_anchor_fingerprint_fails():
    invalid(lambda p: p['snapshots'][0]['anchor_fingerprints'].__setitem__(next(iter(p['snapshots'][0]['anchor_fingerprints'])),'0'*64))
def test_database_migration_none(): assert ref().database_migration=='none'
def test_main_mounts_v414_routes():
    from app.main import app
    paths={r.path for r in app.routes}
    assert '/v1/evidence-context/contract' in paths and '/public/v1/evidence-context/contract' in paths
