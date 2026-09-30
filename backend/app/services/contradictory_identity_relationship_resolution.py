from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .multi_hop_research_investigation_graph_reasoning import (
    MultiHopResearchInvestigationGraphReasoningBundle,
    reference_multi_hop_research_investigation_graph_reasoning_bundle,
)

CORE_RELEASE = "3.86.0"
CONTRACT_VERSION = "sc.core.contradictory-identity-relationship-resolution.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class ContradictionDomain(str, Enum):
    identity = "identity"
    relationship = "relationship"
    mixed = "mixed"


class AssertionPosition(str, Enum):
    supports = "supports"
    contradicts = "contradicts"
    qualifies = "qualifies"
    contextualizes = "contextualizes"


class ResolutionState(str, Enum):
    unresolved = "unresolved"
    under_review = "under-review"
    partially_resolved = "partially-resolved"
    resolved_for_handoff = "resolved-for-handoff"
    preserved_as_irreducible = "preserved-as-irreducible"


class CriterionKind(str, Enum):
    source_independence = "source-independence"
    provenance_completeness = "provenance-completeness"
    temporal_fit = "temporal-fit"
    documentary_integrity = "documentary-integrity"
    identifier_consistency = "identifier-consistency"
    evidence_specificity = "evidence-specificity"
    scope_consistency = "scope-consistency"


class CriterionAssessmentState(str, Enum):
    favors = "favors"
    disfavors = "disfavors"
    mixed = "mixed"
    inconclusive = "inconclusive"


class ResolutionReviewDisposition(str, Enum):
    support = "support"
    reject = "reject"
    defer = "defer"
    insufficient = "insufficient"
    preserve_conflict = "preserve-conflict"


class HandoffTarget(str, Enum):
    identity_resolution = "identity-resolution"
    evidence_validation = "evidence-validation"
    relationship_validation = "relationship-validation"
    manual_review = "manual-review"


class ContradictionResolutionPolicy(BaseModel):
    resolution_policy_id: str = Field(min_length=2, max_length=500)
    minimum_independent_reviewers: int = Field(default=2, ge=1, le=20)
    require_source_provenance: Literal[True] = True
    require_temporal_context: Literal[True] = True
    require_source_independence_accounting: Literal[True] = True
    require_explicit_criterion_assessments: Literal[True] = True
    preserve_disfavored_assertion_lineage: Literal[True] = True
    preserve_unresolved_conflicts: Literal[True] = True
    majority_agreement_can_establish_truth: Literal[False] = False
    source_count_can_establish_truth: Literal[False] = False
    recency_can_establish_truth: Literal[False] = False
    model_confidence_can_establish_truth: Literal[False] = False
    automatic_source_precedence_allowed: Literal[False] = False
    automatic_graph_mutation_allowed: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContradictoryAssertionRecord(BaseModel):
    contradictory_assertion_id: str = Field(min_length=2, max_length=500)
    contradiction_domain: ContradictionDomain
    subject_refs: list[str] = Field(min_length=1)
    object_refs: list[str] = Field(default_factory=list)
    assertion_statement: str = Field(min_length=1, max_length=12000)
    position: AssertionPosition
    source_refs: list[str] = Field(default_factory=list)
    upstream_object_refs: list[str] = Field(min_length=1)
    provenance_refs: list[str] = Field(min_length=1)
    source_independence_groups: list[str] = Field(default_factory=list)
    valid_from: str | None = Field(default=None, max_length=80)
    valid_to: str | None = Field(default=None, max_length=80)
    observed_at: str | None = Field(default=None, max_length=80)
    analytical_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_semantics: str | None = Field(default=None, max_length=2000)
    assertion_is_not_truth_verdict: Literal[True] = True
    confidence_is_not_probability_of_truth: Literal[True] = True
    assertion_does_not_create_graph_edge: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_assertion(self):
        for values, label in (
            (self.subject_refs, "subject_refs"),
            (self.object_refs, "object_refs"),
            (self.source_refs, "source_refs"),
            (self.upstream_object_refs, "upstream_object_refs"),
            (self.provenance_refs, "provenance_refs"),
            (self.source_independence_groups, "source_independence_groups"),
        ):
            _unique(values, label)
        if self.analytical_confidence is not None and not self.confidence_semantics:
            raise ValueError("analytical confidence requires confidence_semantics")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContradictionSet(BaseModel):
    contradiction_set_id: str = Field(min_length=2, max_length=500)
    contradiction_domain: ContradictionDomain
    assertion_refs: list[str] = Field(min_length=2)
    conflict_summary: str = Field(min_length=1, max_length=12000)
    upstream_conflict_refs: list[str] = Field(default_factory=list)
    unresolved_issue_refs: list[str] = Field(default_factory=list)
    resolution_policy_ref: str = Field(min_length=2, max_length=500)
    state: ResolutionState
    created_at: str = Field(min_length=10, max_length=80)
    contradiction_is_not_falsity_verdict: Literal[True] = True
    unresolved_does_not_imply_equal_evidentiary_support: Literal[True] = True
    source_disagreement_is_preserved: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_set(self):
        _unique(self.assertion_refs, "assertion_refs")
        _unique(self.upstream_conflict_refs, "upstream_conflict_refs")
        _unique(self.unresolved_issue_refs, "unresolved_issue_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ResolutionCriterionAssessment(BaseModel):
    criterion_assessment_id: str = Field(min_length=2, max_length=500)
    contradiction_set_ref: str = Field(min_length=2, max_length=500)
    criterion: CriterionKind
    assertion_ref: str = Field(min_length=2, max_length=500)
    assessment_state: CriterionAssessmentState
    basis_refs: list[str] = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=8000)
    assessed_at: str = Field(min_length=10, max_length=80)
    criterion_is_not_truth_test: Literal[True] = True
    criterion_does_not_create_source_precedence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_criterion(self):
        _unique(self.basis_refs, "basis_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContradictionResolutionReview(BaseModel):
    resolution_review_id: str = Field(min_length=2, max_length=500)
    contradiction_set_ref: str = Field(min_length=2, max_length=500)
    reviewer_ref: str = Field(min_length=2, max_length=1000)
    disposition: ResolutionReviewDisposition
    considered_assertion_refs: list[str] = Field(min_length=2)
    considered_criterion_assessment_refs: list[str] = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=10000)
    reviewed_at: str = Field(min_length=10, max_length=80)
    independent_review: Literal[True] = True
    review_is_not_truth_verdict: Literal[True] = True
    review_does_not_mutate_graphs: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_review(self):
        _unique(self.considered_assertion_refs, "considered_assertion_refs")
        _unique(self.considered_criterion_assessment_refs, "considered_criterion_assessment_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContradictionResolutionDecision(BaseModel):
    resolution_decision_id: str = Field(min_length=2, max_length=500)
    contradiction_set_ref: str = Field(min_length=2, max_length=500)
    resolution_policy_ref: str = Field(min_length=2, max_length=500)
    state: ResolutionState
    favored_assertion_refs: list[str] = Field(default_factory=list)
    qualified_assertion_refs: list[str] = Field(default_factory=list)
    preserved_assertion_refs: list[str] = Field(min_length=1)
    criterion_assessment_refs: list[str] = Field(min_length=1)
    review_refs: list[str] = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=12000)
    decided_at: str = Field(min_length=10, max_length=80)
    decision_is_not_truth_verdict: Literal[True] = True
    decision_does_not_delete_source_assertions: Literal[True] = True
    decision_does_not_rewrite_historical_source_state: Literal[True] = True
    decision_does_not_mutate_identity_graph: Literal[True] = True
    decision_does_not_mutate_relationship_graph: Literal[True] = True
    decision_does_not_mutate_evidence_graph: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_decision(self):
        for values, label in (
            (self.favored_assertion_refs, "favored_assertion_refs"),
            (self.qualified_assertion_refs, "qualified_assertion_refs"),
            (self.preserved_assertion_refs, "preserved_assertion_refs"),
            (self.criterion_assessment_refs, "criterion_assessment_refs"),
            (self.review_refs, "review_refs"),
        ):
            _unique(values, label)
        if not set(self.favored_assertion_refs + self.qualified_assertion_refs).issubset(set(self.preserved_assertion_refs)):
            raise ValueError("favored and qualified assertions must remain preserved")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ResolutionSupersessionRecord(BaseModel):
    resolution_supersession_id: str = Field(min_length=2, max_length=500)
    contradiction_set_ref: str = Field(min_length=2, max_length=500)
    superseded_assertion_ref: str = Field(min_length=2, max_length=500)
    replacement_or_qualifying_assertion_ref: str = Field(min_length=2, max_length=500)
    resolution_decision_ref: str = Field(min_length=2, max_length=500)
    supersession_scope: str = Field(min_length=1, max_length=4000)
    provenance_refs: list[str] = Field(min_length=1)
    supersession_does_not_delete_history: Literal[True] = True
    supersession_does_not_make_prior_source_false: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_supersession(self):
        if self.superseded_assertion_ref == self.replacement_or_qualifying_assertion_ref:
            raise ValueError("supersession requires distinct assertion refs")
        _unique(self.provenance_refs, "provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ResolutionHandoff(BaseModel):
    resolution_handoff_id: str = Field(min_length=2, max_length=500)
    contradiction_set_ref: str = Field(min_length=2, max_length=500)
    resolution_decision_ref: str = Field(min_length=2, max_length=500)
    target: HandoffTarget
    target_contract: str = Field(min_length=2, max_length=500)
    object_refs: list[str] = Field(min_length=1)
    unresolved_issue_refs: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1, max_length=8000)
    handoff_is_not_graph_mutation: Literal[True] = True
    downstream_validation_required: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_handoff(self):
        _unique(self.object_refs, "object_refs")
        _unique(self.unresolved_issue_refs, "unresolved_issue_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContradictionResolutionSnapshot(BaseModel):
    resolution_snapshot_id: str = Field(min_length=2, max_length=500)
    multi_hop_reasoning_snapshot_ref: str = Field(min_length=2, max_length=500)
    policy_refs: list[str] = Field(min_length=1)
    contradiction_set_refs: list[str] = Field(min_length=1)
    assertion_refs: list[str] = Field(min_length=2)
    criterion_assessment_refs: list[str] = Field(min_length=1)
    review_refs: list[str] = Field(min_length=1)
    decision_refs: list[str] = Field(min_length=1)
    supersession_refs: list[str] = Field(default_factory=list)
    handoff_refs: list[str] = Field(default_factory=list)
    created_at: str = Field(min_length=10, max_length=80)
    immutable_snapshot: Literal[True] = True
    snapshot_preserves_conflicting_assertions: Literal[True] = True
    snapshot_preserves_resolution_lineage: Literal[True] = True
    snapshot_is_not_truth_verdict: Literal[True] = True
    snapshot_does_not_mutate_graphs: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        for values, label in (
            (self.policy_refs, "policy_refs"),
            (self.contradiction_set_refs, "contradiction_set_refs"),
            (self.assertion_refs, "assertion_refs"),
            (self.criterion_assessment_refs, "criterion_assessment_refs"),
            (self.review_refs, "review_refs"),
            (self.decision_refs, "decision_refs"),
            (self.supersession_refs, "supersession_refs"),
            (self.handoff_refs, "handoff_refs"),
        ):
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContradictoryIdentityRelationshipResolutionBundle(BaseModel):
    multi_hop_research_investigation_graph_reasoning_bundle: MultiHopResearchInvestigationGraphReasoningBundle
    policies: list[ContradictionResolutionPolicy] = Field(min_length=1)
    assertions: list[ContradictoryAssertionRecord] = Field(min_length=2)
    contradiction_sets: list[ContradictionSet] = Field(min_length=1)
    criterion_assessments: list[ResolutionCriterionAssessment] = Field(min_length=1)
    reviews: list[ContradictionResolutionReview] = Field(min_length=1)
    decisions: list[ContradictionResolutionDecision] = Field(min_length=1)
    supersessions: list[ResolutionSupersessionRecord] = Field(default_factory=list)
    handoffs: list[ResolutionHandoff] = Field(default_factory=list)
    snapshots: list[ContradictionResolutionSnapshot] = Field(min_length=1)
    contradiction_is_not_falsity_verdict: Literal[True] = True
    majority_agreement_is_not_truth: Literal[True] = True
    source_count_is_not_truth: Literal[True] = True
    recency_is_not_truth: Literal[True] = True
    model_confidence_is_not_truth: Literal[True] = True
    resolution_preserves_disfavored_assertion_lineage: Literal[True] = True
    unresolved_does_not_imply_equal_evidentiary_support: Literal[True] = True
    identity_graph_mutation_performed: Literal[False] = False
    relationship_graph_mutation_performed: Literal[False] = False
    evidence_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        groups = {
            "policies": [x.resolution_policy_id for x in self.policies],
            "assertions": [x.contradictory_assertion_id for x in self.assertions],
            "contradiction_sets": [x.contradiction_set_id for x in self.contradiction_sets],
            "criterion_assessments": [x.criterion_assessment_id for x in self.criterion_assessments],
            "reviews": [x.resolution_review_id for x in self.reviews],
            "decisions": [x.resolution_decision_id for x in self.decisions],
            "supersessions": [x.resolution_supersession_id for x in self.supersessions],
            "handoffs": [x.resolution_handoff_id for x in self.handoffs],
            "snapshots": [x.resolution_snapshot_id for x in self.snapshots],
        }
        for label, values in groups.items():
            _unique(values, label)
        ids = {k: set(v) for k, v in groups.items()}
        policy_map = {x.resolution_policy_id: x for x in self.policies}
        assertions = {x.contradictory_assertion_id: x for x in self.assertions}
        criteria = {x.criterion_assessment_id: x for x in self.criterion_assessments}
        reviews = {x.resolution_review_id: x for x in self.reviews}
        decisions = {x.resolution_decision_id: x for x in self.decisions}
        sets = {x.contradiction_set_id: x for x in self.contradiction_sets}

        for s in self.contradiction_sets:
            if s.resolution_policy_ref not in ids["policies"]:
                raise ValueError("contradiction set references unknown policy")
            if not set(s.assertion_refs).issubset(ids["assertions"]):
                raise ValueError("contradiction set references unknown assertion")
            domains = {assertions[x].contradiction_domain for x in s.assertion_refs}
            if s.contradiction_domain != ContradictionDomain.mixed and domains != {s.contradiction_domain}:
                raise ValueError("contradiction set domain must match contained assertions")

        for c in self.criterion_assessments:
            if c.contradiction_set_ref not in ids["contradiction_sets"] or c.assertion_ref not in ids["assertions"]:
                raise ValueError("criterion assessment references unknown object")

        for r in self.reviews:
            if r.contradiction_set_ref not in ids["contradiction_sets"]:
                raise ValueError("review references unknown contradiction set")
            if not set(r.considered_assertion_refs).issubset(ids["assertions"]):
                raise ValueError("review references unknown assertion")
            if not set(r.considered_criterion_assessment_refs).issubset(ids["criterion_assessments"]):
                raise ValueError("review references unknown criterion assessment")

        for d in self.decisions:
            if d.contradiction_set_ref not in ids["contradiction_sets"] or d.resolution_policy_ref not in ids["policies"]:
                raise ValueError("decision references unknown set or policy")
            referenced_assertions = set(d.favored_assertion_refs + d.qualified_assertion_refs + d.preserved_assertion_refs)
            if not referenced_assertions.issubset(ids["assertions"]):
                raise ValueError("decision references unknown assertion")
            if not set(d.criterion_assessment_refs).issubset(ids["criterion_assessments"]):
                raise ValueError("decision references unknown criterion")
            if not set(d.review_refs).issubset(ids["reviews"]):
                raise ValueError("decision references unknown review")
            if d.state == ResolutionState.resolved_for_handoff:
                reviewers = {reviews[x].reviewer_ref for x in d.review_refs}
                if len(reviewers) < policy_map[d.resolution_policy_ref].minimum_independent_reviewers:
                    raise ValueError("resolved-for-handoff decision lacks independent reviewers")

        for x in self.supersessions:
            if x.contradiction_set_ref not in ids["contradiction_sets"] or x.resolution_decision_ref not in ids["decisions"]:
                raise ValueError("supersession references unknown set or decision")
            if x.superseded_assertion_ref not in ids["assertions"] or x.replacement_or_qualifying_assertion_ref not in ids["assertions"]:
                raise ValueError("supersession references unknown assertion")

        for h in self.handoffs:
            if h.contradiction_set_ref not in ids["contradiction_sets"] or h.resolution_decision_ref not in ids["decisions"]:
                raise ValueError("handoff references unknown set or decision")

        upstream_snapshot_ids = {x.reasoning_snapshot_id for x in self.multi_hop_research_investigation_graph_reasoning_bundle.snapshots}
        for s in self.snapshots:
            if s.multi_hop_reasoning_snapshot_ref not in upstream_snapshot_ids:
                raise ValueError("snapshot references unknown v3.85 reasoning snapshot")
            checks = (
                (s.policy_refs, ids["policies"]),
                (s.contradiction_set_refs, ids["contradiction_sets"]),
                (s.assertion_refs, ids["assertions"]),
                (s.criterion_assessment_refs, ids["criterion_assessments"]),
                (s.review_refs, ids["reviews"]),
                (s.decision_refs, ids["decisions"]),
                (s.supersession_refs, ids["supersessions"]),
                (s.handoff_refs, ids["handoffs"]),
            )
            if any(not set(refs).issubset(valid) for refs, valid in checks):
                raise ValueError("snapshot contains unresolved reference")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_contradictory_identity_relationship_resolution_bundle() -> ContradictoryIdentityRelationshipResolutionBundle:
    upstream = reference_multi_hop_research_investigation_graph_reasoning_bundle()
    paths = upstream.explainable_connection_paths_evidence_chains_bundle
    network = paths.network_structure_community_motif_bundle
    relationships = network.relationship_discovery_hypothesis_bundle
    documentary = relationships.public_record_documentary_source_bundle
    reconciliation = documentary.cross_source_entity_reconciliation_bundle
    linkage = reconciliation.probabilistic_record_linkage_bundle
    temporal = linkage.temporal_identity_bundle
    identity = temporal.entity_resolution_identity_graph_bundle

    policy = ContradictionResolutionPolicy(
        resolution_policy_id="contradiction-resolution-policy:reference:v1",
        metadata={"synthetic_reference": True},
    )

    entity_a, entity_b = identity.entities[:2]
    candidate = identity.candidate_matches[0]
    recon_conflict = reconciliation.conflicts[0]
    observed_rel = relationships.source_observed_relationships[0]
    hypothesis = relationships.connection_hypotheses[0]
    stop_hypothesis = [x for x in upstream.stopping_decisions if x.stop_reason.value == "unvalidated-hypothesis"][0]
    primary_inference = upstream.inference_steps[0]

    assertions = [
        ContradictoryAssertionRecord(
            contradictory_assertion_id="contradictory-assertion:synthetic:identity-continuity:v1",
            contradiction_domain=ContradictionDomain.identity,
            subject_refs=[entity_a.entity_id, entity_b.entity_id],
            assertion_statement="Independent identity evidence supports treating the two synthetic source records as a candidate continuity match, subject to governed identity resolution rather than automatic merge.",
            position=AssertionPosition.supports,
            source_refs=[x.source_ref for x in identity.identity_evidence_items],
            upstream_object_refs=[candidate.candidate_match_id] + [x.identity_evidence_id for x in identity.identity_evidence_items],
            provenance_refs=[p for x in identity.identity_evidence_items for p in x.provenance_refs],
            source_independence_groups=["identity-group:registry", "identity-group:continuity-filing"],
            analytical_confidence=candidate.match_probability,
            confidence_semantics="upstream model match probability retained only as analytical context; independent evidence and review remain required",
            metadata={"synthetic_reference": True},
        ),
        ContradictoryAssertionRecord(
            contradictory_assertion_id="contradictory-assertion:synthetic:identity-temporal-conflict:v1",
            contradiction_domain=ContradictionDomain.identity,
            subject_refs=[entity_a.entity_id, entity_b.entity_id],
            assertion_statement="A later registry observation changes name, identifier, and validity context, so continuity must remain qualified until the temporal/source conflict is separately resolved.",
            position=AssertionPosition.qualifies,
            source_refs=list(recon_conflict.source_descriptor_refs),
            upstream_object_refs=[recon_conflict.reconciliation_conflict_id],
            provenance_refs=list(recon_conflict.provenance_chain_refs),
            source_independence_groups=["identity-group:later-registry"],
            observed_at="2026-09-30T20:30:00Z",
            metadata={"synthetic_reference": True},
        ),
        ContradictoryAssertionRecord(
            contradictory_assertion_id="contradictory-assertion:synthetic:relationship-bounded-report:v1",
            contradiction_domain=ContradictionDomain.relationship,
            subject_refs=[observed_rel.subject_entity_ref],
            object_refs=[observed_rel.object_entity_ref],
            assertion_statement="The synthetic filing reports a bounded operational association during the represented 2024 interval.",
            position=AssertionPosition.supports,
            source_refs=list(observed_rel.source_refs),
            upstream_object_refs=[observed_rel.source_observed_relationship_id],
            provenance_refs=list(observed_rel.provenance_refs),
            source_independence_groups=["relationship-group:filing"],
            valid_from=observed_rel.valid_from,
            valid_to=observed_rel.valid_to,
            observed_at=observed_rel.observed_at,
            metadata={"synthetic_reference": True},
        ),
        ContradictoryAssertionRecord(
            contradictory_assertion_id="contradictory-assertion:synthetic:relationship-scope-limit:v1",
            contradiction_domain=ContradictionDomain.relationship,
            subject_refs=[hypothesis.subject_entity_ref],
            object_refs=[hypothesis.object_entity_ref],
            assertion_statement="The available reasoning does not establish an unbounded or current relationship beyond the source-bounded hypothesis and therefore stops at the unvalidated-hypothesis boundary.",
            position=AssertionPosition.qualifies,
            source_refs=[],
            upstream_object_refs=[hypothesis.connection_hypothesis_id, stop_hypothesis.reasoning_stopping_decision_id],
            provenance_refs=list(stop_hypothesis.provenance_refs) + list(hypothesis.provenance_refs),
            source_independence_groups=["relationship-group:contextual-review"],
            analytical_confidence=0.48,
            confidence_semantics="synthetic confidence in branch characterization only; not probability that the relationship exists or does not exist",
            metadata={"synthetic_reference": True},
        ),
    ]

    identity_set = ContradictionSet(
        contradiction_set_id="contradiction-set:synthetic:identity-continuity:v1",
        contradiction_domain=ContradictionDomain.identity,
        assertion_refs=[assertions[0].contradictory_assertion_id, assertions[1].contradictory_assertion_id],
        conflict_summary="Candidate identity continuity is supported by independent evidence but qualified by a later temporal/source registry conflict; the conflict is preserved rather than auto-resolved by model score, source count, or recency.",
        upstream_conflict_refs=[recon_conflict.reconciliation_conflict_id, upstream.contradiction_propagations[0].contradiction_propagation_id],
        unresolved_issue_refs=[recon_conflict.reconciliation_conflict_id],
        resolution_policy_ref=policy.resolution_policy_id,
        state=ResolutionState.partially_resolved,
        created_at="2026-09-30T20:31:00Z",
        metadata={"synthetic_reference": True},
    )
    relationship_set = ContradictionSet(
        contradiction_set_id="contradiction-set:synthetic:relationship-scope:v1",
        contradiction_domain=ContradictionDomain.relationship,
        assertion_refs=[assertions[2].contradictory_assertion_id, assertions[3].contradictory_assertion_id],
        conflict_summary="A source-bound 2024 relationship observation is preserved while a broader/current interpretation remains unsupported; resolution narrows scope rather than turning the source observation into a timeless graph fact.",
        upstream_conflict_refs=[hypothesis.connection_hypothesis_id],
        unresolved_issue_refs=[hypothesis.connection_hypothesis_id],
        resolution_policy_ref=policy.resolution_policy_id,
        state=ResolutionState.resolved_for_handoff,
        created_at="2026-09-30T20:32:00Z",
        metadata={"synthetic_reference": True},
    )

    criteria = [
        ResolutionCriterionAssessment(
            criterion_assessment_id="criterion:synthetic:identity-source-independence:v1",
            contradiction_set_ref=identity_set.contradiction_set_id,
            criterion=CriterionKind.source_independence,
            assertion_ref=assertions[0].contradictory_assertion_id,
            assessment_state=CriterionAssessmentState.favors,
            basis_refs=[x.identity_evidence_id for x in identity.identity_evidence_items],
            rationale="Two independently provenance-bearing identity evidence items support continuity; source independence is a criterion, not a truth test.",
            assessed_at="2026-09-30T20:33:00Z",
        ),
        ResolutionCriterionAssessment(
            criterion_assessment_id="criterion:synthetic:identity-temporal-fit:v1",
            contradiction_set_ref=identity_set.contradiction_set_id,
            criterion=CriterionKind.temporal_fit,
            assertion_ref=assertions[1].contradictory_assertion_id,
            assessment_state=CriterionAssessmentState.mixed,
            basis_refs=[recon_conflict.reconciliation_conflict_id],
            rationale="The later registry snapshot requires explicit temporal qualification; recency alone cannot override earlier provenance-bearing observations.",
            assessed_at="2026-09-30T20:34:00Z",
        ),
        ResolutionCriterionAssessment(
            criterion_assessment_id="criterion:synthetic:relationship-scope:v1",
            contradiction_set_ref=relationship_set.contradiction_set_id,
            criterion=CriterionKind.scope_consistency,
            assertion_ref=assertions[2].contradictory_assertion_id,
            assessment_state=CriterionAssessmentState.favors,
            basis_refs=[observed_rel.source_observed_relationship_id, hypothesis.connection_hypothesis_id],
            rationale="The documented observation is explicitly bounded to 2024, while the broader hypothesis remains a validation candidate; preserving the bounded scope avoids overstatement.",
            assessed_at="2026-09-30T20:35:00Z",
        ),
        ResolutionCriterionAssessment(
            criterion_assessment_id="criterion:synthetic:relationship-provenance:v1",
            contradiction_set_ref=relationship_set.contradiction_set_id,
            criterion=CriterionKind.provenance_completeness,
            assertion_ref=assertions[3].contradictory_assertion_id,
            assessment_state=CriterionAssessmentState.favors,
            basis_refs=[stop_hypothesis.reasoning_stopping_decision_id, primary_inference.reasoning_inference_step_id],
            rationale="The reasoning trace explicitly stops at the unvalidated-hypothesis boundary, so a broader/current relationship claim remains qualified.",
            assessed_at="2026-09-30T20:36:00Z",
        ),
    ]

    reviews = [
        ContradictionResolutionReview(
            resolution_review_id="contradiction-review:synthetic:identity:a:v1",
            contradiction_set_ref=identity_set.contradiction_set_id,
            reviewer_ref="reviewer:synthetic:contradiction-identity-a",
            disposition=ResolutionReviewDisposition.defer,
            considered_assertion_refs=list(identity_set.assertion_refs),
            considered_criterion_assessment_refs=[criteria[0].criterion_assessment_id, criteria[1].criterion_assessment_id],
            rationale="Preserve continuity support while deferring final identity resolution until the temporal/source conflict is independently reviewed.",
            reviewed_at="2026-09-30T20:37:00Z",
        ),
        ContradictionResolutionReview(
            resolution_review_id="contradiction-review:synthetic:identity:b:v1",
            contradiction_set_ref=identity_set.contradiction_set_id,
            reviewer_ref="reviewer:synthetic:contradiction-identity-b",
            disposition=ResolutionReviewDisposition.preserve_conflict,
            considered_assertion_refs=list(identity_set.assertion_refs),
            considered_criterion_assessment_refs=[criteria[0].criterion_assessment_id, criteria[1].criterion_assessment_id],
            rationale="The later registry conflict is material and should remain visible rather than being overridden by the earlier match probability or evidence count.",
            reviewed_at="2026-09-30T20:38:00Z",
        ),
        ContradictionResolutionReview(
            resolution_review_id="contradiction-review:synthetic:relationship:a:v1",
            contradiction_set_ref=relationship_set.contradiction_set_id,
            reviewer_ref="reviewer:synthetic:contradiction-relationship-a",
            disposition=ResolutionReviewDisposition.support,
            considered_assertion_refs=list(relationship_set.assertion_refs),
            considered_criterion_assessment_refs=[criteria[2].criterion_assessment_id, criteria[3].criterion_assessment_id],
            rationale="Support a bounded 2024 relationship handoff while retaining the broader/current scope limitation.",
            reviewed_at="2026-09-30T20:39:00Z",
        ),
        ContradictionResolutionReview(
            resolution_review_id="contradiction-review:synthetic:relationship:b:v1",
            contradiction_set_ref=relationship_set.contradiction_set_id,
            reviewer_ref="reviewer:synthetic:contradiction-relationship-b",
            disposition=ResolutionReviewDisposition.support,
            considered_assertion_refs=list(relationship_set.assertion_refs),
            considered_criterion_assessment_refs=[criteria[2].criterion_assessment_id, criteria[3].criterion_assessment_id],
            rationale="Independent review supports preserving the source-bounded observation and preventing scope expansion beyond the validated evidence context.",
            reviewed_at="2026-09-30T20:40:00Z",
        ),
    ]

    decisions = [
        ContradictionResolutionDecision(
            resolution_decision_id="contradiction-decision:synthetic:identity:v1",
            contradiction_set_ref=identity_set.contradiction_set_id,
            resolution_policy_ref=policy.resolution_policy_id,
            state=ResolutionState.partially_resolved,
            favored_assertion_refs=[assertions[0].contradictory_assertion_id],
            qualified_assertion_refs=[assertions[1].contradictory_assertion_id],
            preserved_assertion_refs=list(identity_set.assertion_refs),
            criterion_assessment_refs=[criteria[0].criterion_assessment_id, criteria[1].criterion_assessment_id],
            review_refs=[reviews[0].resolution_review_id, reviews[1].resolution_review_id],
            rationale="Identity continuity remains supported for governed review, but the later temporal/source conflict remains unresolved and visible; no merge or equivalence edge is performed.",
            decided_at="2026-09-30T20:41:00Z",
            metadata={"synthetic_reference": True},
        ),
        ContradictionResolutionDecision(
            resolution_decision_id="contradiction-decision:synthetic:relationship:v1",
            contradiction_set_ref=relationship_set.contradiction_set_id,
            resolution_policy_ref=policy.resolution_policy_id,
            state=ResolutionState.resolved_for_handoff,
            favored_assertion_refs=[assertions[2].contradictory_assertion_id],
            qualified_assertion_refs=[assertions[3].contradictory_assertion_id],
            preserved_assertion_refs=list(relationship_set.assertion_refs),
            criterion_assessment_refs=[criteria[2].criterion_assessment_id, criteria[3].criterion_assessment_id],
            review_refs=[reviews[2].resolution_review_id, reviews[3].resolution_review_id],
            rationale="The resolution narrows the relationship claim to the documented 2024 scope and hands it to separate evidence/relationship validation; it does not create a canonical relationship edge.",
            decided_at="2026-09-30T20:42:00Z",
            metadata={"synthetic_reference": True},
        ),
    ]

    supersession = ResolutionSupersessionRecord(
        resolution_supersession_id="resolution-supersession:synthetic:relationship-scope:v1",
        contradiction_set_ref=relationship_set.contradiction_set_id,
        superseded_assertion_ref=assertions[3].contradictory_assertion_id,
        replacement_or_qualifying_assertion_ref=assertions[2].contradictory_assertion_id,
        resolution_decision_ref=decisions[1].resolution_decision_id,
        supersession_scope="For downstream handoff, replace any unbounded/current reading with the source-bounded 2024 formulation while preserving the broader assertion as historical analytical context.",
        provenance_refs=["provenance:synthetic:resolution-supersession:relationship-scope:v1"],
        metadata={"synthetic_reference": True},
    )

    handoffs = [
        ResolutionHandoff(
            resolution_handoff_id="resolution-handoff:synthetic:identity:v1",
            contradiction_set_ref=identity_set.contradiction_set_id,
            resolution_decision_ref=decisions[0].resolution_decision_id,
            target=HandoffTarget.identity_resolution,
            target_contract="sc.core.entity-resolution-identity-graph-foundation.v1",
            object_refs=[candidate.candidate_match_id, recon_conflict.reconciliation_conflict_id],
            unresolved_issue_refs=[recon_conflict.reconciliation_conflict_id],
            rationale="Return the partially resolved identity contradiction to governed identity resolution with the temporal conflict preserved.",
        ),
        ResolutionHandoff(
            resolution_handoff_id="resolution-handoff:synthetic:relationship:v1",
            contradiction_set_ref=relationship_set.contradiction_set_id,
            resolution_decision_ref=decisions[1].resolution_decision_id,
            target=HandoffTarget.relationship_validation,
            target_contract="sc.core.relationship-discovery-connection-hypothesis.v1",
            object_refs=[observed_rel.source_observed_relationship_id, hypothesis.connection_hypothesis_id],
            unresolved_issue_refs=[hypothesis.connection_hypothesis_id],
            rationale="Hand off only the bounded relationship formulation for separate validation while retaining the unvalidated hypothesis and its scope qualification.",
        ),
    ]

    snapshot = ContradictionResolutionSnapshot(
        resolution_snapshot_id="contradiction-resolution-snapshot:synthetic:2026-09-30:v1",
        multi_hop_reasoning_snapshot_ref=upstream.snapshots[0].reasoning_snapshot_id,
        policy_refs=[policy.resolution_policy_id],
        contradiction_set_refs=[identity_set.contradiction_set_id, relationship_set.contradiction_set_id],
        assertion_refs=[x.contradictory_assertion_id for x in assertions],
        criterion_assessment_refs=[x.criterion_assessment_id for x in criteria],
        review_refs=[x.resolution_review_id for x in reviews],
        decision_refs=[x.resolution_decision_id for x in decisions],
        supersession_refs=[supersession.resolution_supersession_id],
        handoff_refs=[x.resolution_handoff_id for x in handoffs],
        created_at="2026-09-30T20:43:00Z",
        metadata={"synthetic_reference": True},
    )

    return ContradictoryIdentityRelationshipResolutionBundle(
        multi_hop_research_investigation_graph_reasoning_bundle=upstream,
        policies=[policy],
        assertions=assertions,
        contradiction_sets=[identity_set, relationship_set],
        criterion_assessments=criteria,
        reviews=reviews,
        decisions=decisions,
        supersessions=[supersession],
        handoffs=handoffs,
        snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    b = reference_contradictory_identity_relationship_resolution_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contracts": [
            "sc.core.multi-hop-research-investigation-graph-reasoning.v1",
            "sc.core.explainable-connection-paths-evidence-chains.v1",
            "sc.core.relationship-discovery-connection-hypothesis.v1",
            "sc.core.public-record-documentary-source-object-model.v1",
            "sc.core.cross-source-entity-reconciliation-identity-provenance.v1",
            "sc.core.probabilistic-record-linkage-entity-matching.v1",
            "sc.core.temporal-identity-alias-name-variant-intelligence.v1",
            "sc.core.entity-resolution-identity-graph-foundation.v1",
            "sc.core.evidence-graph-neural-analysis-validation.v1",
        ],
        "object_types": [
            "ContradictionResolutionPolicy",
            "ContradictoryAssertionRecord",
            "ContradictionSet",
            "ResolutionCriterionAssessment",
            "ContradictionResolutionReview",
            "ContradictionResolutionDecision",
            "ResolutionSupersessionRecord",
            "ResolutionHandoff",
            "ContradictionResolutionSnapshot",
            "ContradictoryIdentityRelationshipResolutionBundle",
        ],
        "principles": {
            "contradiction_is_not_falsity_verdict": True,
            "majority_agreement_is_not_truth": True,
            "source_count_is_not_truth": True,
            "recency_is_not_truth": True,
            "model_confidence_is_not_truth": True,
            "resolution_preserves_disfavored_assertion_lineage": True,
            "unresolved_does_not_imply_equal_evidentiary_support": True,
            "resolution_is_scope_and_provenance_aware": True,
            "source_disagreement_remains_auditable": True,
        },
        "boundaries": {
            "runtime_may_auto_prioritize_sources": False,
            "runtime_may_auto_merge_identity": False,
            "runtime_may_create_relationship_edge": False,
            "runtime_may_create_evidence_edge": False,
            "runtime_may_delete_disfavored_assertions": False,
            "v386_resolution_is_truth_verdict": False,
            "identity_graph_mutation_performed": False,
            "relationship_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
        },
        "reference": {
            "assertions": len(b.assertions),
            "contradiction_sets": len(b.contradiction_sets),
            "criterion_assessments": len(b.criterion_assessments),
            "reviews": len(b.reviews),
            "decisions": len(b.decisions),
            "supersessions": len(b.supersessions),
            "handoffs": len(b.handoffs),
            "identity_set_state": b.contradiction_sets[0].state.value,
            "relationship_set_state": b.contradiction_sets[1].state.value,
            "identity_graph_mutation_performed": b.identity_graph_mutation_performed,
            "relationship_graph_mutation_performed": b.relationship_graph_mutation_performed,
            "evidence_graph_mutation_performed": b.evidence_graph_mutation_performed,
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
