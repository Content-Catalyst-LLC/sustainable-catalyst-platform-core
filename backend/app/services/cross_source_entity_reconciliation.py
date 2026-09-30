from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .probabilistic_record_linkage import (
    ProbabilisticRecordLinkageBundle,
    reference_probabilistic_record_linkage_bundle,
)

CORE_RELEASE = "3.80.0"
CONTRACT_VERSION = "sc.core.cross-source-entity-reconciliation-identity-provenance.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class ReconciliationSourceKind(str, Enum):
    publication = "publication"
    dataset = "dataset"
    registry = "registry"
    archive = "archive"
    public_record = "public-record"
    knowledge_base = "knowledge-base"
    repository = "repository"
    other = "other"


class ReconciliationObservationState(str, Enum):
    observed = "observed"
    supported = "supported"
    contradicted = "contradicted"
    disputed = "disputed"
    superseded = "superseded"
    unresolved = "unresolved"


class ReconciliationClusterState(str, Enum):
    candidate = "candidate"
    under_review = "under-review"
    source_aligned_candidate = "source-aligned-candidate"
    conflicted = "conflicted"
    rejected = "rejected"


class ReconciliationDecisionState(str, Enum):
    review_required = "review-required"
    candidate_supported = "candidate-supported"
    candidate_rejected = "candidate-rejected"
    source_conflicted = "source-conflicted"
    unresolved = "unresolved"


class ReconciliationReviewDisposition(str, Enum):
    support_candidate = "support-candidate"
    reject_candidate = "reject-candidate"
    preserve_conflict = "preserve-conflict"
    insufficient = "insufficient"


class ReconciliationSourceDescriptor(BaseModel):
    source_descriptor_id: str = Field(min_length=2, max_length=500)
    source_ref: str = Field(min_length=2, max_length=1000)
    source_kind: ReconciliationSourceKind
    source_label: str = Field(min_length=1, max_length=1000)
    source_scope: str = Field(min_length=1, max_length=2000)
    jurisdiction_or_context: str | None = Field(default=None, max_length=1000)
    retrieved_at: str = Field(min_length=10, max_length=80)
    provenance_refs: list[str] = Field(min_length=1)
    independence_group: str = Field(min_length=1, max_length=500)
    source_quality_ref: str | None = Field(default=None, max_length=1000)
    source_descriptor_is_not_trust_verdict: Literal[True] = True
    source_independence_must_be_evaluated_explicitly: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.provenance_refs, "provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SourceIdentityObservation(BaseModel):
    source_identity_observation_id: str = Field(min_length=2, max_length=500)
    source_descriptor_ref: str = Field(min_length=2, max_length=500)
    entity_ref: str = Field(min_length=2, max_length=1000)
    source_entity_key: str = Field(min_length=1, max_length=1000)
    asserted_name: str = Field(min_length=1, max_length=2000)
    identifier_values: list[str] = Field(default_factory=list)
    source_identity_assertion_ref: str | None = Field(default=None, max_length=500)
    temporal_source_assertion_ref: str | None = Field(default=None, max_length=500)
    observed_at: str = Field(min_length=10, max_length=80)
    valid_from: str | None = Field(default=None, max_length=80)
    valid_to: str | None = Field(default=None, max_length=80)
    observation_state: ReconciliationObservationState = ReconciliationObservationState.observed
    provenance_refs: list[str] = Field(min_length=1)
    source_observation_is_not_canonical_identity: Literal[True] = True
    source_observation_does_not_override_other_sources: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.identifier_values, "identifier_values")
        _unique(self.provenance_refs, "provenance_refs")
        if not self.source_identity_assertion_ref and not self.temporal_source_assertion_ref:
            raise ValueError("source identity observation requires an upstream source assertion reference")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossSourceComparisonObservation(BaseModel):
    cross_source_comparison_id: str = Field(min_length=2, max_length=500)
    left_observation_ref: str = Field(min_length=2, max_length=500)
    right_observation_ref: str = Field(min_length=2, max_length=500)
    compared_fields: list[str] = Field(min_length=1)
    agreement_fields: list[str] = Field(default_factory=list)
    disagreement_fields: list[str] = Field(default_factory=list)
    temporal_overlap: bool | None = None
    linkage_probability_ref: str | None = Field(default=None, max_length=500)
    comparison_provenance_refs: list[str] = Field(min_length=1)
    source_agreement_is_not_identity_fact: Literal[True] = True
    source_disagreement_is_not_nonidentity_fact: Literal[True] = True
    linkage_probability_is_context_only: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        if self.left_observation_ref == self.right_observation_ref:
            raise ValueError("cross-source comparison requires two distinct observations")
        for values, label in (
            (self.compared_fields, "compared_fields"),
            (self.agreement_fields, "agreement_fields"),
            (self.disagreement_fields, "disagreement_fields"),
            (self.comparison_provenance_refs, "comparison_provenance_refs"),
        ):
            _unique(values, label)
        if not set(self.agreement_fields + self.disagreement_fields) <= set(self.compared_fields):
            raise ValueError("agreement/disagreement fields must be included in compared_fields")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class IdentityProvenanceChain(BaseModel):
    identity_provenance_chain_id: str = Field(min_length=2, max_length=500)
    source_observation_refs: list[str] = Field(min_length=1)
    source_descriptor_refs: list[str] = Field(min_length=1)
    provenance_refs: list[str] = Field(min_length=1)
    transformation_refs: list[str] = Field(default_factory=list)
    derived_object_refs: list[str] = Field(default_factory=list)
    chain_complete: bool
    missing_link_notes: list[str] = Field(default_factory=list)
    provenance_chain_is_not_identity_proof: Literal[True] = True
    completeness_is_not_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        for values, label in (
            (self.source_observation_refs, "source_observation_refs"),
            (self.source_descriptor_refs, "source_descriptor_refs"),
            (self.provenance_refs, "provenance_refs"),
            (self.transformation_refs, "transformation_refs"),
            (self.derived_object_refs, "derived_object_refs"),
            (self.missing_link_notes, "missing_link_notes"),
        ):
            _unique(values, label)
        if self.chain_complete and self.missing_link_notes:
            raise ValueError("complete provenance chain cannot declare missing links")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossSourceReconciliationConflict(BaseModel):
    reconciliation_conflict_id: str = Field(min_length=2, max_length=500)
    observation_refs: list[str] = Field(min_length=2)
    source_descriptor_refs: list[str] = Field(min_length=2)
    conflict_fields: list[str] = Field(min_length=1)
    conflict_summary: str = Field(min_length=1, max_length=8000)
    provenance_chain_refs: list[str] = Field(min_length=1)
    unresolved: bool = True
    conflicting_sources_are_preserved: Literal[True] = True
    no_automatic_source_precedence: Literal[True] = True
    conflict_is_not_proof_of_distinct_identity: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        for values, label in (
            (self.observation_refs, "observation_refs"),
            (self.source_descriptor_refs, "source_descriptor_refs"),
            (self.conflict_fields, "conflict_fields"),
            (self.provenance_chain_refs, "provenance_chain_refs"),
        ):
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossSourceEntityReconciliationCluster(BaseModel):
    reconciliation_cluster_id: str = Field(min_length=2, max_length=500)
    entity_refs: list[str] = Field(min_length=2)
    source_observation_refs: list[str] = Field(min_length=2)
    comparison_refs: list[str] = Field(min_length=1)
    candidate_match_refs: list[str] = Field(default_factory=list)
    pairwise_match_decision_refs: list[str] = Field(default_factory=list)
    temporal_snapshot_refs: list[str] = Field(default_factory=list)
    conflict_refs: list[str] = Field(default_factory=list)
    provenance_chain_refs: list[str] = Field(min_length=1)
    cluster_state: ReconciliationClusterState
    cluster_membership_is_not_identity_fact: Literal[True] = True
    cluster_is_not_canonical_equivalence: Literal[True] = True
    cluster_does_not_merge_entities: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        for values, label in (
            (self.entity_refs, "entity_refs"),
            (self.source_observation_refs, "source_observation_refs"),
            (self.comparison_refs, "comparison_refs"),
            (self.candidate_match_refs, "candidate_match_refs"),
            (self.pairwise_match_decision_refs, "pairwise_match_decision_refs"),
            (self.temporal_snapshot_refs, "temporal_snapshot_refs"),
            (self.conflict_refs, "conflict_refs"),
            (self.provenance_chain_refs, "provenance_chain_refs"),
        ):
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossSourceReconciliationPolicy(BaseModel):
    reconciliation_policy_id: str = Field(min_length=2, max_length=500)
    require_provenance_chain: Literal[True] = True
    require_independent_review: Literal[True] = True
    minimum_independent_source_groups: int = Field(ge=1, le=100)
    preserve_source_disagreement: Literal[True] = True
    automatic_source_precedence_allowed: Literal[False] = False
    source_count_can_satisfy_identity_gate: Literal[False] = False
    linkage_probability_can_satisfy_identity_gate: Literal[False] = False
    source_agreement_can_satisfy_identity_gate: Literal[False] = False
    downstream_v377_resolution_required_for_merge: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossSourceReconciliationReview(BaseModel):
    reconciliation_review_id: str = Field(min_length=2, max_length=500)
    reconciliation_cluster_ref: str = Field(min_length=2, max_length=500)
    reviewer_ref: str = Field(min_length=2, max_length=1000)
    disposition: ReconciliationReviewDisposition
    source_observation_refs: list[str] = Field(min_length=1)
    identity_evidence_refs: list[str] = Field(default_factory=list)
    conflict_refs: list[str] = Field(default_factory=list)
    considered_probability_refs: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1, max_length=8000)
    reviewed_at: str = Field(min_length=10, max_length=80)
    probability_is_context_not_identity_evidence: Literal[True] = True
    review_does_not_merge_entities: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        for values, label in (
            (self.source_observation_refs, "source_observation_refs"),
            (self.identity_evidence_refs, "identity_evidence_refs"),
            (self.conflict_refs, "conflict_refs"),
            (self.considered_probability_refs, "considered_probability_refs"),
        ):
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossSourceReconciliationDecision(BaseModel):
    reconciliation_decision_id: str = Field(min_length=2, max_length=500)
    reconciliation_cluster_ref: str = Field(min_length=2, max_length=500)
    reconciliation_policy_ref: str = Field(min_length=2, max_length=500)
    decision_state: ReconciliationDecisionState
    supporting_observation_refs: list[str] = Field(default_factory=list)
    contradicting_observation_refs: list[str] = Field(default_factory=list)
    identity_evidence_refs: list[str] = Field(default_factory=list)
    conflict_refs: list[str] = Field(default_factory=list)
    provenance_chain_refs: list[str] = Field(min_length=1)
    review_refs: list[str] = Field(default_factory=list)
    v377_candidate_match_ref: str | None = Field(default=None, max_length=500)
    decision_is_not_canonical_identity: Literal[True] = True
    decision_does_not_create_equivalence_edge: Literal[True] = True
    decision_does_not_merge_entities: Literal[True] = True
    downstream_v377_identity_resolution_required: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        for values, label in (
            (self.supporting_observation_refs, "supporting_observation_refs"),
            (self.contradicting_observation_refs, "contradicting_observation_refs"),
            (self.identity_evidence_refs, "identity_evidence_refs"),
            (self.conflict_refs, "conflict_refs"),
            (self.provenance_chain_refs, "provenance_chain_refs"),
            (self.review_refs, "review_refs"),
        ):
            _unique(values, label)
        if self.decision_state == ReconciliationDecisionState.candidate_supported:
            if not self.supporting_observation_refs or not self.identity_evidence_refs:
                raise ValueError("supported reconciliation candidate requires observations and identity evidence")
            if not self.review_refs or not self.v377_candidate_match_ref:
                raise ValueError("supported reconciliation candidate requires reviews and v3.77 candidate match")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class IdentityProvenanceSnapshot(BaseModel):
    identity_provenance_snapshot_id: str = Field(min_length=2, max_length=500)
    reconciliation_cluster_refs: list[str] = Field(min_length=1)
    source_descriptor_refs: list[str] = Field(min_length=1)
    source_observation_refs: list[str] = Field(min_length=1)
    provenance_chain_refs: list[str] = Field(min_length=1)
    reconciliation_decision_refs: list[str] = Field(default_factory=list)
    unresolved_conflict_refs: list[str] = Field(default_factory=list)
    created_at: str = Field(min_length=10, max_length=80)
    immutable_snapshot: Literal[True] = True
    source_specific_assertions_preserved: Literal[True] = True
    snapshot_does_not_mutate_identity_graph: Literal[True] = True
    snapshot_is_not_identity_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        for values, label in (
            (self.reconciliation_cluster_refs, "reconciliation_cluster_refs"),
            (self.source_descriptor_refs, "source_descriptor_refs"),
            (self.source_observation_refs, "source_observation_refs"),
            (self.provenance_chain_refs, "provenance_chain_refs"),
            (self.reconciliation_decision_refs, "reconciliation_decision_refs"),
            (self.unresolved_conflict_refs, "unresolved_conflict_refs"),
        ):
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossSourceEntityReconciliationBundle(BaseModel):
    probabilistic_record_linkage_bundle: ProbabilisticRecordLinkageBundle
    source_descriptors: list[ReconciliationSourceDescriptor] = Field(min_length=2)
    source_observations: list[SourceIdentityObservation] = Field(min_length=2)
    comparisons: list[CrossSourceComparisonObservation] = Field(min_length=1)
    provenance_chains: list[IdentityProvenanceChain] = Field(min_length=1)
    conflicts: list[CrossSourceReconciliationConflict] = Field(default_factory=list)
    clusters: list[CrossSourceEntityReconciliationCluster] = Field(min_length=1)
    policies: list[CrossSourceReconciliationPolicy] = Field(min_length=1)
    reviews: list[CrossSourceReconciliationReview] = Field(min_length=1)
    decisions: list[CrossSourceReconciliationDecision] = Field(min_length=1)
    provenance_snapshots: list[IdentityProvenanceSnapshot] = Field(min_length=1)
    source_agreement_is_not_identity_fact: Literal[True] = True
    source_count_is_not_identity_evidence: Literal[True] = True
    automatic_source_precedence_allowed: Literal[False] = False
    canonical_identity_merge_performed: Literal[False] = False
    identity_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        linkage = self.probabilistic_record_linkage_bundle
        temporal = linkage.temporal_identity_bundle
        base = temporal.entity_resolution_identity_graph_bundle

        def ids(items, attr, label):
            values = [getattr(x, attr) for x in items]
            _unique(values, label)
            return set(values)

        entity_ids = {x.entity_id for x in base.entities}
        source_assertion_ids = {x.source_identity_assertion_id for x in base.source_identity_assertions}
        temporal_source_assertion_ids = {x.temporal_source_assertion_id for x in temporal.temporal_source_assertions}
        temporal_snapshot_ids = {x.temporal_snapshot_id for x in temporal.temporal_snapshots}
        identity_evidence_ids = {x.identity_evidence_id for x in base.identity_evidence_items}
        candidate_match_ids = {x.candidate_match_id for x in base.candidate_matches}
        probability_ids = {x.entity_match_probability_id for x in linkage.probability_records}
        pairwise_decision_ids = {x.pairwise_match_decision_id for x in linkage.decisions}

        descriptor_ids = ids(self.source_descriptors, "source_descriptor_id", "source_descriptor_ids")
        observation_ids = ids(self.source_observations, "source_identity_observation_id", "source_observation_ids")
        comparison_ids = ids(self.comparisons, "cross_source_comparison_id", "comparison_ids")
        chain_ids = ids(self.provenance_chains, "identity_provenance_chain_id", "provenance_chain_ids")
        conflict_ids = ids(self.conflicts, "reconciliation_conflict_id", "conflict_ids")
        cluster_ids = ids(self.clusters, "reconciliation_cluster_id", "cluster_ids")
        policy_ids = ids(self.policies, "reconciliation_policy_id", "policy_ids")
        review_ids = ids(self.reviews, "reconciliation_review_id", "review_ids")
        decision_ids = ids(self.decisions, "reconciliation_decision_id", "decision_ids")
        ids(self.provenance_snapshots, "identity_provenance_snapshot_id", "snapshot_ids")

        descriptor_source_refs = {x.source_ref for x in self.source_descriptors}
        if len(descriptor_source_refs) != len(self.source_descriptors):
            raise ValueError("source descriptors must refer to distinct source_ref values")

        for obs in self.source_observations:
            if obs.source_descriptor_ref not in descriptor_ids:
                raise ValueError("source observation references unknown source descriptor")
            if obs.entity_ref not in entity_ids:
                raise ValueError("source observation references unknown entity")
            if obs.source_identity_assertion_ref and obs.source_identity_assertion_ref not in source_assertion_ids:
                raise ValueError("source observation references unknown source identity assertion")
            if obs.temporal_source_assertion_ref and obs.temporal_source_assertion_ref not in temporal_source_assertion_ids:
                raise ValueError("source observation references unknown temporal source assertion")

        for comp in self.comparisons:
            if comp.left_observation_ref not in observation_ids or comp.right_observation_ref not in observation_ids:
                raise ValueError("comparison references unknown source observation")
            if comp.linkage_probability_ref and comp.linkage_probability_ref not in probability_ids:
                raise ValueError("comparison references unknown linkage probability")

        for chain in self.provenance_chains:
            if not set(chain.source_observation_refs) <= observation_ids:
                raise ValueError("provenance chain references unknown source observation")
            if not set(chain.source_descriptor_refs) <= descriptor_ids:
                raise ValueError("provenance chain references unknown source descriptor")

        for conflict in self.conflicts:
            if not set(conflict.observation_refs) <= observation_ids:
                raise ValueError("conflict references unknown observation")
            if not set(conflict.source_descriptor_refs) <= descriptor_ids:
                raise ValueError("conflict references unknown source descriptor")
            if not set(conflict.provenance_chain_refs) <= chain_ids:
                raise ValueError("conflict references unknown provenance chain")

        for cluster in self.clusters:
            if not set(cluster.entity_refs) <= entity_ids:
                raise ValueError("cluster references unknown entity")
            if not set(cluster.source_observation_refs) <= observation_ids:
                raise ValueError("cluster references unknown source observation")
            if not set(cluster.comparison_refs) <= comparison_ids:
                raise ValueError("cluster references unknown comparison")
            if not set(cluster.candidate_match_refs) <= candidate_match_ids:
                raise ValueError("cluster references unknown v3.77 candidate match")
            if not set(cluster.pairwise_match_decision_refs) <= pairwise_decision_ids:
                raise ValueError("cluster references unknown v3.79 pairwise decision")
            if not set(cluster.temporal_snapshot_refs) <= temporal_snapshot_ids:
                raise ValueError("cluster references unknown temporal snapshot")
            if not set(cluster.conflict_refs) <= conflict_ids:
                raise ValueError("cluster references unknown conflict")
            if not set(cluster.provenance_chain_refs) <= chain_ids:
                raise ValueError("cluster references unknown provenance chain")

        for review in self.reviews:
            if review.reconciliation_cluster_ref not in cluster_ids:
                raise ValueError("review references unknown cluster")
            if not set(review.source_observation_refs) <= observation_ids:
                raise ValueError("review references unknown source observation")
            if not set(review.identity_evidence_refs) <= identity_evidence_ids:
                raise ValueError("review references unknown identity evidence")
            if not set(review.conflict_refs) <= conflict_ids:
                raise ValueError("review references unknown conflict")
            if not set(review.considered_probability_refs) <= probability_ids:
                raise ValueError("review references unknown match probability")

        for decision in self.decisions:
            if decision.reconciliation_cluster_ref not in cluster_ids:
                raise ValueError("decision references unknown cluster")
            if decision.reconciliation_policy_ref not in policy_ids:
                raise ValueError("decision references unknown policy")
            if not set(decision.supporting_observation_refs + decision.contradicting_observation_refs) <= observation_ids:
                raise ValueError("decision references unknown source observation")
            if not set(decision.identity_evidence_refs) <= identity_evidence_ids:
                raise ValueError("decision references unknown identity evidence")
            if not set(decision.conflict_refs) <= conflict_ids:
                raise ValueError("decision references unknown conflict")
            if not set(decision.provenance_chain_refs) <= chain_ids:
                raise ValueError("decision references unknown provenance chain")
            if not set(decision.review_refs) <= review_ids:
                raise ValueError("decision references unknown review")
            if decision.v377_candidate_match_ref and decision.v377_candidate_match_ref not in candidate_match_ids:
                raise ValueError("decision references unknown v3.77 candidate match")

        for snap in self.provenance_snapshots:
            if not set(snap.reconciliation_cluster_refs) <= cluster_ids:
                raise ValueError("snapshot references unknown cluster")
            if not set(snap.source_descriptor_refs) <= descriptor_ids:
                raise ValueError("snapshot references unknown source descriptor")
            if not set(snap.source_observation_refs) <= observation_ids:
                raise ValueError("snapshot references unknown source observation")
            if not set(snap.provenance_chain_refs) <= chain_ids:
                raise ValueError("snapshot references unknown provenance chain")
            if not set(snap.reconciliation_decision_refs) <= decision_ids:
                raise ValueError("snapshot references unknown decision")
            if not set(snap.unresolved_conflict_refs) <= conflict_ids:
                raise ValueError("snapshot references unknown conflict")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_cross_source_entity_reconciliation_bundle() -> CrossSourceEntityReconciliationBundle:
    upstream = reference_probabilistic_record_linkage_bundle()
    temporal = upstream.temporal_identity_bundle
    base = temporal.entity_resolution_identity_graph_bundle

    entity_a = base.entities[0].entity_id
    entity_b = base.entities[1].entity_id
    source_a = base.source_identity_assertions[0]
    source_b = base.source_identity_assertions[1]
    temporal_current = temporal.temporal_source_assertions[-1]
    probability = upstream.probability_records[0]
    pairwise_decision = upstream.decisions[0]
    candidate_match = base.candidate_matches[0]
    evidence_refs = [x.identity_evidence_id for x in base.identity_evidence_items[:2]]

    descriptors = [
        ReconciliationSourceDescriptor(
            source_descriptor_id="reconciliation-source:synthetic:registry-a:v1",
            source_ref=source_a.source_ref,
            source_kind=ReconciliationSourceKind.registry,
            source_label="Synthetic Registry A",
            source_scope="Synthetic organization registry record",
            jurisdiction_or_context="synthetic-jurisdiction-a",
            retrieved_at="2026-09-29T18:00:00Z",
            provenance_refs=source_a.provenance_refs,
            independence_group="independence-group:synthetic:registry-a",
            metadata={"synthetic_reference": True},
        ),
        ReconciliationSourceDescriptor(
            source_descriptor_id="reconciliation-source:synthetic:annual-report-b:v1",
            source_ref=source_b.source_ref,
            source_kind=ReconciliationSourceKind.publication,
            source_label="Synthetic Annual Report B",
            source_scope="Synthetic independently published annual report",
            retrieved_at="2026-09-29T18:01:00Z",
            provenance_refs=source_b.provenance_refs,
            independence_group="independence-group:synthetic:publication-b",
            metadata={"synthetic_reference": True},
        ),
        ReconciliationSourceDescriptor(
            source_descriptor_id="reconciliation-source:synthetic:registry-2024:v1",
            source_ref=temporal_current.source_ref,
            source_kind=ReconciliationSourceKind.registry,
            source_label="Synthetic Registry 2024",
            source_scope="Synthetic later registry snapshot",
            jurisdiction_or_context="synthetic-jurisdiction-a",
            retrieved_at="2026-09-29T18:02:00Z",
            provenance_refs=temporal_current.provenance_refs,
            independence_group="independence-group:synthetic:registry-a",
            metadata={"synthetic_reference": True, "same_independence_group_as_registry_a": True},
        ),
    ]

    observations = [
        SourceIdentityObservation(
            source_identity_observation_id="source-observation:synthetic:registry-a:v1",
            source_descriptor_ref=descriptors[0].source_descriptor_id,
            entity_ref=entity_a,
            source_entity_key=source_a.source_entity_key,
            asserted_name=source_a.asserted_name,
            identifier_values=["SYN-NRC-001"],
            source_identity_assertion_ref=source_a.source_identity_assertion_id,
            observed_at="2026-09-29T18:00:00Z",
            observation_state=ReconciliationObservationState.supported,
            provenance_refs=source_a.provenance_refs,
            metadata={"synthetic_reference": True},
        ),
        SourceIdentityObservation(
            source_identity_observation_id="source-observation:synthetic:annual-report-b:v1",
            source_descriptor_ref=descriptors[1].source_descriptor_id,
            entity_ref=entity_b,
            source_entity_key=source_b.source_entity_key,
            asserted_name=source_b.asserted_name,
            identifier_values=["SYN-NRC-001"],
            source_identity_assertion_ref=source_b.source_identity_assertion_id,
            observed_at="2026-09-29T18:01:00Z",
            observation_state=ReconciliationObservationState.supported,
            provenance_refs=source_b.provenance_refs,
            metadata={"synthetic_reference": True},
        ),
        SourceIdentityObservation(
            source_identity_observation_id="source-observation:synthetic:registry-2024:v1",
            source_descriptor_ref=descriptors[2].source_descriptor_id,
            entity_ref=entity_a,
            source_entity_key=temporal_current.source_entity_key,
            asserted_name=temporal_current.asserted_name,
            identifier_values=["SCI-2042"],
            temporal_source_assertion_ref=temporal_current.temporal_source_assertion_id,
            observed_at=temporal_current.observed_at,
            valid_from=temporal_current.valid_from,
            valid_to=temporal_current.valid_to,
            observation_state=ReconciliationObservationState.disputed,
            provenance_refs=temporal_current.provenance_refs,
            metadata={"synthetic_reference": True, "temporal_context_preserved": True},
        ),
    ]

    comparisons = [
        CrossSourceComparisonObservation(
            cross_source_comparison_id="cross-source-comparison:synthetic:registry-a-report-b:v1",
            left_observation_ref=observations[0].source_identity_observation_id,
            right_observation_ref=observations[1].source_identity_observation_id,
            compared_fields=["normalized-name", "registry-identifier", "legal-suffix"],
            agreement_fields=["normalized-name", "registry-identifier"],
            disagreement_fields=["legal-suffix"],
            temporal_overlap=True,
            linkage_probability_ref=probability.entity_match_probability_id,
            comparison_provenance_refs=["provenance:synthetic:cross-source-comparison:a-b:v1"],
            metadata={"synthetic_reference": True},
        ),
        CrossSourceComparisonObservation(
            cross_source_comparison_id="cross-source-comparison:synthetic:registry-a-2024:v1",
            left_observation_ref=observations[0].source_identity_observation_id,
            right_observation_ref=observations[2].source_identity_observation_id,
            compared_fields=["name", "identifier", "validity-period"],
            agreement_fields=[],
            disagreement_fields=["name", "identifier", "validity-period"],
            temporal_overlap=False,
            comparison_provenance_refs=["provenance:synthetic:cross-source-comparison:a-2024:v1"],
            metadata={"synthetic_reference": True, "possible_successor_identity_context": True},
        ),
    ]

    provenance_chains = [
        IdentityProvenanceChain(
            identity_provenance_chain_id="identity-provenance-chain:synthetic:registry-a-report-b:v1",
            source_observation_refs=[observations[0].source_identity_observation_id, observations[1].source_identity_observation_id],
            source_descriptor_refs=[descriptors[0].source_descriptor_id, descriptors[1].source_descriptor_id],
            provenance_refs=source_a.provenance_refs + source_b.provenance_refs,
            transformation_refs=["transform:synthetic:name-normalization:v1"],
            derived_object_refs=[comparisons[0].cross_source_comparison_id, probability.entity_match_probability_id],
            chain_complete=True,
            metadata={"synthetic_reference": True},
        ),
        IdentityProvenanceChain(
            identity_provenance_chain_id="identity-provenance-chain:synthetic:registry-temporal:v1",
            source_observation_refs=[observations[0].source_identity_observation_id, observations[2].source_identity_observation_id],
            source_descriptor_refs=[descriptors[0].source_descriptor_id, descriptors[2].source_descriptor_id],
            provenance_refs=source_a.provenance_refs + temporal_current.provenance_refs,
            derived_object_refs=[comparisons[1].cross_source_comparison_id],
            chain_complete=True,
            metadata={"synthetic_reference": True},
        ),
    ]

    conflict = CrossSourceReconciliationConflict(
        reconciliation_conflict_id="reconciliation-conflict:synthetic:registry-temporal-name-id:v1",
        observation_refs=[observations[0].source_identity_observation_id, observations[2].source_identity_observation_id],
        source_descriptor_refs=[descriptors[0].source_descriptor_id, descriptors[2].source_descriptor_id],
        conflict_fields=["asserted-name", "identifier", "validity-period"],
        conflict_summary="The later registry snapshot uses a different name and identifier; temporal succession is preserved as a conflict/context object rather than auto-collapsed.",
        provenance_chain_refs=[provenance_chains[1].identity_provenance_chain_id],
        unresolved=True,
        metadata={"synthetic_reference": True},
    )

    cluster = CrossSourceEntityReconciliationCluster(
        reconciliation_cluster_id="reconciliation-cluster:synthetic:northstar-cross-source:v1",
        entity_refs=[entity_a, entity_b],
        source_observation_refs=[x.source_identity_observation_id for x in observations],
        comparison_refs=[x.cross_source_comparison_id for x in comparisons],
        candidate_match_refs=[candidate_match.candidate_match_id],
        pairwise_match_decision_refs=[pairwise_decision.pairwise_match_decision_id],
        temporal_snapshot_refs=[temporal.temporal_snapshots[0].temporal_snapshot_id],
        conflict_refs=[conflict.reconciliation_conflict_id],
        provenance_chain_refs=[x.identity_provenance_chain_id for x in provenance_chains],
        cluster_state=ReconciliationClusterState.source_aligned_candidate,
        metadata={"synthetic_reference": True},
    )

    policy = CrossSourceReconciliationPolicy(
        reconciliation_policy_id="cross-source-reconciliation-policy:reference:v1",
        minimum_independent_source_groups=2,
        metadata={"synthetic_reference": True},
    )

    reviews = [
        CrossSourceReconciliationReview(
            reconciliation_review_id="reconciliation-review:synthetic:a:v1",
            reconciliation_cluster_ref=cluster.reconciliation_cluster_id,
            reviewer_ref="reviewer:synthetic:cross-source-a",
            disposition=ReconciliationReviewDisposition.support_candidate,
            source_observation_refs=[observations[0].source_identity_observation_id, observations[1].source_identity_observation_id],
            identity_evidence_refs=evidence_refs,
            conflict_refs=[conflict.reconciliation_conflict_id],
            considered_probability_refs=[probability.entity_match_probability_id],
            rationale="Independent source observations and provenance-bearing identity evidence support continued identity-resolution review while preserving the temporal conflict.",
            reviewed_at="2026-09-29T18:10:00Z",
            metadata={"synthetic_reference": True},
        ),
        CrossSourceReconciliationReview(
            reconciliation_review_id="reconciliation-review:synthetic:b:v1",
            reconciliation_cluster_ref=cluster.reconciliation_cluster_id,
            reviewer_ref="reviewer:synthetic:cross-source-b",
            disposition=ReconciliationReviewDisposition.preserve_conflict,
            source_observation_refs=[x.source_identity_observation_id for x in observations],
            identity_evidence_refs=evidence_refs,
            conflict_refs=[conflict.reconciliation_conflict_id],
            considered_probability_refs=[probability.entity_match_probability_id],
            rationale="The cross-source candidate is supportable for downstream identity resolution, but the later registry variation remains unresolved and must not be erased.",
            reviewed_at="2026-09-29T18:12:00Z",
            metadata={"synthetic_reference": True},
        ),
    ]

    decision = CrossSourceReconciliationDecision(
        reconciliation_decision_id="reconciliation-decision:synthetic:northstar:v1",
        reconciliation_cluster_ref=cluster.reconciliation_cluster_id,
        reconciliation_policy_ref=policy.reconciliation_policy_id,
        decision_state=ReconciliationDecisionState.candidate_supported,
        supporting_observation_refs=[observations[0].source_identity_observation_id, observations[1].source_identity_observation_id],
        contradicting_observation_refs=[observations[2].source_identity_observation_id],
        identity_evidence_refs=evidence_refs,
        conflict_refs=[conflict.reconciliation_conflict_id],
        provenance_chain_refs=[x.identity_provenance_chain_id for x in provenance_chains],
        review_refs=[x.reconciliation_review_id for x in reviews],
        v377_candidate_match_ref=candidate_match.candidate_match_id,
        metadata={"synthetic_reference": True, "handoff_only": True},
    )

    snapshot = IdentityProvenanceSnapshot(
        identity_provenance_snapshot_id="identity-provenance-snapshot:synthetic:2026-09-29:v1",
        reconciliation_cluster_refs=[cluster.reconciliation_cluster_id],
        source_descriptor_refs=[x.source_descriptor_id for x in descriptors],
        source_observation_refs=[x.source_identity_observation_id for x in observations],
        provenance_chain_refs=[x.identity_provenance_chain_id for x in provenance_chains],
        reconciliation_decision_refs=[decision.reconciliation_decision_id],
        unresolved_conflict_refs=[conflict.reconciliation_conflict_id],
        created_at="2026-09-29T18:15:00Z",
        metadata={"synthetic_reference": True},
    )

    return CrossSourceEntityReconciliationBundle(
        probabilistic_record_linkage_bundle=upstream,
        source_descriptors=descriptors,
        source_observations=observations,
        comparisons=comparisons,
        provenance_chains=provenance_chains,
        conflicts=[conflict],
        clusters=[cluster],
        policies=[policy],
        reviews=reviews,
        decisions=[decision],
        provenance_snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    b = reference_cross_source_entity_reconciliation_bundle()
    independent_groups = {x.independence_group for x in b.source_descriptors}
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contracts": [
            "sc.core.entity-resolution-identity-graph-foundation.v1",
            "sc.core.temporal-identity-alias-name-variant-intelligence.v1",
            "sc.core.probabilistic-record-linkage-entity-matching.v1",
        ],
        "object_types": [
            "ReconciliationSourceDescriptor",
            "SourceIdentityObservation",
            "CrossSourceComparisonObservation",
            "IdentityProvenanceChain",
            "CrossSourceReconciliationConflict",
            "CrossSourceEntityReconciliationCluster",
            "CrossSourceReconciliationPolicy",
            "CrossSourceReconciliationReview",
            "CrossSourceReconciliationDecision",
            "IdentityProvenanceSnapshot",
            "CrossSourceEntityReconciliationBundle",
        ],
        "principles": {
            "source_specific_identity_assertions_are_preserved": True,
            "source_agreement_is_not_identity_fact": True,
            "source_count_is_not_identity_evidence": True,
            "source_disagreement_is_not_nonidentity_fact": True,
            "linkage_probability_is_context_not_identity_evidence": True,
            "provenance_completeness_is_not_truth": True,
            "reconciliation_does_not_flatten_source_disagreement": True,
            "reconciliation_does_not_merge_canonical_entities": True,
        },
        "capabilities": {
            "cross_source_identity_observations": True,
            "source_kind_and_independence_groups": True,
            "field_level_agreement_and_disagreement": True,
            "probabilistic_linkage_context": True,
            "identity_provenance_chains": True,
            "explicit_reconciliation_conflicts": True,
            "source_preserving_reconciliation_clusters": True,
            "independent_reconciliation_review": True,
            "immutable_identity_provenance_snapshots": True,
            "deterministic_object_fingerprints": True,
        },
        "boundaries": {
            "core_fetches_or_scrapes_sources": False,
            "core_auto_prioritizes_one_source_over_another": False,
            "core_treats_source_count_as_identity_evidence": False,
            "core_treats_source_agreement_as_identity_fact": False,
            "core_treats_linkage_probability_as_identity_evidence": False,
            "core_auto_resolves_source_conflicts": False,
            "core_auto_merges_reconciled_entities": False,
            "core_mutates_identity_graph_during_reconciliation": False,
            "core_bypasses_v377_identity_resolution_policy": False,
        },
        "roadmap_integration": {
            "extends_v3770_entity_resolution_identity_graph_foundation": True,
            "extends_v3780_temporal_identity_intelligence": True,
            "extends_v3790_probabilistic_record_linkage": True,
            "prepares_v3810_public_record_documentary_source_object_model": True,
            "prepares_v3820_relationship_discovery_connection_hypotheses": True,
            "preserves_v3760_evidence_validation_boundary": True,
        },
        "reference": {
            "source_descriptor_count": len(b.source_descriptors),
            "source_observation_count": len(b.source_observations),
            "comparison_count": len(b.comparisons),
            "provenance_chain_count": len(b.provenance_chains),
            "conflict_count": len(b.conflicts),
            "cluster_count": len(b.clusters),
            "independent_source_group_count": len(independent_groups),
            "review_count": len(b.reviews),
            "decision_state": b.decisions[0].decision_state.value,
            "unresolved_conflicts_preserved": True,
            "canonical_identity_merge_performed": False,
            "identity_graph_mutation_performed": False,
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
    }
