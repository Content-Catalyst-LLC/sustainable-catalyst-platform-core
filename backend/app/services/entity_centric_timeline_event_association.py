from __future__ import annotations

from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .contradictory_identity_relationship_resolution import (
    ContradictoryIdentityRelationshipResolutionBundle,
    reference_contradictory_identity_relationship_resolution_bundle,
)

CORE_RELEASE = "3.87.0"
CONTRACT_VERSION = "sc.core.entity-centric-timeline-event-association.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class EventType(str, Enum):
    filing = "filing"
    disclosure = "disclosure"
    registry_observation = "registry-observation"
    reported_interaction = "reported-interaction"
    organizational_change = "organizational-change"
    communication = "communication"
    meeting = "meeting"
    transaction = "transaction"
    publication = "publication"
    legal_action = "legal-action"
    research_observation = "research-observation"
    other = "other"


class EventAssertionState(str, Enum):
    source_reported = "source-reported"
    independently_corroborated = "independently-corroborated"
    analytically_derived = "analytically-derived"
    disputed = "disputed"
    qualified = "qualified"
    unresolved = "unresolved"


class ParticipationRole(str, Enum):
    subject = "subject"
    object = "object"
    participant = "participant"
    issuer = "issuer"
    recipient = "recipient"
    observer = "observer"
    referenced = "referenced"
    unknown = "unknown"


class TemporalPrecision(str, Enum):
    instant = "instant"
    day = "day"
    month = "month"
    year = "year"
    interval = "interval"
    approximate = "approximate"
    unknown = "unknown"


class TemporalRelation(str, Enum):
    before = "before"
    after = "after"
    overlaps = "overlaps"
    contains = "contains"
    during = "during"
    contemporaneous = "contemporaneous"
    uncertain = "uncertain"


class EventAssociationKind(str, Enum):
    temporal_sequence = "temporal-sequence"
    temporal_overlap = "temporal-overlap"
    shared_entity = "shared-entity"
    shared_document = "shared-document"
    shared_source_group = "shared-source-group"
    relationship_context = "relationship-context"
    contradiction_context = "contradiction-context"
    analytical_pattern = "analytical-pattern"


class ReviewDisposition(str, Enum):
    support = "support"
    qualify = "qualify"
    reject = "reject"
    defer = "defer"
    unresolved = "unresolved"


class EventAssociationPolicy(BaseModel):
    event_association_policy_id: str = Field(min_length=2, max_length=500)
    require_temporal_provenance: Literal[True] = True
    require_source_provenance: Literal[True] = True
    require_explicit_entity_roles: Literal[True] = True
    require_assertion_state: Literal[True] = True
    preserve_temporal_uncertainty: Literal[True] = True
    preserve_source_disagreement: Literal[True] = True
    temporal_proximity_can_establish_causality: Literal[False] = False
    co_presence_can_establish_relationship: Literal[False] = False
    event_sequence_can_establish_intent: Literal[False] = False
    repeated_association_can_establish_coordination: Literal[False] = False
    automatic_graph_mutation_allowed: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class EventRecord(BaseModel):
    event_id: str = Field(min_length=2, max_length=500)
    event_type: EventType
    label: str = Field(min_length=1, max_length=2000)
    description: str = Field(min_length=1, max_length=12000)
    assertion_state: EventAssertionState
    start_time: str | None = Field(default=None, max_length=80)
    end_time: str | None = Field(default=None, max_length=80)
    temporal_precision: TemporalPrecision
    temporal_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    temporal_confidence_semantics: str | None = Field(default=None, max_length=2000)
    source_refs: list[str] = Field(min_length=1)
    upstream_object_refs: list[str] = Field(min_length=1)
    provenance_refs: list[str] = Field(min_length=1)
    event_record_is_not_truth_verdict: Literal[True] = True
    temporal_position_is_not_causal_claim: Literal[True] = True
    event_record_does_not_create_relationship: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_event(self):
        for vals,label in ((self.source_refs,"source_refs"),(self.upstream_object_refs,"upstream_object_refs"),(self.provenance_refs,"provenance_refs")):
            _unique(vals,label)
        if self.temporal_confidence is not None and not self.temporal_confidence_semantics:
            raise ValueError("temporal confidence requires semantics")
        if self.start_time is None and self.temporal_precision != TemporalPrecision.unknown:
            raise ValueError("known temporal precision requires start_time")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class EventEntityParticipation(BaseModel):
    event_participation_id: str = Field(min_length=2, max_length=500)
    event_ref: str = Field(min_length=2, max_length=500)
    entity_ref: str = Field(min_length=2, max_length=500)
    role: ParticipationRole
    assertion_state: EventAssertionState
    source_refs: list[str] = Field(min_length=1)
    provenance_refs: list[str] = Field(min_length=1)
    participation_is_not_affiliation: Literal[True] = True
    co_participation_is_not_relationship_proof: Literal[True] = True
    participation_is_not_intent: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_participation(self):
        _unique(self.source_refs,"source_refs"); _unique(self.provenance_refs,"provenance_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class EventSourceAssertion(BaseModel):
    event_source_assertion_id: str = Field(min_length=2, max_length=500)
    event_ref: str = Field(min_length=2, max_length=500)
    statement: str = Field(min_length=1, max_length=12000)
    assertion_state: EventAssertionState
    source_refs: list[str] = Field(min_length=1)
    document_segment_refs: list[str] = Field(default_factory=list)
    upstream_assertion_refs: list[str] = Field(default_factory=list)
    source_independence_group: str = Field(min_length=2, max_length=500)
    observed_at: str = Field(min_length=10, max_length=80)
    provenance_refs: list[str] = Field(min_length=1)
    source_statement_is_not_event_truth: Literal[True] = True
    source_independence_group_is_not_corroboration_count: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_assertion(self):
        for vals,label in ((self.source_refs,"source_refs"),(self.document_segment_refs,"document_segment_refs"),(self.upstream_assertion_refs,"upstream_assertion_refs"),(self.provenance_refs,"provenance_refs")):
            _unique(vals,label)
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class EventTemporalQualification(BaseModel):
    temporal_qualification_id: str = Field(min_length=2, max_length=500)
    event_ref: str = Field(min_length=2, max_length=500)
    qualification: str = Field(min_length=1, max_length=8000)
    precision: TemporalPrecision
    earliest_time: str | None = Field(default=None, max_length=80)
    latest_time: str | None = Field(default=None, max_length=80)
    basis_refs: list[str] = Field(min_length=1)
    contradiction_refs: list[str] = Field(default_factory=list)
    temporal_uncertainty_preserved: Literal[True] = True
    temporal_order_is_not_causality: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_qualification(self):
        _unique(self.basis_refs,"basis_refs"); _unique(self.contradiction_refs,"contradiction_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class CrossEventAssociation(BaseModel):
    event_association_id: str = Field(min_length=2, max_length=500)
    source_event_ref: str = Field(min_length=2, max_length=500)
    target_event_ref: str = Field(min_length=2, max_length=500)
    association_kind: EventAssociationKind
    temporal_relation: TemporalRelation
    shared_entity_refs: list[str] = Field(default_factory=list)
    basis_refs: list[str] = Field(min_length=1)
    contradiction_refs: list[str] = Field(default_factory=list)
    analytical_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_semantics: str | None = Field(default=None, max_length=2000)
    association_is_not_causal_claim: Literal[True] = True
    association_is_not_coordination_claim: Literal[True] = True
    association_is_not_relationship_fact: Literal[True] = True
    association_does_not_create_graph_edge: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_association(self):
        if self.source_event_ref == self.target_event_ref: raise ValueError("cross-event association requires distinct events")
        for vals,label in ((self.shared_entity_refs,"shared_entity_refs"),(self.basis_refs,"basis_refs"),(self.contradiction_refs,"contradiction_refs")):
            _unique(vals,label)
        if self.analytical_confidence is not None and not self.confidence_semantics:
            raise ValueError("analytical confidence requires semantics")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class EventAssociationReview(BaseModel):
    event_association_review_id: str = Field(min_length=2, max_length=500)
    event_association_ref: str = Field(min_length=2, max_length=500)
    reviewer_ref: str = Field(min_length=2, max_length=1000)
    disposition: ReviewDisposition
    considered_basis_refs: list[str] = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=8000)
    reviewed_at: str = Field(min_length=10, max_length=80)
    independent_review: Literal[True] = True
    review_is_not_truth_verdict: Literal[True] = True
    review_does_not_create_causality: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_review(self): _unique(self.considered_basis_refs,"considered_basis_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class EntityTimeline(BaseModel):
    entity_timeline_id: str = Field(min_length=2, max_length=500)
    entity_ref: str = Field(min_length=2, max_length=500)
    event_refs: list[str] = Field(min_length=1)
    participation_refs: list[str] = Field(min_length=1)
    temporal_qualification_refs: list[str] = Field(default_factory=list)
    as_of: str = Field(min_length=10, max_length=80)
    ordering_basis: str = Field(min_length=1, max_length=3000)
    timeline_is_view_not_source_record: Literal[True] = True
    timeline_order_is_not_causal_order: Literal[True] = True
    omission_from_timeline_is_not_nonoccurrence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_timeline(self):
        _unique(self.event_refs,"event_refs"); _unique(self.participation_refs,"participation_refs"); _unique(self.temporal_qualification_refs,"temporal_qualification_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class EventTimelineSnapshot(BaseModel):
    event_timeline_snapshot_id: str = Field(min_length=2, max_length=500)
    contradiction_resolution_snapshot_ref: str = Field(min_length=2, max_length=500)
    policy_refs: list[str] = Field(min_length=1)
    event_refs: list[str] = Field(min_length=1)
    participation_refs: list[str] = Field(min_length=1)
    source_assertion_refs: list[str] = Field(min_length=1)
    temporal_qualification_refs: list[str] = Field(default_factory=list)
    association_refs: list[str] = Field(default_factory=list)
    review_refs: list[str] = Field(default_factory=list)
    timeline_refs: list[str] = Field(min_length=1)
    created_at: str = Field(min_length=10, max_length=80)
    immutable_snapshot: Literal[True] = True
    snapshot_preserves_source_disagreement: Literal[True] = True
    snapshot_preserves_temporal_uncertainty: Literal[True] = True
    snapshot_is_not_truth_verdict: Literal[True] = True
    snapshot_does_not_mutate_graphs: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_snapshot(self):
        for vals,label in ((self.policy_refs,"policy_refs"),(self.event_refs,"event_refs"),(self.participation_refs,"participation_refs"),(self.source_assertion_refs,"source_assertion_refs"),(self.temporal_qualification_refs,"temporal_qualification_refs"),(self.association_refs,"association_refs"),(self.review_refs,"review_refs"),(self.timeline_refs,"timeline_refs")):
            _unique(vals,label)
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class EntityCentricTimelineEventAssociationBundle(BaseModel):
    contradictory_identity_relationship_resolution_bundle: ContradictoryIdentityRelationshipResolutionBundle
    policies: list[EventAssociationPolicy] = Field(min_length=1)
    events: list[EventRecord] = Field(min_length=1)
    participations: list[EventEntityParticipation] = Field(min_length=1)
    source_assertions: list[EventSourceAssertion] = Field(min_length=1)
    temporal_qualifications: list[EventTemporalQualification] = Field(default_factory=list)
    event_associations: list[CrossEventAssociation] = Field(default_factory=list)
    reviews: list[EventAssociationReview] = Field(default_factory=list)
    timelines: list[EntityTimeline] = Field(min_length=1)
    snapshots: list[EventTimelineSnapshot] = Field(min_length=1)
    temporal_proximity_is_not_causality: Literal[True] = True
    co_presence_is_not_relationship: Literal[True] = True
    sequence_is_not_intent: Literal[True] = True
    repeated_association_is_not_coordination: Literal[True] = True
    timeline_is_not_truth_verdict: Literal[True] = True
    identity_graph_mutation_performed: Literal[False] = False
    relationship_graph_mutation_performed: Literal[False] = False
    evidence_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        groups={
            "policies":[x.event_association_policy_id for x in self.policies],
            "events":[x.event_id for x in self.events],
            "participations":[x.event_participation_id for x in self.participations],
            "source_assertions":[x.event_source_assertion_id for x in self.source_assertions],
            "temporal_qualifications":[x.temporal_qualification_id for x in self.temporal_qualifications],
            "event_associations":[x.event_association_id for x in self.event_associations],
            "reviews":[x.event_association_review_id for x in self.reviews],
            "timelines":[x.entity_timeline_id for x in self.timelines],
            "snapshots":[x.event_timeline_snapshot_id for x in self.snapshots],
        }
        for label,vals in groups.items(): _unique(vals,label)
        ids={k:set(v) for k,v in groups.items()}
        event_map={x.event_id:x for x in self.events}
        entity_ids=set()
        upstream=self.contradictory_identity_relationship_resolution_bundle
        reasoning=upstream.multi_hop_research_investigation_graph_reasoning_bundle
        paths=reasoning.explainable_connection_paths_evidence_chains_bundle
        network=paths.network_structure_community_motif_bundle
        relationships=network.relationship_discovery_hypothesis_bundle
        documentary=relationships.public_record_documentary_source_bundle
        reconciliation=documentary.cross_source_entity_reconciliation_bundle
        linkage=reconciliation.probabilistic_record_linkage_bundle
        temporal=linkage.temporal_identity_bundle
        identity=temporal.entity_resolution_identity_graph_bundle
        entity_ids={x.entity_id for x in identity.entities}
        segment_ids={x.document_segment_id for x in documentary.segments}
        upstream_assertion_ids={x.contradictory_assertion_id for x in upstream.assertions}
        upstream_snapshot_ids={x.resolution_snapshot_id for x in upstream.snapshots}
        contradiction_ids={x.contradiction_set_id for x in upstream.contradiction_sets}
        for p in self.participations:
            if p.event_ref not in ids['events'] or p.entity_ref not in entity_ids: raise ValueError('participation references unknown event or entity')
        for a in self.source_assertions:
            if a.event_ref not in ids['events']: raise ValueError('source assertion references unknown event')
            if not set(a.document_segment_refs).issubset(segment_ids): raise ValueError('source assertion references unknown document segment')
            if not set(a.upstream_assertion_refs).issubset(upstream_assertion_ids): raise ValueError('source assertion references unknown upstream contradiction assertion')
        for q in self.temporal_qualifications:
            if q.event_ref not in ids['events']: raise ValueError('temporal qualification references unknown event')
            if not set(q.contradiction_refs).issubset(contradiction_ids): raise ValueError('temporal qualification references unknown contradiction')
        for a in self.event_associations:
            if a.source_event_ref not in ids['events'] or a.target_event_ref not in ids['events']: raise ValueError('association references unknown event')
            if not set(a.shared_entity_refs).issubset(entity_ids): raise ValueError('association references unknown entity')
            if not set(a.contradiction_refs).issubset(contradiction_ids): raise ValueError('association references unknown contradiction')
        for r in self.reviews:
            if r.event_association_ref not in ids['event_associations']: raise ValueError('review references unknown association')
        part_map={x.event_participation_id:x for x in self.participations}
        for t in self.timelines:
            if t.entity_ref not in entity_ids: raise ValueError('timeline references unknown entity')
            if not set(t.event_refs).issubset(ids['events']) or not set(t.participation_refs).issubset(ids['participations']): raise ValueError('timeline references unknown event/participation')
            if not set(t.temporal_qualification_refs).issubset(ids['temporal_qualifications']): raise ValueError('timeline references unknown temporal qualification')
            for pr in t.participation_refs:
                if part_map[pr].entity_ref != t.entity_ref: raise ValueError('timeline participation must belong to timeline entity')
        for s in self.snapshots:
            if s.contradiction_resolution_snapshot_ref not in upstream_snapshot_ids: raise ValueError('snapshot references unknown v3.86 resolution snapshot')
            checks=((s.policy_refs,ids['policies']),(s.event_refs,ids['events']),(s.participation_refs,ids['participations']),(s.source_assertion_refs,ids['source_assertions']),(s.temporal_qualification_refs,ids['temporal_qualifications']),(s.association_refs,ids['event_associations']),(s.review_refs,ids['reviews']),(s.timeline_refs,ids['timelines']))
            if any(not set(refs).issubset(valid) for refs,valid in checks): raise ValueError('snapshot contains unresolved reference')
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


def reference_entity_centric_timeline_event_association_bundle() -> EntityCentricTimelineEventAssociationBundle:
    upstream=reference_contradictory_identity_relationship_resolution_bundle()
    reasoning=upstream.multi_hop_research_investigation_graph_reasoning_bundle
    paths=reasoning.explainable_connection_paths_evidence_chains_bundle
    network=paths.network_structure_community_motif_bundle
    relationships=network.relationship_discovery_hypothesis_bundle
    documentary=relationships.public_record_documentary_source_bundle
    reconciliation=documentary.cross_source_entity_reconciliation_bundle
    linkage=reconciliation.probabilistic_record_linkage_bundle
    temporal=linkage.temporal_identity_bundle
    identity=temporal.entity_resolution_identity_graph_bundle
    e1,e2=identity.entities[:2]
    observed=relationships.source_observed_relationships[0]
    doc1,doc2=documentary.documentary_sources[:2]
    seg1,seg2,seg3=documentary.segments[:3]
    identity_set,relationship_set=upstream.contradiction_sets[:2]
    policy=EventAssociationPolicy(event_association_policy_id='event-association-policy:reference:v1',metadata={'synthetic_reference':True})
    events=[
        EventRecord(event_id='event:synthetic:reported-association-2024:v1',event_type=EventType.reported_interaction,label='Reported 2024 operational association',description='Synthetic filing reports a bounded operational association involving the two reference entities during 2024.',assertion_state=EventAssertionState.source_reported,start_time=observed.valid_from,end_time=observed.valid_to,temporal_precision=TemporalPrecision.interval,source_refs=list(observed.source_refs),upstream_object_refs=[observed.source_observed_relationship_id,upstream.assertions[2].contradictory_assertion_id],provenance_refs=list(observed.provenance_refs),metadata={'synthetic_reference':True}),
        EventRecord(event_id='event:synthetic:filing-issued-2026:v1',event_type=EventType.filing,label='Synthetic annual filing issued',description='Issuance/publication event for the synthetic annual filing; the event records the document occurrence and does not validate every statement contained in it.',assertion_state=EventAssertionState.source_reported,start_time=doc1.publication_or_issue_date+'T00:00:00Z',temporal_precision=TemporalPrecision.day,source_refs=[doc1.documentary_source_id],upstream_object_refs=[doc1.documentary_source_id,seg1.document_segment_id],provenance_refs=list(doc1.provenance_refs),metadata={'synthetic_reference':True}),
        EventRecord(event_id='event:synthetic:disclosure-response-2026:v1',event_type=EventType.disclosure,label='Synthetic disclosure response',description='Synthetic disclosure response event documenting receipt/issuance of the disclosure letter without inferring anything from withheld or absent material.',assertion_state=EventAssertionState.source_reported,start_time=doc2.publication_or_issue_date+'T00:00:00Z',temporal_precision=TemporalPrecision.day,source_refs=[doc2.documentary_source_id],upstream_object_refs=[doc2.documentary_source_id,seg3.document_segment_id],provenance_refs=list(doc2.provenance_refs),metadata={'synthetic_reference':True}),
        EventRecord(event_id='event:synthetic:identity-review-2026:v1',event_type=EventType.research_observation,label='Identity contradiction review checkpoint',description='Research workflow checkpoint at which continuity evidence and later temporal/source conflict remain partially resolved.',assertion_state=EventAssertionState.qualified,start_time='2026-09-30T20:41:00Z',temporal_precision=TemporalPrecision.instant,source_refs=['research-workflow:synthetic:v1'],upstream_object_refs=[upstream.decisions[0].resolution_decision_id,identity_set.contradiction_set_id],provenance_refs=['provenance:synthetic:identity-review:v1'],metadata={'synthetic_reference':True}),
    ]
    parts=[
        EventEntityParticipation(event_participation_id='participation:synthetic:e1:reported-association:v1',event_ref=events[0].event_id,entity_ref=e1.entity_id,role=ParticipationRole.subject,assertion_state=EventAssertionState.source_reported,source_refs=list(observed.source_refs),provenance_refs=list(observed.provenance_refs)),
        EventEntityParticipation(event_participation_id='participation:synthetic:e2:reported-association:v1',event_ref=events[0].event_id,entity_ref=e2.entity_id,role=ParticipationRole.object,assertion_state=EventAssertionState.source_reported,source_refs=list(observed.source_refs),provenance_refs=list(observed.provenance_refs)),
        EventEntityParticipation(event_participation_id='participation:synthetic:e1:filing:v1',event_ref=events[1].event_id,entity_ref=e1.entity_id,role=ParticipationRole.referenced,assertion_state=EventAssertionState.source_reported,source_refs=[doc1.documentary_source_id],provenance_refs=list(seg1.provenance_refs)),
        EventEntityParticipation(event_participation_id='participation:synthetic:e2:filing:v1',event_ref=events[1].event_id,entity_ref=e2.entity_id,role=ParticipationRole.referenced,assertion_state=EventAssertionState.source_reported,source_refs=[doc1.documentary_source_id],provenance_refs=list(seg2.provenance_refs)),
        EventEntityParticipation(event_participation_id='participation:synthetic:e1:review:v1',event_ref=events[3].event_id,entity_ref=e1.entity_id,role=ParticipationRole.subject,assertion_state=EventAssertionState.qualified,source_refs=['research-workflow:synthetic:v1'],provenance_refs=['provenance:synthetic:identity-review:v1']),
        EventEntityParticipation(event_participation_id='participation:synthetic:e2:review:v1',event_ref=events[3].event_id,entity_ref=e2.entity_id,role=ParticipationRole.subject,assertion_state=EventAssertionState.qualified,source_refs=['research-workflow:synthetic:v1'],provenance_refs=['provenance:synthetic:identity-review:v1']),
    ]
    assertions=[
        EventSourceAssertion(event_source_assertion_id='event-assertion:synthetic:association:v1',event_ref=events[0].event_id,statement='The filing reports the bounded 2024 association represented by the source-observed relationship object.',assertion_state=EventAssertionState.source_reported,source_refs=[doc1.documentary_source_id],document_segment_refs=[seg1.document_segment_id],upstream_assertion_refs=[upstream.assertions[2].contradictory_assertion_id],source_independence_group='source-group:synthetic:filing',observed_at='2026-03-31T00:00:00Z',provenance_refs=list(seg1.provenance_refs)),
        EventSourceAssertion(event_source_assertion_id='event-assertion:synthetic:filing-issued:v1',event_ref=events[1].event_id,statement='The synthetic annual filing carries an issue date of 2026-03-31.',assertion_state=EventAssertionState.source_reported,source_refs=[doc1.documentary_source_id],document_segment_refs=[seg1.document_segment_id],source_independence_group='source-group:synthetic:filing',observed_at='2026-03-31T00:00:00Z',provenance_refs=list(doc1.provenance_refs)),
        EventSourceAssertion(event_source_assertion_id='event-assertion:synthetic:disclosure:v1',event_ref=events[2].event_id,statement='The synthetic disclosure response letter carries an issue date of 2026-09-20.',assertion_state=EventAssertionState.source_reported,source_refs=[doc2.documentary_source_id],document_segment_refs=[seg3.document_segment_id],source_independence_group='source-group:synthetic:disclosure',observed_at='2026-09-20T00:00:00Z',provenance_refs=list(doc2.provenance_refs)),
        EventSourceAssertion(event_source_assertion_id='event-assertion:synthetic:identity-review:v1',event_ref=events[3].event_id,statement='The governed review preserves the identity continuity conflict as partially resolved.',assertion_state=EventAssertionState.qualified,source_refs=['research-workflow:synthetic:v1'],upstream_assertion_refs=[upstream.assertions[0].contradictory_assertion_id,upstream.assertions[1].contradictory_assertion_id],source_independence_group='source-group:synthetic:review',observed_at='2026-09-30T20:41:00Z',provenance_refs=['provenance:synthetic:identity-review:v1']),
    ]
    quals=[
        EventTemporalQualification(temporal_qualification_id='temporal-qualification:synthetic:association:v1',event_ref=events[0].event_id,qualification='The association is bounded to the represented 2024 interval; it must not be projected as current or timeless.',precision=TemporalPrecision.interval,earliest_time=observed.valid_from,latest_time=observed.valid_to,basis_refs=[observed.source_observed_relationship_id],contradiction_refs=[relationship_set.contradiction_set_id]),
        EventTemporalQualification(temporal_qualification_id='temporal-qualification:synthetic:identity-review:v1',event_ref=events[3].event_id,qualification='The identity continuity review remains qualified by the later temporal/source conflict and is not a merge decision.',precision=TemporalPrecision.instant,earliest_time='2026-09-30T20:41:00Z',latest_time='2026-09-30T20:41:00Z',basis_refs=[upstream.decisions[0].resolution_decision_id],contradiction_refs=[identity_set.contradiction_set_id]),
    ]
    associations=[
        CrossEventAssociation(event_association_id='event-association:synthetic:association-to-filing:v1',source_event_ref=events[0].event_id,target_event_ref=events[1].event_id,association_kind=EventAssociationKind.shared_entity,temporal_relation=TemporalRelation.before,shared_entity_refs=[e1.entity_id,e2.entity_id],basis_refs=[observed.source_observed_relationship_id,seg1.document_segment_id],contradiction_refs=[relationship_set.contradiction_set_id],analytical_confidence=0.92,confidence_semantics='confidence that these synthetic records share entity references and chronological ordering; not probability of causality or coordination'),
        CrossEventAssociation(event_association_id='event-association:synthetic:filing-to-disclosure:v1',source_event_ref=events[1].event_id,target_event_ref=events[2].event_id,association_kind=EventAssociationKind.temporal_sequence,temporal_relation=TemporalRelation.before,basis_refs=[doc1.documentary_source_id,doc2.documentary_source_id],analytical_confidence=1.0,confidence_semantics='deterministic ordering of represented issue dates only; not causal significance'),
        CrossEventAssociation(event_association_id='event-association:synthetic:disclosure-to-review:v1',source_event_ref=events[2].event_id,target_event_ref=events[3].event_id,association_kind=EventAssociationKind.contradiction_context,temporal_relation=TemporalRelation.before,shared_entity_refs=[e1.entity_id,e2.entity_id],basis_refs=[identity_set.contradiction_set_id,upstream.decisions[0].resolution_decision_id],contradiction_refs=[identity_set.contradiction_set_id],analytical_confidence=0.75,confidence_semantics='analytical confidence in workflow/context association only; not probability of a real-world causal link'),
    ]
    reviews=[
        EventAssociationReview(event_association_review_id='event-association-review:synthetic:a:v1',event_association_ref=associations[0].event_association_id,reviewer_ref='reviewer:synthetic:timeline-a',disposition=ReviewDisposition.qualify,considered_basis_refs=list(associations[0].basis_refs),rationale='The two events share entities and chronological ordering, but this does not establish causality, coordination, or an unbounded relationship.',reviewed_at='2026-09-30T20:50:00Z'),
        EventAssociationReview(event_association_review_id='event-association-review:synthetic:b:v1',event_association_ref=associations[2].event_association_id,reviewer_ref='reviewer:synthetic:timeline-b',disposition=ReviewDisposition.qualify,considered_basis_refs=list(associations[2].basis_refs),rationale='The later review can be linked as research context while the underlying identity contradiction remains preserved and partially resolved.',reviewed_at='2026-09-30T20:51:00Z'),
    ]
    timelines=[
        EntityTimeline(entity_timeline_id='entity-timeline:synthetic:e1:v1',entity_ref=e1.entity_id,event_refs=[events[0].event_id,events[1].event_id,events[3].event_id],participation_refs=[parts[0].event_participation_id,parts[2].event_participation_id,parts[4].event_participation_id],temporal_qualification_refs=[quals[0].temporal_qualification_id,quals[1].temporal_qualification_id],as_of='2026-09-30T20:52:00Z',ordering_basis='Represented event start times with source-specific temporal qualification preserved.'),
        EntityTimeline(entity_timeline_id='entity-timeline:synthetic:e2:v1',entity_ref=e2.entity_id,event_refs=[events[0].event_id,events[1].event_id,events[3].event_id],participation_refs=[parts[1].event_participation_id,parts[3].event_participation_id,parts[5].event_participation_id],temporal_qualification_refs=[quals[0].temporal_qualification_id,quals[1].temporal_qualification_id],as_of='2026-09-30T20:52:00Z',ordering_basis='Represented event start times with source-specific temporal qualification preserved.'),
    ]
    snapshot=EventTimelineSnapshot(event_timeline_snapshot_id='event-timeline-snapshot:synthetic:2026-09-30:v1',contradiction_resolution_snapshot_ref=upstream.snapshots[0].resolution_snapshot_id,policy_refs=[policy.event_association_policy_id],event_refs=[x.event_id for x in events],participation_refs=[x.event_participation_id for x in parts],source_assertion_refs=[x.event_source_assertion_id for x in assertions],temporal_qualification_refs=[x.temporal_qualification_id for x in quals],association_refs=[x.event_association_id for x in associations],review_refs=[x.event_association_review_id for x in reviews],timeline_refs=[x.entity_timeline_id for x in timelines],created_at='2026-09-30T20:53:00Z',metadata={'synthetic_reference':True})
    return EntityCentricTimelineEventAssociationBundle(contradictory_identity_relationship_resolution_bundle=upstream,policies=[policy],events=events,participations=parts,source_assertions=assertions,temporal_qualifications=quals,event_associations=associations,reviews=reviews,timelines=timelines,snapshots=[snapshot])


def contract_document() -> dict[str, Any]:
    b=reference_entity_centric_timeline_event_association_bundle()
    return {
        'ok':True,'release':CORE_RELEASE,'contract':CONTRACT_VERSION,
        'extends_contracts':['sc.core.contradictory-identity-relationship-resolution.v1','sc.core.multi-hop-research-investigation-graph-reasoning.v1','sc.core.explainable-connection-paths-evidence-chains.v1','sc.core.relationship-discovery-connection-hypothesis.v1','sc.core.public-record-documentary-source-object-model.v1','sc.core.temporal-identity-alias-name-variant-intelligence.v1','sc.core.entity-resolution-identity-graph-foundation.v1'],
        'object_types':['EventAssociationPolicy','EventRecord','EventEntityParticipation','EventSourceAssertion','EventTemporalQualification','CrossEventAssociation','EventAssociationReview','EntityTimeline','EventTimelineSnapshot','EntityCentricTimelineEventAssociationBundle'],
        'principles':{'temporal_proximity_is_not_causality':True,'co_presence_is_not_relationship':True,'sequence_is_not_intent':True,'repeated_association_is_not_coordination':True,'timeline_is_view_not_source_record':True,'source_disagreement_is_preserved':True,'temporal_uncertainty_is_preserved':True,'event_association_is_explanatory_not_dispositive':True},
        'boundaries':{'runtime_may_infer_causality_from_sequence':False,'runtime_may_infer_relationship_from_copresence':False,'runtime_may_infer_coordination_from_repetition':False,'runtime_may_infer_intent_from_ordering':False,'runtime_may_erase_temporal_uncertainty':False,'v387_timeline_is_truth_verdict':False,'identity_graph_mutation_performed':False,'relationship_graph_mutation_performed':False,'evidence_graph_mutation_performed':False},
        'reference':{'events':len(b.events),'participations':len(b.participations),'source_assertions':len(b.source_assertions),'temporal_qualifications':len(b.temporal_qualifications),'event_associations':len(b.event_associations),'reviews':len(b.reviews),'timelines':len(b.timelines),'identity_graph_mutation_performed':b.identity_graph_mutation_performed,'relationship_graph_mutation_performed':b.relationship_graph_mutation_performed,'evidence_graph_mutation_performed':b.evidence_graph_mutation_performed,'bundle_fingerprint_sha256':b.fingerprint()},
        'database_migration':'none',
    }
