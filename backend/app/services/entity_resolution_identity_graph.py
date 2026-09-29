from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .evidence_graph_neural_validation import (
    EvidenceGraphNeuralValidationBundle,
    reference_evidence_graph_neural_validation_bundle,
)

CORE_RELEASE = "3.77.0"
CONTRACT_VERSION = "sc.core.entity-resolution-identity-graph-foundation.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class EntityKind(str, Enum):
    person = "person"
    organization = "organization"
    place = "place"
    event = "event"
    document = "document"
    dataset = "dataset"
    project = "project"
    artifact = "artifact"
    concept = "concept"
    other = "other"


class AliasKind(str, Enum):
    preferred = "preferred"
    legal = "legal"
    former = "former"
    abbreviation = "abbreviation"
    transliteration = "transliteration"
    translation = "translation"
    historical = "historical"
    source_supplied = "source-supplied"
    other = "other"


class IdentifierState(str, Enum):
    asserted = "asserted"
    verified = "verified"
    disputed = "disputed"
    contradicted = "contradicted"
    superseded = "superseded"


class SourceAssertionState(str, Enum):
    asserted = "asserted"
    supported = "supported"
    disputed = "disputed"
    rejected = "rejected"


class IdentityEvidenceKind(str, Enum):
    official_identifier = "official-identifier"
    registry_record = "registry-record"
    source_document = "source-document"
    archival_record = "archival-record"
    direct_assertion = "direct-assertion"
    other = "other"


class CandidateMatchState(str, Enum):
    proposed = "proposed"
    under_review = "under-review"
    supported = "supported"
    rejected = "rejected"
    disputed = "disputed"


class IdentityReviewDisposition(str, Enum):
    support = "support"
    reject = "reject"
    disputed = "disputed"
    insufficient = "insufficient"


class IdentityMutationKind(str, Enum):
    merge = "merge"
    split = "split"


class IdentityMutationDecision(str, Enum):
    authorized = "authorized"
    denied = "denied"
    deferred = "deferred"


class EntityAlias(BaseModel):
    alias_id: str = Field(min_length=2, max_length=500)
    entity_ref: str = Field(min_length=2, max_length=1000)
    value: str = Field(min_length=1, max_length=2000)
    alias_kind: AliasKind
    language_tag: str | None = Field(default=None, max_length=80)
    script_code: str | None = Field(default=None, max_length=80)
    valid_from: str | None = Field(default=None, max_length=80)
    valid_to: str | None = Field(default=None, max_length=80)
    source_refs: list[str] = Field(min_length=1)
    provenance_refs: list[str] = Field(min_length=1)
    alias_is_not_identity_proof: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_alias(self):
        _unique(self.source_refs, "source_refs")
        _unique(self.provenance_refs, "provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ExternalIdentifierAssertion(BaseModel):
    identifier_assertion_id: str = Field(min_length=2, max_length=500)
    entity_ref: str = Field(min_length=2, max_length=1000)
    namespace: str = Field(min_length=1, max_length=300)
    identifier_value: str = Field(min_length=1, max_length=1000)
    issuing_authority_ref: str | None = Field(default=None, max_length=1000)
    source_refs: list[str] = Field(min_length=1)
    provenance_refs: list[str] = Field(min_length=1)
    verification_state: IdentifierState = IdentifierState.asserted
    verified_by_refs: list[str] = Field(default_factory=list)
    shared_identifier_is_not_automatically_same_entity: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_identifier(self):
        _unique(self.source_refs, "source_refs")
        _unique(self.provenance_refs, "provenance_refs")
        _unique(self.verified_by_refs, "verified_by_refs")
        if self.verification_state == IdentifierState.verified and not self.verified_by_refs:
            raise ValueError("verified identifier requires verified_by_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SourceEntityIdentityAssertion(BaseModel):
    source_identity_assertion_id: str = Field(min_length=2, max_length=500)
    source_ref: str = Field(min_length=2, max_length=1000)
    source_entity_key: str = Field(min_length=1, max_length=1000)
    asserted_entity_ref: str = Field(min_length=2, max_length=1000)
    asserted_name: str = Field(min_length=1, max_length=2000)
    alias_refs: list[str] = Field(default_factory=list)
    identifier_assertion_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(min_length=1)
    assertion_state: SourceAssertionState = SourceAssertionState.asserted
    source_assertion_is_not_canonical_identity: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_source_assertion(self):
        for values, label in (
            (self.alias_refs, "alias_refs"),
            (self.identifier_assertion_refs, "identifier_assertion_refs"),
            (self.provenance_refs, "provenance_refs"),
        ):
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CanonicalEntityRecord(BaseModel):
    entity_id: str = Field(min_length=2, max_length=1000)
    entity_kind: EntityKind
    canonical_label: str = Field(min_length=1, max_length=2000)
    alias_refs: list[str] = Field(default_factory=list)
    identifier_assertion_refs: list[str] = Field(default_factory=list)
    source_identity_assertion_refs: list[str] = Field(default_factory=list)
    active: bool = True
    superseded_by_entity_ref: str | None = Field(default=None, max_length=1000)
    lineage_refs: list[str] = Field(default_factory=list)
    canonical_record_is_governed_identity_container: Literal[True] = True
    canonical_record_does_not_imply_all_sources_agree: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_entity(self):
        for values, label in (
            (self.alias_refs, "alias_refs"),
            (self.identifier_assertion_refs, "identifier_assertion_refs"),
            (self.source_identity_assertion_refs, "source_identity_assertion_refs"),
            (self.lineage_refs, "lineage_refs"),
        ):
            _unique(values, label)
        if not self.active and not self.superseded_by_entity_ref:
            raise ValueError("inactive canonical entity requires superseded_by_entity_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class IdentityEvidenceItem(BaseModel):
    identity_evidence_id: str = Field(min_length=2, max_length=500)
    evidence_kind: IdentityEvidenceKind
    source_ref: str = Field(min_length=2, max_length=1000)
    provenance_refs: list[str] = Field(min_length=1)
    relevant_entity_refs: list[str] = Field(min_length=1)
    relevant_identifier_assertion_refs: list[str] = Field(default_factory=list)
    relevant_source_assertion_refs: list[str] = Field(default_factory=list)
    independent_of_match_model: Literal[True] = True
    model_score_is_not_identity_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_evidence(self):
        for values, label in (
            (self.provenance_refs, "provenance_refs"),
            (self.relevant_entity_refs, "relevant_entity_refs"),
            (self.relevant_identifier_assertion_refs, "relevant_identifier_assertion_refs"),
            (self.relevant_source_assertion_refs, "relevant_source_assertion_refs"),
        ):
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EntityResolutionPolicy(BaseModel):
    resolution_policy_id: str = Field(min_length=2, max_length=500)
    minimum_identity_evidence_items_for_merge: int = Field(default=2, ge=1, le=100)
    minimum_independent_reviewers_for_merge: int = Field(default=2, ge=1, le=20)
    require_identifier_provenance: Literal[True] = True
    require_source_assertion_provenance: Literal[True] = True
    require_contradictory_identity_evidence_review: Literal[True] = True
    require_human_or_governed_independent_review: Literal[True] = True
    match_probability_can_establish_identity: Literal[False] = False
    shared_name_can_establish_identity: Literal[False] = False
    shared_identifier_can_bypass_review: Literal[False] = False
    automatic_merge_allowed: Literal[False] = False
    automatic_split_allowed: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CandidateEntityMatch(BaseModel):
    candidate_match_id: str = Field(min_length=2, max_length=500)
    left_entity_ref: str = Field(min_length=2, max_length=1000)
    right_entity_ref: str = Field(min_length=2, max_length=1000)
    resolution_policy_ref: str = Field(min_length=2, max_length=500)
    resolver_ref: str = Field(min_length=2, max_length=1000)
    match_score: float | None = None
    match_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    feature_refs: list[str] = Field(default_factory=list)
    source_identity_assertion_refs: list[str] = Field(default_factory=list)
    identity_evidence_refs: list[str] = Field(default_factory=list)
    contradicting_identity_evidence_refs: list[str] = Field(default_factory=list)
    review_refs: list[str] = Field(default_factory=list)
    state: CandidateMatchState = CandidateMatchState.proposed
    is_identity_fact: Literal[False] = False
    is_canonical_equivalence_edge: Literal[False] = False
    match_probability_is_not_identity_fact: Literal[True] = True
    same_name_is_not_identity_fact: Literal[True] = True
    automated_resolution_may_not_merge_entities: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_match(self):
        if self.left_entity_ref == self.right_entity_ref:
            raise ValueError("candidate entity match requires two distinct entities")
        for values, label in (
            (self.feature_refs, "feature_refs"),
            (self.source_identity_assertion_refs, "source_identity_assertion_refs"),
            (self.identity_evidence_refs, "identity_evidence_refs"),
            (self.contradicting_identity_evidence_refs, "contradicting_identity_evidence_refs"),
            (self.review_refs, "review_refs"),
        ):
            _unique(values, label)
        if self.state == CandidateMatchState.supported and not self.review_refs:
            raise ValueError("supported candidate match requires review_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class IndependentIdentityReview(BaseModel):
    identity_review_id: str = Field(min_length=2, max_length=500)
    candidate_match_ref: str = Field(min_length=2, max_length=500)
    reviewer_ref: str = Field(min_length=2, max_length=1000)
    disposition: IdentityReviewDisposition
    supporting_identity_evidence_refs: list[str] = Field(default_factory=list)
    contradicting_identity_evidence_refs: list[str] = Field(default_factory=list)
    considered_match_signal_refs: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1, max_length=8000)
    reviewed_at: str | None = Field(default=None, max_length=80)
    reviewer_independent_of_match_model: Literal[True] = True
    model_scores_are_context_not_identity_evidence: Literal[True] = True
    review_does_not_itself_merge_entities: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_review(self):
        for values, label in (
            (self.supporting_identity_evidence_refs, "supporting_identity_evidence_refs"),
            (self.contradicting_identity_evidence_refs, "contradicting_identity_evidence_refs"),
            (self.considered_match_signal_refs, "considered_match_signal_refs"),
        ):
            _unique(values, label)
        if self.disposition == IdentityReviewDisposition.support and not self.supporting_identity_evidence_refs:
            raise ValueError("supporting review requires identity evidence")
        if self.disposition == IdentityReviewDisposition.reject and not self.contradicting_identity_evidence_refs:
            raise ValueError("reject review requires contradicting identity evidence")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class IdentityMutationAuthorization(BaseModel):
    identity_mutation_authorization_id: str = Field(min_length=2, max_length=500)
    operation: IdentityMutationKind
    decision: IdentityMutationDecision
    resolution_policy_ref: str = Field(min_length=2, max_length=500)
    candidate_match_ref: str | None = Field(default=None, max_length=500)
    source_entity_refs: list[str] = Field(min_length=1)
    proposed_result_entity_refs: list[str] = Field(min_length=1)
    supporting_identity_evidence_refs: list[str] = Field(default_factory=list)
    contradicting_identity_evidence_refs: list[str] = Field(default_factory=list)
    reviewer_refs: list[str] = Field(default_factory=list)
    identifier_provenance_verified: bool
    source_assertion_provenance_verified: bool
    contradictory_evidence_review_completed: bool
    independent_review_completed: bool
    model_outputs_counted_as_identity_evidence: Literal[False] = False
    model_outputs_can_authorize_identity_mutation: Literal[False] = False
    actual_identity_graph_mutation_performed: Literal[False] = False
    authorization_requires_downstream_audited_mutation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_authorization(self):
        for values, label in (
            (self.source_entity_refs, "source_entity_refs"),
            (self.proposed_result_entity_refs, "proposed_result_entity_refs"),
            (self.supporting_identity_evidence_refs, "supporting_identity_evidence_refs"),
            (self.contradicting_identity_evidence_refs, "contradicting_identity_evidence_refs"),
            (self.reviewer_refs, "reviewer_refs"),
        ):
            _unique(values, label)
        if self.operation == IdentityMutationKind.merge:
            if len(self.source_entity_refs) < 2 or len(self.proposed_result_entity_refs) != 1:
                raise ValueError("merge authorization requires at least two source entities and one proposed result")
            if not self.candidate_match_ref:
                raise ValueError("merge authorization requires candidate_match_ref")
        if self.operation == IdentityMutationKind.split:
            if len(self.source_entity_refs) != 1 or len(self.proposed_result_entity_refs) < 2:
                raise ValueError("split authorization requires one source entity and at least two proposed results")
        if self.decision == IdentityMutationDecision.authorized:
            if not self.supporting_identity_evidence_refs or not self.reviewer_refs:
                raise ValueError("authorized identity mutation requires supporting evidence and reviewers")
            if not (
                self.identifier_provenance_verified
                and self.source_assertion_provenance_verified
                and self.contradictory_evidence_review_completed
                and self.independent_review_completed
            ):
                raise ValueError("authorized identity mutation requires all governance gates")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class IdentityResolutionAuditRecord(BaseModel):
    identity_audit_id: str = Field(min_length=2, max_length=500)
    event_type: str = Field(min_length=1, max_length=200)
    actor_ref: str = Field(min_length=2, max_length=1000)
    candidate_match_ref: str | None = Field(default=None, max_length=500)
    mutation_authorization_ref: str | None = Field(default=None, max_length=500)
    occurred_at: str = Field(min_length=10, max_length=80)
    input_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_fingerprint_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    append_only_audit_event: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_audit(self):
        if not self.candidate_match_ref and not self.mutation_authorization_ref:
            raise ValueError("identity audit must reference a candidate match or mutation authorization")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EntityIdentityGraphSnapshot(BaseModel):
    identity_graph_snapshot_id: str = Field(min_length=2, max_length=500)
    entity_refs: list[str] = Field(min_length=1)
    alias_refs: list[str] = Field(default_factory=list)
    identifier_assertion_refs: list[str] = Field(default_factory=list)
    source_identity_assertion_refs: list[str] = Field(default_factory=list)
    candidate_match_refs: list[str] = Field(default_factory=list)
    mutation_authorization_refs: list[str] = Field(default_factory=list)
    created_at: str = Field(min_length=10, max_length=80)
    immutable_snapshot: Literal[True] = True
    candidate_matches_are_not_canonical_equivalence_edges: Literal[True] = True
    identity_graph_is_distinct_from_evidence_graph: Literal[True] = True
    authorized_mutation_is_not_applied_in_snapshot: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        for values, label in (
            (self.entity_refs, "entity_refs"),
            (self.alias_refs, "alias_refs"),
            (self.identifier_assertion_refs, "identifier_assertion_refs"),
            (self.source_identity_assertion_refs, "source_identity_assertion_refs"),
            (self.candidate_match_refs, "candidate_match_refs"),
            (self.mutation_authorization_refs, "mutation_authorization_refs"),
        ):
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EntityResolutionIdentityGraphBundle(BaseModel):
    evidence_graph_neural_validation_bundle: EvidenceGraphNeuralValidationBundle
    aliases: list[EntityAlias] = Field(min_length=1)
    identifier_assertions: list[ExternalIdentifierAssertion] = Field(min_length=1)
    source_identity_assertions: list[SourceEntityIdentityAssertion] = Field(min_length=1)
    entities: list[CanonicalEntityRecord] = Field(min_length=1)
    identity_evidence_items: list[IdentityEvidenceItem] = Field(min_length=1)
    resolution_policies: list[EntityResolutionPolicy] = Field(min_length=1)
    candidate_matches: list[CandidateEntityMatch] = Field(min_length=1)
    identity_reviews: list[IndependentIdentityReview] = Field(min_length=1)
    mutation_authorizations: list[IdentityMutationAuthorization] = Field(min_length=1)
    audit_records: list[IdentityResolutionAuditRecord] = Field(min_length=1)
    identity_graph_snapshots: list[EntityIdentityGraphSnapshot] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        groups = (
            (self.aliases, "aliases", "alias_id"),
            (self.identifier_assertions, "identifier_assertions", "identifier_assertion_id"),
            (self.source_identity_assertions, "source_identity_assertions", "source_identity_assertion_id"),
            (self.entities, "entities", "entity_id"),
            (self.identity_evidence_items, "identity_evidence_items", "identity_evidence_id"),
            (self.resolution_policies, "resolution_policies", "resolution_policy_id"),
            (self.candidate_matches, "candidate_matches", "candidate_match_id"),
            (self.identity_reviews, "identity_reviews", "identity_review_id"),
            (self.mutation_authorizations, "mutation_authorizations", "identity_mutation_authorization_id"),
            (self.audit_records, "audit_records", "identity_audit_id"),
            (self.identity_graph_snapshots, "identity_graph_snapshots", "identity_graph_snapshot_id"),
        )
        for values, label, attr in groups:
            _unique([getattr(x, attr) for x in values], label)

        entity_map = {x.entity_id: x for x in self.entities}
        alias_map = {x.alias_id: x for x in self.aliases}
        identifier_map = {x.identifier_assertion_id: x for x in self.identifier_assertions}
        source_map = {x.source_identity_assertion_id: x for x in self.source_identity_assertions}
        evidence_map = {x.identity_evidence_id: x for x in self.identity_evidence_items}
        policy_map = {x.resolution_policy_id: x for x in self.resolution_policies}
        match_map = {x.candidate_match_id: x for x in self.candidate_matches}
        review_map = {x.identity_review_id: x for x in self.identity_reviews}
        auth_map = {x.identity_mutation_authorization_id: x for x in self.mutation_authorizations}

        for alias in self.aliases:
            if alias.entity_ref not in entity_map:
                raise ValueError("alias entity_ref must resolve")
        for identifier in self.identifier_assertions:
            if identifier.entity_ref not in entity_map:
                raise ValueError("identifier entity_ref must resolve")
        for assertion in self.source_identity_assertions:
            if assertion.asserted_entity_ref not in entity_map:
                raise ValueError("source identity assertion entity_ref must resolve")
            if any(x not in alias_map for x in assertion.alias_refs):
                raise ValueError("source identity assertion alias_refs must resolve")
            if any(x not in identifier_map for x in assertion.identifier_assertion_refs):
                raise ValueError("source identity assertion identifier refs must resolve")

        for entity in self.entities:
            if any(x not in alias_map for x in entity.alias_refs):
                raise ValueError("entity alias refs must resolve")
            if any(x not in identifier_map for x in entity.identifier_assertion_refs):
                raise ValueError("entity identifier refs must resolve")
            if any(x not in source_map for x in entity.source_identity_assertion_refs):
                raise ValueError("entity source identity assertion refs must resolve")
            if entity.superseded_by_entity_ref and entity.superseded_by_entity_ref not in entity_map:
                raise ValueError("superseded_by_entity_ref must resolve")

        for evidence in self.identity_evidence_items:
            if any(x not in entity_map for x in evidence.relevant_entity_refs):
                raise ValueError("identity evidence entity refs must resolve")
            if any(x not in identifier_map for x in evidence.relevant_identifier_assertion_refs):
                raise ValueError("identity evidence identifier refs must resolve")
            if any(x not in source_map for x in evidence.relevant_source_assertion_refs):
                raise ValueError("identity evidence source assertion refs must resolve")

        for match in self.candidate_matches:
            if match.left_entity_ref not in entity_map or match.right_entity_ref not in entity_map:
                raise ValueError("candidate entity refs must resolve")
            if match.resolution_policy_ref not in policy_map:
                raise ValueError("candidate resolution policy must resolve")
            if any(x not in source_map for x in match.source_identity_assertion_refs):
                raise ValueError("candidate source identity assertions must resolve")
            if any(x not in evidence_map for x in match.identity_evidence_refs + match.contradicting_identity_evidence_refs):
                raise ValueError("candidate identity evidence refs must resolve")
            if any(x not in review_map for x in match.review_refs):
                raise ValueError("candidate review refs must resolve")

        for review in self.identity_reviews:
            if review.candidate_match_ref not in match_map:
                raise ValueError("identity review candidate match must resolve")
            match = match_map[review.candidate_match_ref]
            if any(x not in match.identity_evidence_refs for x in review.supporting_identity_evidence_refs):
                raise ValueError("review supporting evidence must belong to candidate")
            if any(x not in match.contradicting_identity_evidence_refs for x in review.contradicting_identity_evidence_refs):
                raise ValueError("review contradicting evidence must belong to candidate")

        for auth in self.mutation_authorizations:
            if auth.resolution_policy_ref not in policy_map:
                raise ValueError("mutation authorization policy must resolve")
            policy = policy_map[auth.resolution_policy_ref]
            if auth.candidate_match_ref and auth.candidate_match_ref not in match_map:
                raise ValueError("mutation authorization candidate match must resolve")
            if any(x not in entity_map for x in auth.source_entity_refs):
                raise ValueError("mutation authorization source entities must resolve")
            if any(x not in evidence_map for x in auth.supporting_identity_evidence_refs + auth.contradicting_identity_evidence_refs):
                raise ValueError("mutation authorization identity evidence refs must resolve")
            if any(x not in review_map for x in auth.reviewer_refs):
                raise ValueError("mutation authorization reviewer refs must resolve")
            if auth.decision == IdentityMutationDecision.authorized:
                if len(auth.supporting_identity_evidence_refs) < policy.minimum_identity_evidence_items_for_merge:
                    raise ValueError("authorized mutation does not satisfy minimum identity evidence")
                reviewers = {review_map[x].reviewer_ref for x in auth.reviewer_refs}
                if len(reviewers) < policy.minimum_independent_reviewers_for_merge:
                    raise ValueError("authorized mutation does not satisfy reviewer minimum")
                if auth.operation == IdentityMutationKind.merge:
                    match = match_map[auth.candidate_match_ref or ""]
                    if set(auth.source_entity_refs) != {match.left_entity_ref, match.right_entity_ref}:
                        raise ValueError("merge authorization must preserve candidate entity pair")

        for audit in self.audit_records:
            if audit.candidate_match_ref and audit.candidate_match_ref not in match_map:
                raise ValueError("audit candidate match must resolve")
            if audit.mutation_authorization_ref and audit.mutation_authorization_ref not in auth_map:
                raise ValueError("audit mutation authorization must resolve")

        for snapshot in self.identity_graph_snapshots:
            if any(x not in entity_map for x in snapshot.entity_refs):
                raise ValueError("identity snapshot entity refs must resolve")
            if any(x not in alias_map for x in snapshot.alias_refs):
                raise ValueError("identity snapshot alias refs must resolve")
            if any(x not in identifier_map for x in snapshot.identifier_assertion_refs):
                raise ValueError("identity snapshot identifier refs must resolve")
            if any(x not in source_map for x in snapshot.source_identity_assertion_refs):
                raise ValueError("identity snapshot source assertion refs must resolve")
            if any(x not in match_map for x in snapshot.candidate_match_refs):
                raise ValueError("identity snapshot candidate match refs must resolve")
            if any(x not in auth_map for x in snapshot.mutation_authorization_refs):
                raise ValueError("identity snapshot mutation authorization refs must resolve")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_entity_resolution_identity_graph_bundle() -> EntityResolutionIdentityGraphBundle:
    predecessor = reference_evidence_graph_neural_validation_bundle()

    entity_a = CanonicalEntityRecord(
        entity_id="entity:synthetic:northstar-record-a:v1",
        entity_kind=EntityKind.organization,
        canonical_label="Northstar Research Collective",
        alias_refs=["alias:synthetic:northstar-a:preferred:v1"],
        identifier_assertion_refs=["identifier:synthetic:northstar-a:registry:v1"],
        source_identity_assertion_refs=["source-identity:synthetic:registry-a:v1"],
        metadata={"synthetic_reference": True, "pre_resolution_record": True},
    )
    entity_b = CanonicalEntityRecord(
        entity_id="entity:synthetic:northstar-record-b:v1",
        entity_kind=EntityKind.organization,
        canonical_label="Northstar Research Collective Incorporated",
        alias_refs=["alias:synthetic:northstar-b:legal:v1", "alias:synthetic:northstar-b:abbreviation:v1"],
        identifier_assertion_refs=["identifier:synthetic:northstar-b:registry:v1"],
        source_identity_assertion_refs=["source-identity:synthetic:report-b:v1"],
        metadata={"synthetic_reference": True, "pre_resolution_record": True},
    )
    entities = [entity_a, entity_b]

    aliases = [
        EntityAlias(
            alias_id="alias:synthetic:northstar-a:preferred:v1",
            entity_ref=entity_a.entity_id,
            value="Northstar Research Collective",
            alias_kind=AliasKind.preferred,
            language_tag="en",
            source_refs=["source:synthetic:registry-a"],
            provenance_refs=["provenance:synthetic:registry-a:name"],
            metadata={"synthetic_reference": True},
        ),
        EntityAlias(
            alias_id="alias:synthetic:northstar-b:legal:v1",
            entity_ref=entity_b.entity_id,
            value="Northstar Research Collective Incorporated",
            alias_kind=AliasKind.legal,
            language_tag="en",
            source_refs=["source:synthetic:annual-report-b"],
            provenance_refs=["provenance:synthetic:annual-report-b:legal-name"],
            metadata={"synthetic_reference": True},
        ),
        EntityAlias(
            alias_id="alias:synthetic:northstar-b:abbreviation:v1",
            entity_ref=entity_b.entity_id,
            value="Northstar Research Collective",
            alias_kind=AliasKind.source_supplied,
            language_tag="en",
            source_refs=["source:synthetic:annual-report-b"],
            provenance_refs=["provenance:synthetic:annual-report-b:short-name"],
            metadata={"synthetic_reference": True},
        ),
    ]

    identifiers = [
        ExternalIdentifierAssertion(
            identifier_assertion_id="identifier:synthetic:northstar-a:registry:v1",
            entity_ref=entity_a.entity_id,
            namespace="synthetic-corporate-registry",
            identifier_value="SYN-NRC-001",
            issuing_authority_ref="authority:synthetic:corporate-registry",
            source_refs=["source:synthetic:registry-a"],
            provenance_refs=["provenance:synthetic:registry-a:identifier"],
            verification_state=IdentifierState.verified,
            verified_by_refs=["verification:synthetic:registry-a:v1"],
            metadata={"synthetic_reference": True},
        ),
        ExternalIdentifierAssertion(
            identifier_assertion_id="identifier:synthetic:northstar-b:registry:v1",
            entity_ref=entity_b.entity_id,
            namespace="synthetic-corporate-registry",
            identifier_value="SYN-NRC-001",
            issuing_authority_ref="authority:synthetic:corporate-registry",
            source_refs=["source:synthetic:annual-report-b", "source:synthetic:registry-crosscheck-b"],
            provenance_refs=["provenance:synthetic:annual-report-b:identifier", "provenance:synthetic:registry-crosscheck-b:identifier"],
            verification_state=IdentifierState.verified,
            verified_by_refs=["verification:synthetic:registry-crosscheck-b:v1"],
            metadata={"synthetic_reference": True},
        ),
    ]

    source_assertions = [
        SourceEntityIdentityAssertion(
            source_identity_assertion_id="source-identity:synthetic:registry-a:v1",
            source_ref="source:synthetic:registry-a",
            source_entity_key="registry-record:SYN-NRC-001:A",
            asserted_entity_ref=entity_a.entity_id,
            asserted_name="Northstar Research Collective",
            alias_refs=[aliases[0].alias_id],
            identifier_assertion_refs=[identifiers[0].identifier_assertion_id],
            provenance_refs=["provenance:synthetic:registry-a:record"],
            assertion_state=SourceAssertionState.supported,
            metadata={"synthetic_reference": True},
        ),
        SourceEntityIdentityAssertion(
            source_identity_assertion_id="source-identity:synthetic:report-b:v1",
            source_ref="source:synthetic:annual-report-b",
            source_entity_key="annual-report:entity:NRC-inc",
            asserted_entity_ref=entity_b.entity_id,
            asserted_name="Northstar Research Collective Incorporated",
            alias_refs=[aliases[1].alias_id, aliases[2].alias_id],
            identifier_assertion_refs=[identifiers[1].identifier_assertion_id],
            provenance_refs=["provenance:synthetic:annual-report-b:entity-block"],
            assertion_state=SourceAssertionState.supported,
            metadata={"synthetic_reference": True},
        ),
    ]

    evidence_items = [
        IdentityEvidenceItem(
            identity_evidence_id="identity-evidence:synthetic:shared-registry-id:v1",
            evidence_kind=IdentityEvidenceKind.official_identifier,
            source_ref="source:synthetic:corporate-registry-crosscheck",
            provenance_refs=["provenance:synthetic:registry-crosscheck:shared-id"],
            relevant_entity_refs=[entity_a.entity_id, entity_b.entity_id],
            relevant_identifier_assertion_refs=[x.identifier_assertion_id for x in identifiers],
            relevant_source_assertion_refs=[x.source_identity_assertion_id for x in source_assertions],
            metadata={"synthetic_reference": True, "finding": "same synthetic registry identifier observed with source provenance"},
        ),
        IdentityEvidenceItem(
            identity_evidence_id="identity-evidence:synthetic:report-registry-continuity:v1",
            evidence_kind=IdentityEvidenceKind.source_document,
            source_ref="source:synthetic:continuity-filing",
            provenance_refs=["provenance:synthetic:continuity-filing:entity-reference"],
            relevant_entity_refs=[entity_a.entity_id, entity_b.entity_id],
            relevant_identifier_assertion_refs=[identifiers[0].identifier_assertion_id, identifiers[1].identifier_assertion_id],
            relevant_source_assertion_refs=[source_assertions[0].source_identity_assertion_id, source_assertions[1].source_identity_assertion_id],
            metadata={"synthetic_reference": True, "finding": "synthetic continuity record links legal-name variation to the same registry identifier"},
        ),
    ]

    policy = EntityResolutionPolicy(
        resolution_policy_id="entity-resolution-policy:reference:v1",
        minimum_identity_evidence_items_for_merge=2,
        minimum_independent_reviewers_for_merge=2,
        metadata={"synthetic_reference": True},
    )

    match = CandidateEntityMatch(
        candidate_match_id="candidate-entity-match:synthetic:northstar-a-b:v1",
        left_entity_ref=entity_a.entity_id,
        right_entity_ref=entity_b.entity_id,
        resolution_policy_ref=policy.resolution_policy_id,
        resolver_ref="resolver:synthetic:entity-match-model:v1",
        match_score=8.4,
        match_probability=0.97,
        feature_refs=["match-feature:normalized-name:v1", "match-feature:shared-identifier:v1"],
        source_identity_assertion_refs=[x.source_identity_assertion_id for x in source_assertions],
        identity_evidence_refs=[x.identity_evidence_id for x in evidence_items],
        contradicting_identity_evidence_refs=[],
        review_refs=["identity-review:synthetic:reviewer-a:v1", "identity-review:synthetic:reviewer-b:v1"],
        state=CandidateMatchState.supported,
        metadata={"synthetic_reference": True, "model_output_context_only": True},
    )

    reviews = [
        IndependentIdentityReview(
            identity_review_id="identity-review:synthetic:reviewer-a:v1",
            candidate_match_ref=match.candidate_match_id,
            reviewer_ref="reviewer:synthetic:identity-a:v1",
            disposition=IdentityReviewDisposition.support,
            supporting_identity_evidence_refs=[x.identity_evidence_id for x in evidence_items],
            considered_match_signal_refs=["match-signal:synthetic:probability:0.97"],
            rationale="Synthetic reviewer A supports a merge authorization based on provenance-bearing registry and continuity evidence; the model probability is contextual only.",
            reviewed_at="2026-09-29T10:00:00Z",
            metadata={"synthetic_reference": True},
        ),
        IndependentIdentityReview(
            identity_review_id="identity-review:synthetic:reviewer-b:v1",
            candidate_match_ref=match.candidate_match_id,
            reviewer_ref="reviewer:synthetic:identity-b:v1",
            disposition=IdentityReviewDisposition.support,
            supporting_identity_evidence_refs=[x.identity_evidence_id for x in evidence_items],
            considered_match_signal_refs=["match-signal:synthetic:name-similarity", "match-signal:synthetic:shared-identifier"],
            rationale="Synthetic reviewer B independently supports a merge authorization from source provenance and identifier continuity, not from automated similarity alone.",
            reviewed_at="2026-09-29T10:05:00Z",
            metadata={"synthetic_reference": True},
        ),
    ]

    authorization = IdentityMutationAuthorization(
        identity_mutation_authorization_id="identity-mutation-authorization:synthetic:northstar-merge:v1",
        operation=IdentityMutationKind.merge,
        decision=IdentityMutationDecision.authorized,
        resolution_policy_ref=policy.resolution_policy_id,
        candidate_match_ref=match.candidate_match_id,
        source_entity_refs=[entity_a.entity_id, entity_b.entity_id],
        proposed_result_entity_refs=["entity:synthetic:northstar-resolved:proposed:v1"],
        supporting_identity_evidence_refs=[x.identity_evidence_id for x in evidence_items],
        contradicting_identity_evidence_refs=[],
        reviewer_refs=[x.identity_review_id for x in reviews],
        identifier_provenance_verified=True,
        source_assertion_provenance_verified=True,
        contradictory_evidence_review_completed=True,
        independent_review_completed=True,
        metadata={"synthetic_reference": True, "authorization_only": True},
    )

    audits = [
        IdentityResolutionAuditRecord(
            identity_audit_id="identity-audit:synthetic:candidate-reviewed:v1",
            event_type="candidate-reviewed",
            actor_ref="governance:synthetic:entity-resolution:v1",
            candidate_match_ref=match.candidate_match_id,
            occurred_at="2026-09-29T10:05:30Z",
            input_fingerprint_sha256=match.fingerprint(),
            output_fingerprint_sha256=reviews[1].fingerprint(),
            metadata={"synthetic_reference": True},
        ),
        IdentityResolutionAuditRecord(
            identity_audit_id="identity-audit:synthetic:merge-authorized:v1",
            event_type="merge-authorized",
            actor_ref="governance:synthetic:entity-resolution:v1",
            candidate_match_ref=match.candidate_match_id,
            mutation_authorization_ref=authorization.identity_mutation_authorization_id,
            occurred_at="2026-09-29T10:06:00Z",
            input_fingerprint_sha256=match.fingerprint(),
            output_fingerprint_sha256=authorization.fingerprint(),
            metadata={"synthetic_reference": True, "graph_mutation_performed": False},
        ),
    ]

    snapshot = EntityIdentityGraphSnapshot(
        identity_graph_snapshot_id="identity-graph-snapshot:synthetic:pre-merge:v1",
        entity_refs=[x.entity_id for x in entities],
        alias_refs=[x.alias_id for x in aliases],
        identifier_assertion_refs=[x.identifier_assertion_id for x in identifiers],
        source_identity_assertion_refs=[x.source_identity_assertion_id for x in source_assertions],
        candidate_match_refs=[match.candidate_match_id],
        mutation_authorization_refs=[authorization.identity_mutation_authorization_id],
        created_at="2026-09-29T10:06:00Z",
        metadata={"synthetic_reference": True, "pre_mutation_snapshot": True},
    )

    return EntityResolutionIdentityGraphBundle(
        evidence_graph_neural_validation_bundle=predecessor,
        aliases=aliases,
        identifier_assertions=identifiers,
        source_identity_assertions=source_assertions,
        entities=entities,
        identity_evidence_items=evidence_items,
        resolution_policies=[policy],
        candidate_matches=[match],
        identity_reviews=reviews,
        mutation_authorizations=[authorization],
        audit_records=audits,
        identity_graph_snapshots=[snapshot],
        metadata={
            "reference_fixture": "synthetic-contract-fixture",
            "match_probability_is_not_identity_fact": True,
            "automated_resolution_may_not_silently_merge": True,
            "identity_graph_mutation_requires_downstream_audited_action": True,
        },
    )


def contract_document() -> dict[str, Any]:
    bundle = reference_entity_resolution_identity_graph_bundle()
    authorization = bundle.mutation_authorizations[0]
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contracts": [
            "sc.core.evidence-graph-neural-analysis-validation.v1",
            "sc.core.graph-link-prediction-candidate-relationship.v1",
            "sc.core.cross-lingual-semantic-linguistic-exchange.v1",
        ],
        "object_types": [
            "EntityAlias",
            "ExternalIdentifierAssertion",
            "SourceEntityIdentityAssertion",
            "CanonicalEntityRecord",
            "IdentityEvidenceItem",
            "EntityResolutionPolicy",
            "CandidateEntityMatch",
            "IndependentIdentityReview",
            "IdentityMutationAuthorization",
            "IdentityResolutionAuditRecord",
            "EntityIdentityGraphSnapshot",
            "EntityResolutionIdentityGraphBundle",
        ],
        "principles": {
            "match_probability_is_not_identity_fact": True,
            "same_name_is_not_identity_fact": True,
            "shared_identifier_requires_provenance_and_review": True,
            "source_identity_assertion_is_not_canonical_identity": True,
            "alias_is_not_identity_proof": True,
            "candidate_match_is_not_canonical_equivalence_edge": True,
            "automated_resolution_may_not_silently_merge_entities": True,
            "automated_resolution_may_not_silently_split_entities": True,
            "identity_mutation_requires_independent_evidence": True,
            "identity_mutation_requires_provenance": True,
            "authorization_is_not_identity_graph_mutation": True,
            "identity_graph_is_distinct_from_evidence_graph": True,
            "gnn_prediction_is_not_graph_fact": True,
        },
        "capabilities": {
            "canonical_entity_records": True,
            "aliases_and_name_variants": True,
            "external_identifier_assertions": True,
            "source_specific_identity_assertions": True,
            "identity_evidence_items": True,
            "candidate_entity_matching": True,
            "independent_identity_review": True,
            "merge_and_split_authorization_contracts": True,
            "append_only_identity_resolution_audit": True,
            "immutable_identity_graph_snapshots": True,
        },
        "boundaries": {
            "core_auto_merges_entities_from_match_score": False,
            "core_auto_splits_entities_from_model_output": False,
            "core_treats_alias_match_as_identity_proof": False,
            "core_treats_shared_identifier_as_unreviewed_identity_fact": False,
            "core_mutates_identity_graph_during_authorization": False,
            "runtime_may_create_canonical_equivalence_edge_from_probability": False,
            "identity_authorization_itself_creates_or_deletes_entity_records": False,
        },
        "roadmap_integration": {
            "begins_entity_evidence_connection_intelligence_block_v3770_through_v3900": True,
            "follows_graph_neural_wave_v3700_through_v3760": True,
            "prepares_temporal_identity_alias_name_variant_intelligence_v3780": True,
            "prepares_probabilistic_record_linkage_entity_matching_v3790": True,
            "prepares_cross_source_entity_reconciliation_v3800": True,
        },
        "reference": {
            "entity_count": len(bundle.entities),
            "alias_count": len(bundle.aliases),
            "identifier_assertion_count": len(bundle.identifier_assertions),
            "source_identity_assertion_count": len(bundle.source_identity_assertions),
            "candidate_match_count": len(bundle.candidate_matches),
            "independent_reviewer_count": len({x.reviewer_ref for x in bundle.identity_reviews}),
            "merge_decision": authorization.decision.value,
            "proposed_result_entity_refs": authorization.proposed_result_entity_refs,
            "actual_identity_graph_mutation_performed": authorization.actual_identity_graph_mutation_performed,
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
    }
