from copy import deepcopy
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.routers import contextual_causal_language_mechanism as api
from app.services.contextual_causal_language_mechanism import (
    CausalEvidenceClass,
    CausalLanguageKind,
    CausalRelationKind,
    CausalReviewState,
    ContextualCausalLanguageMechanismBundle,
    MechanismState,
    contract_document,
    reference_contextual_causal_language_mechanism_bundle,
)

def ref(): return reference_contextual_causal_language_mechanism_bundle()
def payload(): return ref().model_dump(mode="json")
def invalid(mutator):
    p=deepcopy(payload()); mutator(p)
    with pytest.raises((ValidationError, ValueError)): ContextualCausalLanguageMechanismBundle.model_validate(p)

def test_release_identity():
    assert tuple(map(int, Settings().version.split('.'))) >= (4,15,0)
    assert ref().release == '4.15.0'
    assert ref().contract == 'sc.core.contextual-causal-language-mechanism-intelligence.v1'
    assert ref().predecessor_contract == 'sc.core.evidence-context-integration-layer.v1'

def test_predecessor_exact():
    assert ref().predecessor_evidence_context.release == '4.14.0'
    assert ref().predecessor_evidence_context.contract == ref().predecessor_contract

def test_reference_inventory():
    assert len(ref().signals)==7
    assert len(ref().mechanisms)==2
    assert len(ref().intervention_contexts)==1
    assert len(ref().counterfactual_contexts)==2
    assert len(ref().assessments)==4
    assert len(ref().provenance_records)==1
    assert len(ref().snapshots)==1

def test_every_signal_preserves_anchor_binding():
    anchors={x.anchor_id:x for x in ref().predecessor_evidence_context.evidence_anchors}
    assert all(anchors[x.evidence_anchor_ref].claim_ref==x.claim_ref for x in ref().signals)

def test_translation_derivative_preserved():
    s=next(x for x in ref().signals if x.claim_ref=='claim:v48:en-proposal-may-reduce-costs')
    assert 'translation-derived' in s.qualification_refs
    assert s.language_tag=='en'

def test_original_language_preserved():
    s=next(x for x in ref().signals if x.claim_ref=='claim:v48:zh-proposal-may-lower-costs')
    assert s.language_tag=='zh'
    assert 'translation-derived' not in s.qualification_refs

def test_possible_causal_language_stays_modal():
    s=next(x for x in ref().signals if x.claim_ref=='claim:v46:measure-may-reduce-emissions')
    assert s.language_kind == CausalLanguageKind.causal_possibility
    assert s.modality == 'possible'

def test_negative_causal_claim_preserved():
    s=next(x for x in ref().signals if x.claim_ref=='claim:v45:measure-no-emissions-reduction')
    assert s.language_kind == CausalLanguageKind.causal_denial
    assert s.polarity == 'negative'

def test_mechanisms_are_proposed_not_validated():
    assert all(x.state == MechanismState.proposed for x in ref().mechanisms)
    assert all(x.mechanism_is_hypothesis_not_validated_pathway for x in ref().mechanisms)

def test_intervention_context_not_identified():
    x=ref().intervention_contexts[0]
    assert x.evidence_class == CausalEvidenceClass.evidence_linked
    assert x.sufficient_for_causal_identification is False
    assert x.design_ref is None

def test_counterfactuals_have_no_estimate():
    assert all(x.estimate_available is False for x in ref().counterfactual_contexts)
    assert all(x.identification_strategy_ref is None for x in ref().counterfactual_contexts)

def test_strict_evidence_conflict_stays_unresolved():
    a=next(x for x in ref().assessments if x.assessment_id=='causal-assessment:emissions-effect-conflict')
    assert a.relation_kind == CausalRelationKind.unresolved
    assert a.evidence_class == CausalEvidenceClass.unresolved
    assert a.state == CausalReviewState.unresolved

def test_agency_possible_effect_not_promoted():
    a=next(x for x in ref().assessments if x.assessment_id=='causal-assessment:agency-possible-emissions-effect')
    assert a.evidence_class == CausalEvidenceClass.linguistic_only
    assert a.establishes_causal_truth is False

def test_no_intervention_supported_assessment_in_fixture():
    assert not any(x.evidence_class == CausalEvidenceClass.intervention_supported for x in ref().assessments)

def test_policy_boundaries():
    p=ref().policy
    assert p.causal_language_is_distinct_from_causal_identification
    assert p.temporal_precedence_is_not_causality
    assert p.association_is_not_causality
    assert p.mechanism_plausibility_is_not_mechanism_validation
    assert p.intervention_language_is_not_experimental_evidence
    assert p.counterfactual_language_is_not_counterfactual_estimate
    assert p.evidence_link_is_not_causal_identification
    assert p.causal_score_establishes_truth is False
    assert p.causal_wording_establishes_causality is False

def test_policy_no_graph_mutation():
    p=ref().policy
    assert not p.automatic_causal_graph_mutation_authorized
    assert not p.evidence_graph_mutation_authorized
    assert not p.knowledge_graph_mutation_authorized
    assert not p.identity_graph_mutation_authorized

def test_snapshot_exact_signal_fingerprints():
    assert ref().snapshots[0].signal_fingerprints == {x.signal_id:x.fingerprint() for x in ref().signals}

def test_snapshot_exact_mechanism_fingerprints():
    assert ref().snapshots[0].mechanism_fingerprints == {x.mechanism_id:x.fingerprint() for x in ref().mechanisms}

def test_snapshot_exact_assessment_fingerprints():
    assert ref().snapshots[0].assessment_fingerprints == {x.assessment_id:x.fingerprint() for x in ref().assessments}

def test_snapshot_deterministic(): assert ref().snapshots[0].fingerprint() == ref().snapshots[0].fingerprint()
def test_bundle_deterministic(): assert ref().fingerprint() == ref().fingerprint()

def test_contract_counts():
    c=contract_document()['reference']
    assert c['causal_language_signals']==7
    assert c['mechanism_hypotheses']==2
    assert c['intervention_contexts']==1
    assert c['counterfactual_contexts']==2
    assert c['causal_assessments']==4

def test_contract_unresolved_reference(): assert contract_document()['reference']['unresolved_causal_assessments']==1
def test_contract_no_intervention_supported_reference(): assert contract_document()['reference']['intervention_supported_assessments']==0

def test_contract_boundaries():
    b=contract_document()['boundaries']
    assert not b['causal_wording_establishes_causality']
    assert not b['automatic_causal_graph_mutation_performed']

def test_contract_prepares_next_line(): assert contract_document()['roadmap_integration']['prepares_v4160_narrative_framing_perspective_intelligence'] is True

def test_api_contract(): assert api.contract()['release']=='4.15.0'
def test_api_reference(): assert api.reference()['ok'] is True
def test_api_signals(): assert api.reference_signals()['count']==7
def test_api_mechanisms(): assert api.reference_mechanisms()['count']==2
def test_api_interventions(): assert api.reference_interventions()['count']==1
def test_api_counterfactuals(): assert api.reference_counterfactuals()['count']==2
def test_api_assessments(): assert api.reference_assessments()['count']==4

def test_bad_signal_claim_fails(): invalid(lambda p: p['signals'][0].__setitem__('claim_ref','missing'))
def test_bad_signal_anchor_fails(): invalid(lambda p: p['signals'][0].__setitem__('evidence_anchor_ref','missing'))
def test_bad_signal_binding_fails(): invalid(lambda p: p['signals'][0].__setitem__('evidence_anchor_ref',p['signals'][1]['evidence_anchor_ref']))

def test_bad_derived_translation_qualification_fails():
    idx=next(i for i,x in enumerate(payload()['signals']) if x['claim_ref']=='claim:v48:en-proposal-may-reduce-costs')
    invalid(lambda p: p['signals'][idx].__setitem__('qualification_refs',[]))

def test_bad_mechanism_signal_fails(): invalid(lambda p: p['mechanisms'][0]['supporting_signal_refs'].__setitem__(0,'missing'))
def test_bad_mechanism_anchor_fails(): invalid(lambda p: p['mechanisms'][0]['evidence_anchor_refs'].__setitem__(0,'missing'))

def test_bad_intervention_signal_fails(): invalid(lambda p: p['intervention_contexts'][0]['source_signal_refs'].__setitem__(0,'missing'))
def test_bad_intervention_anchor_fails(): invalid(lambda p: p['intervention_contexts'][0]['evidence_anchor_refs'].__setitem__(0,'missing'))

def test_intervention_supported_requires_design():
    invalid(lambda p: p['intervention_contexts'][0].__setitem__('evidence_class','intervention-supported'))

def test_counterfactual_cannot_claim_strategy_without_estimate():
    invalid(lambda p: p['counterfactual_contexts'][0].__setitem__('identification_strategy_ref','design:fake'))

def test_bad_assessment_signal_fails(): invalid(lambda p: p['assessments'][0]['subject_signal_refs'].__setitem__(0,'missing'))
def test_bad_assessment_mechanism_fails(): invalid(lambda p: p['assessments'][0]['mechanism_refs'].__setitem__(0,'missing'))
def test_bad_assessment_evidence_context_fails(): invalid(lambda p: p['assessments'][0]['evidence_context_assessment_refs'].__setitem__(0,'missing'))

def test_linguistic_only_cannot_claim_causes_relation():
    idx=next(i for i,x in enumerate(payload()['assessments']) if x['evidence_class']=='linguistic-only')
    invalid(lambda p: p['assessments'][idx].__setitem__('relation_kind','causes'))

def test_bad_snapshot_predecessor_fails(): invalid(lambda p: p['snapshots'][0].__setitem__('predecessor_evidence_context_fingerprint_sha256','0'*64))
def test_bad_snapshot_signal_fingerprint_fails():
    invalid(lambda p: p['snapshots'][0]['signal_fingerprints'].__setitem__(next(iter(p['snapshots'][0]['signal_fingerprints'])),'0'*64))

def test_database_migration_none(): assert ref().database_migration=='none'

def test_main_mounts_v415_routes():
    from app.main import app
    paths={r.path for r in app.routes}
    assert '/v1/causal-context/contract' in paths
    assert '/public/v1/causal-context/contract' in paths
