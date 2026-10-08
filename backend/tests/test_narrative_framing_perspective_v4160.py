from copy import deepcopy
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.routers import narrative_framing_perspective as api
from app.services.narrative_framing_perspective import (
    EmphasisState,
    FramingReviewState,
    NarrativeFramingPerspectiveBundle,
    PerspectiveRelationship,
    contract_document,
    reference_narrative_framing_perspective_bundle,
)

def ref(): return reference_narrative_framing_perspective_bundle()
def payload(): return ref().model_dump(mode="json")
def invalid(mutator):
    p=deepcopy(payload()); mutator(p)
    with pytest.raises((ValidationError,ValueError)): NarrativeFramingPerspectiveBundle.model_validate(p)

def test_release_identity():
    assert tuple(map(int,Settings().version.split('.'))) >= (4,16,0)
    assert ref().release=='4.16.0'
    assert ref().contract=='sc.core.narrative-framing-perspective-intelligence.v1'
    assert ref().predecessor_contract=='sc.core.contextual-causal-language-mechanism-intelligence.v1'

def test_predecessor_exact():
    assert ref().predecessor_causal_context.release=='4.15.0'
    assert ref().predecessor_causal_context.contract==ref().predecessor_contract

def test_reference_inventory():
    assert len(ref().perspectives)==6
    assert len(ref().signals)==12
    assert len(ref().frames)==6
    assert len(ref().comparisons)==4
    assert len(ref().assessments)==4
    assert len(ref().provenance_records)==1
    assert len(ref().snapshots)==1

def test_each_perspective_has_claims(): assert all(x.claim_refs for x in ref().perspectives)
def test_each_frame_has_signals(): assert all(x.signal_refs for x in ref().frames)
def test_each_signal_is_descriptive(): assert all(x.signal_is_descriptive_not_motive_inference for x in ref().signals)
def test_no_signal_is_bias_verdict(): assert all(x.signal_is_not_bias_verdict for x in ref().signals)
def test_foregrounded_signals_exist(): assert any(x.emphasis==EmphasisState.foregrounded for x in ref().signals)

def test_derived_english_perspective_preserved():
    p=next(x for x in ref().perspectives if x.perspective_id=='perspective:v48-en')
    assert p.derived_representation is True
    assert 'translation-derived' in p.qualification_refs

def test_chinese_original_not_derived():
    p=next(x for x in ref().perspectives if x.perspective_id=='perspective:v48-zh')
    assert p.language_tag=='zh'
    assert p.derived_representation is False

def test_report_vs_agency_is_modality_dependent():
    c=next(x for x in ref().comparisons if x.comparison_id=='comparison:report-vs-agency')
    assert c.relationship==PerspectiveRelationship.modality_dependent
    assert c.comparison_establishes_truth is False
    assert c.comparison_establishes_bias is False

def test_audit_vs_review_is_scope_dependent():
    c=next(x for x in ref().comparisons if x.comparison_id=='comparison:audit-vs-review')
    assert c.relationship==PerspectiveRelationship.scope_dependent

def test_cross_language_alignment_preserves_derivation():
    c=next(x for x in ref().comparisons if x.comparison_id=='comparison:zh-vs-en-cost')
    assert c.relationship==PerspectiveRelationship.cross_language_aligned
    assert 'translation-derived-not-independent' in c.qualification_refs

def test_plurality_assessment_stays_unresolved():
    a=next(x for x in ref().assessments if x.assessment_id=='framing-assessment:emissions-perspective-plurality')
    assert a.state==FramingReviewState.unresolved
    assert a.establishes_truth is False
    assert a.establishes_bias is False
    assert a.establishes_motive is False

def test_policy_boundaries():
    p=ref().policy
    assert p.framing_is_descriptive_not_truth_adjudication
    assert p.framing_difference_is_not_factual_contradiction
    assert p.emphasis_is_not_manipulation
    assert p.omission_is_not_deception
    assert p.perspective_is_not_private_motive
    assert p.framing_analysis_is_not_ideology_classification
    assert not p.framing_score_establishes_truth
    assert not p.framing_score_establishes_bias
    assert not p.framing_score_establishes_credibility

def test_policy_no_graph_mutation():
    p=ref().policy
    assert not p.automatic_context_graph_mutation_authorized
    assert not p.automatic_evidence_graph_mutation_authorized
    assert not p.automatic_knowledge_graph_mutation_authorized
    assert not p.automatic_identity_graph_mutation_authorized

def test_snapshot_exact_perspectives(): assert ref().snapshots[0].perspective_fingerprints=={x.perspective_id:x.fingerprint() for x in ref().perspectives}
def test_snapshot_exact_signals(): assert ref().snapshots[0].signal_fingerprints=={x.signal_id:x.fingerprint() for x in ref().signals}
def test_snapshot_exact_frames(): assert ref().snapshots[0].frame_fingerprints=={x.frame_id:x.fingerprint() for x in ref().frames}
def test_snapshot_exact_comparisons(): assert ref().snapshots[0].comparison_fingerprints=={x.comparison_id:x.fingerprint() for x in ref().comparisons}
def test_snapshot_exact_assessments(): assert ref().snapshots[0].assessment_fingerprints=={x.assessment_id:x.fingerprint() for x in ref().assessments}
def test_bundle_deterministic(): assert ref().fingerprint()==ref().fingerprint()

def test_contract_counts():
    c=contract_document()['reference']
    assert c['source_perspectives']==6
    assert c['framing_signals']==12
    assert c['narrative_frames']==6
    assert c['perspective_comparisons']==4
    assert c['framing_assessments']==4
    assert c['derived_perspectives']==1

def test_contract_boundaries():
    b=contract_document()['boundaries']
    assert not b['framing_score_establishes_truth']
    assert not b['framing_score_establishes_bias']
    assert not b['framing_score_establishes_credibility']

def test_contract_prepares_next_line(): assert contract_document()['roadmap_integration']['prepares_v4170_cross_source_semantic_reconciliation'] is True

def test_api_contract(): assert api.contract()['release']=='4.16.0'
def test_api_reference(): assert api.reference()['ok'] is True
def test_api_perspectives(): assert api.reference_perspectives()['count']==6
def test_api_signals(): assert api.reference_signals()['count']==12
def test_api_frames(): assert api.reference_frames()['count']==6
def test_api_comparisons(): assert api.reference_comparisons()['count']==4
def test_api_assessments(): assert api.reference_assessments()['count']==4

def test_bad_perspective_source_fails(): invalid(lambda p:p['perspectives'][0].__setitem__('source_context_ref','missing'))
def test_bad_perspective_claim_fails(): invalid(lambda p:p['perspectives'][0]['claim_refs'].__setitem__(0,'missing'))
def test_bad_perspective_cross_source_claim_fails(): invalid(lambda p:p['perspectives'][0]['claim_refs'].__setitem__(0,p['perspectives'][1]['claim_refs'][0]))
def test_bad_perspective_causal_assessment_fails(): invalid(lambda p:p['perspectives'][0]['causal_assessment_refs'].__setitem__(0,'missing'))

def test_derived_source_cannot_be_marked_original():
    idx=next(i for i,x in enumerate(payload()['perspectives']) if x['perspective_id']=='perspective:v48-en')
    invalid(lambda p:p['perspectives'][idx].__setitem__('derived_representation',False))

def test_bad_signal_perspective_fails(): invalid(lambda p:p['signals'][0].__setitem__('perspective_ref','missing'))
def test_bad_signal_claim_fails(): invalid(lambda p:p['signals'][0]['claim_refs'].__setitem__(0,'missing'))
def test_signal_claim_must_belong_to_perspective(): invalid(lambda p:p['signals'][0]['claim_refs'].__setitem__(0,p['perspectives'][1]['claim_refs'][0]))
def test_bad_frame_perspective_fails(): invalid(lambda p:p['frames'][0]['perspective_refs'].__setitem__(0,'missing'))
def test_bad_frame_signal_fails(): invalid(lambda p:p['frames'][0]['signal_refs'].__setitem__(0,'missing'))
def test_frame_signal_must_belong_to_frame_perspective(): invalid(lambda p:p['frames'][0]['signal_refs'].__setitem__(0,p['frames'][1]['signal_refs'][0]))
def test_comparison_same_frame_fails(): invalid(lambda p:p['comparisons'][0].__setitem__('right_frame_ref',p['comparisons'][0]['left_frame_ref']))
def test_bad_comparison_frame_fails(): invalid(lambda p:p['comparisons'][0].__setitem__('left_frame_ref','missing'))

def test_cross_language_requires_different_languages():
    idx=next(i for i,x in enumerate(payload()['comparisons']) if x['relationship']=='cross-language-aligned')
    invalid(lambda p:p['comparisons'][idx].__setitem__('right_frame_ref','frame:v48:zh-economic-possibility'))

def test_bad_assessment_frame_fails(): invalid(lambda p:p['assessments'][0]['frame_refs'].__setitem__(0,'missing'))
def test_bad_assessment_comparison_fails(): invalid(lambda p:p['assessments'][0]['comparison_refs'].__setitem__(0,'missing'))
def test_bad_assessment_causal_ref_fails(): invalid(lambda p:p['assessments'][0]['causal_assessment_refs'].__setitem__(0,'missing'))
def test_reviewed_assessment_requires_reviewer():
    idx=next(i for i,x in enumerate(payload()['assessments']) if x['state']=='reviewed')
    invalid(lambda p:p['assessments'][idx].__setitem__('reviewer_ref',None))
def test_bad_snapshot_predecessor_fails(): invalid(lambda p:p['snapshots'][0].__setitem__('predecessor_causal_context_fingerprint_sha256','0'*64))
def test_bad_snapshot_frame_fingerprint_fails(): invalid(lambda p:p['snapshots'][0]['frame_fingerprints'].__setitem__(next(iter(p['snapshots'][0]['frame_fingerprints'])),'0'*64))
def test_database_migration_none(): assert ref().database_migration=='none'

def test_main_mounts_v416_routes():
    from app.main import app
    paths={r.path for r in app.routes}
    assert '/v1/narrative-framing/contract' in paths
    assert '/public/v1/narrative-framing/contract' in paths
