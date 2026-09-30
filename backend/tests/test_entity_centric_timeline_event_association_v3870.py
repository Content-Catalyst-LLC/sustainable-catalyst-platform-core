import pytest
from pydantic import ValidationError
from app.services.entity_centric_timeline_event_association import *

def ref(): return reference_entity_centric_timeline_event_association_bundle()

def test_release_contract():
    assert CORE_RELEASE=='3.87.0'; assert CONTRACT_VERSION=='sc.core.entity-centric-timeline-event-association.v1'

def test_reference_counts():
    b=ref(); assert (len(b.events),len(b.participations),len(b.source_assertions),len(b.temporal_qualifications),len(b.event_associations),len(b.reviews),len(b.timelines))==(4,6,4,2,3,2,2)

@pytest.mark.parametrize('field',['temporal_proximity_is_not_causality','co_presence_is_not_relationship','sequence_is_not_intent','repeated_association_is_not_coordination','timeline_is_not_truth_verdict'])
def test_bundle_principles(field): assert getattr(ref(),field) is True

@pytest.mark.parametrize('field',['identity_graph_mutation_performed','relationship_graph_mutation_performed','evidence_graph_mutation_performed'])
def test_mutations_false(field): assert getattr(ref(),field) is False

@pytest.mark.parametrize('field',['temporal_proximity_is_not_causality','co_presence_is_not_relationship','sequence_is_not_intent','repeated_association_is_not_coordination','timeline_is_view_not_source_record','source_disagreement_is_preserved','temporal_uncertainty_is_preserved','event_association_is_explanatory_not_dispositive'])
def test_contract_principles(field): assert contract_document()['principles'][field] is True

@pytest.mark.parametrize('field',['runtime_may_infer_causality_from_sequence','runtime_may_infer_relationship_from_copresence','runtime_may_infer_coordination_from_repetition','runtime_may_infer_intent_from_ordering','runtime_may_erase_temporal_uncertainty','v387_timeline_is_truth_verdict','identity_graph_mutation_performed','relationship_graph_mutation_performed','evidence_graph_mutation_performed'])
def test_contract_boundaries(field): assert contract_document()['boundaries'][field] is False

@pytest.mark.parametrize('i',range(4))
def test_event_nontruth_boundaries(i):
    e=ref().events[i]; assert e.event_record_is_not_truth_verdict and e.temporal_position_is_not_causal_claim and e.event_record_does_not_create_relationship

@pytest.mark.parametrize('i',range(6))
def test_participation_boundaries(i):
    p=ref().participations[i]; assert p.participation_is_not_affiliation and p.co_participation_is_not_relationship_proof and p.participation_is_not_intent

@pytest.mark.parametrize('i',range(4))
def test_source_assertion_boundaries(i):
    a=ref().source_assertions[i]; assert a.source_statement_is_not_event_truth and a.source_independence_group_is_not_corroboration_count

@pytest.mark.parametrize('i',range(2))
def test_temporal_qualification_boundaries(i):
    q=ref().temporal_qualifications[i]; assert q.temporal_uncertainty_preserved and q.temporal_order_is_not_causality

@pytest.mark.parametrize('i',range(3))
def test_association_boundaries(i):
    a=ref().event_associations[i]; assert a.association_is_not_causal_claim and a.association_is_not_coordination_claim and a.association_is_not_relationship_fact and a.association_does_not_create_graph_edge

@pytest.mark.parametrize('i',range(2))
def test_review_boundaries(i):
    r=ref().reviews[i]; assert r.independent_review and r.review_is_not_truth_verdict and r.review_does_not_create_causality

@pytest.mark.parametrize('i',range(2))
def test_timeline_boundaries(i):
    t=ref().timelines[i]; assert t.timeline_is_view_not_source_record and t.timeline_order_is_not_causal_order and t.omission_from_timeline_is_not_nonoccurrence

def test_snapshot_boundaries():
    s=ref().snapshots[0]; assert s.immutable_snapshot and s.snapshot_preserves_source_disagreement and s.snapshot_preserves_temporal_uncertainty and s.snapshot_is_not_truth_verdict and s.snapshot_does_not_mutate_graphs

@pytest.mark.parametrize('enum_cls',[EventType,EventAssertionState,ParticipationRole,TemporalPrecision,TemporalRelation,EventAssociationKind,ReviewDisposition])
def test_enum_roundtrip(enum_cls):
    for x in enum_cls: assert enum_cls(x.value) is x

@pytest.mark.parametrize('i',range(4))
def test_event_fingerprint(i): assert len(ref().events[i].fingerprint())==64 and ref().events[i].fingerprint()==ref().events[i].fingerprint()
@pytest.mark.parametrize('i',range(6))
def test_participation_fingerprint(i): assert len(ref().participations[i].fingerprint())==64
@pytest.mark.parametrize('i',range(4))
def test_assertion_fingerprint(i): assert len(ref().source_assertions[i].fingerprint())==64
@pytest.mark.parametrize('i',range(2))
def test_qualification_fingerprint(i): assert len(ref().temporal_qualifications[i].fingerprint())==64
@pytest.mark.parametrize('i',range(3))
def test_association_fingerprint(i): assert len(ref().event_associations[i].fingerprint())==64
@pytest.mark.parametrize('i',range(2))
def test_review_fingerprint(i): assert len(ref().reviews[i].fingerprint())==64
@pytest.mark.parametrize('i',range(2))
def test_timeline_fingerprint(i): assert len(ref().timelines[i].fingerprint())==64

def test_bundle_fingerprint_contract(): assert contract_document()['reference']['bundle_fingerprint_sha256']==ref().fingerprint()

def test_event_temporal_confidence_requires_semantics():
    d=ref().events[0].model_dump(mode='python'); d['temporal_confidence']=.5; d['temporal_confidence_semantics']=None
    with pytest.raises(ValidationError): EventRecord(**d)

def test_known_precision_requires_start():
    d=ref().events[0].model_dump(mode='python'); d['start_time']=None
    with pytest.raises(ValidationError): EventRecord(**d)

def test_association_distinct_events():
    d=ref().event_associations[0].model_dump(mode='python'); d['target_event_ref']=d['source_event_ref']
    with pytest.raises(ValidationError): CrossEventAssociation(**d)

def test_association_confidence_requires_semantics():
    d=ref().event_associations[0].model_dump(mode='python'); d['confidence_semantics']=None
    with pytest.raises(ValidationError): CrossEventAssociation(**d)

def test_duplicate_event_source_rejected():
    d=ref().events[0].model_dump(mode='python'); d['source_refs']=d['source_refs']+[d['source_refs'][0]]
    with pytest.raises(ValidationError): EventRecord(**d)

def test_unknown_participation_event_rejected():
    d=ref().model_dump(mode='python'); d['participations'][0]['event_ref']='event:missing'
    with pytest.raises(ValidationError): EntityCentricTimelineEventAssociationBundle(**d)

def test_unknown_participation_entity_rejected():
    d=ref().model_dump(mode='python'); d['participations'][0]['entity_ref']='entity:missing'
    with pytest.raises(ValidationError): EntityCentricTimelineEventAssociationBundle(**d)

def test_unknown_segment_rejected():
    d=ref().model_dump(mode='python'); d['source_assertions'][0]['document_segment_refs']=['segment:missing']
    with pytest.raises(ValidationError): EntityCentricTimelineEventAssociationBundle(**d)

def test_unknown_upstream_assertion_rejected():
    d=ref().model_dump(mode='python'); d['source_assertions'][0]['upstream_assertion_refs']=['assertion:missing']
    with pytest.raises(ValidationError): EntityCentricTimelineEventAssociationBundle(**d)

def test_unknown_qualification_event_rejected():
    d=ref().model_dump(mode='python'); d['temporal_qualifications'][0]['event_ref']='event:missing'
    with pytest.raises(ValidationError): EntityCentricTimelineEventAssociationBundle(**d)

def test_unknown_contradiction_rejected():
    d=ref().model_dump(mode='python'); d['temporal_qualifications'][0]['contradiction_refs']=['contradiction:missing']
    with pytest.raises(ValidationError): EntityCentricTimelineEventAssociationBundle(**d)

def test_unknown_association_event_rejected():
    d=ref().model_dump(mode='python'); d['event_associations'][0]['target_event_ref']='event:missing'
    with pytest.raises(ValidationError): EntityCentricTimelineEventAssociationBundle(**d)

def test_unknown_association_entity_rejected():
    d=ref().model_dump(mode='python'); d['event_associations'][0]['shared_entity_refs']=['entity:missing']
    with pytest.raises(ValidationError): EntityCentricTimelineEventAssociationBundle(**d)

def test_unknown_review_association_rejected():
    d=ref().model_dump(mode='python'); d['reviews'][0]['event_association_ref']='association:missing'
    with pytest.raises(ValidationError): EntityCentricTimelineEventAssociationBundle(**d)

def test_timeline_wrong_entity_participation_rejected():
    d=ref().model_dump(mode='python'); d['timelines'][0]['participation_refs']=[d['participations'][1]['event_participation_id']]
    with pytest.raises(ValidationError): EntityCentricTimelineEventAssociationBundle(**d)

def test_unknown_snapshot_upstream_rejected():
    d=ref().model_dump(mode='python'); d['snapshots'][0]['contradiction_resolution_snapshot_ref']='snapshot:missing'
    with pytest.raises(ValidationError): EntityCentricTimelineEventAssociationBundle(**d)

def test_unknown_snapshot_event_rejected():
    d=ref().model_dump(mode='python'); d['snapshots'][0]['event_refs']=['event:missing']
    with pytest.raises(ValidationError): EntityCentricTimelineEventAssociationBundle(**d)

def test_schema_generation():
    s=EntityCentricTimelineEventAssociationBundle.model_json_schema(); assert s['title']=='EntityCentricTimelineEventAssociationBundle'; assert '$defs' in s

@pytest.mark.parametrize('i,state',[ (0,'source-reported'),(1,'source-reported'),(2,'source-reported'),(3,'qualified') ])
def test_event_states(i,state): assert ref().events[i].assertion_state.value==state

@pytest.mark.parametrize('i,kind',[ (0,'reported-interaction'),(1,'filing'),(2,'disclosure'),(3,'research-observation') ])
def test_event_types(i,kind): assert ref().events[i].event_type.value==kind

@pytest.mark.parametrize('i,kind',[ (0,'shared-entity'),(1,'temporal-sequence'),(2,'contradiction-context') ])
def test_association_kinds(i,kind): assert ref().event_associations[i].association_kind.value==kind

@pytest.mark.parametrize('i,relation',[ (0,'before'),(1,'before'),(2,'before') ])
def test_temporal_relations(i,relation): assert ref().event_associations[i].temporal_relation.value==relation

@pytest.mark.parametrize('i',range(4))
def test_events_have_provenance(i): assert ref().events[i].provenance_refs and ref().events[i].upstream_object_refs and ref().events[i].source_refs
@pytest.mark.parametrize('i',range(6))
def test_participations_have_provenance(i): assert ref().participations[i].provenance_refs and ref().participations[i].source_refs
@pytest.mark.parametrize('i',range(4))
def test_source_assertions_have_group(i): assert ref().source_assertions[i].source_independence_group
@pytest.mark.parametrize('i',range(3))
def test_associations_have_basis(i): assert ref().event_associations[i].basis_refs
@pytest.mark.parametrize('i',range(2))
def test_reviews_have_rationale(i): assert len(ref().reviews[i].rationale)>20
@pytest.mark.parametrize('i',range(2))
def test_timelines_have_three_events(i): assert len(ref().timelines[i].event_refs)==3

@pytest.mark.parametrize('field',['require_temporal_provenance','require_source_provenance','require_explicit_entity_roles','require_assertion_state','preserve_temporal_uncertainty','preserve_source_disagreement'])
def test_policy_requirements(field): assert getattr(ref().policies[0],field) is True
@pytest.mark.parametrize('field',['temporal_proximity_can_establish_causality','co_presence_can_establish_relationship','event_sequence_can_establish_intent','repeated_association_can_establish_coordination','automatic_graph_mutation_allowed'])
def test_policy_prohibitions(field): assert getattr(ref().policies[0],field) is False
