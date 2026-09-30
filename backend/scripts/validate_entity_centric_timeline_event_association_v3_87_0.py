#!/usr/bin/env python3
from app.services.entity_centric_timeline_event_association import contract_document, reference_entity_centric_timeline_event_association_bundle
b=reference_entity_centric_timeline_event_association_bundle(); c=contract_document()
assert c['release']=='3.87.0' and c['contract']=='sc.core.entity-centric-timeline-event-association.v1'
assert len(b.events)==4 and len(b.participations)==6 and len(b.event_associations)==3 and len(b.timelines)==2
for k in ['temporal_proximity_is_not_causality','co_presence_is_not_relationship','sequence_is_not_intent','repeated_association_is_not_coordination','timeline_is_view_not_source_record','source_disagreement_is_preserved','temporal_uncertainty_is_preserved']:
    assert c['principles'][k] is True
for k in ['runtime_may_infer_causality_from_sequence','runtime_may_infer_relationship_from_copresence','runtime_may_infer_coordination_from_repetition','runtime_may_infer_intent_from_ordering','runtime_may_erase_temporal_uncertainty','v387_timeline_is_truth_verdict','identity_graph_mutation_performed','relationship_graph_mutation_performed','evidence_graph_mutation_performed']:
    assert c['boundaries'][k] is False
print('PASS - Platform Core v3.87.0 Entity-Centric Timeline & Event Association')
print('CONTRACT='+c['contract'])
print('EVENTS='+str(len(b.events)))
print('PARTICIPATIONS='+str(len(b.participations)))
print('SOURCE_ASSERTIONS='+str(len(b.source_assertions)))
print('TEMPORAL_QUALIFICATIONS='+str(len(b.temporal_qualifications)))
print('EVENT_ASSOCIATIONS='+str(len(b.event_associations)))
print('REVIEWS='+str(len(b.reviews)))
print('TIMELINES='+str(len(b.timelines)))
print('TEMPORAL_PROXIMITY_IS_CAUSALITY=false')
print('CO_PRESENCE_IS_RELATIONSHIP=false')
print('SEQUENCE_IS_INTENT=false')
print('RELATIONSHIP_GRAPH_MUTATION_PERFORMED=false')
