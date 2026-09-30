from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .public_record_documentary_source import (
    PublicRecordDocumentarySourceBundle,
    reference_public_record_documentary_source_bundle,
)

CORE_RELEASE = "3.82.0"
CONTRACT_VERSION = "sc.core.relationship-discovery-connection-hypothesis.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class RelationshipSignalKind(str, Enum):
    documentary_cooccurrence = "documentary-cooccurrence"
    documentary_assertion = "documentary-assertion"
    shared_attribute = "shared-attribute"
    temporal_overlap = "temporal-overlap"
    spatial_cooccurrence = "spatial-cooccurrence"
    graph_proximity = "graph-proximity"
    embedding_similarity = "embedding-similarity"
    link_prediction = "link-prediction"
    communication_record = "communication-record"
    transaction_record = "transaction-record"
    common_affiliation = "common-affiliation"
    other = "other"


class SourceObservedRelationshipState(str, Enum):
    reported = "reported"
    documented = "documented"
    disputed = "disputed"
    retracted = "retracted"
    unresolved = "unresolved"


class ConnectionCandidateState(str, Enum):
    candidate = "candidate"
    under_review = "under-review"
    supported_for_hypothesis = "supported-for-hypothesis"
    rejected = "rejected"
    disputed = "disputed"


class ConnectionHypothesisState(str, Enum):
    proposed = "proposed"
    under_review = "under-review"
    supported_for_validation = "supported-for-validation"
    contradicted = "contradicted"
    disputed = "disputed"
    insufficient = "insufficient"
    rejected = "rejected"


class EvidencePosition(str, Enum):
    supports = "supports"
    contradicts = "contradicts"
    contextualizes = "contextualizes"


class HypothesisReviewDisposition(str, Enum):
    support_validation = "support-validation"
    contradict = "contradict"
    disputed = "disputed"
    insufficient = "insufficient"
    reject = "reject"


class RelationshipDiscoveryPolicy(BaseModel):
    relationship_discovery_policy_id: str = Field(min_length=2, max_length=500)
    minimum_independent_evidence_groups_for_supported_hypothesis: int = Field(default=2, ge=1, le=100)
    minimum_independent_reviewers_for_supported_hypothesis: int = Field(default=2, ge=1, le=20)
    require_contradictory_evidence_review: Literal[True] = True
    require_document_or_source_provenance_for_observed_relationship: Literal[True] = True
    require_separate_evidence_validation_before_edge_creation: Literal[True] = True
    cooccurrence_can_establish_relationship: Literal[False] = False
    shared_attribute_can_establish_relationship: Literal[False] = False
    graph_proximity_can_establish_relationship: Literal[False] = False
    embedding_similarity_can_establish_relationship: Literal[False] = False
    model_score_can_establish_relationship: Literal[False] = False
    source_count_can_establish_relationship: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RelationshipDiscoverySignal(BaseModel):
    relationship_signal_id: str = Field(min_length=2, max_length=500)
    signal_kind: RelationshipSignalKind
    subject_entity_ref: str = Field(min_length=2, max_length=1000)
    object_entity_ref: str = Field(min_length=2, max_length=1000)
    relationship_type_candidate: str = Field(min_length=1, max_length=500)
    source_refs: list[str] = Field(default_factory=list)
    document_segment_refs: list[str] = Field(default_factory=list)
    documentary_interpretation_refs: list[str] = Field(default_factory=list)
    identity_evidence_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(min_length=1)
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    score_semantics: str | None = Field(default=None, max_length=1000)
    observed_at: str | None = Field(default=None, max_length=80)
    valid_from: str | None = Field(default=None, max_length=80)
    valid_to: str | None = Field(default=None, max_length=80)
    signal_is_not_relationship_fact: Literal[True] = True
    signal_is_not_evidence_by_itself: Literal[True] = True
    score_is_not_evidence_strength: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_signal(self):
        if self.subject_entity_ref == self.object_entity_ref:
            raise ValueError("relationship discovery signal requires two distinct entities")
        for vals, label in (
            (self.source_refs, "source_refs"),
            (self.document_segment_refs, "document_segment_refs"),
            (self.documentary_interpretation_refs, "documentary_interpretation_refs"),
            (self.identity_evidence_refs, "identity_evidence_refs"),
            (self.provenance_refs, "provenance_refs"),
        ):
            _unique(vals, label)
        if self.signal_kind in {RelationshipSignalKind.documentary_cooccurrence, RelationshipSignalKind.documentary_assertion}:
            if not self.source_refs and not self.documentary_interpretation_refs:
                raise ValueError("documentary relationship signals require a source or interpretation reference")
        if self.score is not None and not self.score_semantics:
            raise ValueError("scored relationship signal requires score_semantics")
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValueError("signal valid_from must not be after valid_to")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SourceObservedRelationship(BaseModel):
    source_observed_relationship_id: str = Field(min_length=2, max_length=500)
    subject_entity_ref: str = Field(min_length=2, max_length=1000)
    object_entity_ref: str = Field(min_length=2, max_length=1000)
    relationship_type: str = Field(min_length=1, max_length=500)
    observation_state: SourceObservedRelationshipState
    observation_summary: str = Field(min_length=1, max_length=8000)
    source_refs: list[str] = Field(min_length=1)
    document_segment_refs: list[str] = Field(default_factory=list)
    documentary_interpretation_refs: list[str] = Field(default_factory=list)
    identity_evidence_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(min_length=1)
    observed_at: str = Field(min_length=10, max_length=80)
    valid_from: str | None = Field(default=None, max_length=80)
    valid_to: str | None = Field(default=None, max_length=80)
    source_observation_is_not_canonical_relationship_fact: Literal[True] = True
    source_assertion_is_not_truth_verdict: Literal[True] = True
    observation_does_not_create_graph_edge: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_observation(self):
        if self.subject_entity_ref == self.object_entity_ref:
            raise ValueError("observed relationship requires two distinct entities")
        for vals, label in (
            (self.source_refs, "source_refs"),
            (self.document_segment_refs, "document_segment_refs"),
            (self.documentary_interpretation_refs, "documentary_interpretation_refs"),
            (self.identity_evidence_refs, "identity_evidence_refs"),
            (self.provenance_refs, "provenance_refs"),
        ):
            _unique(vals, label)
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValueError("observed relationship valid_from must not be after valid_to")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ConnectionCandidate(BaseModel):
    connection_candidate_id: str = Field(min_length=2, max_length=500)
    subject_entity_ref: str = Field(min_length=2, max_length=1000)
    object_entity_ref: str = Field(min_length=2, max_length=1000)
    relationship_type_candidate: str = Field(min_length=1, max_length=500)
    signal_refs: list[str] = Field(min_length=1)
    source_observed_relationship_refs: list[str] = Field(default_factory=list)
    candidate_score: float | None = Field(default=None, ge=0.0, le=1.0)
    candidate_score_semantics: str | None = Field(default=None, max_length=1000)
    state: ConnectionCandidateState = ConnectionCandidateState.candidate
    generated_by: str = Field(min_length=1, max_length=1000)
    generated_at: str = Field(min_length=10, max_length=80)
    candidate_is_not_relationship_fact: Literal[True] = True
    candidate_is_not_evidence: Literal[True] = True
    candidate_does_not_create_graph_edge: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_candidate(self):
        if self.subject_entity_ref == self.object_entity_ref:
            raise ValueError("connection candidate requires two distinct entities")
        _unique(self.signal_refs, "signal_refs")
        _unique(self.source_observed_relationship_refs, "source_observed_relationship_refs")
        if self.candidate_score is not None and not self.candidate_score_semantics:
            raise ValueError("scored connection candidate requires candidate_score_semantics")
        if self.state == ConnectionCandidateState.supported_for_hypothesis and not self.source_observed_relationship_refs:
            raise ValueError("supported-for-hypothesis candidate requires source-observed relationship context")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ConnectionHypothesisEvidencePosition(BaseModel):
    evidence_position_id: str = Field(min_length=2, max_length=500)
    connection_hypothesis_ref: str = Field(min_length=2, max_length=500)
    position: EvidencePosition
    identity_evidence_refs: list[str] = Field(default_factory=list)
    documentary_interpretation_refs: list[str] = Field(default_factory=list)
    document_segment_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    source_observed_relationship_refs: list[str] = Field(default_factory=list)
    independence_group: str = Field(min_length=1, max_length=1000)
    rationale: str = Field(min_length=1, max_length=8000)
    provenance_refs: list[str] = Field(min_length=1)
    evidence_material_is_not_automatic_truth_verdict: Literal[True] = True
    evidence_position_is_not_relationship_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_position(self):
        for vals, label in (
            (self.identity_evidence_refs, "identity_evidence_refs"),
            (self.documentary_interpretation_refs, "documentary_interpretation_refs"),
            (self.document_segment_refs, "document_segment_refs"),
            (self.source_refs, "source_refs"),
            (self.source_observed_relationship_refs, "source_observed_relationship_refs"),
            (self.provenance_refs, "provenance_refs"),
        ):
            _unique(vals, label)
        if not (self.identity_evidence_refs or self.documentary_interpretation_refs or self.document_segment_refs or self.source_observed_relationship_refs):
            raise ValueError("connection hypothesis evidence position requires source-bound evidence material")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ConnectionHypothesisReview(BaseModel):
    connection_hypothesis_review_id: str = Field(min_length=2, max_length=500)
    connection_hypothesis_ref: str = Field(min_length=2, max_length=500)
    reviewer_ref: str = Field(min_length=2, max_length=1000)
    disposition: HypothesisReviewDisposition
    considered_evidence_position_refs: list[str] = Field(min_length=1)
    considered_signal_refs: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1, max_length=8000)
    reviewed_at: str = Field(min_length=10, max_length=80)
    independent_review: Literal[True] = True
    review_does_not_establish_relationship_truth: Literal[True] = True
    review_does_not_create_graph_edge: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_review(self):
        _unique(self.considered_evidence_position_refs, "considered_evidence_position_refs")
        _unique(self.considered_signal_refs, "considered_signal_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ConnectionHypothesis(BaseModel):
    connection_hypothesis_id: str = Field(min_length=2, max_length=500)
    connection_candidate_ref: str = Field(min_length=2, max_length=500)
    subject_entity_ref: str = Field(min_length=2, max_length=1000)
    object_entity_ref: str = Field(min_length=2, max_length=1000)
    relationship_type_hypothesis: str = Field(min_length=1, max_length=500)
    hypothesis_statement: str = Field(min_length=1, max_length=12000)
    state: ConnectionHypothesisState
    evidence_position_refs: list[str] = Field(default_factory=list)
    review_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(min_length=1)
    created_at: str = Field(min_length=10, max_length=80)
    hypothesis_is_not_graph_fact: Literal[True] = True
    hypothesis_is_not_evidence: Literal[True] = True
    hypothesis_does_not_create_graph_edge: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_hypothesis(self):
        if self.subject_entity_ref == self.object_entity_ref:
            raise ValueError("connection hypothesis requires two distinct entities")
        _unique(self.evidence_position_refs, "evidence_position_refs")
        _unique(self.review_refs, "review_refs")
        _unique(self.provenance_refs, "provenance_refs")
        if self.state == ConnectionHypothesisState.supported_for_validation:
            if not self.evidence_position_refs or not self.review_refs:
                raise ValueError("supported-for-validation hypothesis requires evidence positions and reviews")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RelationshipPromotionGate(BaseModel):
    relationship_promotion_gate_id: str = Field(min_length=2, max_length=500)
    connection_hypothesis_ref: str = Field(min_length=2, max_length=500)
    relationship_discovery_policy_ref: str = Field(min_length=2, max_length=500)
    required_evidence_position_refs: list[str] = Field(min_length=1)
    required_review_refs: list[str] = Field(min_length=1)
    separate_v376_evidence_validation_required: Literal[True] = True
    contradictory_evidence_review_required: Literal[True] = True
    cooccurrence_can_satisfy_gate: Literal[False] = False
    shared_attribute_can_satisfy_gate: Literal[False] = False
    graph_proximity_can_satisfy_gate: Literal[False] = False
    embedding_similarity_can_satisfy_gate: Literal[False] = False
    model_score_can_satisfy_gate: Literal[False] = False
    source_count_can_satisfy_gate: Literal[False] = False
    v382_may_create_evidence_edge: Literal[False] = False
    gate_state: Literal["eligible-for-evidence-validation"] = "eligible-for-evidence-validation"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_gate(self):
        _unique(self.required_evidence_position_refs, "required_evidence_position_refs")
        _unique(self.required_review_refs, "required_review_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RelationshipDiscoverySnapshot(BaseModel):
    relationship_discovery_snapshot_id: str = Field(min_length=2, max_length=500)
    policy_refs: list[str] = Field(min_length=1)
    signal_refs: list[str] = Field(min_length=1)
    source_observed_relationship_refs: list[str] = Field(default_factory=list)
    connection_candidate_refs: list[str] = Field(min_length=1)
    connection_hypothesis_refs: list[str] = Field(min_length=1)
    evidence_position_refs: list[str] = Field(default_factory=list)
    review_refs: list[str] = Field(default_factory=list)
    promotion_gate_refs: list[str] = Field(default_factory=list)
    unresolved_hypothesis_refs: list[str] = Field(default_factory=list)
    created_at: str = Field(min_length=10, max_length=80)
    immutable_snapshot: Literal[True] = True
    snapshot_preserves_source_and_hypothesis_provenance: Literal[True] = True
    snapshot_is_not_relationship_truth_verdict: Literal[True] = True
    snapshot_does_not_mutate_graphs: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        for vals, label in (
            (self.policy_refs, "policy_refs"),
            (self.signal_refs, "signal_refs"),
            (self.source_observed_relationship_refs, "source_observed_relationship_refs"),
            (self.connection_candidate_refs, "connection_candidate_refs"),
            (self.connection_hypothesis_refs, "connection_hypothesis_refs"),
            (self.evidence_position_refs, "evidence_position_refs"),
            (self.review_refs, "review_refs"),
            (self.promotion_gate_refs, "promotion_gate_refs"),
            (self.unresolved_hypothesis_refs, "unresolved_hypothesis_refs"),
        ):
            _unique(vals, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RelationshipDiscoveryHypothesisBundle(BaseModel):
    public_record_documentary_source_bundle: PublicRecordDocumentarySourceBundle
    policies: list[RelationshipDiscoveryPolicy] = Field(min_length=1)
    signals: list[RelationshipDiscoverySignal] = Field(min_length=1)
    source_observed_relationships: list[SourceObservedRelationship] = Field(min_length=1)
    connection_candidates: list[ConnectionCandidate] = Field(min_length=1)
    connection_hypotheses: list[ConnectionHypothesis] = Field(min_length=1)
    evidence_positions: list[ConnectionHypothesisEvidencePosition] = Field(min_length=1)
    reviews: list[ConnectionHypothesisReview] = Field(min_length=1)
    promotion_gates: list[RelationshipPromotionGate] = Field(min_length=1)
    snapshots: list[RelationshipDiscoverySnapshot] = Field(min_length=1)
    cooccurrence_is_not_relationship: Literal[True] = True
    shared_attribute_is_not_relationship: Literal[True] = True
    graph_proximity_is_not_relationship: Literal[True] = True
    model_score_is_not_relationship_fact: Literal[True] = True
    source_observation_is_not_canonical_relationship_fact: Literal[True] = True
    hypothesis_is_not_graph_fact: Literal[True] = True
    relationship_graph_mutation_performed: Literal[False] = False
    evidence_graph_mutation_performed: Literal[False] = False
    identity_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        upstream = self.public_record_documentary_source_bundle
        reconciliation = upstream.cross_source_entity_reconciliation_bundle
        base = reconciliation.probabilistic_record_linkage_bundle.temporal_identity_bundle.entity_resolution_identity_graph_bundle

        def ids(items, attr, label):
            vals = [getattr(x, attr) for x in items]
            _unique(vals, label)
            return set(vals)

        entity_ids = {x.entity_id for x in base.entities}
        identity_evidence_ids = {x.identity_evidence_id for x in base.identity_evidence_items}
        source_ids = {x.documentary_source_id for x in upstream.documentary_sources}
        segment_ids = {x.document_segment_id for x in upstream.segments}
        interpretation_ids = {x.documentary_interpretation_id for x in upstream.evidence_interpretations}

        policy_ids = ids(self.policies, "relationship_discovery_policy_id", "policy_ids")
        signal_ids = ids(self.signals, "relationship_signal_id", "signal_ids")
        observed_ids = ids(self.source_observed_relationships, "source_observed_relationship_id", "source_observed_relationship_ids")
        candidate_ids = ids(self.connection_candidates, "connection_candidate_id", "connection_candidate_ids")
        hypothesis_ids = ids(self.connection_hypotheses, "connection_hypothesis_id", "connection_hypothesis_ids")
        position_ids = ids(self.evidence_positions, "evidence_position_id", "evidence_position_ids")
        review_ids = ids(self.reviews, "connection_hypothesis_review_id", "review_ids")
        gate_ids = ids(self.promotion_gates, "relationship_promotion_gate_id", "promotion_gate_ids")
        ids(self.snapshots, "relationship_discovery_snapshot_id", "snapshot_ids")

        for signal in self.signals:
            if signal.subject_entity_ref not in entity_ids or signal.object_entity_ref not in entity_ids:
                raise ValueError("relationship signal entity refs must resolve")
            if not set(signal.source_refs) <= source_ids:
                raise ValueError("relationship signal source refs must resolve")
            if not set(signal.document_segment_refs) <= segment_ids:
                raise ValueError("relationship signal segment refs must resolve")
            if not set(signal.documentary_interpretation_refs) <= interpretation_ids:
                raise ValueError("relationship signal interpretation refs must resolve")
            if not set(signal.identity_evidence_refs) <= identity_evidence_ids:
                raise ValueError("relationship signal identity evidence refs must resolve")

        for observed in self.source_observed_relationships:
            if observed.subject_entity_ref not in entity_ids or observed.object_entity_ref not in entity_ids:
                raise ValueError("source-observed relationship entity refs must resolve")
            if not set(observed.source_refs) <= source_ids:
                raise ValueError("source-observed relationship source refs must resolve")
            if not set(observed.document_segment_refs) <= segment_ids:
                raise ValueError("source-observed relationship segment refs must resolve")
            if not set(observed.documentary_interpretation_refs) <= interpretation_ids:
                raise ValueError("source-observed relationship interpretation refs must resolve")
            if not set(observed.identity_evidence_refs) <= identity_evidence_ids:
                raise ValueError("source-observed relationship identity evidence refs must resolve")

        for candidate in self.connection_candidates:
            if candidate.subject_entity_ref not in entity_ids or candidate.object_entity_ref not in entity_ids:
                raise ValueError("connection candidate entity refs must resolve")
            if not set(candidate.signal_refs) <= signal_ids:
                raise ValueError("connection candidate signal refs must resolve")
            if not set(candidate.source_observed_relationship_refs) <= observed_ids:
                raise ValueError("connection candidate observed relationship refs must resolve")
            for ref in candidate.signal_refs:
                signal = next(x for x in self.signals if x.relationship_signal_id == ref)
                if {signal.subject_entity_ref, signal.object_entity_ref} != {candidate.subject_entity_ref, candidate.object_entity_ref}:
                    raise ValueError("connection candidate endpoints must match signal endpoints")

        for position in self.evidence_positions:
            if position.connection_hypothesis_ref not in hypothesis_ids:
                raise ValueError("evidence position hypothesis ref must resolve")
            if not set(position.identity_evidence_refs) <= identity_evidence_ids:
                raise ValueError("evidence position identity evidence refs must resolve")
            if not set(position.documentary_interpretation_refs) <= interpretation_ids:
                raise ValueError("evidence position interpretation refs must resolve")
            if not set(position.document_segment_refs) <= segment_ids:
                raise ValueError("evidence position segment refs must resolve")
            if not set(position.source_refs) <= source_ids:
                raise ValueError("evidence position source refs must resolve")
            if not set(position.source_observed_relationship_refs) <= observed_ids:
                raise ValueError("evidence position observed relationship refs must resolve")

        for review in self.reviews:
            if review.connection_hypothesis_ref not in hypothesis_ids:
                raise ValueError("hypothesis review ref must resolve")
            if not set(review.considered_evidence_position_refs) <= position_ids:
                raise ValueError("hypothesis review evidence position refs must resolve")
            if not set(review.considered_signal_refs) <= signal_ids:
                raise ValueError("hypothesis review signal refs must resolve")

        reviewer_groups: dict[str, set[str]] = {}
        for review in self.reviews:
            reviewer_groups.setdefault(review.connection_hypothesis_ref, set()).add(review.reviewer_ref)

        position_groups: dict[str, set[str]] = {}
        for pos in self.evidence_positions:
            position_groups.setdefault(pos.connection_hypothesis_ref, set()).add(pos.independence_group)

        policy_by_id = {x.relationship_discovery_policy_id: x for x in self.policies}
        for hypothesis in self.connection_hypotheses:
            if hypothesis.connection_candidate_ref not in candidate_ids:
                raise ValueError("connection hypothesis candidate ref must resolve")
            candidate = next(x for x in self.connection_candidates if x.connection_candidate_id == hypothesis.connection_candidate_ref)
            if hypothesis.subject_entity_ref != candidate.subject_entity_ref or hypothesis.object_entity_ref != candidate.object_entity_ref:
                raise ValueError("connection hypothesis endpoints must match candidate endpoints")
            if hypothesis.relationship_type_hypothesis != candidate.relationship_type_candidate:
                raise ValueError("connection hypothesis relationship type must match candidate")
            if not set(hypothesis.evidence_position_refs) <= position_ids:
                raise ValueError("connection hypothesis evidence position refs must resolve")
            if not set(hypothesis.review_refs) <= review_ids:
                raise ValueError("connection hypothesis review refs must resolve")

        for gate in self.promotion_gates:
            if gate.connection_hypothesis_ref not in hypothesis_ids:
                raise ValueError("relationship promotion gate hypothesis ref must resolve")
            if gate.relationship_discovery_policy_ref not in policy_ids:
                raise ValueError("relationship promotion gate policy ref must resolve")
            if not set(gate.required_evidence_position_refs) <= position_ids:
                raise ValueError("relationship promotion gate evidence refs must resolve")
            if not set(gate.required_review_refs) <= review_ids:
                raise ValueError("relationship promotion gate review refs must resolve")
            policy = policy_by_id[gate.relationship_discovery_policy_ref]
            hypothesis = next(x for x in self.connection_hypotheses if x.connection_hypothesis_id == gate.connection_hypothesis_ref)
            if hypothesis.state == ConnectionHypothesisState.supported_for_validation:
                groups = position_groups.get(hypothesis.connection_hypothesis_id, set())
                reviewers = reviewer_groups.get(hypothesis.connection_hypothesis_id, set())
                if len(groups) < policy.minimum_independent_evidence_groups_for_supported_hypothesis:
                    raise ValueError("supported relationship hypothesis lacks required independent evidence groups")
                if len(reviewers) < policy.minimum_independent_reviewers_for_supported_hypothesis:
                    raise ValueError("supported relationship hypothesis lacks required independent reviewers")
                if not set(hypothesis.evidence_position_refs) <= set(gate.required_evidence_position_refs):
                    raise ValueError("promotion gate must cover supported hypothesis evidence positions")
                if not set(hypothesis.review_refs) <= set(gate.required_review_refs):
                    raise ValueError("promotion gate must cover supported hypothesis reviews")

        for snap in self.snapshots:
            if not set(snap.policy_refs) <= policy_ids: raise ValueError("snapshot policy refs must resolve")
            if not set(snap.signal_refs) <= signal_ids: raise ValueError("snapshot signal refs must resolve")
            if not set(snap.source_observed_relationship_refs) <= observed_ids: raise ValueError("snapshot observed relationship refs must resolve")
            if not set(snap.connection_candidate_refs) <= candidate_ids: raise ValueError("snapshot candidate refs must resolve")
            if not set(snap.connection_hypothesis_refs) <= hypothesis_ids: raise ValueError("snapshot hypothesis refs must resolve")
            if not set(snap.evidence_position_refs) <= position_ids: raise ValueError("snapshot evidence position refs must resolve")
            if not set(snap.review_refs) <= review_ids: raise ValueError("snapshot review refs must resolve")
            if not set(snap.promotion_gate_refs) <= gate_ids: raise ValueError("snapshot promotion gate refs must resolve")
            if not set(snap.unresolved_hypothesis_refs) <= hypothesis_ids: raise ValueError("snapshot unresolved hypothesis refs must resolve")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_relationship_discovery_hypothesis_bundle() -> RelationshipDiscoveryHypothesisBundle:
    upstream = reference_public_record_documentary_source_bundle()
    base = upstream.cross_source_entity_reconciliation_bundle.probabilistic_record_linkage_bundle.temporal_identity_bundle.entity_resolution_identity_graph_bundle
    entity_a = base.entities[0].entity_id
    entity_b = base.entities[1].entity_id
    evidence_a = base.identity_evidence_items[0].identity_evidence_id
    evidence_b = base.identity_evidence_items[1].identity_evidence_id
    source_a = upstream.documentary_sources[0].documentary_source_id
    source_b = upstream.documentary_sources[1].documentary_source_id
    segment_a = upstream.segments[0].document_segment_id
    segment_b = upstream.segments[2].document_segment_id
    interp_a = upstream.evidence_interpretations[0].documentary_interpretation_id
    interp_b = upstream.evidence_interpretations[1].documentary_interpretation_id

    policy = RelationshipDiscoveryPolicy(
        relationship_discovery_policy_id="relationship-discovery-policy:synthetic:default:v1",
        metadata={"synthetic_reference": True},
    )

    signals = [
        RelationshipDiscoverySignal(
            relationship_signal_id="relationship-signal:synthetic:documentary-cooccurrence:v1",
            signal_kind=RelationshipSignalKind.documentary_cooccurrence,
            subject_entity_ref=entity_a,
            object_entity_ref=entity_b,
            relationship_type_candidate="reported-operational-association",
            source_refs=[source_a],
            document_segment_refs=[segment_a],
            documentary_interpretation_refs=[interp_a],
            identity_evidence_refs=[evidence_a],
            provenance_refs=["provenance:synthetic:relationship-signal:documentary:v1"],
            score=0.82,
            score_semantics="synthetic document-context association score; not relationship probability",
            observed_at="2026-09-30T16:00:00Z",
            metadata={"synthetic_reference": True},
        ),
        RelationshipDiscoverySignal(
            relationship_signal_id="relationship-signal:synthetic:shared-context:v1",
            signal_kind=RelationshipSignalKind.common_affiliation,
            subject_entity_ref=entity_a,
            object_entity_ref=entity_b,
            relationship_type_candidate="reported-operational-association",
            source_refs=[source_b],
            document_segment_refs=[segment_b],
            documentary_interpretation_refs=[interp_b],
            identity_evidence_refs=[evidence_b],
            provenance_refs=["provenance:synthetic:relationship-signal:context:v1"],
            score=0.61,
            score_semantics="synthetic contextual association score; not evidence strength",
            observed_at="2026-09-30T16:01:00Z",
            metadata={"synthetic_reference": True},
        ),
    ]

    observed = SourceObservedRelationship(
        source_observed_relationship_id="source-observed-relationship:synthetic:filing-association:v1",
        subject_entity_ref=entity_a,
        object_entity_ref=entity_b,
        relationship_type="reported-operational-association",
        observation_state=SourceObservedRelationshipState.reported,
        observation_summary="Synthetic filing material reports an operational association between the two source-resolved entities; the observation remains source-bound and does not establish a canonical relationship fact.",
        source_refs=[source_a],
        document_segment_refs=[segment_a],
        documentary_interpretation_refs=[interp_a],
        identity_evidence_refs=[evidence_a],
        provenance_refs=["provenance:synthetic:observed-relationship:v1"],
        observed_at="2026-09-30T16:02:00Z",
        valid_from="2024-01-01T00:00:00Z",
        valid_to="2024-12-31T23:59:59Z",
        metadata={"synthetic_reference": True},
    )

    candidate = ConnectionCandidate(
        connection_candidate_id="connection-candidate:synthetic:northstar-association:v1",
        subject_entity_ref=entity_a,
        object_entity_ref=entity_b,
        relationship_type_candidate="reported-operational-association",
        signal_refs=[x.relationship_signal_id for x in signals],
        source_observed_relationship_refs=[observed.source_observed_relationship_id],
        candidate_score=0.74,
        candidate_score_semantics="synthetic aggregate discovery score; not relationship probability or evidence strength",
        state=ConnectionCandidateState.supported_for_hypothesis,
        generated_by="relationship-discovery-runtime:synthetic:v1",
        generated_at="2026-09-30T16:03:00Z",
        metadata={"synthetic_reference": True},
    )

    hypothesis = ConnectionHypothesis(
        connection_hypothesis_id="connection-hypothesis:synthetic:northstar-association:v1",
        connection_candidate_ref=candidate.connection_candidate_id,
        subject_entity_ref=entity_a,
        object_entity_ref=entity_b,
        relationship_type_hypothesis="reported-operational-association",
        hypothesis_statement="The two source-resolved entities may have had a documented operational association during the bounded 2024 period represented by the synthetic source material.",
        state=ConnectionHypothesisState.supported_for_validation,
        evidence_position_refs=[
            "connection-evidence-position:synthetic:filing:v1",
            "connection-evidence-position:synthetic:letter:v1",
        ],
        review_refs=[
            "connection-hypothesis-review:synthetic:a:v1",
            "connection-hypothesis-review:synthetic:b:v1",
        ],
        provenance_refs=["provenance:synthetic:connection-hypothesis:v1"],
        created_at="2026-09-30T16:04:00Z",
        metadata={"synthetic_reference": True},
    )

    positions = [
        ConnectionHypothesisEvidencePosition(
            evidence_position_id="connection-evidence-position:synthetic:filing:v1",
            connection_hypothesis_ref=hypothesis.connection_hypothesis_id,
            position=EvidencePosition.supports,
            identity_evidence_refs=[evidence_a],
            documentary_interpretation_refs=[interp_a],
            document_segment_refs=[segment_a],
            source_refs=[source_a],
            source_observed_relationship_refs=[observed.source_observed_relationship_id],
            independence_group="independence-group:synthetic:filing",
            rationale="Synthetic filing evidence supports further validation of the relationship hypothesis without establishing it as fact.",
            provenance_refs=["provenance:synthetic:evidence-position:filing:v1"],
            metadata={"synthetic_reference": True},
        ),
        ConnectionHypothesisEvidencePosition(
            evidence_position_id="connection-evidence-position:synthetic:letter:v1",
            connection_hypothesis_ref=hypothesis.connection_hypothesis_id,
            position=EvidencePosition.contextualizes,
            identity_evidence_refs=[evidence_b],
            documentary_interpretation_refs=[interp_b],
            document_segment_refs=[segment_b],
            source_refs=[source_b],
            independence_group="independence-group:synthetic:letter",
            rationale="Synthetic disclosure material provides independent context relevant to validation while remaining non-dispositive.",
            provenance_refs=["provenance:synthetic:evidence-position:letter:v1"],
            metadata={"synthetic_reference": True},
        ),
    ]

    reviews = [
        ConnectionHypothesisReview(
            connection_hypothesis_review_id="connection-hypothesis-review:synthetic:a:v1",
            connection_hypothesis_ref=hypothesis.connection_hypothesis_id,
            reviewer_ref="reviewer:synthetic:relationship-a",
            disposition=HypothesisReviewDisposition.support_validation,
            considered_evidence_position_refs=[x.evidence_position_id for x in positions],
            considered_signal_refs=[x.relationship_signal_id for x in signals],
            rationale="Evidence provenance and competing context are sufficient to advance this synthetic hypothesis to separate evidence validation, not to factual promotion.",
            reviewed_at="2026-09-30T16:05:00Z",
            metadata={"synthetic_reference": True},
        ),
        ConnectionHypothesisReview(
            connection_hypothesis_review_id="connection-hypothesis-review:synthetic:b:v1",
            connection_hypothesis_ref=hypothesis.connection_hypothesis_id,
            reviewer_ref="reviewer:synthetic:relationship-b",
            disposition=HypothesisReviewDisposition.support_validation,
            considered_evidence_position_refs=[x.evidence_position_id for x in positions],
            considered_signal_refs=[signals[0].relationship_signal_id],
            rationale="Independent synthetic review supports validation eligibility while preserving the distinction between source observations and graph facts.",
            reviewed_at="2026-09-30T16:06:00Z",
            metadata={"synthetic_reference": True},
        ),
    ]

    gate = RelationshipPromotionGate(
        relationship_promotion_gate_id="relationship-promotion-gate:synthetic:northstar:v1",
        connection_hypothesis_ref=hypothesis.connection_hypothesis_id,
        relationship_discovery_policy_ref=policy.relationship_discovery_policy_id,
        required_evidence_position_refs=[x.evidence_position_id for x in positions],
        required_review_refs=[x.connection_hypothesis_review_id for x in reviews],
        metadata={"synthetic_reference": True},
    )

    snapshot = RelationshipDiscoverySnapshot(
        relationship_discovery_snapshot_id="relationship-discovery-snapshot:synthetic:2026-09-30:v1",
        policy_refs=[policy.relationship_discovery_policy_id],
        signal_refs=[x.relationship_signal_id for x in signals],
        source_observed_relationship_refs=[observed.source_observed_relationship_id],
        connection_candidate_refs=[candidate.connection_candidate_id],
        connection_hypothesis_refs=[hypothesis.connection_hypothesis_id],
        evidence_position_refs=[x.evidence_position_id for x in positions],
        review_refs=[x.connection_hypothesis_review_id for x in reviews],
        promotion_gate_refs=[gate.relationship_promotion_gate_id],
        unresolved_hypothesis_refs=[hypothesis.connection_hypothesis_id],
        created_at="2026-09-30T16:07:00Z",
        metadata={"synthetic_reference": True},
    )

    return RelationshipDiscoveryHypothesisBundle(
        public_record_documentary_source_bundle=upstream,
        policies=[policy],
        signals=signals,
        source_observed_relationships=[observed],
        connection_candidates=[candidate],
        connection_hypotheses=[hypothesis],
        evidence_positions=positions,
        reviews=reviews,
        promotion_gates=[gate],
        snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    b = reference_relationship_discovery_hypothesis_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contracts": [
            "sc.core.public-record-documentary-source-object-model.v1",
            "sc.core.cross-source-entity-reconciliation-identity-provenance.v1",
            "sc.core.probabilistic-record-linkage-entity-matching.v1",
            "sc.core.entity-resolution-identity-graph-foundation.v1",
            "sc.core.evidence-graph-neural-analysis-validation.v1",
        ],
        "object_types": [
            "RelationshipDiscoveryPolicy",
            "RelationshipDiscoverySignal",
            "SourceObservedRelationship",
            "ConnectionCandidate",
            "ConnectionHypothesisEvidencePosition",
            "ConnectionHypothesisReview",
            "ConnectionHypothesis",
            "RelationshipPromotionGate",
            "RelationshipDiscoverySnapshot",
            "RelationshipDiscoveryHypothesisBundle",
        ],
        "principles": {
            "cooccurrence_is_not_relationship": True,
            "shared_attribute_is_not_relationship": True,
            "graph_proximity_is_not_relationship": True,
            "embedding_similarity_is_not_relationship": True,
            "model_score_is_not_relationship_fact": True,
            "source_observation_is_not_canonical_relationship_fact": True,
            "hypothesis_is_not_graph_fact": True,
            "relationship_promotion_requires_separate_evidence_validation": True,
        },
        "capabilities": {
            "source_bound_relationship_observations": True,
            "multi_signal_connection_discovery": True,
            "explicit_connection_candidates": True,
            "connection_hypothesis_objects": True,
            "supporting_contradicting_contextual_evidence_positions": True,
            "independence_group_tracking": True,
            "independent_hypothesis_review": True,
            "governed_promotion_gates": True,
            "immutable_relationship_discovery_snapshots": True,
            "deterministic_object_fingerprints": True,
        },
        "boundaries": {
            "core_infers_relationship_truth_from_cooccurrence": False,
            "core_infers_relationship_truth_from_shared_attribute": False,
            "core_infers_relationship_truth_from_graph_proximity": False,
            "core_infers_relationship_truth_from_embedding_similarity": False,
            "core_treats_model_score_as_relationship_evidence": False,
            "core_treats_source_count_as_relationship_evidence": False,
            "core_auto_promotes_connection_candidate": False,
            "core_auto_promotes_connection_hypothesis": False,
            "core_creates_evidence_edge_in_v382": False,
            "core_mutates_relationship_graph_during_discovery": False,
            "core_mutates_evidence_graph_during_discovery": False,
            "core_mutates_identity_graph_during_discovery": False,
        },
        "roadmap_integration": {
            "extends_v3770_entity_resolution_foundation": True,
            "extends_v3800_cross_source_entity_reconciliation": True,
            "extends_v3810_documentary_source_model": True,
            "prepares_v3830_network_structure_community_motif_intelligence": True,
            "prepares_v3840_explainable_connection_paths_evidence_chains": True,
            "prepares_v3850_multihop_research_investigation_graph_reasoning": True,
            "preserves_v3760_evidence_validation_boundary": True,
        },
        "reference": {
            "policy_count": len(b.policies),
            "signal_count": len(b.signals),
            "source_observed_relationship_count": len(b.source_observed_relationships),
            "connection_candidate_count": len(b.connection_candidates),
            "connection_hypothesis_count": len(b.connection_hypotheses),
            "evidence_position_count": len(b.evidence_positions),
            "review_count": len(b.reviews),
            "promotion_gate_count": len(b.promotion_gates),
            "hypothesis_state": b.connection_hypotheses[0].state.value,
            "promotion_gate_state": b.promotion_gates[0].gate_state,
            "cooccurrence_is_relationship": False,
            "shared_attribute_is_relationship": False,
            "graph_proximity_is_relationship": False,
            "model_score_is_relationship_fact": False,
            "source_observation_is_canonical_relationship_fact": False,
            "hypothesis_is_graph_fact": False,
            "relationship_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
            "identity_graph_mutation_performed": False,
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
