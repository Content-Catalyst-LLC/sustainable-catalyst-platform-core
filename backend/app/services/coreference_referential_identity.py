from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .context_semantic_frame import InterpretationMethod
from .discourse_rhetorical_semantics import (
    DiscourseStructureRhetoricalSemanticsBundle,
    reference_discourse_structure_rhetorical_semantics_bundle,
)

CORE_RELEASE = "4.3.0"
CONTRACT_VERSION = "sc.core.coreference-reference-referential-identity-intelligence.v1"
PREDECESSOR_CONTRACT = "sc.core.discourse-structure-rhetorical-semantics.v1"

EXTENDS_CONTRACTS = [
    PREDECESSOR_CONTRACT,
    "sc.core.context-object-semantic-frame-foundation.v1",
    "sc.core.entity-resolution-identity-graph-foundation.v1",
    "sc.core.temporal-identity-alias-name-variant-intelligence.v1",
    "sc.core.cross-source-entity-reconciliation-identity-provenance.v1",
]


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class ReferenceExpressionKind(str, Enum):
    pronoun = "pronoun"
    demonstrative = "demonstrative"
    definite_description = "definite-description"
    proper_name = "proper-name"
    alias = "alias"
    appositive = "appositive"
    ellipsis = "ellipsis"
    zero_anaphora = "zero-anaphora"
    discourse_deixis = "discourse-deixis"
    other = "other"


class ReferentKind(str, Enum):
    entity = "entity"
    concept = "concept"
    event = "event"
    proposition = "proposition"
    time = "time"
    place = "place"
    context = "context"
    discourse_segment = "discourse-segment"
    other = "other"


class ResolutionRelationKind(str, Enum):
    coreference = "coreference"
    anaphora = "anaphora"
    cataphora = "cataphora"
    bridging = "bridging"
    discourse_deixis = "discourse-deixis"
    apposition = "apposition"
    alias = "alias"
    name_variant = "name-variant"
    associative = "associative"


class ResolutionState(str, Enum):
    candidate = "candidate"
    reviewed = "reviewed"
    accepted = "accepted"
    rejected = "rejected"
    disputed = "disputed"
    unresolved = "unresolved"


class IdentityBindingState(str, Enum):
    candidate = "candidate"
    reviewed = "reviewed"
    accepted = "accepted"
    rejected = "rejected"
    disputed = "disputed"
    deferred = "deferred"


class ReferentialIdentityPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    source_mentions_remain_immutable: Literal[True] = True
    candidate_referents_are_explicit: Literal[True] = True
    competing_referents_may_coexist: Literal[True] = True
    resolution_confidence_preserves_uncertainty: Literal[True] = True
    coreference_is_distinct_from_canonical_identity: Literal[True] = True
    source_description_does_not_establish_canonical_identity: Literal[True] = True
    model_scores_are_advisory: Literal[True] = True
    accepted_resolution_requires_governed_review: Literal[True] = True
    identity_binding_requires_upstream_identity_governance: Literal[True] = True
    reference_resolution_does_not_promote_evidence: Literal[True] = True
    identity_graph_mutation_authorized: Literal[False] = False
    relationship_graph_mutation_authorized: Literal[False] = False
    evidence_graph_mutation_authorized: Literal[False] = False
    context_graph_mutation_authorized: Literal[False] = False

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReferenceExpression(BaseModel):
    reference_expression_id: str = Field(min_length=3, max_length=500)
    mention_ref: str = Field(min_length=3, max_length=500)
    context_ref: str = Field(min_length=3, max_length=500)
    expression_kind: ReferenceExpressionKind
    surface_text: str = Field(min_length=1, max_length=10000)
    candidate_set_ref: str = Field(min_length=3, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    original_mention_preserved: Literal[True] = True
    expression_is_not_canonical_identity: Literal[True] = True
    expression_is_not_evidence_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReferentAnchor(BaseModel):
    referent_id: str = Field(min_length=3, max_length=500)
    referent_kind: ReferentKind
    source_contract: str = Field(min_length=10, max_length=500)
    source_object_ref: str = Field(min_length=3, max_length=1000)
    source_mention_ref: str | None = Field(default=None, max_length=500)
    source_frame_ref: str | None = Field(default=None, max_length=500)
    source_segment_ref: str | None = Field(default=None, max_length=500)
    canonical_entity_ref: str | None = Field(default=None, max_length=1000)
    language_ref: str | None = Field(default=None, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    source_anchor_is_not_canonical_identity: Literal[True] = True
    referent_anchor_does_not_establish_source_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_anchor(self):
        if not any((self.source_mention_ref, self.source_frame_ref, self.source_segment_ref, self.canonical_entity_ref)):
            raise ValueError("referent anchor requires at least one source anchor")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReferentCandidate(BaseModel):
    candidate_id: str = Field(min_length=3, max_length=500)
    candidate_set_ref: str = Field(min_length=3, max_length=500)
    referent_ref: str = Field(min_length=3, max_length=500)
    rank: int = Field(ge=1)
    score: float | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    supporting_signal_refs: list[str] = Field(default_factory=list)
    contradicting_signal_refs: list[str] = Field(default_factory=list)
    state: ResolutionState = ResolutionState.candidate
    provenance_ref: str = Field(min_length=3, max_length=500)
    candidate_is_not_identity_fact: Literal[True] = True
    score_is_not_truth_probability: Literal[True] = True
    candidate_does_not_mutate_identity_graph: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_candidate(self):
        _unique(self.supporting_signal_refs, "supporting_signal_refs")
        _unique(self.contradicting_signal_refs, "contradicting_signal_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReferentCandidateSet(BaseModel):
    candidate_set_id: str = Field(min_length=3, max_length=500)
    reference_expression_ref: str = Field(min_length=3, max_length=500)
    candidate_refs: list[str] = Field(min_length=1)
    method: InterpretationMethod
    provenance_ref: str = Field(min_length=3, max_length=500)
    selection_state: ResolutionState = ResolutionState.candidate
    selected_candidate_ref: str | None = Field(default=None, max_length=500)
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    rationale: str | None = Field(default=None, max_length=8000)
    competing_candidates_preserved: Literal[True] = True
    selected_candidate_is_interpretation_not_identity_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_candidate_set(self):
        _unique(self.candidate_refs, "candidate_refs")
        if self.selected_candidate_ref and self.selected_candidate_ref not in self.candidate_refs:
            raise ValueError("selected_candidate_ref must be present in candidate_refs")
        if self.selection_state == ResolutionState.accepted:
            if not self.selected_candidate_ref:
                raise ValueError("accepted candidate set requires selected_candidate_ref")
            if not self.reviewer_ref:
                raise ValueError("accepted candidate set requires reviewer_ref")
        if self.selection_state == ResolutionState.unresolved and self.selected_candidate_ref:
            raise ValueError("unresolved candidate set cannot select a candidate")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CoreferenceLink(BaseModel):
    coreference_link_id: str = Field(min_length=3, max_length=500)
    reference_expression_ref: str = Field(min_length=3, max_length=500)
    antecedent_referent_ref: str = Field(min_length=3, max_length=500)
    relation_kind: ResolutionRelationKind
    state: ResolutionState = ResolutionState.candidate
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    provenance_ref: str = Field(min_length=3, max_length=500)
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    link_is_interpretation_not_canonical_identity: Literal[True] = True
    link_does_not_establish_source_truth: Literal[True] = True
    link_does_not_mutate_identity_graph: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_link(self):
        if self.state == ResolutionState.accepted and not self.reviewer_ref:
            raise ValueError("accepted coreference link requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CoreferenceChain(BaseModel):
    coreference_chain_id: str = Field(min_length=3, max_length=500)
    referent_refs: list[str] = Field(min_length=1)
    mention_refs: list[str] = Field(min_length=2)
    coreference_link_refs: list[str] = Field(min_length=1)
    provenance_ref: str = Field(min_length=3, max_length=500)
    state: ResolutionState = ResolutionState.candidate
    chain_is_interpretation_not_entity_merge: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_chain(self):
        _unique(self.referent_refs, "referent_refs")
        _unique(self.mention_refs, "mention_refs")
        _unique(self.coreference_link_refs, "coreference_link_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReferentialIdentityBinding(BaseModel):
    identity_binding_id: str = Field(min_length=3, max_length=500)
    referent_ref: str = Field(min_length=3, max_length=500)
    mention_refs: list[str] = Field(min_length=1)
    upstream_identity_contract: Literal["sc.core.entity-resolution-identity-graph-foundation.v1"] = "sc.core.entity-resolution-identity-graph-foundation.v1"
    candidate_entity_refs: list[str] = Field(default_factory=list)
    selected_entity_ref: str | None = Field(default=None, max_length=1000)
    source_identity_assertion_refs: list[str] = Field(default_factory=list)
    identity_evidence_refs: list[str] = Field(default_factory=list)
    review_refs: list[str] = Field(default_factory=list)
    state: IdentityBindingState = IdentityBindingState.deferred
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    provenance_ref: str = Field(min_length=3, max_length=500)
    local_validation_required: Literal[True] = True
    binding_is_reference_resolution_not_entity_merge: Literal[True] = True
    source_wording_does_not_establish_canonical_identity: Literal[True] = True
    identity_graph_mutation_authorized: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_binding(self):
        for values, label in (
            (self.mention_refs, "mention_refs"),
            (self.candidate_entity_refs, "candidate_entity_refs"),
            (self.source_identity_assertion_refs, "source_identity_assertion_refs"),
            (self.identity_evidence_refs, "identity_evidence_refs"),
            (self.review_refs, "review_refs"),
        ):
            _unique(values, label)
        if self.selected_entity_ref and self.selected_entity_ref not in self.candidate_entity_refs:
            raise ValueError("selected_entity_ref must be among candidate_entity_refs")
        if self.state == IdentityBindingState.accepted:
            if not self.selected_entity_ref:
                raise ValueError("accepted identity binding requires selected_entity_ref")
            if not self.identity_evidence_refs or not self.review_refs:
                raise ValueError("accepted identity binding requires evidence and review refs")
        if self.state == IdentityBindingState.deferred and self.selected_entity_ref:
            raise ValueError("deferred identity binding cannot select a canonical entity")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReferenceResolutionProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3, max_length=500)
    subject_refs: list[str] = Field(min_length=1)
    method: InterpretationMethod
    produced_by_ref: str = Field(min_length=3, max_length=1000)
    source_refs: list[str] = Field(min_length=1)
    model_ref: str | None = Field(default=None, max_length=1000)
    model_version: str | None = Field(default=None, max_length=240)
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    created_at: str | None = Field(default=None, max_length=80)
    machine_or_graph_output_is_advisory: Literal[True] = True
    provenance_does_not_establish_reference_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_provenance(self):
        _unique(self.subject_refs, "provenance subject_refs")
        _unique(self.source_refs, "provenance source_refs")
        if self.method in {InterpretationMethod.model_assisted, InterpretationMethod.graph_assisted} and not self.model_ref:
            raise ValueError("model/graph-assisted resolution provenance requires model_ref")
        if self.model_version and not self.model_ref:
            raise ValueError("model_version requires model_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReferentialInterpretation(BaseModel):
    interpretation_id: str = Field(min_length=3, max_length=500)
    discourse_interpretation_ref: str = Field(min_length=3, max_length=500)
    reference_expression_refs: list[str] = Field(default_factory=list)
    candidate_set_refs: list[str] = Field(default_factory=list)
    coreference_link_refs: list[str] = Field(default_factory=list)
    coreference_chain_refs: list[str] = Field(default_factory=list)
    identity_binding_refs: list[str] = Field(default_factory=list)
    unresolved_reference_expression_refs: list[str] = Field(default_factory=list)
    provenance_ref: str = Field(min_length=3, max_length=500)
    state: ResolutionState = ResolutionState.candidate
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    interpretation_does_not_rewrite_predecessor_objects: Literal[True] = True
    interpretation_is_not_truth_verdict: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_interpretation(self):
        for values, label in (
            (self.reference_expression_refs, "reference_expression_refs"),
            (self.candidate_set_refs, "candidate_set_refs"),
            (self.coreference_link_refs, "coreference_link_refs"),
            (self.coreference_chain_refs, "coreference_chain_refs"),
            (self.identity_binding_refs, "identity_binding_refs"),
            (self.unresolved_reference_expression_refs, "unresolved_reference_expression_refs"),
        ):
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReferentialIdentitySnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    discourse_semantics_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    referential_interpretation_refs: list[str] = Field(min_length=1)
    deterministic_referential_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        _unique(self.referential_interpretation_refs, "referential_interpretation_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CoreferenceReferentialIdentityBundle(BaseModel):
    release: Literal["4.3.0"] = "4.3.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    extends_contracts: list[str] = Field(min_length=5)
    policy: ReferentialIdentityPolicy
    discourse_semantics: DiscourseStructureRhetoricalSemanticsBundle
    reference_expressions: list[ReferenceExpression] = Field(default_factory=list)
    referents: list[ReferentAnchor] = Field(min_length=1)
    candidate_sets: list[ReferentCandidateSet] = Field(default_factory=list)
    candidates: list[ReferentCandidate] = Field(default_factory=list)
    coreference_links: list[CoreferenceLink] = Field(default_factory=list)
    coreference_chains: list[CoreferenceChain] = Field(default_factory=list)
    identity_bindings: list[ReferentialIdentityBinding] = Field(default_factory=list)
    provenance_records: list[ReferenceResolutionProvenanceRecord] = Field(min_length=1)
    interpretations: list[ReferentialInterpretation] = Field(min_length=1)
    snapshots: list[ReferentialIdentitySnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.extends_contracts != EXTENDS_CONTRACTS:
            raise ValueError("extends_contracts must preserve the declared v4.3 dependency order")
        if self.discourse_semantics.release != "4.2.0" or self.discourse_semantics.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.3 must embed the governed v4.2 discourse-semantics predecessor")

        groups = (
            ([x.reference_expression_id for x in self.reference_expressions], "reference expression ids"),
            ([x.referent_id for x in self.referents], "referent ids"),
            ([x.candidate_set_id for x in self.candidate_sets], "candidate set ids"),
            ([x.candidate_id for x in self.candidates], "candidate ids"),
            ([x.coreference_link_id for x in self.coreference_links], "coreference link ids"),
            ([x.coreference_chain_id for x in self.coreference_chains], "coreference chain ids"),
            ([x.identity_binding_id for x in self.identity_bindings], "identity binding ids"),
            ([x.provenance_id for x in self.provenance_records], "provenance ids"),
            ([x.interpretation_id for x in self.interpretations], "interpretation ids"),
            ([x.snapshot_id for x in self.snapshots], "snapshot ids"),
        )
        for values, label in groups:
            _unique(values, label)

        context_bundle = self.discourse_semantics.context_semantics
        mentions = {x.mention_id: x for x in context_bundle.mentions}
        contexts = {x.context_id: x for x in context_bundle.contexts}
        frames = {x.frame_id: x for x in context_bundle.frames}
        segments = {x.segment_id: x for x in self.discourse_semantics.segments}
        discourse_interpretations = {x.interpretation_id: x for x in self.discourse_semantics.interpretations}

        refs = {x.reference_expression_id: x for x in self.reference_expressions}
        referents = {x.referent_id: x for x in self.referents}
        sets = {x.candidate_set_id: x for x in self.candidate_sets}
        candidates = {x.candidate_id: x for x in self.candidates}
        links = {x.coreference_link_id: x for x in self.coreference_links}
        chains = {x.coreference_chain_id: x for x in self.coreference_chains}
        bindings = {x.identity_binding_id: x for x in self.identity_bindings}
        provenances = {x.provenance_id: x for x in self.provenance_records}
        interpretations = {x.interpretation_id: x for x in self.interpretations}

        for expression in self.reference_expressions:
            if expression.mention_ref not in mentions:
                raise ValueError("reference expression mention_ref must resolve")
            if expression.context_ref not in contexts:
                raise ValueError("reference expression context_ref must resolve")
            mention = mentions[expression.mention_ref]
            if mention.context_ref != expression.context_ref:
                raise ValueError("reference expression context must match mention context")
            if mention.surface_text != expression.surface_text:
                raise ValueError("reference expression surface_text must preserve source mention")
            if expression.candidate_set_ref not in sets:
                raise ValueError("reference expression candidate_set_ref must resolve")
            if sets[expression.candidate_set_ref].reference_expression_ref != expression.reference_expression_id:
                raise ValueError("candidate set must point back to reference expression")
            if expression.provenance_ref not in provenances:
                raise ValueError("reference expression provenance_ref must resolve")

        for referent in self.referents:
            if referent.provenance_ref not in provenances:
                raise ValueError("referent provenance_ref must resolve")
            if referent.source_mention_ref and referent.source_mention_ref not in mentions:
                raise ValueError("referent source_mention_ref must resolve")
            if referent.source_frame_ref and referent.source_frame_ref not in frames:
                raise ValueError("referent source_frame_ref must resolve")
            if referent.source_segment_ref and referent.source_segment_ref not in segments:
                raise ValueError("referent source_segment_ref must resolve")

        candidates_by_set: dict[str, list[ReferentCandidate]] = {}
        for candidate in self.candidates:
            if candidate.candidate_set_ref not in sets:
                raise ValueError("candidate candidate_set_ref must resolve")
            if candidate.referent_ref not in referents:
                raise ValueError("candidate referent_ref must resolve")
            if candidate.provenance_ref not in provenances:
                raise ValueError("candidate provenance_ref must resolve")
            candidates_by_set.setdefault(candidate.candidate_set_ref, []).append(candidate)

        for candidate_set in self.candidate_sets:
            if candidate_set.reference_expression_ref not in refs:
                raise ValueError("candidate set reference_expression_ref must resolve")
            if candidate_set.provenance_ref not in provenances:
                raise ValueError("candidate set provenance_ref must resolve")
            if any(ref not in candidates for ref in candidate_set.candidate_refs):
                raise ValueError("candidate set candidate_ref must resolve")
            actual = {x.candidate_id for x in candidates_by_set.get(candidate_set.candidate_set_id, [])}
            if set(candidate_set.candidate_refs) != actual:
                raise ValueError("candidate set must enumerate exactly its candidates")
            ranks = [candidates[ref].rank for ref in candidate_set.candidate_refs]
            if len(ranks) != len(set(ranks)):
                raise ValueError("candidate ranks must be unique within a candidate set")
            if candidate_set.selected_candidate_ref:
                selected = candidates[candidate_set.selected_candidate_ref]
                if selected.state != ResolutionState.accepted:
                    raise ValueError("selected candidate must be accepted")

        for link in self.coreference_links:
            if link.reference_expression_ref not in refs:
                raise ValueError("coreference link reference_expression_ref must resolve")
            if link.antecedent_referent_ref not in referents:
                raise ValueError("coreference link antecedent_referent_ref must resolve")
            if link.provenance_ref not in provenances:
                raise ValueError("coreference link provenance_ref must resolve")
            if link.state == ResolutionState.accepted:
                expr = refs[link.reference_expression_ref]
                selected_ref = sets[expr.candidate_set_ref].selected_candidate_ref
                if not selected_ref or candidates[selected_ref].referent_ref != link.antecedent_referent_ref:
                    raise ValueError("accepted coreference link must match selected candidate referent")

        for chain in self.coreference_chains:
            if any(ref not in referents for ref in chain.referent_refs):
                raise ValueError("coreference chain referent_ref must resolve")
            if any(ref not in mentions for ref in chain.mention_refs):
                raise ValueError("coreference chain mention_ref must resolve")
            if any(ref not in links for ref in chain.coreference_link_refs):
                raise ValueError("coreference chain link_ref must resolve")
            if chain.provenance_ref not in provenances:
                raise ValueError("coreference chain provenance_ref must resolve")

        for binding in self.identity_bindings:
            if binding.referent_ref not in referents:
                raise ValueError("identity binding referent_ref must resolve")
            if any(ref not in mentions for ref in binding.mention_refs):
                raise ValueError("identity binding mention_ref must resolve")
            if binding.provenance_ref not in provenances:
                raise ValueError("identity binding provenance_ref must resolve")

        for interpretation in self.interpretations:
            if interpretation.discourse_interpretation_ref not in discourse_interpretations:
                raise ValueError("referential interpretation discourse_interpretation_ref must resolve")
            if any(ref not in refs for ref in interpretation.reference_expression_refs):
                raise ValueError("referential interpretation reference_expression_ref must resolve")
            if any(ref not in sets for ref in interpretation.candidate_set_refs):
                raise ValueError("referential interpretation candidate_set_ref must resolve")
            if any(ref not in links for ref in interpretation.coreference_link_refs):
                raise ValueError("referential interpretation coreference_link_ref must resolve")
            if any(ref not in chains for ref in interpretation.coreference_chain_refs):
                raise ValueError("referential interpretation coreference_chain_ref must resolve")
            if any(ref not in bindings for ref in interpretation.identity_binding_refs):
                raise ValueError("referential interpretation identity_binding_ref must resolve")
            if any(ref not in refs for ref in interpretation.unresolved_reference_expression_refs):
                raise ValueError("unresolved reference expression must resolve")
            if interpretation.provenance_ref not in provenances:
                raise ValueError("referential interpretation provenance_ref must resolve")

        object_ids = set(refs) | set(referents) | set(sets) | set(candidates) | set(links) | set(chains) | set(bindings) | set(interpretations) | {x.snapshot_id for x in self.snapshots}
        for provenance in self.provenance_records:
            for ref in provenance.subject_refs:
                if ref not in object_ids:
                    raise ValueError("provenance subject_ref must resolve to a v4.3 object")

        expected_discourse_fingerprint = self.discourse_semantics.fingerprint()
        for snapshot in self.snapshots:
            if snapshot.discourse_semantics_fingerprint_sha256 != expected_discourse_fingerprint:
                raise ValueError("snapshot discourse semantics fingerprint must match embedded v4.2 bundle")
            if any(ref not in interpretations for ref in snapshot.referential_interpretation_refs):
                raise ValueError("snapshot referential_interpretation_ref must resolve")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


@lru_cache(maxsize=1)
def reference_coreference_referential_identity_bundle() -> CoreferenceReferentialIdentityBundle:
    discourse = reference_discourse_structure_rhetorical_semantics_bundle()

    expression = ReferenceExpression(
        reference_expression_id="reference-expression:it",
        mention_ref="mention:it-unresolved",
        context_ref="context:policy-note:sentence-2",
        expression_kind=ReferenceExpressionKind.pronoun,
        surface_text="It",
        candidate_set_ref="candidate-set:it",
        provenance_ref="prov:reference-expression:reference",
        metadata={"deferred_by_v4.1": True, "deferred_by_v4.2": True},
    )

    referents = [
        ReferentAnchor(
            referent_id="referent:proposal",
            referent_kind=ReferentKind.concept,
            source_contract="sc.core.context-object-semantic-frame-foundation.v1",
            source_object_ref="mention:proposal",
            source_mention_ref="mention:proposal",
            language_ref="language:en",
            provenance_ref="prov:referent-anchor:reference",
        ),
        ReferentAnchor(
            referent_id="referent:estimate",
            referent_kind=ReferentKind.concept,
            source_contract="sc.core.context-object-semantic-frame-foundation.v1",
            source_object_ref="mention:estimate",
            source_mention_ref="mention:estimate",
            language_ref="language:en",
            provenance_ref="prov:referent-anchor:reference",
        ),
        ReferentAnchor(
            referent_id="referent:rejection-event",
            referent_kind=ReferentKind.event,
            source_contract="sc.core.context-object-semantic-frame-foundation.v1",
            source_object_ref="frame:rejection",
            source_frame_ref="frame:rejection",
            language_ref="language:en",
            provenance_ref="prov:referent-anchor:reference",
        ),
        ReferentAnchor(
            referent_id="referent:commission",
            referent_kind=ReferentKind.entity,
            source_contract="sc.core.context-object-semantic-frame-foundation.v1",
            source_object_ref="mention:commission",
            source_mention_ref="mention:commission",
            language_ref="language:en",
            provenance_ref="prov:referent-anchor:reference",
        ),
        ReferentAnchor(
            referent_id="referent:ministry",
            referent_kind=ReferentKind.entity,
            source_contract="sc.core.context-object-semantic-frame-foundation.v1",
            source_object_ref="mention:ministry",
            source_mention_ref="mention:ministry",
            language_ref="language:en",
            provenance_ref="prov:referent-anchor:reference",
        ),
    ]

    candidates = [
        ReferentCandidate(
            candidate_id="candidate:it:proposal",
            candidate_set_ref="candidate-set:it",
            referent_ref="referent:proposal",
            rank=1,
            score=8.2,
            confidence=0.82,
            supporting_signal_refs=["discourse-signal:nevertheless", "rhetorical-relation:concession-viability"],
            state=ResolutionState.accepted,
            provenance_ref="prov:reference-candidates:reference",
            metadata={"selection_basis": "manual contextual review of discourse continuity"},
        ),
        ReferentCandidate(
            candidate_id="candidate:it:estimate",
            candidate_set_ref="candidate-set:it",
            referent_ref="referent:estimate",
            rank=2,
            score=1.2,
            confidence=0.12,
            contradicting_signal_refs=["semantic-role:political-viability-mismatch"],
            state=ResolutionState.reviewed,
            provenance_ref="prov:reference-candidates:reference",
        ),
        ReferentCandidate(
            candidate_id="candidate:it:rejection-event",
            candidate_set_ref="candidate-set:it",
            referent_ref="referent:rejection-event",
            rank=3,
            score=0.6,
            confidence=0.06,
            contradicting_signal_refs=["semantic-role:state-theme-preference"],
            state=ResolutionState.reviewed,
            provenance_ref="prov:reference-candidates:reference",
        ),
    ]

    candidate_set = ReferentCandidateSet(
        candidate_set_id="candidate-set:it",
        reference_expression_ref=expression.reference_expression_id,
        candidate_refs=[x.candidate_id for x in candidates],
        method=InterpretationMethod.manual,
        provenance_ref="prov:reference-candidates:reference",
        selection_state=ResolutionState.accepted,
        selected_candidate_ref="candidate:it:proposal",
        reviewer_ref="reviewer:reference-resolution:v1",
        rationale="The manually reviewed reference example selects the proposal as the antecedent while preserving lower-ranked alternatives and their uncertainty.",
    )

    link = CoreferenceLink(
        coreference_link_id="coreference-link:it-to-proposal",
        reference_expression_ref=expression.reference_expression_id,
        antecedent_referent_ref="referent:proposal",
        relation_kind=ResolutionRelationKind.anaphora,
        state=ResolutionState.accepted,
        confidence=0.82,
        provenance_ref="prov:coreference-link:reference",
        reviewer_ref="reviewer:reference-resolution:v1",
        metadata={"v41_mention_remains_unresolved_reference_object": True},
    )

    chain = CoreferenceChain(
        coreference_chain_id="coreference-chain:proposal-it",
        referent_refs=["referent:proposal"],
        mention_refs=["mention:proposal", "mention:it-unresolved"],
        coreference_link_refs=[link.coreference_link_id],
        provenance_ref="prov:coreference-link:reference",
        state=ResolutionState.accepted,
    )

    identity_bindings = [
        ReferentialIdentityBinding(
            identity_binding_id="identity-binding:commission:deferred",
            referent_ref="referent:commission",
            mention_refs=["mention:commission"],
            state=IdentityBindingState.deferred,
            provenance_ref="prov:identity-binding:reference",
            metadata={"reason": "source text names a commission generically and does not identify a canonical institution"},
        ),
        ReferentialIdentityBinding(
            identity_binding_id="identity-binding:ministry:deferred",
            referent_ref="referent:ministry",
            mention_refs=["mention:ministry"],
            state=IdentityBindingState.deferred,
            provenance_ref="prov:identity-binding:reference",
            metadata={"reason": "source text names a ministry generically and requires upstream identity evidence before canonical binding"},
        ),
    ]

    interpretation = ReferentialInterpretation(
        interpretation_id="referential-interpretation:policy-note:baseline",
        discourse_interpretation_ref="discourse-interpretation:policy-note:baseline",
        reference_expression_refs=[expression.reference_expression_id],
        candidate_set_refs=[candidate_set.candidate_set_id],
        coreference_link_refs=[link.coreference_link_id],
        coreference_chain_refs=[chain.coreference_chain_id],
        identity_binding_refs=[x.identity_binding_id for x in identity_bindings],
        unresolved_reference_expression_refs=[],
        provenance_ref="prov:referential-interpretation:reference",
        state=ResolutionState.accepted,
        confidence=0.82,
        metadata={
            "resolution_overlays_v4.1_without_rewriting_v4.1": True,
            "canonical_identity_for_commission_and_ministry_remains_deferred": True,
        },
    )

    snapshot_material = {
        "discourse_semantics": discourse.fingerprint(),
        "reference_expression": expression.fingerprint(),
        "referents": [x.fingerprint() for x in referents],
        "candidate_set": candidate_set.fingerprint(),
        "candidates": [x.fingerprint() for x in candidates],
        "coreference_link": link.fingerprint(),
        "coreference_chain": chain.fingerprint(),
        "identity_bindings": [x.fingerprint() for x in identity_bindings],
        "interpretation": interpretation.fingerprint(),
    }
    snapshot = ReferentialIdentitySnapshot(
        snapshot_id="snapshot:coreference-referential-identity:reference:v1",
        discourse_semantics_fingerprint_sha256=discourse.fingerprint(),
        referential_interpretation_refs=[interpretation.interpretation_id],
        deterministic_referential_fingerprint_sha256=canonical_sha256(snapshot_material),
    )

    provenances = [
        ReferenceResolutionProvenanceRecord(
            provenance_id="prov:reference-expression:reference",
            subject_refs=[expression.reference_expression_id],
            method=InterpretationMethod.manual,
            produced_by_ref="actor:platform-core-reference-builder",
            source_refs=["source:policy-note:v1"],
        ),
        ReferenceResolutionProvenanceRecord(
            provenance_id="prov:referent-anchor:reference",
            subject_refs=[x.referent_id for x in referents],
            method=InterpretationMethod.manual,
            produced_by_ref="actor:platform-core-reference-builder",
            source_refs=["source:policy-note:v1"],
        ),
        ReferenceResolutionProvenanceRecord(
            provenance_id="prov:reference-candidates:reference",
            subject_refs=[candidate_set.candidate_set_id] + [x.candidate_id for x in candidates],
            method=InterpretationMethod.manual,
            produced_by_ref="reviewer:reference-resolution:v1",
            source_refs=["source:policy-note:v1"],
            reviewer_ref="reviewer:reference-resolution:v1",
        ),
        ReferenceResolutionProvenanceRecord(
            provenance_id="prov:coreference-link:reference",
            subject_refs=[link.coreference_link_id, chain.coreference_chain_id],
            method=InterpretationMethod.manual,
            produced_by_ref="reviewer:reference-resolution:v1",
            source_refs=["source:policy-note:v1"],
            reviewer_ref="reviewer:reference-resolution:v1",
        ),
        ReferenceResolutionProvenanceRecord(
            provenance_id="prov:identity-binding:reference",
            subject_refs=[x.identity_binding_id for x in identity_bindings],
            method=InterpretationMethod.manual,
            produced_by_ref="actor:platform-core-reference-builder",
            source_refs=["source:policy-note:v1"],
        ),
        ReferenceResolutionProvenanceRecord(
            provenance_id="prov:referential-interpretation:reference",
            subject_refs=[interpretation.interpretation_id, snapshot.snapshot_id],
            method=InterpretationMethod.manual,
            produced_by_ref="reviewer:reference-resolution:v1",
            source_refs=["source:policy-note:v1"],
            reviewer_ref="reviewer:reference-resolution:v1",
        ),
    ]

    return CoreferenceReferentialIdentityBundle(
        extends_contracts=list(EXTENDS_CONTRACTS),
        policy=ReferentialIdentityPolicy(policy_id="referential-identity-policy:v4.3"),
        discourse_semantics=discourse,
        reference_expressions=[expression],
        referents=referents,
        candidate_sets=[candidate_set],
        candidates=candidates,
        coreference_links=[link],
        coreference_chains=[chain],
        identity_bindings=identity_bindings,
        provenance_records=provenances,
        interpretations=[interpretation],
        snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    bundle = reference_coreference_referential_identity_bundle()
    accepted_sets = [x for x in bundle.candidate_sets if x.selection_state == ResolutionState.accepted]
    unresolved_expressions = sum(len(x.unresolved_reference_expression_refs) for x in bundle.interpretations)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "extends_contracts": list(EXTENDS_CONTRACTS),
        "identity": {
            "product": "Sustainable Catalyst Platform Core",
            "build": "Coreference, Reference & Referential Identity Intelligence",
            "major_api": "v4",
        },
        "principles": {
            "reference_expressions_are_first_class_objects": True,
            "candidate_referents_are_ranked_and_persistent": True,
            "competing_referents_are_preserved": True,
            "accepted_resolution_requires_governed_review": True,
            "coreference_is_distinct_from_canonical_entity_identity": True,
            "reference_resolution_overlays_without_rewriting_source_mentions": True,
            "source_description_does_not_establish_canonical_identity": True,
            "identity_binding_requires_upstream_identity_governance": True,
            "machine_resolution_output_is_advisory": True,
            "resolution_is_not_truth_verdict": True,
        },
        "boundaries": {
            "core_autonomously_selects_referent": False,
            "resolution_score_establishes_identity": False,
            "coreference_link_establishes_canonical_identity": False,
            "accepted_resolution_rewrites_v410_source": False,
            "source_description_establishes_entity_identity": False,
            "referential_identity_binding_merges_entities": False,
            "identity_graph_mutation_performed": False,
            "relationship_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
            "context_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "extends_v420_discourse_structure_rhetorical_semantics": True,
            "closes_v410_v420_reference_deferral": True,
            "prepares_v440_temporal_spatial_language_grounding": True,
            "prepares_v450_epistemic_modal_negation_certainty": True,
            "prepares_v460_pragmatic_meaning_speech_act_intent": True,
            "prepares_v470_cross_document_context_graph": True,
            "prepares_v480_multilingual_context_alignment": True,
            "prepares_v490_contextual_semantic_evaluation": True,
        },
        "reference": {
            "discourse_semantics_release": bundle.discourse_semantics.release,
            "discourse_semantics_fingerprint_sha256": bundle.discourse_semantics.fingerprint(),
            "v410_unresolved_mentions_preserved": sum(
                x.mention_kind.value == "unresolved-reference"
                for x in bundle.discourse_semantics.context_semantics.mentions
            ),
            "reference_expressions": len(bundle.reference_expressions),
            "referents": len(bundle.referents),
            "candidate_sets": len(bundle.candidate_sets),
            "candidates": len(bundle.candidates),
            "accepted_candidate_sets": len(accepted_sets),
            "coreference_links": len(bundle.coreference_links),
            "coreference_chains": len(bundle.coreference_chains),
            "identity_bindings": len(bundle.identity_bindings),
            "deferred_identity_bindings": sum(x.state == IdentityBindingState.deferred for x in bundle.identity_bindings),
            "resolved_reference_expressions": len(bundle.reference_expressions) - unresolved_expressions,
            "unresolved_reference_expressions": unresolved_expressions,
            "interpretations": len(bundle.interpretations),
            "snapshots": len(bundle.snapshots),
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
        "database_migration": "none",
    }
