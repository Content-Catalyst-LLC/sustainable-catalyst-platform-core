from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .contextual_memory_semantic_state import (
    ContextualMemorySemanticStateBundle,
    MemoryRevisionState,
    SemanticMemoryKind,
    reference_contextual_memory_semantic_state_bundle,
)

CORE_RELEASE = "4.12.0"
CONTRACT_VERSION = "sc.core.context-retrieval-relevance-intelligence.v1"
PREDECESSOR_CONTRACT = "sc.core.contextual-memory-semantic-state-foundation.v1"


class RetrievalQueryKind(str, Enum):
    targeted_context = "targeted-context"
    cross_document = "cross-document"
    multilingual = "multilingual"
    investigation = "investigation"
    research_project = "research-project"


class RetrievalMethodKind(str, Enum):
    semantic_anchor = "semantic-anchor"
    memory_kind = "memory-kind"
    scope = "scope"
    contextual_link = "contextual-link"
    qualification = "qualification"
    unresolved_state = "unresolved-state"
    multilingual_alignment = "multilingual-alignment"
    hybrid = "hybrid"


class RelevanceSignalKind(str, Enum):
    semantic_anchor_match = "semantic-anchor-match"
    preferred_memory_kind = "preferred-memory-kind"
    scope_match = "scope-match"
    contextual_link_support = "contextual-link-support"
    qualification_preservation = "qualification-preservation"
    unresolved_context_materiality = "unresolved-context-materiality"
    current_revision = "current-revision"


class RetrievalReviewState(str, Enum):
    generated = "generated"
    reviewed = "reviewed"
    accepted = "accepted"
    disputed = "disputed"


class ContextRetrievalPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    predecessor_memory_objects_remain_immutable: Literal[True] = True
    retrieval_scope_must_be_explicit: Literal[True] = True
    ranking_must_be_explainable: Literal[True] = True
    qualifications_must_travel_with_results: Literal[True] = True
    unresolved_context_must_not_be_silently_dropped: Literal[True] = True
    current_revision_is_default_but_superseded_history_remains_addressable: Literal[True] = True
    multilingual_lineage_must_be_preserved: Literal[True] = True
    candidate_generation_and_ranking_are_distinct: Literal[True] = True
    external_similarity_runtime_output_is_advisory: Literal[True] = True
    retrieval_rank_establishes_truth: Literal[False] = False
    relevance_score_is_evidence_weight: Literal[False] = False
    semantic_similarity_establishes_equivalence: Literal[False] = False
    scope_proximity_establishes_authority: Literal[False] = False
    provenance_completeness_establishes_credibility: Literal[False] = False
    retrieval_frequency_increases_truth_or_authority: Literal[False] = False
    retrieval_mutates_memory: Literal[False] = False
    context_graph_mutation_authorized: Literal[False] = False
    identity_graph_mutation_authorized: Literal[False] = False
    evidence_graph_mutation_authorized: Literal[False] = False
    knowledge_graph_mutation_authorized: Literal[False] = False


class ContextRetrievalQuery(BaseModel):
    query_id: str = Field(min_length=3, max_length=500)
    kind: RetrievalQueryKind
    question: str = Field(min_length=3, max_length=4000)
    requested_scope_refs: list[str] = Field(min_length=1)
    preferred_memory_kinds: list[SemanticMemoryKind] = Field(default_factory=list)
    semantic_anchor_refs: list[str] = Field(default_factory=list)
    qualification_refs: list[str] = Field(default_factory=list)
    language_tags: list[str] = Field(default_factory=list)
    methods: list[RetrievalMethodKind] = Field(min_length=1)
    preserve_unresolved: Literal[True] = True
    include_superseded: bool = False
    max_results: int = Field(default=10, ge=1, le=100)
    query_does_not_assert_truth_or_identity: Literal[True] = True

    @model_validator(mode="after")
    def validate_unique_refs(self):
        for values, label in [
            (self.requested_scope_refs, "requested_scope_refs"),
            ([x.value for x in self.preferred_memory_kinds], "preferred_memory_kinds"),
            (self.semantic_anchor_refs, "semantic_anchor_refs"),
            (self.qualification_refs, "qualification_refs"),
            (self.language_tags, "language_tags"),
            ([x.value for x in self.methods], "methods"),
        ]:
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RelevanceSignal(BaseModel):
    signal_id: str = Field(min_length=3, max_length=500)
    candidate_ref: str = Field(min_length=3, max_length=500)
    kind: RelevanceSignalKind
    raw_score: float = Field(ge=0.0, le=1.0)
    weight: float = Field(gt=0.0, le=1.0)
    contribution: float = Field(ge=0.0, le=1.0)
    source_refs: list[str] = Field(min_length=1)
    explanation: str = Field(min_length=3, max_length=2000)
    advisory: Literal[True] = True
    signal_does_not_establish_truth_authority_or_evidence_weight: Literal[True] = True

    @model_validator(mode="after")
    def validate_contribution(self):
        if abs(self.contribution - (self.raw_score * self.weight)) > 1e-8:
            raise ValueError("relevance contribution must equal raw_score * weight")
        if len(self.source_refs) != len(set(self.source_refs)):
            raise ValueError("signal source_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RetrievalCandidate(BaseModel):
    candidate_id: str = Field(min_length=3, max_length=500)
    memory_ref: str = Field(min_length=3, max_length=500)
    revision_ref: str = Field(min_length=3, max_length=500)
    scope_ref: str = Field(min_length=3, max_length=500)
    memory_kind: SemanticMemoryKind
    retrieval_methods: list[RetrievalMethodKind] = Field(min_length=1)
    signal_refs: list[str] = Field(min_length=1)
    aggregate_relevance_score: float = Field(ge=0.0, le=1.0)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    current_revision: bool
    review_state: RetrievalReviewState = RetrievalReviewState.generated
    reviewer_ref: str | None = Field(default=None, max_length=500)
    explanation: str = Field(min_length=3, max_length=3000)
    rankable: Literal[True] = True
    candidate_is_context_not_fact: Literal[True] = True

    @model_validator(mode="after")
    def validate_candidate(self):
        for values, label in [
            ([x.value for x in self.retrieval_methods], "retrieval_methods"),
            (self.signal_refs, "signal_refs"),
            (self.qualification_refs, "qualification_refs"),
            (self.unresolved_refs, "unresolved_refs"),
        ]:
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        if self.review_state in {RetrievalReviewState.reviewed, RetrievalReviewState.accepted, RetrievalReviewState.disputed} and not self.reviewer_ref:
            raise ValueError("reviewed/accepted/disputed retrieval candidate requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RankedRetrievalResult(BaseModel):
    result_id: str = Field(min_length=3, max_length=500)
    candidate_ref: str = Field(min_length=3, max_length=500)
    rank: int = Field(ge=1)
    relevance_score: float = Field(ge=0.0, le=1.0)
    selected: Literal[True] = True
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    selection_reason: str = Field(min_length=3, max_length=2000)
    result_rank_is_not_truth_or_evidence_rank: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextRetrievalResultSet(BaseModel):
    result_set_id: str = Field(min_length=3, max_length=500)
    query_ref: str = Field(min_length=3, max_length=500)
    candidate_refs: list[str] = Field(min_length=1)
    results: list[RankedRetrievalResult] = Field(min_length=1)
    omitted_candidate_refs: list[str] = Field(default_factory=list)
    preserves_unresolved_context: Literal[True] = True
    ranking_explanations_required: Literal[True] = True
    result_set_does_not_establish_truth_authority_or_evidence_weight: Literal[True] = True

    @model_validator(mode="after")
    def validate_ranks(self):
        ranks = [x.rank for x in self.results]
        if ranks != list(range(1, len(ranks) + 1)):
            raise ValueError("retrieval result ranks must be contiguous and ordered")
        refs = [x.candidate_ref for x in self.results]
        if len(refs) != len(set(refs)):
            raise ValueError("retrieval result candidates must be unique")
        if not set(refs).issubset(set(self.candidate_refs)):
            raise ValueError("retrieval results must resolve to candidate_refs")
        if set(self.omitted_candidate_refs) & set(refs):
            raise ValueError("omitted candidates cannot also be selected")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RetrievalProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3, max_length=500)
    query_ref: str = Field(min_length=3, max_length=500)
    predecessor_memory_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    subject_refs: list[str] = Field(min_length=1)
    source_refs: list[str] = Field(min_length=1)
    produced_by_ref: str = Field(min_length=3, max_length=500)
    notes: list[str] = Field(default_factory=list)
    replayable: Literal[True] = True
    provenance_does_not_establish_truth_authority_or_credibility: Literal[True] = True

    @model_validator(mode="after")
    def validate_unique_refs(self):
        if len(self.subject_refs) != len(set(self.subject_refs)):
            raise ValueError("provenance subject_refs must be unique")
        if len(self.source_refs) != len(set(self.source_refs)):
            raise ValueError("provenance source_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextRetrievalSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    predecessor_memory_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    query_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_fingerprints: dict[str, str] = Field(min_length=1)
    signal_fingerprints: dict[str, str] = Field(min_length=1)
    result_set_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    deterministic_retrieval_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_is_reproducible_retrieval_state_not_truth_freeze: Literal[True] = True

    @model_validator(mode="after")
    def validate_hash_maps(self):
        for mapping in (self.candidate_fingerprints, self.signal_fingerprints):
            for value in mapping.values():
                if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                    raise ValueError("retrieval snapshot maps must contain sha256 hex")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextRetrievalRelevanceBundle(BaseModel):
    release: Literal["4.12.0"] = "4.12.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    policy: ContextRetrievalPolicy
    predecessor_memory: ContextualMemorySemanticStateBundle
    queries: list[ContextRetrievalQuery] = Field(min_length=1)
    signals: list[RelevanceSignal] = Field(min_length=1)
    candidates: list[RetrievalCandidate] = Field(min_length=1)
    result_sets: list[ContextRetrievalResultSet] = Field(min_length=1)
    provenance_records: list[RetrievalProvenanceRecord] = Field(min_length=1)
    snapshots: list[ContextRetrievalSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.predecessor_memory.release != "4.11.0" or self.predecessor_memory.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.12 must preserve governed v4.11 contextual memory predecessor")

        def unique(values: list[str], label: str):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")

        unique([x.query_id for x in self.queries], "query ids")
        unique([x.signal_id for x in self.signals], "signal ids")
        unique([x.candidate_id for x in self.candidates], "candidate ids")
        unique([x.result_set_id for x in self.result_sets], "result set ids")
        unique([x.provenance_id for x in self.provenance_records], "provenance ids")
        unique([x.snapshot_id for x in self.snapshots], "snapshot ids")

        scopes = {x.scope_id for x in self.predecessor_memory.scopes}
        memories = {x.memory_id: x for x in self.predecessor_memory.memories}
        revisions = {x.revision_id: x for x in self.predecessor_memory.revisions}
        qualifications = {x.qualification_id for x in self.predecessor_memory.predecessor_runtime.qualifications}
        links = {x.link_id for x in self.predecessor_memory.links}
        contextual_refs = set().union(
            *[set(x.external_context_refs) for x in self.predecessor_memory.scopes],
            *[set(x.source_artifact_refs) | set(x.qualification_refs) | set(x.unresolved_refs) for x in self.predecessor_memory.memories],
            *[set(x.source_artifact_refs) | set(x.qualification_refs) | set(x.unresolved_refs) for x in self.predecessor_memory.revisions],
        )
        queries = {x.query_id: x for x in self.queries}
        signals = {x.signal_id: x for x in self.signals}
        candidates = {x.candidate_id: x for x in self.candidates}

        for q in self.queries:
            if not set(q.requested_scope_refs).issubset(scopes):
                raise ValueError("query requested_scope_refs must resolve to v4.11 memory scopes")
            if not set(q.qualification_refs).issubset(qualifications):
                raise ValueError("query qualification_refs must resolve to v4.10 qualifications carried by v4.11")

        signal_refs_by_candidate: dict[str, set[str]] = {x.candidate_id: set() for x in self.candidates}
        for s in self.signals:
            if s.candidate_ref not in candidates:
                raise ValueError("relevance signal candidate_ref must resolve")
            signal_refs_by_candidate[s.candidate_ref].add(s.signal_id)
            for ref in s.source_refs:
                if ref not in scopes and ref not in memories and ref not in revisions and ref not in qualifications and ref not in links and ref not in contextual_refs:
                    raise ValueError("relevance signal source_refs must resolve to predecessor memory context")

        current_revisions = {m.current_revision_ref for m in memories.values()}
        for c in self.candidates:
            if c.memory_ref not in memories or c.revision_ref not in revisions or c.scope_ref not in scopes:
                raise ValueError("retrieval candidate memory/revision/scope refs must resolve")
            if revisions[c.revision_ref].memory_ref != c.memory_ref:
                raise ValueError("candidate revision_ref must belong to candidate memory")
            if memories[c.memory_ref].scope_ref != c.scope_ref:
                raise ValueError("candidate scope_ref must match predecessor memory scope")
            if memories[c.memory_ref].kind != c.memory_kind:
                raise ValueError("candidate memory_kind must match predecessor memory")
            if set(c.signal_refs) != signal_refs_by_candidate[c.candidate_id]:
                raise ValueError("candidate signal_refs must exactly identify its relevance signals")
            expected_score = sum(signals[x].contribution for x in c.signal_refs)
            if abs(c.aggregate_relevance_score - expected_score) > 1e-8:
                raise ValueError("candidate aggregate_relevance_score must equal signal contributions")
            if c.current_revision != (c.revision_ref in current_revisions):
                raise ValueError("candidate current_revision flag is inconsistent")
            if not set(c.qualification_refs).issubset(qualifications):
                raise ValueError("candidate qualification_refs must resolve")
            if self.queries[0].preserve_unresolved and memories[c.memory_ref].unresolved_refs:
                if not set(memories[c.memory_ref].unresolved_refs).issubset(set(c.unresolved_refs)):
                    raise ValueError("material unresolved predecessor refs must be preserved on retrieval candidate")

        for rs in self.result_sets:
            if rs.query_ref not in queries:
                raise ValueError("result set query_ref must resolve")
            if not set(rs.candidate_refs).issubset(candidates):
                raise ValueError("result set candidate_refs must resolve")
            if not set(rs.omitted_candidate_refs).issubset(set(rs.candidate_refs)):
                raise ValueError("result set omitted candidates must be generated candidates")
            q = queries[rs.query_ref]
            if len(rs.results) > q.max_results:
                raise ValueError("result set exceeds query max_results")
            last = 2.0
            for result in rs.results:
                c = candidates[result.candidate_ref]
                if abs(result.relevance_score - c.aggregate_relevance_score) > 1e-8:
                    raise ValueError("ranked result score must match candidate relevance score")
                if result.relevance_score > last + 1e-8:
                    raise ValueError("results must be sorted by non-increasing relevance score")
                last = result.relevance_score
                if set(result.qualification_refs) != set(c.qualification_refs):
                    raise ValueError("ranked result must preserve candidate qualifications")
                if q.preserve_unresolved and set(result.unresolved_refs) != set(c.unresolved_refs):
                    raise ValueError("ranked result must preserve candidate unresolved refs")

        memory_fp = self.predecessor_memory.fingerprint()
        all_subjects = set(queries) | set(signals) | set(candidates) | {x.result_set_id for x in self.result_sets}
        for p in self.provenance_records:
            if p.query_ref not in queries:
                raise ValueError("retrieval provenance query_ref must resolve")
            if p.predecessor_memory_fingerprint_sha256 != memory_fp:
                raise ValueError("retrieval provenance predecessor fingerprint must match v4.11 memory bundle")
            if not set(p.subject_refs).issubset(all_subjects):
                raise ValueError("retrieval provenance subject_refs must resolve")

        result_sets = {x.result_set_id: x for x in self.result_sets}
        for snap in self.snapshots:
            if snap.predecessor_memory_fingerprint_sha256 != memory_fp:
                raise ValueError("retrieval snapshot predecessor fingerprint must match v4.11")
            if snap.query_fingerprint_sha256 not in {x.fingerprint() for x in self.queries}:
                raise ValueError("retrieval snapshot query fingerprint must resolve")
            if snap.candidate_fingerprints != {x.candidate_id: x.fingerprint() for x in self.candidates}:
                raise ValueError("retrieval snapshot candidate fingerprints must match")
            if snap.signal_fingerprints != {x.signal_id: x.fingerprint() for x in self.signals}:
                raise ValueError("retrieval snapshot signal fingerprints must match")
            if snap.result_set_fingerprint_sha256 not in {x.fingerprint() for x in result_sets.values()}:
                raise ValueError("retrieval snapshot result set fingerprint must resolve")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


_SIGNAL_WEIGHTS = {
    RelevanceSignalKind.semantic_anchor_match: 0.35,
    RelevanceSignalKind.preferred_memory_kind: 0.15,
    RelevanceSignalKind.scope_match: 0.10,
    RelevanceSignalKind.contextual_link_support: 0.15,
    RelevanceSignalKind.qualification_preservation: 0.10,
    RelevanceSignalKind.unresolved_context_materiality: 0.10,
    RelevanceSignalKind.current_revision: 0.05,
}


def _signal(candidate_id: str, idx: int, kind: RelevanceSignalKind, raw: float, refs: list[str], explanation: str) -> RelevanceSignal:
    weight = _SIGNAL_WEIGHTS[kind]
    return RelevanceSignal(
        signal_id=f"relevance-signal:{candidate_id.split(':', 1)[1]}:{idx:02d}",
        candidate_ref=candidate_id,
        kind=kind,
        raw_score=raw,
        weight=weight,
        contribution=raw * weight,
        source_refs=refs,
        explanation=explanation,
    )


@lru_cache(maxsize=1)
def reference_context_retrieval_relevance_bundle() -> ContextRetrievalRelevanceBundle:
    memory = reference_contextual_memory_semantic_state_bundle()
    query = ContextRetrievalQuery(
        query_id="retrieval-query:actor-continuity-cross-language-policy",
        kind=RetrievalQueryKind.research_project,
        question=(
            "What governed context should be retrieved when reviewing whether the ministry-agency "
            "continuity hypothesis should inform analysis of a policy measure across languages?"
        ),
        requested_scope_refs=[
            "memory-scope:research-project:contextual-intelligence-reference",
            "memory-scope:investigation:cross-source-policy",
        ],
        preferred_memory_kinds=[
            SemanticMemoryKind.cross_document_continuity,
            SemanticMemoryKind.epistemic_stance,
            SemanticMemoryKind.multilingual_divergence,
        ],
        semantic_anchor_refs=[
            "thread:actor-continuity:candidate",
            "assessment:ministry-explicit-uncertainty",
            "universal-equivalence:治理-governance-gobernanza",
        ],
        qualification_refs=[
            "qualification:05:source-uncertainty-preserved",
            "qualification:07:continuity-hypothesis-unresolved",
            "qualification:08:cultural-divergence-preserved",
        ],
        language_tags=["zh", "en", "es"],
        methods=[
            RetrievalMethodKind.semantic_anchor,
            RetrievalMethodKind.memory_kind,
            RetrievalMethodKind.scope,
            RetrievalMethodKind.contextual_link,
            RetrievalMethodKind.qualification,
            RetrievalMethodKind.unresolved_state,
            RetrievalMethodKind.multilingual_alignment,
            RetrievalMethodKind.hybrid,
        ],
        max_results=5,
    )

    memories = {x.memory_id: x for x in memory.memories}
    revisions = {x.revision_id: x for x in memory.revisions}

    specs = [
        (
            "memory:continuity:actor-ministry-agency",
            [1.00, 1.00, 1.00, 1.00, 0.90, 1.00, 1.00],
            "Directly matches the requested actor-continuity thread and remains unresolved; it is the primary contextual candidate.",
        ),
        (
            "memory:multilingual-divergence:governance",
            [0.78, 1.00, 1.00, 1.00, 0.90, 1.00, 1.00],
            "Cross-language governance divergence directly conditions whether continuity can be interpreted consistently across Chinese, English, and Spanish.",
        ),
        (
            "memory:epistemic-state:ministry-uncertainty",
            [0.75, 1.00, 0.75, 1.00, 1.00, 1.00, 1.00],
            "The source-level uncertainty attached to the ministry context materially qualifies later continuity reasoning.",
        ),
        (
            "memory:referential-ambiguity:it",
            [0.55, 0.00, 0.55, 0.00, 0.80, 1.00, 1.00],
            "Referential ambiguity is less directly related but remains material context because unresolved reference can alter downstream source interpretation.",
        ),
        (
            "memory:runtime-summary:v4.10-qualified-complete",
            [0.30, 0.00, 0.80, 0.00, 1.00, 0.20, 1.00],
            "The qualified-complete runtime summary provides reproducibility and qualification context but does not dominate semantic relevance.",
        ),
        (
            "memory:geographic-grounding:brussels",
            [0.20, 0.00, 0.60, 0.00, 0.80, 0.20, 1.00],
            "Brussels grounding is valid governed context but is peripheral to the actor-continuity and multilingual policy question.",
        ),
    ]

    candidates: list[RetrievalCandidate] = []
    signals: list[RelevanceSignal] = []
    signal_kinds = list(_SIGNAL_WEIGHTS)
    for n, (memory_id, raw_scores, explanation) in enumerate(specs, start=1):
        m = memories[memory_id]
        rev = revisions[m.current_revision_ref]
        cid = f"retrieval-candidate:{n:02d}:{memory_id.split(':', 1)[1]}"
        source_by_kind = {
            RelevanceSignalKind.semantic_anchor_match: [m.memory_id, rev.revision_id],
            RelevanceSignalKind.preferred_memory_kind: [m.memory_id],
            RelevanceSignalKind.scope_match: [m.scope_ref],
            RelevanceSignalKind.contextual_link_support: [
                x.link_id for x in memory.links if x.source_memory_ref == memory_id or x.target_memory_ref == memory_id
            ] or [m.memory_id],
            RelevanceSignalKind.qualification_preservation: m.qualification_refs or [m.memory_id],
            RelevanceSignalKind.unresolved_context_materiality: m.unresolved_refs or [m.memory_id],
            RelevanceSignalKind.current_revision: [rev.revision_id],
        }
        local: list[RelevanceSignal] = []
        for idx, (kind, raw) in enumerate(zip(signal_kinds, raw_scores), start=1):
            s = _signal(
                cid,
                idx,
                kind,
                raw,
                source_by_kind[kind],
                f"{kind.value} contributes {raw * _SIGNAL_WEIGHTS[kind]:.4f} to this advisory relevance score.",
            )
            local.append(s)
            signals.append(s)
        score = sum(x.contribution for x in local)
        methods = [RetrievalMethodKind.hybrid]
        if raw_scores[0] > 0:
            methods.append(RetrievalMethodKind.semantic_anchor)
        if raw_scores[1] > 0:
            methods.append(RetrievalMethodKind.memory_kind)
        if raw_scores[2] > 0:
            methods.append(RetrievalMethodKind.scope)
        if raw_scores[3] > 0:
            methods.append(RetrievalMethodKind.contextual_link)
        if raw_scores[4] > 0:
            methods.append(RetrievalMethodKind.qualification)
        if raw_scores[5] > 0:
            methods.append(RetrievalMethodKind.unresolved_state)
        if m.kind == SemanticMemoryKind.multilingual_divergence:
            methods.append(RetrievalMethodKind.multilingual_alignment)
        candidates.append(
            RetrievalCandidate(
                candidate_id=cid,
                memory_ref=m.memory_id,
                revision_ref=rev.revision_id,
                scope_ref=m.scope_ref,
                memory_kind=m.kind,
                retrieval_methods=methods,
                signal_refs=[x.signal_id for x in local],
                aggregate_relevance_score=score,
                qualification_refs=m.qualification_refs,
                unresolved_refs=m.unresolved_refs,
                current_revision=True,
                review_state=RetrievalReviewState.reviewed,
                reviewer_ref="reviewer:context-retrieval-reference",
                explanation=explanation,
            )
        )

    ranked = sorted(candidates, key=lambda x: (-x.aggregate_relevance_score, x.candidate_id))
    selected = ranked[: query.max_results]
    omitted = ranked[query.max_results :]
    results = [
        RankedRetrievalResult(
            result_id=f"retrieval-result:{i:02d}",
            candidate_ref=c.candidate_id,
            rank=i,
            relevance_score=c.aggregate_relevance_score,
            qualification_refs=c.qualification_refs,
            unresolved_refs=c.unresolved_refs,
            selection_reason=c.explanation,
        )
        for i, c in enumerate(selected, start=1)
    ]
    result_set = ContextRetrievalResultSet(
        result_set_id="retrieval-result-set:actor-continuity-cross-language-policy:v1",
        query_ref=query.query_id,
        candidate_refs=[x.candidate_id for x in candidates],
        results=results,
        omitted_candidate_refs=[x.candidate_id for x in omitted],
    )

    provenance = RetrievalProvenanceRecord(
        provenance_id="retrieval-provenance:actor-continuity-cross-language-policy:v1",
        query_ref=query.query_id,
        predecessor_memory_fingerprint_sha256=memory.fingerprint(),
        subject_refs=[query.query_id, *[x.candidate_id for x in candidates], result_set.result_set_id],
        source_refs=[memory.snapshots[0].snapshot_id, memory.checkpoints[0].checkpoint_id, *[x.memory_id for x in memory.memories]],
        produced_by_ref=CONTRACT_VERSION,
        notes=[
            "Reference ranking is a deterministic governed fixture for retrieval mechanics; it is not an empirical model-performance claim.",
            "All qualifications and unresolved references remain attached to selected results.",
        ],
    )

    candidate_fps = {x.candidate_id: x.fingerprint() for x in candidates}
    signal_fps = {x.signal_id: x.fingerprint() for x in signals}
    deterministic = canonical_sha256({
        "predecessor_memory_fingerprint_sha256": memory.fingerprint(),
        "query_fingerprint_sha256": query.fingerprint(),
        "candidate_fingerprints": candidate_fps,
        "signal_fingerprints": signal_fps,
        "result_set_fingerprint_sha256": result_set.fingerprint(),
    })
    snapshot = ContextRetrievalSnapshot(
        snapshot_id="retrieval-snapshot:actor-continuity-cross-language-policy:v1",
        predecessor_memory_fingerprint_sha256=memory.fingerprint(),
        query_fingerprint_sha256=query.fingerprint(),
        candidate_fingerprints=candidate_fps,
        signal_fingerprints=signal_fps,
        result_set_fingerprint_sha256=result_set.fingerprint(),
        deterministic_retrieval_fingerprint_sha256=deterministic,
    )

    return ContextRetrievalRelevanceBundle(
        policy=ContextRetrievalPolicy(policy_id="policy:context-retrieval-relevance:v1"),
        predecessor_memory=memory,
        queries=[query],
        signals=signals,
        candidates=candidates,
        result_sets=[result_set],
        provenance_records=[provenance],
        snapshots=[snapshot],
    )


def contract_document() -> dict:
    bundle = reference_context_retrieval_relevance_bundle()
    query = bundle.queries[0]
    result_set = bundle.result_sets[0]
    top = result_set.results[0]
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "identity": {
            "product": "Sustainable Catalyst Platform Core",
            "build": "Context Retrieval & Relevance Intelligence",
            "major_api": "v4",
        },
        "principles": {
            "retrieval_scope_must_be_explicit": True,
            "ranking_must_be_explainable": True,
            "qualifications_must_travel_with_results": True,
            "unresolved_context_must_not_be_silently_dropped": True,
            "candidate_generation_and_ranking_are_distinct": True,
            "current_revision_is_default_but_history_remains_addressable": True,
            "multilingual_lineage_must_be_preserved": True,
            "external_similarity_runtime_output_is_advisory": True,
        },
        "boundaries": {
            "retrieval_rank_establishes_truth": False,
            "relevance_score_is_evidence_weight": False,
            "semantic_similarity_establishes_equivalence": False,
            "scope_proximity_establishes_authority": False,
            "provenance_completeness_establishes_credibility": False,
            "retrieval_frequency_increases_truth_or_authority": False,
            "retrieval_mutates_memory": False,
            "context_graph_mutation_performed": False,
            "identity_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
            "knowledge_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "extends_v4110_contextual_memory_semantic_state": True,
            "prepares_v4130_claim_alignment_contradiction_intelligence": True,
            "prepares_v4140_evidence_context_integration": True,
            "prepares_v4150_contextual_causal_language_mechanism_intelligence": True,
            "prepares_v4160_narrative_framing_perspective_intelligence": True,
            "prepares_v4200_unified_contextual_reasoning_runtime": True,
        },
        "reference": {
            "predecessor_release": bundle.predecessor_memory.release,
            "predecessor_fingerprint_sha256": bundle.predecessor_memory.fingerprint(),
            "queries": len(bundle.queries),
            "generated_candidates": len(bundle.candidates),
            "relevance_signals": len(bundle.signals),
            "selected_results": len(result_set.results),
            "omitted_candidates": len(result_set.omitted_candidate_refs),
            "top_result_rank": top.rank,
            "top_result_memory_ref": next(x for x in bundle.candidates if x.candidate_id == top.candidate_ref).memory_ref,
            "top_result_relevance_score": top.relevance_score,
            "results_with_qualifications": sum(1 for x in result_set.results if x.qualification_refs),
            "results_with_unresolved_context": sum(1 for x in result_set.results if x.unresolved_refs),
            "snapshots": len(bundle.snapshots),
            "deterministic_reference_ranking_is_model_performance_claim": False,
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
        "database_migration": "none",
    }
