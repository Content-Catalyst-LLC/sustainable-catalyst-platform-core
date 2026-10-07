from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .context_retrieval_relevance import (
    ContextRetrievalRelevanceBundle,
    reference_context_retrieval_relevance_bundle,
)
from .epistemic_modal_negation_certainty import reference_epistemic_modal_negation_certainty_bundle
from .pragmatic_meaning_speech_act_intent import reference_pragmatic_meaning_speech_act_intent_bundle
from .multilingual_context_semantic_alignment import reference_multilingual_context_semantic_alignment_bundle

CORE_RELEASE = "4.13.0"
CONTRACT_VERSION = "sc.core.claim-alignment-agreement-contradiction-intelligence.v1"
PREDECESSOR_CONTRACT = "sc.core.context-retrieval-relevance-intelligence.v1"


class ClaimPolarity(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"
    unknown = "unknown"


class ClaimModality(str, Enum):
    asserted = "asserted"
    possible = "possible"
    probable = "probable"
    hypothetical = "hypothetical"
    uncertain = "uncertain"
    unknown = "unknown"


class ClaimReviewState(str, Enum):
    generated = "generated"
    reviewed = "reviewed"
    accepted = "accepted"
    disputed = "disputed"
    unresolved = "unresolved"


class ClaimRelationKind(str, Enum):
    agreement = "agreement"
    qualified_agreement = "qualified-agreement"
    partial_agreement = "partial-agreement"
    contradiction = "contradiction"
    apparent_contradiction = "apparent-contradiction"
    scope_mismatch = "scope-mismatch"
    distinct_claim = "distinct-claim"
    unresolved = "unresolved"


class AlignmentDimension(str, Enum):
    subject = "subject"
    predicate = "predicate"
    object_scope = "object-scope"
    polarity = "polarity"
    modality = "modality"
    temporal_scope = "temporal-scope"
    spatial_scope = "spatial-scope"
    attribution = "attribution"
    language_semantics = "language-semantics"


class ClaimComparisonPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    predecessor_retrieval_objects_remain_immutable: Literal[True] = True
    claim_surface_and_normalized_semantics_are_both_preserved: Literal[True] = True
    comparison_requires_explicit_scope: Literal[True] = True
    polarity_difference_alone_is_not_contradiction: Literal[True] = True
    modality_mismatch_may_downgrade_contradiction: Literal[True] = True
    temporal_and_spatial_scope_must_be_compared: Literal[True] = True
    attribution_and_source_stance_must_be_preserved: Literal[True] = True
    multilingual_alignment_must_preserve_translation_lineage: Literal[True] = True
    unresolved_identity_must_not_be_silently_collapsed: Literal[True] = True
    competing_relation_assessments_may_coexist: Literal[True] = True
    reviewed_relation_establishes_truth: Literal[False] = False
    contradiction_identifies_false_claim: Literal[False] = False
    agreement_establishes_evidence_validity: Literal[False] = False
    agreement_count_increases_truth: Literal[False] = False
    source_majority_establishes_truth: Literal[False] = False
    alignment_score_is_credibility_score: Literal[False] = False
    contradiction_score_is_deception_score: Literal[False] = False
    claim_comparison_mutates_predecessor_objects: Literal[False] = False
    context_graph_mutation_authorized: Literal[False] = False
    identity_graph_mutation_authorized: Literal[False] = False
    evidence_graph_mutation_authorized: Literal[False] = False
    knowledge_graph_mutation_authorized: Literal[False] = False


class ClaimSourceContext(BaseModel):
    source_context_id: str = Field(min_length=3, max_length=500)
    label: str = Field(min_length=3, max_length=1000)
    language_tag: str = Field(min_length=2, max_length=40)
    source_text: str = Field(min_length=3, max_length=6000)
    predecessor_object_refs: list[str] = Field(default_factory=list)
    derived_representation: bool = False
    source_context_is_not_authority_or_truth: Literal[True] = True

    @model_validator(mode="after")
    def validate_refs(self):
        if len(self.predecessor_object_refs) != len(set(self.predecessor_object_refs)):
            raise ValueError("predecessor_object_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ClaimUnit(BaseModel):
    claim_id: str = Field(min_length=3, max_length=500)
    source_context_ref: str = Field(min_length=3, max_length=500)
    source_object_ref: str = Field(min_length=3, max_length=500)
    surface_text: str = Field(min_length=3, max_length=4000)
    language_tag: str = Field(min_length=2, max_length=40)
    subject_key: str = Field(min_length=1, max_length=500)
    predicate_key: str = Field(min_length=1, max_length=500)
    object_scope_key: str = Field(min_length=1, max_length=500)
    polarity: ClaimPolarity
    modality: ClaimModality
    temporal_scope_ref: str = Field(min_length=1, max_length=500)
    spatial_scope_ref: str = Field(min_length=1, max_length=500)
    attribution_ref: str = Field(min_length=1, max_length=500)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    normalized_for_comparison_only: Literal[True] = True
    normalization_does_not_establish_identity_or_equivalence: Literal[True] = True

    @model_validator(mode="after")
    def validate_unique_refs(self):
        if len(self.qualification_refs) != len(set(self.qualification_refs)):
            raise ValueError("qualification_refs must be unique")
        if len(self.unresolved_refs) != len(set(self.unresolved_refs)):
            raise ValueError("unresolved_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ClaimComparisonQuery(BaseModel):
    query_id: str = Field(min_length=3, max_length=500)
    question: str = Field(min_length=3, max_length=4000)
    predecessor_result_set_ref: str = Field(min_length=3, max_length=500)
    claim_refs: list[str] = Field(min_length=2)
    required_dimensions: list[AlignmentDimension] = Field(min_length=1)
    preserve_qualifications: Literal[True] = True
    preserve_unresolved: Literal[True] = True
    permit_multiple_relation_types: Literal[True] = True
    query_does_not_assert_same_claim_truth_or_identity: Literal[True] = True

    @model_validator(mode="after")
    def validate_unique(self):
        if len(self.claim_refs) != len(set(self.claim_refs)):
            raise ValueError("claim_refs must be unique")
        values = [x.value for x in self.required_dimensions]
        if len(values) != len(set(values)):
            raise ValueError("required_dimensions must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ClaimAlignmentSignal(BaseModel):
    signal_id: str = Field(min_length=3, max_length=500)
    pair_ref: str = Field(min_length=3, max_length=500)
    dimension: AlignmentDimension
    score: float = Field(ge=0.0, le=1.0)
    source_refs: list[str] = Field(min_length=1)
    explanation: str = Field(min_length=3, max_length=3000)
    advisory: Literal[True] = True
    signal_does_not_establish_truth_or_equivalence: Literal[True] = True

    @model_validator(mode="after")
    def validate_unique_refs(self):
        if len(self.source_refs) != len(set(self.source_refs)):
            raise ValueError("source_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ClaimComparisonPair(BaseModel):
    pair_id: str = Field(min_length=3, max_length=500)
    left_claim_ref: str = Field(min_length=3, max_length=500)
    right_claim_ref: str = Field(min_length=3, max_length=500)
    signal_refs: list[str] = Field(min_length=1)
    alignment_score: float = Field(ge=0.0, le=1.0)
    same_claim_candidate: bool
    polarity_conflict: bool
    modality_mismatch: bool
    scope_compatible: bool
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    state: ClaimReviewState = ClaimReviewState.reviewed
    reviewer_ref: str | None = Field(default=None, max_length=500)
    pair_is_comparison_not_equivalence_assertion: Literal[True] = True

    @model_validator(mode="after")
    def validate_pair(self):
        if self.left_claim_ref == self.right_claim_ref:
            raise ValueError("claim comparison pair requires two distinct claims")
        if len(self.signal_refs) != len(set(self.signal_refs)):
            raise ValueError("signal_refs must be unique")
        if len(self.qualification_refs) != len(set(self.qualification_refs)):
            raise ValueError("qualification_refs must be unique")
        if len(self.unresolved_refs) != len(set(self.unresolved_refs)):
            raise ValueError("unresolved_refs must be unique")
        if self.state in {ClaimReviewState.reviewed, ClaimReviewState.accepted, ClaimReviewState.disputed} and not self.reviewer_ref:
            raise ValueError("reviewed/accepted/disputed pair requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ClaimRelationAssessment(BaseModel):
    assessment_id: str = Field(min_length=3, max_length=500)
    pair_ref: str = Field(min_length=3, max_length=500)
    relation_kind: ClaimRelationKind
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=3, max_length=4000)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    state: ClaimReviewState = ClaimReviewState.reviewed
    reviewer_ref: str | None = Field(default=None, max_length=500)
    relation_is_contextual_assessment_not_truth_verdict: Literal[True] = True

    @model_validator(mode="after")
    def validate_assessment(self):
        if self.state in {ClaimReviewState.reviewed, ClaimReviewState.accepted, ClaimReviewState.disputed} and not self.reviewer_ref:
            raise ValueError("reviewed/accepted/disputed assessment requires reviewer_ref")
        if len(self.qualification_refs) != len(set(self.qualification_refs)):
            raise ValueError("qualification_refs must be unique")
        if len(self.unresolved_refs) != len(set(self.unresolved_refs)):
            raise ValueError("unresolved_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ClaimComparisonProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3, max_length=500)
    predecessor_retrieval_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    subject_refs: list[str] = Field(min_length=1)
    method: str = Field(min_length=3, max_length=1000)
    replayable: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ClaimComparisonSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    predecessor_retrieval_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    query_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    claim_fingerprints: dict[str, str]
    pair_fingerprints: dict[str, str]
    assessment_fingerprints: dict[str, str]
    deterministic_comparison_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    supersedable: Literal[True] = True
    snapshot_is_not_truth_certification: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ClaimAlignmentAgreementContradictionBundle(BaseModel):
    release: Literal["4.13.0"] = "4.13.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    policy: ClaimComparisonPolicy
    predecessor_retrieval: ContextRetrievalRelevanceBundle
    source_contexts: list[ClaimSourceContext] = Field(min_length=1)
    claims: list[ClaimUnit] = Field(min_length=2)
    queries: list[ClaimComparisonQuery] = Field(min_length=1)
    signals: list[ClaimAlignmentSignal] = Field(min_length=1)
    pairs: list[ClaimComparisonPair] = Field(min_length=1)
    assessments: list[ClaimRelationAssessment] = Field(min_length=1)
    provenance_records: list[ClaimComparisonProvenanceRecord] = Field(min_length=1)
    snapshots: list[ClaimComparisonSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.predecessor_retrieval.release != "4.12.0" or self.predecessor_retrieval.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.13 must preserve governed v4.12 retrieval predecessor")

        def unique(values: list[str], label: str):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")

        unique([x.source_context_id for x in self.source_contexts], "source context ids")
        unique([x.claim_id for x in self.claims], "claim ids")
        unique([x.query_id for x in self.queries], "query ids")
        unique([x.signal_id for x in self.signals], "signal ids")
        unique([x.pair_id for x in self.pairs], "pair ids")
        unique([x.assessment_id for x in self.assessments], "assessment ids")
        unique([x.provenance_id for x in self.provenance_records], "provenance ids")
        unique([x.snapshot_id for x in self.snapshots], "snapshot ids")

        contexts = {x.source_context_id: x for x in self.source_contexts}
        claims = {x.claim_id: x for x in self.claims}
        queries = {x.query_id: x for x in self.queries}
        signals = {x.signal_id: x for x in self.signals}
        pairs = {x.pair_id: x for x in self.pairs}
        assessments = {x.assessment_id: x for x in self.assessments}
        predecessor_result_sets = {x.result_set_id for x in self.predecessor_retrieval.result_sets}

        predecessor_qualifications = {
            q
            for c in self.predecessor_retrieval.candidates
            for q in c.qualification_refs
        }
        predecessor_unresolved = {
            u
            for c in self.predecessor_retrieval.candidates
            for u in c.unresolved_refs
        }

        for claim in self.claims:
            if claim.source_context_ref not in contexts:
                raise ValueError("claim source_context_ref must resolve")
            if contexts[claim.source_context_ref].language_tag != claim.language_tag:
                raise ValueError("claim language_tag must match source context")
            if not set(claim.qualification_refs).issubset(predecessor_qualifications):
                raise ValueError("claim qualification_refs must resolve to predecessor retrieval context")
            if not set(claim.unresolved_refs).issubset(predecessor_unresolved | {"same-measure:reference-corpus", "same-period:reference-corpus", "direct-vs-total-emissions-scope", "thread:policy-topic-continuity:candidate", "same-policy-object:v48-v47"}):
                raise ValueError("claim unresolved_refs must resolve to governed or explicit v4.13 comparison uncertainty")

        for query in self.queries:
            if query.predecessor_result_set_ref not in predecessor_result_sets:
                raise ValueError("query predecessor_result_set_ref must resolve")
            if not set(query.claim_refs).issubset(claims):
                raise ValueError("query claim_refs must resolve")

        signals_by_pair: dict[str, set[str]] = {x.pair_id: set() for x in self.pairs}
        for signal in self.signals:
            if signal.pair_ref not in pairs:
                raise ValueError("alignment signal pair_ref must resolve")
            signals_by_pair[signal.pair_ref].add(signal.signal_id)
            if len(signal.source_refs) < 1:
                raise ValueError("alignment signal requires source refs")

        for pair in self.pairs:
            if pair.left_claim_ref not in claims or pair.right_claim_ref not in claims:
                raise ValueError("claim pair refs must resolve")
            if set(pair.signal_refs) != signals_by_pair[pair.pair_id]:
                raise ValueError("pair signal_refs must exactly identify pair signals")
            expected = sum(signals[x].score for x in pair.signal_refs) / len(pair.signal_refs)
            if abs(pair.alignment_score - expected) > 1e-8:
                raise ValueError("pair alignment_score must equal mean alignment signal score")
            expected_polarity_conflict = claims[pair.left_claim_ref].polarity != claims[pair.right_claim_ref].polarity
            if pair.polarity_conflict != expected_polarity_conflict:
                raise ValueError("pair polarity_conflict inconsistent with claim polarity")
            expected_modality_mismatch = claims[pair.left_claim_ref].modality != claims[pair.right_claim_ref].modality
            if pair.modality_mismatch != expected_modality_mismatch:
                raise ValueError("pair modality_mismatch inconsistent with claim modality")

        assessments_by_pair: dict[str, list[ClaimRelationAssessment]] = {x.pair_id: [] for x in self.pairs}
        for assessment in self.assessments:
            if assessment.pair_ref not in pairs:
                raise ValueError("assessment pair_ref must resolve")
            assessments_by_pair[assessment.pair_ref].append(assessment)
            pair = pairs[assessment.pair_ref]
            if assessment.relation_kind == ClaimRelationKind.contradiction:
                if not pair.polarity_conflict or pair.modality_mismatch or not pair.scope_compatible:
                    raise ValueError("strict contradiction requires polarity conflict, compatible scope, and aligned modality")
            if assessment.relation_kind == ClaimRelationKind.apparent_contradiction:
                if not pair.polarity_conflict:
                    raise ValueError("apparent contradiction requires polarity conflict")
            if assessment.relation_kind == ClaimRelationKind.agreement:
                if pair.polarity_conflict or not pair.scope_compatible:
                    raise ValueError("agreement requires compatible scope and no polarity conflict")
        if any(not values for values in assessments_by_pair.values()):
            raise ValueError("every claim pair requires at least one relation assessment")

        predecessor_fp = self.predecessor_retrieval.fingerprint()
        subjects = set(claims) | set(queries) | set(pairs) | set(assessments)
        for prov in self.provenance_records:
            if prov.predecessor_retrieval_fingerprint_sha256 != predecessor_fp:
                raise ValueError("provenance predecessor fingerprint must match v4.12")
            if not set(prov.subject_refs).issubset(subjects):
                raise ValueError("provenance subject_refs must resolve")

        for snap in self.snapshots:
            if snap.predecessor_retrieval_fingerprint_sha256 != predecessor_fp:
                raise ValueError("snapshot predecessor fingerprint must match v4.12")
            if snap.query_fingerprint_sha256 not in {x.fingerprint() for x in self.queries}:
                raise ValueError("snapshot query fingerprint must resolve")
            if snap.claim_fingerprints != {x.claim_id: x.fingerprint() for x in self.claims}:
                raise ValueError("snapshot claim fingerprints must match")
            if snap.pair_fingerprints != {x.pair_id: x.fingerprint() for x in self.pairs}:
                raise ValueError("snapshot pair fingerprints must match")
            if snap.assessment_fingerprints != {x.assessment_id: x.fingerprint() for x in self.assessments}:
                raise ValueError("snapshot assessment fingerprints must match")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def _signal(pair_id: str, idx: int, dimension: AlignmentDimension, score: float, refs: list[str], explanation: str) -> ClaimAlignmentSignal:
    return ClaimAlignmentSignal(
        signal_id=f"claim-signal:{pair_id.split(':', 1)[1]}:{idx:02d}",
        pair_ref=pair_id,
        dimension=dimension,
        score=score,
        source_refs=refs,
        explanation=explanation,
    )


@lru_cache(maxsize=1)
def reference_claim_alignment_agreement_contradiction_bundle() -> ClaimAlignmentAgreementContradictionBundle:
    retrieval = reference_context_retrieval_relevance_bundle()
    epistemic = reference_epistemic_modal_negation_certainty_bundle()
    pragmatic = reference_pragmatic_meaning_speech_act_intent_bundle()
    multilingual = reference_multilingual_context_semantic_alignment_bundle()

    result_set = retrieval.result_sets[0]
    candidate_by_memory = {x.memory_ref: x for x in retrieval.candidates}
    q_actor = candidate_by_memory["memory:continuity:actor-ministry-agency"].qualification_refs
    u_actor = candidate_by_memory["memory:continuity:actor-ministry-agency"].unresolved_refs
    q_epistemic = candidate_by_memory["memory:epistemic-state:ministry-uncertainty"].qualification_refs
    q_multilingual = candidate_by_memory["memory:multilingual-divergence:governance"].qualification_refs

    source_contexts = [
        ClaimSourceContext(
            source_context_id="claim-source:v45:epistemic-report",
            label="v4.5 epistemic reference report",
            language_tag="en",
            source_text=epistemic.source_excerpts[0].content,
            predecessor_object_refs=["proposition:measure-no-emissions-reduction", "proposition:may-lower-costs"],
        ),
        ClaimSourceContext(
            source_context_id="claim-source:v46:public-hearing",
            label="v4.6 pragmatic public-hearing reference",
            language_tag="en",
            source_text=pragmatic.source_excerpts[0].content,
            predecessor_object_refs=["content:measure-may-reduce-emissions", "speech-act:assert-measure"],
        ),
        ClaimSourceContext(
            source_context_id="claim-source:v48:zh-original",
            label="v4.8 Chinese original-language reference",
            language_tag="zh",
            source_text=next(x.content for x in multilingual.representations if x.language_ref == "language:zh"),
            predecessor_object_refs=["context-unit:zh:proposal-cost:v1"],
        ),
        ClaimSourceContext(
            source_context_id="claim-source:v48:en-derived",
            label="v4.8 English derived representation",
            language_tag="en",
            source_text=next(x.content for x in multilingual.representations if x.language_ref == "language:en"),
            predecessor_object_refs=["context-unit:en:proposal-cost:v1"],
            derived_representation=True,
        ),
        ClaimSourceContext(
            source_context_id="claim-source:v413:audit",
            label="v4.13 controlled audit comparison fixture",
            language_tag="en",
            source_text="The audit concludes that the measure reduced emissions during the reference evaluation period.",
        ),
        ClaimSourceContext(
            source_context_id="claim-source:v413:review",
            label="v4.13 controlled qualified-review comparison fixture",
            language_tag="en",
            source_text="The review reports that the measure did not reduce direct emissions during the reference evaluation period; indirect emissions were not assessed.",
        ),
    ]

    claims = [
        ClaimUnit(
            claim_id="claim:v45:measure-no-emissions-reduction",
            source_context_ref="claim-source:v45:epistemic-report",
            source_object_ref="proposition:measure-no-emissions-reduction",
            surface_text="the measure did not reduce emissions",
            language_tag="en",
            subject_key="policy-measure:reference",
            predicate_key="reduce-emissions",
            object_scope_key="emissions:total-unspecified",
            polarity=ClaimPolarity.negative,
            modality=ClaimModality.asserted,
            temporal_scope_ref="temporal-scope:reference-evaluation-period",
            spatial_scope_ref="spatial-scope:unspecified",
            attribution_ref="attribution:report-states",
            qualification_refs=q_epistemic,
            unresolved_refs=["same-measure:reference-corpus", "same-period:reference-corpus"],
        ),
        ClaimUnit(
            claim_id="claim:v46:measure-may-reduce-emissions",
            source_context_ref="claim-source:v46:public-hearing",
            source_object_ref="content:measure-may-reduce-emissions",
            surface_text="the measure may reduce emissions",
            language_tag="en",
            subject_key="policy-measure:reference",
            predicate_key="reduce-emissions",
            object_scope_key="emissions:total-unspecified",
            polarity=ClaimPolarity.positive,
            modality=ClaimModality.possible,
            temporal_scope_ref="temporal-scope:prospective-unspecified",
            spatial_scope_ref="spatial-scope:unspecified",
            attribution_ref="participant:agency-speaker",
            qualification_refs=q_actor,
            unresolved_refs=u_actor + ["same-measure:reference-corpus"],
        ),
        ClaimUnit(
            claim_id="claim:v413:audit-reduced-emissions",
            source_context_ref="claim-source:v413:audit",
            source_object_ref="fixture-claim:audit-reduced-emissions",
            surface_text="the measure reduced emissions during the reference evaluation period",
            language_tag="en",
            subject_key="policy-measure:reference",
            predicate_key="reduce-emissions",
            object_scope_key="emissions:total-unspecified",
            polarity=ClaimPolarity.positive,
            modality=ClaimModality.asserted,
            temporal_scope_ref="temporal-scope:reference-evaluation-period",
            spatial_scope_ref="spatial-scope:unspecified",
            attribution_ref="source:audit-reference",
            qualification_refs=q_epistemic,
            unresolved_refs=["same-measure:reference-corpus", "same-period:reference-corpus"],
        ),
        ClaimUnit(
            claim_id="claim:v413:review-no-direct-emissions-reduction",
            source_context_ref="claim-source:v413:review",
            source_object_ref="fixture-claim:review-no-direct-emissions-reduction",
            surface_text="the measure did not reduce direct emissions during the reference evaluation period",
            language_tag="en",
            subject_key="policy-measure:reference",
            predicate_key="reduce-emissions",
            object_scope_key="emissions:direct-only",
            polarity=ClaimPolarity.negative,
            modality=ClaimModality.asserted,
            temporal_scope_ref="temporal-scope:reference-evaluation-period",
            spatial_scope_ref="spatial-scope:unspecified",
            attribution_ref="source:review-reference",
            qualification_refs=q_epistemic,
            unresolved_refs=["same-measure:reference-corpus", "same-period:reference-corpus", "direct-vs-total-emissions-scope"],
        ),
        ClaimUnit(
            claim_id="claim:v45:proposal-may-lower-costs",
            source_context_ref="claim-source:v45:epistemic-report",
            source_object_ref="proposition:may-lower-costs",
            surface_text="it may lower costs",
            language_tag="en",
            subject_key="policy-proposal:reference",
            predicate_key="reduce-costs",
            object_scope_key="costs:unspecified",
            polarity=ClaimPolarity.positive,
            modality=ClaimModality.possible,
            temporal_scope_ref="temporal-scope:unspecified",
            spatial_scope_ref="spatial-scope:unspecified",
            attribution_ref="attribution:researchers-suggest",
            qualification_refs=q_actor,
            unresolved_refs=["thread:policy-topic-continuity:candidate"],
        ),
        ClaimUnit(
            claim_id="claim:v48:zh-proposal-may-lower-costs",
            source_context_ref="claim-source:v48:zh-original",
            source_object_ref="context-unit:zh:proposal-cost:v1",
            surface_text="该提案可能降低成本。",
            language_tag="zh",
            subject_key="policy-proposal:reference",
            predicate_key="reduce-costs",
            object_scope_key="costs:unspecified",
            polarity=ClaimPolarity.positive,
            modality=ClaimModality.possible,
            temporal_scope_ref="temporal-scope:unspecified",
            spatial_scope_ref="spatial-scope:unspecified",
            attribution_ref="source:v48:zh-original",
            qualification_refs=q_multilingual,
            unresolved_refs=["same-policy-object:v48-v47"],
        ),
        ClaimUnit(
            claim_id="claim:v48:en-proposal-may-reduce-costs",
            source_context_ref="claim-source:v48:en-derived",
            source_object_ref="context-unit:en:proposal-cost:v1",
            surface_text="The proposal may reduce costs.",
            language_tag="en",
            subject_key="policy-proposal:reference",
            predicate_key="reduce-costs",
            object_scope_key="costs:unspecified",
            polarity=ClaimPolarity.positive,
            modality=ClaimModality.possible,
            temporal_scope_ref="temporal-scope:unspecified",
            spatial_scope_ref="spatial-scope:unspecified",
            attribution_ref="source:v48:en-derived",
            qualification_refs=q_multilingual,
            unresolved_refs=["same-policy-object:v48-v47"],
        ),
    ]

    query = ClaimComparisonQuery(
        query_id="claim-comparison-query:policy-emissions-costs",
        question="Where do the retrieved policy claims agree, qualify one another, or conflict once polarity, modality, scope, attribution, language, and unresolved identity are preserved?",
        predecessor_result_set_ref=result_set.result_set_id,
        claim_refs=[x.claim_id for x in claims],
        required_dimensions=list(AlignmentDimension),
    )

    pair_specs = [
        (
            "claim-pair:report-negative-vs-agency-possible-positive",
            claims[0].claim_id, claims[1].claim_id,
            [1.0, 1.0, 1.0, 0.0, 0.2, 0.35, 1.0, 0.4, 1.0],
            True, True, True, False,
            ClaimRelationKind.apparent_contradiction, 0.95,
            "The claims point in opposite directions, but the agency claim is modal/prospective while the report claim is negative/asserted; this is tension or apparent contradiction, not a strict logical contradiction without aligned scope.",
            q_actor + q_epistemic, list(dict.fromkeys(u_actor + ["same-measure:reference-corpus", "same-period:reference-corpus"])),
        ),
        (
            "claim-pair:report-negative-vs-audit-positive",
            claims[0].claim_id, claims[2].claim_id,
            [1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.8, 1.0],
            True, True, False, True,
            ClaimRelationKind.contradiction, 0.98,
            "Within the controlled reference fixture, both claims concern the same normalized measure/predicate and evaluation scope with asserted modality but opposite polarity, supporting a strict contradiction assessment. The assessment does not identify which claim is true.",
            q_epistemic, ["same-measure:reference-corpus", "same-period:reference-corpus"],
        ),
        (
            "claim-pair:report-negative-vs-review-direct-negative",
            claims[0].claim_id, claims[3].claim_id,
            [1.0, 1.0, 0.65, 1.0, 1.0, 1.0, 1.0, 0.8, 1.0],
            True, False, False, True,
            ClaimRelationKind.qualified_agreement, 0.97,
            "Both claims report no emissions reduction, but one is total/unspecified while the other is limited to direct emissions; the narrower claim qualifies rather than fully duplicates the broader claim.",
            q_epistemic, ["direct-vs-total-emissions-scope", "same-measure:reference-corpus", "same-period:reference-corpus"],
        ),
        (
            "claim-pair:v45-cost-vs-v48-zh-cost",
            claims[4].claim_id, claims[5].claim_id,
            [0.82, 1.0, 1.0, 1.0, 1.0, 0.8, 1.0, 0.55, 0.9],
            True, False, False, True,
            ClaimRelationKind.qualified_agreement, 0.94,
            "The English attributed claim and Chinese original-language claim share positive possibility semantics around proposal cost reduction, but cross-document policy-object continuity remains qualified.",
            list(dict.fromkeys(q_actor + q_multilingual)), ["thread:policy-topic-continuity:candidate", "same-policy-object:v48-v47"],
        ),
        (
            "claim-pair:v48-zh-vs-en-derived-cost",
            claims[5].claim_id, claims[6].claim_id,
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.98],
            True, False, False, True,
            ClaimRelationKind.agreement, 0.99,
            "The English derived representation preserves the Chinese source proposition's subject, possibility modality, polarity, and cost-reduction semantics in this governed context; agreement is contextual and retains translation provenance.",
            q_multilingual, ["same-policy-object:v48-v47"],
        ),
        (
            "claim-pair:agency-possible-vs-audit-asserted-positive",
            claims[1].claim_id, claims[2].claim_id,
            [1.0, 1.0, 1.0, 1.0, 0.2, 0.35, 1.0, 0.4, 1.0],
            True, False, True, False,
            ClaimRelationKind.partial_agreement, 0.93,
            "Both claims point toward emissions reduction, but one expresses prospective possibility and the other an asserted result in a controlled evaluation period; they partially agree in direction while differing materially in modality and temporal scope.",
            list(dict.fromkeys(q_actor + q_epistemic)), list(dict.fromkeys(u_actor + ["same-measure:reference-corpus", "same-period:reference-corpus"])),
        ),
    ]

    signals: list[ClaimAlignmentSignal] = []
    pairs: list[ClaimComparisonPair] = []
    assessments: list[ClaimRelationAssessment] = []
    dimensions = list(AlignmentDimension)
    claim_map = {x.claim_id: x for x in claims}
    for pair_id, left, right, scores, same_claim, polarity_conflict, modality_mismatch, scope_compatible, relation, confidence, rationale, quals, unresolved in pair_specs:
        pair_signal_refs = []
        for idx, (dimension, score) in enumerate(zip(dimensions, scores), start=1):
            sig = _signal(
                pair_id,
                idx,
                dimension,
                score,
                [left, right],
                f"{dimension.value} comparison between {claim_map[left].surface_text!r} and {claim_map[right].surface_text!r}; score is advisory and comparison-specific.",
            )
            signals.append(sig)
            pair_signal_refs.append(sig.signal_id)
        pair = ClaimComparisonPair(
            pair_id=pair_id,
            left_claim_ref=left,
            right_claim_ref=right,
            signal_refs=pair_signal_refs,
            alignment_score=sum(scores) / len(scores),
            same_claim_candidate=same_claim,
            polarity_conflict=polarity_conflict,
            modality_mismatch=modality_mismatch,
            scope_compatible=scope_compatible,
            qualification_refs=quals,
            unresolved_refs=unresolved,
            state=ClaimReviewState.reviewed,
            reviewer_ref="reviewer:claim-comparison-reference",
        )
        pairs.append(pair)
        assessments.append(
            ClaimRelationAssessment(
                assessment_id=f"claim-assessment:{pair_id.split(':', 1)[1]}",
                pair_ref=pair_id,
                relation_kind=relation,
                confidence=confidence,
                rationale=rationale,
                qualification_refs=quals,
                unresolved_refs=unresolved,
                state=ClaimReviewState.reviewed,
                reviewer_ref="reviewer:claim-comparison-reference",
            )
        )

    provenance = ClaimComparisonProvenanceRecord(
        provenance_id="claim-comparison-provenance:reference",
        predecessor_retrieval_fingerprint_sha256=retrieval.fingerprint(),
        subject_refs=[query.query_id] + [x.pair_id for x in pairs] + [x.assessment_id for x in assessments],
        method="reviewed reference comparison over governed v4.12 retrieval context with explicit dimension scoring and preserved qualifications",
    )

    comparison_material = {
        "predecessor": retrieval.fingerprint(),
        "query": query.fingerprint(),
        "claims": {x.claim_id: x.fingerprint() for x in claims},
        "pairs": {x.pair_id: x.fingerprint() for x in pairs},
        "assessments": {x.assessment_id: x.fingerprint() for x in assessments},
    }
    snapshot = ClaimComparisonSnapshot(
        snapshot_id="claim-comparison-snapshot:reference:v1",
        predecessor_retrieval_fingerprint_sha256=retrieval.fingerprint(),
        query_fingerprint_sha256=query.fingerprint(),
        claim_fingerprints={x.claim_id: x.fingerprint() for x in claims},
        pair_fingerprints={x.pair_id: x.fingerprint() for x in pairs},
        assessment_fingerprints={x.assessment_id: x.fingerprint() for x in assessments},
        deterministic_comparison_fingerprint_sha256=canonical_sha256(comparison_material),
    )

    return ClaimAlignmentAgreementContradictionBundle(
        policy=ClaimComparisonPolicy(policy_id="claim-comparison-policy:v1"),
        predecessor_retrieval=retrieval,
        source_contexts=source_contexts,
        claims=claims,
        queries=[query],
        signals=signals,
        pairs=pairs,
        assessments=assessments,
        provenance_records=[provenance],
        snapshots=[snapshot],
    )


def contract_document() -> dict:
    bundle = reference_claim_alignment_agreement_contradiction_bundle()
    relation_counts = {kind.value: 0 for kind in ClaimRelationKind}
    for a in bundle.assessments:
        relation_counts[a.relation_kind.value] += 1
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "identity": {
            "product": "Sustainable Catalyst Platform Core",
            "build": "Claim Alignment, Agreement & Contradiction Intelligence",
            "major_api": "v4",
        },
        "principles": {
            "claim_surface_and_normalized_semantics_are_both_preserved": True,
            "comparison_requires_explicit_scope": True,
            "polarity_difference_alone_is_not_contradiction": True,
            "modality_mismatch_may_downgrade_contradiction": True,
            "temporal_and_spatial_scope_must_be_compared": True,
            "attribution_and_source_stance_must_be_preserved": True,
            "multilingual_alignment_must_preserve_translation_lineage": True,
            "unresolved_identity_must_not_be_silently_collapsed": True,
            "competing_relation_assessments_may_coexist": True,
        },
        "boundaries": {
            "reviewed_relation_establishes_truth": False,
            "contradiction_identifies_false_claim": False,
            "agreement_establishes_evidence_validity": False,
            "agreement_count_increases_truth": False,
            "source_majority_establishes_truth": False,
            "alignment_score_is_credibility_score": False,
            "contradiction_score_is_deception_score": False,
            "claim_comparison_mutates_predecessor_objects": False,
            "context_graph_mutation_performed": False,
            "identity_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
            "knowledge_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "extends_v4120_context_retrieval_relevance": True,
            "prepares_v4140_evidence_context_integration": True,
            "prepares_v4150_contextual_causal_language_mechanism_intelligence": True,
            "prepares_v4160_narrative_framing_perspective_intelligence": True,
            "prepares_v4170_cross_source_semantic_reconciliation": True,
            "prepares_v4180_contextual_hypothesis_competing_explanations": True,
            "prepares_v4200_unified_contextual_reasoning_runtime": True,
        },
        "reference": {
            "predecessor_release": bundle.predecessor_retrieval.release,
            "predecessor_fingerprint_sha256": bundle.predecessor_retrieval.fingerprint(),
            "source_contexts": len(bundle.source_contexts),
            "claims": len(bundle.claims),
            "queries": len(bundle.queries),
            "comparison_pairs": len(bundle.pairs),
            "alignment_signals": len(bundle.signals),
            "assessments": len(bundle.assessments),
            "relation_counts": relation_counts,
            "strict_contradictions": relation_counts[ClaimRelationKind.contradiction.value],
            "apparent_contradictions": relation_counts[ClaimRelationKind.apparent_contradiction.value],
            "agreements": relation_counts[ClaimRelationKind.agreement.value],
            "qualified_agreements": relation_counts[ClaimRelationKind.qualified_agreement.value],
            "partial_agreements": relation_counts[ClaimRelationKind.partial_agreement.value],
            "pairs_with_unresolved_context": sum(bool(x.unresolved_refs) for x in bundle.pairs),
            "snapshots": len(bundle.snapshots),
            "deterministic_reference_relations_are_model_performance_claim": False,
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
        "database_migration": "none",
    }
