from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .context_semantic_frame import InterpretationMethod
from .temporal_spatial_language_grounding import (
    TemporalSpatialLanguageGroundingBundle,
    reference_temporal_spatial_language_grounding_bundle,
)

CORE_RELEASE = "4.5.0"
CONTRACT_VERSION = "sc.core.epistemic-modal-negation-certainty-semantics.v1"
PREDECESSOR_CONTRACT = "sc.core.temporal-spatial-language-grounding.v1"

EXTENDS_CONTRACTS = [
    PREDECESSOR_CONTRACT,
    "sc.core.coreference-reference-referential-identity-intelligence.v1",
    "sc.core.discourse-structure-rhetorical-semantics.v1",
    "sc.core.context-object-semantic-frame-foundation.v1",
]


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class EpistemicState(str, Enum):
    asserted = "asserted"
    reported = "reported"
    attributed = "attributed"
    inferred = "inferred"
    estimated = "estimated"
    predicted = "predicted"
    hypothetical = "hypothetical"
    disputed = "disputed"
    denied = "denied"
    uncertain = "uncertain"
    unknown = "unknown"


class ModalForce(str, Enum):
    none = "none"
    possible = "possible"
    probable = "probable"
    necessary = "necessary"
    permitted = "permitted"
    obligated = "obligated"
    conditional = "conditional"
    counterfactual = "counterfactual"
    predictive = "predictive"


class Polarity(str, Enum):
    positive = "positive"
    negative = "negative"
    mixed = "mixed"


class CertaintyLevel(str, Enum):
    source_asserted = "source-asserted"
    high = "high"
    moderate = "moderate"
    low = "low"
    explicit_uncertainty = "explicit-uncertainty"
    unspecified = "unspecified"


class EpistemicReviewState(str, Enum):
    candidate = "candidate"
    reviewed = "reviewed"
    accepted = "accepted"
    rejected = "rejected"
    disputed = "disputed"
    deferred = "deferred"


class EpistemicPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    source_text_remains_immutable: Literal[True] = True
    proposition_is_distinct_from_truth: Literal[True] = True
    source_assertion_is_not_platform_assertion: Literal[True] = True
    attribution_is_preserved: Literal[True] = True
    negation_scope_is_explicit: Literal[True] = True
    modal_scope_is_explicit: Literal[True] = True
    certainty_is_distinct_from_model_confidence: Literal[True] = True
    competing_interpretations_may_coexist: Literal[True] = True
    machine_interpretation_is_advisory: Literal[True] = True
    accepted_interpretation_requires_governed_review: Literal[True] = True
    epistemic_state_does_not_promote_evidence: Literal[True] = True
    canonical_speaker_identity_is_not_inferred_from_surface_form: Literal[True] = True
    identity_graph_mutation_authorized: Literal[False] = False
    evidence_graph_mutation_authorized: Literal[False] = False
    context_graph_mutation_authorized: Literal[False] = False
    knowledge_graph_mutation_authorized: Literal[False] = False

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EpistemicSourceExcerpt(BaseModel):
    source_excerpt_id: str = Field(min_length=3, max_length=500)
    source_ref: str = Field(min_length=3, max_length=1000)
    language_ref: str = Field(min_length=3, max_length=500)
    content: str = Field(min_length=1, max_length=50000)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    provenance_ref: str = Field(min_length=3, max_length=500)
    immutable: Literal[True] = True
    source_excerpt_is_not_truth_validation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_content_hash(self):
        if self.content_sha256 != canonical_sha256(self.content):
            raise ValueError("content_sha256 must match immutable source excerpt content")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class Proposition(BaseModel):
    proposition_id: str = Field(min_length=3, max_length=500)
    source_excerpt_ref: str = Field(min_length=3, max_length=500)
    surface_text: str = Field(min_length=1, max_length=20000)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=1)
    semantic_subject_ref: str | None = Field(default=None, max_length=1000)
    predecessor_reference_ref: str | None = Field(default=None, max_length=1000)
    provenance_ref: str = Field(min_length=3, max_length=500)
    proposition_does_not_establish_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_span(self):
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class Attribution(BaseModel):
    attribution_id: str = Field(min_length=3, max_length=500)
    source_excerpt_ref: str = Field(min_length=3, max_length=500)
    surface_source_text: str = Field(min_length=1, max_length=5000)
    attribution_verb: str = Field(min_length=1, max_length=200)
    proposition_refs: list[str] = Field(min_length=1)
    canonical_actor_ref: str | None = Field(default=None, max_length=1000)
    provenance_ref: str = Field(min_length=3, max_length=500)
    surface_source_does_not_establish_canonical_identity: Literal[True] = True
    attribution_does_not_validate_proposition: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EpistemicCue(BaseModel):
    cue_id: str = Field(min_length=3, max_length=500)
    source_excerpt_ref: str = Field(min_length=3, max_length=500)
    surface_text: str = Field(min_length=1, max_length=1000)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=1)
    cue_type: Literal["attribution", "modal", "negation", "certainty", "conditional", "epistemic"]
    proposition_ref: str = Field(min_length=3, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_span(self):
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class NegationScope(BaseModel):
    negation_scope_id: str = Field(min_length=3, max_length=500)
    proposition_ref: str = Field(min_length=3, max_length=500)
    cue_ref: str = Field(min_length=3, max_length=500)
    negated_text: str = Field(min_length=1, max_length=10000)
    scope_char_start: int = Field(ge=0)
    scope_char_end: int = Field(ge=1)
    polarity: Literal[Polarity.negative] = Polarity.negative
    state: EpistemicReviewState
    provenance_ref: str = Field(min_length=3, max_length=500)
    negation_scope_is_linguistic_analysis_not_truth_verdict: Literal[True] = True

    @model_validator(mode="after")
    def validate_span(self):
        if self.scope_char_end <= self.scope_char_start:
            raise ValueError("scope_char_end must be greater than scope_char_start")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ModalScope(BaseModel):
    modal_scope_id: str = Field(min_length=3, max_length=500)
    proposition_ref: str = Field(min_length=3, max_length=500)
    cue_ref: str = Field(min_length=3, max_length=500)
    modal_force: ModalForce
    state: EpistemicReviewState
    confidence: float = Field(ge=0.0, le=1.0)
    provenance_ref: str = Field(min_length=3, max_length=500)
    modal_force_is_interpretation_not_world_state: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ConditionalScope(BaseModel):
    conditional_scope_id: str = Field(min_length=3, max_length=500)
    source_excerpt_ref: str = Field(min_length=3, max_length=500)
    condition_text: str = Field(min_length=1, max_length=10000)
    condition_char_start: int = Field(ge=0)
    condition_char_end: int = Field(ge=1)
    consequent_proposition_ref: str = Field(min_length=3, max_length=500)
    state: EpistemicReviewState
    provenance_ref: str = Field(min_length=3, max_length=500)
    condition_is_not_asserted_as_realized: Literal[True] = True

    @model_validator(mode="after")
    def validate_span(self):
        if self.condition_char_end <= self.condition_char_start:
            raise ValueError("condition_char_end must be greater than condition_char_start")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EpistemicAssessment(BaseModel):
    assessment_id: str = Field(min_length=3, max_length=500)
    proposition_ref: str = Field(min_length=3, max_length=500)
    epistemic_state: EpistemicState
    polarity: Polarity
    modal_force: ModalForce = ModalForce.none
    certainty_level: CertaintyLevel
    linguistic_confidence: float = Field(ge=0.0, le=1.0)
    attribution_ref: str | None = Field(default=None, max_length=500)
    negation_scope_ref: str | None = Field(default=None, max_length=500)
    modal_scope_ref: str | None = Field(default=None, max_length=500)
    conditional_scope_ref: str | None = Field(default=None, max_length=500)
    state: EpistemicReviewState
    method: InterpretationMethod
    reviewer_ref: str | None = Field(default=None, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    epistemic_state_is_not_platform_truth_state: Literal[True] = True
    linguistic_confidence_is_not_claim_probability: Literal[True] = True
    evidence_status_unchanged: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_review(self):
        if self.state == EpistemicReviewState.accepted and not self.reviewer_ref:
            raise ValueError("accepted epistemic assessment requires reviewer_ref")
        if self.polarity == Polarity.negative and not self.negation_scope_ref:
            raise ValueError("negative assessment requires explicit negation_scope_ref")
        if self.modal_force != ModalForce.none and not self.modal_scope_ref:
            raise ValueError("non-none modal force requires modal_scope_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EpistemicInterpretation(BaseModel):
    interpretation_id: str = Field(min_length=3, max_length=500)
    predecessor_grounding_interpretation_ref: str = Field(min_length=3, max_length=500)
    source_excerpt_refs: list[str] = Field(min_length=1)
    proposition_refs: list[str] = Field(min_length=1)
    assessment_refs: list[str] = Field(min_length=1)
    unresolved_refs: list[str] = Field(default_factory=list)
    state: EpistemicReviewState
    confidence: float = Field(ge=0.0, le=1.0)
    provenance_ref: str = Field(min_length=3, max_length=500)
    predecessor_objects_remain_immutable: Literal[True] = True
    interpretation_is_not_truth_verdict: Literal[True] = True
    interpretation_does_not_change_evidence_status: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EpistemicProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3, max_length=500)
    subject_refs: list[str] = Field(min_length=1)
    method: InterpretationMethod
    produced_by_ref: str = Field(min_length=3, max_length=500)
    source_refs: list[str] = Field(min_length=1)
    reviewer_ref: str | None = Field(default=None, max_length=500)
    transformation_notes: list[str] = Field(default_factory=list)
    machine_output_is_advisory: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EpistemicSemanticSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    predecessor_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    interpretation_refs: list[str] = Field(min_length=1)
    deterministic_semantic_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_does_not_freeze_truth: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EpistemicModalNegationCertaintyBundle(BaseModel):
    release: Literal["4.5.0"] = "4.5.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    extends_contracts: list[str] = Field(min_length=4)
    policy: EpistemicPolicy
    temporal_spatial_grounding: TemporalSpatialLanguageGroundingBundle
    source_excerpts: list[EpistemicSourceExcerpt] = Field(min_length=1)
    propositions: list[Proposition] = Field(min_length=1)
    attributions: list[Attribution] = Field(min_length=1)
    cues: list[EpistemicCue] = Field(min_length=1)
    negation_scopes: list[NegationScope] = Field(default_factory=list)
    modal_scopes: list[ModalScope] = Field(default_factory=list)
    conditional_scopes: list[ConditionalScope] = Field(default_factory=list)
    assessments: list[EpistemicAssessment] = Field(min_length=1)
    provenance_records: list[EpistemicProvenanceRecord] = Field(min_length=1)
    interpretations: list[EpistemicInterpretation] = Field(min_length=1)
    snapshots: list[EpistemicSemanticSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.extends_contracts != EXTENDS_CONTRACTS:
            raise ValueError("extends_contracts must preserve declared v4.5 dependency order")
        if self.temporal_spatial_grounding.release != "4.4.0" or self.temporal_spatial_grounding.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.5 must embed governed v4.4 temporal/spatial grounding predecessor")

        groups = (
            ([x.source_excerpt_id for x in self.source_excerpts], "source excerpt ids"),
            ([x.proposition_id for x in self.propositions], "proposition ids"),
            ([x.attribution_id for x in self.attributions], "attribution ids"),
            ([x.cue_id for x in self.cues], "cue ids"),
            ([x.negation_scope_id for x in self.negation_scopes], "negation scope ids"),
            ([x.modal_scope_id for x in self.modal_scopes], "modal scope ids"),
            ([x.conditional_scope_id for x in self.conditional_scopes], "conditional scope ids"),
            ([x.assessment_id for x in self.assessments], "assessment ids"),
            ([x.provenance_id for x in self.provenance_records], "provenance ids"),
            ([x.interpretation_id for x in self.interpretations], "interpretation ids"),
            ([x.snapshot_id for x in self.snapshots], "snapshot ids"),
        )
        for values, label in groups:
            _unique(values, label)

        excerpts = {x.source_excerpt_id: x for x in self.source_excerpts}
        propositions = {x.proposition_id: x for x in self.propositions}
        attributions = {x.attribution_id: x for x in self.attributions}
        cues = {x.cue_id: x for x in self.cues}
        negations = {x.negation_scope_id: x for x in self.negation_scopes}
        modals = {x.modal_scope_id: x for x in self.modal_scopes}
        conditionals = {x.conditional_scope_id: x for x in self.conditional_scopes}
        assessments = {x.assessment_id: x for x in self.assessments}
        provenances = {x.provenance_id: x for x in self.provenance_records}
        interpretations = {x.interpretation_id: x for x in self.interpretations}
        predecessor_interpretations = {x.interpretation_id for x in self.temporal_spatial_grounding.interpretations}
        predecessor_refs = {x.reference_expression_id for x in self.temporal_spatial_grounding.referential_identity.reference_expressions}

        for proposition in self.propositions:
            if proposition.source_excerpt_ref not in excerpts:
                raise ValueError("proposition source_excerpt_ref must resolve")
            excerpt = excerpts[proposition.source_excerpt_ref]
            if excerpt.content[proposition.char_start:proposition.char_end] != proposition.surface_text:
                raise ValueError("proposition span must reproduce immutable source text")
            if proposition.predecessor_reference_ref and proposition.predecessor_reference_ref not in predecessor_refs:
                raise ValueError("predecessor_reference_ref must resolve to v4.3/v4.4 predecessor")
            if proposition.provenance_ref not in provenances:
                raise ValueError("proposition provenance_ref must resolve")

        for attribution in self.attributions:
            if attribution.source_excerpt_ref not in excerpts:
                raise ValueError("attribution source excerpt must resolve")
            if any(ref not in propositions for ref in attribution.proposition_refs):
                raise ValueError("attribution proposition_refs must resolve")
            if attribution.provenance_ref not in provenances:
                raise ValueError("attribution provenance_ref must resolve")

        for cue in self.cues:
            if cue.source_excerpt_ref not in excerpts or cue.proposition_ref not in propositions:
                raise ValueError("cue source/proposition refs must resolve")
            excerpt = excerpts[cue.source_excerpt_ref]
            if excerpt.content[cue.char_start:cue.char_end] != cue.surface_text:
                raise ValueError("cue span must reproduce immutable source text")
            if cue.provenance_ref not in provenances:
                raise ValueError("cue provenance_ref must resolve")

        for scope in self.negation_scopes:
            if scope.proposition_ref not in propositions or scope.cue_ref not in cues:
                raise ValueError("negation scope refs must resolve")
            p = propositions[scope.proposition_ref]
            excerpt = excerpts[p.source_excerpt_ref]
            if excerpt.content[scope.scope_char_start:scope.scope_char_end] != scope.negated_text:
                raise ValueError("negation scope span must reproduce source text")
            if scope.provenance_ref not in provenances:
                raise ValueError("negation scope provenance_ref must resolve")

        for scope in self.modal_scopes:
            if scope.proposition_ref not in propositions or scope.cue_ref not in cues:
                raise ValueError("modal scope refs must resolve")
            if scope.provenance_ref not in provenances:
                raise ValueError("modal scope provenance_ref must resolve")

        for scope in self.conditional_scopes:
            if scope.source_excerpt_ref not in excerpts or scope.consequent_proposition_ref not in propositions:
                raise ValueError("conditional scope refs must resolve")
            excerpt = excerpts[scope.source_excerpt_ref]
            if excerpt.content[scope.condition_char_start:scope.condition_char_end] != scope.condition_text:
                raise ValueError("conditional scope span must reproduce source text")
            if scope.provenance_ref not in provenances:
                raise ValueError("conditional scope provenance_ref must resolve")

        for assessment in self.assessments:
            if assessment.proposition_ref not in propositions:
                raise ValueError("assessment proposition_ref must resolve")
            if assessment.attribution_ref and assessment.attribution_ref not in attributions:
                raise ValueError("assessment attribution_ref must resolve")
            if assessment.negation_scope_ref and assessment.negation_scope_ref not in negations:
                raise ValueError("assessment negation_scope_ref must resolve")
            if assessment.modal_scope_ref and assessment.modal_scope_ref not in modals:
                raise ValueError("assessment modal_scope_ref must resolve")
            if assessment.conditional_scope_ref and assessment.conditional_scope_ref not in conditionals:
                raise ValueError("assessment conditional_scope_ref must resolve")
            if assessment.provenance_ref not in provenances:
                raise ValueError("assessment provenance_ref must resolve")

        for interpretation in self.interpretations:
            if interpretation.predecessor_grounding_interpretation_ref not in predecessor_interpretations:
                raise ValueError("interpretation predecessor grounding ref must resolve")
            if any(ref not in excerpts for ref in interpretation.source_excerpt_refs):
                raise ValueError("interpretation source excerpt refs must resolve")
            if any(ref not in propositions for ref in interpretation.proposition_refs):
                raise ValueError("interpretation proposition refs must resolve")
            if any(ref not in assessments for ref in interpretation.assessment_refs):
                raise ValueError("interpretation assessment refs must resolve")
            if interpretation.provenance_ref not in provenances:
                raise ValueError("interpretation provenance_ref must resolve")

        object_ids = (
            set(excerpts) | set(propositions) | set(attributions) | set(cues) | set(negations) |
            set(modals) | set(conditionals) | set(assessments) | set(interpretations) |
            {x.snapshot_id for x in self.snapshots}
        )
        for provenance in self.provenance_records:
            if any(ref not in object_ids for ref in provenance.subject_refs):
                raise ValueError("provenance subject_ref must resolve to a v4.5 object")

        predecessor_fp = self.temporal_spatial_grounding.fingerprint()
        for snapshot in self.snapshots:
            if snapshot.predecessor_fingerprint_sha256 != predecessor_fp:
                raise ValueError("snapshot predecessor fingerprint must match embedded v4.4 bundle")
            if any(ref not in interpretations for ref in snapshot.interpretation_refs):
                raise ValueError("snapshot interpretation refs must resolve")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def _span(text: str, fragment: str, start: int = 0) -> tuple[int, int]:
    i = text.index(fragment, start)
    return i, i + len(fragment)


@lru_cache(maxsize=1)
def reference_epistemic_modal_negation_certainty_bundle() -> EpistemicModalNegationCertaintyBundle:
    predecessor = reference_temporal_spatial_language_grounding_bundle()
    content = (
        "The report states that the measure did not reduce emissions. "
        "Researchers suggest it may lower costs, but the ministry says the estimate is uncertain. "
        "If subsidies were extended, adoption could increase."
    )
    excerpt = EpistemicSourceExcerpt(
        source_excerpt_id="epistemic-source:reference-note:v1",
        source_ref="source:epistemic-reference-note:v1",
        language_ref="language:en",
        content=content,
        content_sha256=canonical_sha256(content),
        provenance_ref="prov:epistemic-source:reference",
        metadata={"purpose": "reference-only epistemic/modal/negation/certainty semantics fixture"},
    )

    proposition_specs = [
        ("proposition:measure-no-emissions-reduction", "the measure did not reduce emissions"),
        ("proposition:may-lower-costs", "it may lower costs"),
        ("proposition:estimate-uncertain", "the estimate is uncertain"),
        ("proposition:adoption-could-increase", "adoption could increase"),
    ]
    propositions: list[Proposition] = []
    for pid, surface in proposition_specs:
        s, e = _span(content, surface)
        propositions.append(Proposition(
            proposition_id=pid,
            source_excerpt_ref=excerpt.source_excerpt_id,
            surface_text=surface,
            char_start=s,
            char_end=e,
            predecessor_reference_ref="reference-expression:it" if pid == "proposition:may-lower-costs" else None,
            provenance_ref="prov:epistemic-propositions:reference",
        ))

    attributions = [
        Attribution(
            attribution_id="attribution:report-states",
            source_excerpt_ref=excerpt.source_excerpt_id,
            surface_source_text="The report",
            attribution_verb="states",
            proposition_refs=["proposition:measure-no-emissions-reduction"],
            provenance_ref="prov:epistemic-attribution:reference",
        ),
        Attribution(
            attribution_id="attribution:researchers-suggest",
            source_excerpt_ref=excerpt.source_excerpt_id,
            surface_source_text="Researchers",
            attribution_verb="suggest",
            proposition_refs=["proposition:may-lower-costs"],
            provenance_ref="prov:epistemic-attribution:reference",
        ),
        Attribution(
            attribution_id="attribution:ministry-says",
            source_excerpt_ref=excerpt.source_excerpt_id,
            surface_source_text="the ministry",
            attribution_verb="says",
            proposition_refs=["proposition:estimate-uncertain"],
            provenance_ref="prov:epistemic-attribution:reference",
        ),
    ]

    cue_specs = [
        ("cue:states", "states", "attribution", "proposition:measure-no-emissions-reduction"),
        ("cue:not", "not", "negation", "proposition:measure-no-emissions-reduction"),
        ("cue:suggest", "suggest", "attribution", "proposition:may-lower-costs"),
        ("cue:may", "may", "modal", "proposition:may-lower-costs"),
        ("cue:says", "says", "attribution", "proposition:estimate-uncertain"),
        ("cue:uncertain", "uncertain", "certainty", "proposition:estimate-uncertain"),
        ("cue:if", "If", "conditional", "proposition:adoption-could-increase"),
        ("cue:could", "could", "modal", "proposition:adoption-could-increase"),
    ]
    cues: list[EpistemicCue] = []
    search_cursor: dict[str, int] = {}
    for cid, surface, ctype, pref in cue_specs:
        start = search_cursor.get(surface, 0)
        s, e = _span(content, surface, start)
        search_cursor[surface] = e
        cues.append(EpistemicCue(
            cue_id=cid,
            source_excerpt_ref=excerpt.source_excerpt_id,
            surface_text=surface,
            char_start=s,
            char_end=e,
            cue_type=ctype,
            proposition_ref=pref,
            provenance_ref="prov:epistemic-cues:reference",
        ))

    neg_text = "not reduce emissions"
    ns, ne = _span(content, neg_text)
    negations = [NegationScope(
        negation_scope_id="negation-scope:measure-no-emissions-reduction",
        proposition_ref="proposition:measure-no-emissions-reduction",
        cue_ref="cue:not",
        negated_text=neg_text,
        scope_char_start=ns,
        scope_char_end=ne,
        state=EpistemicReviewState.accepted,
        provenance_ref="prov:epistemic-scopes:reference",
    )]

    modals = [
        ModalScope(
            modal_scope_id="modal-scope:may-lower-costs",
            proposition_ref="proposition:may-lower-costs",
            cue_ref="cue:may",
            modal_force=ModalForce.possible,
            state=EpistemicReviewState.accepted,
            confidence=0.99,
            provenance_ref="prov:epistemic-scopes:reference",
        ),
        ModalScope(
            modal_scope_id="modal-scope:could-increase",
            proposition_ref="proposition:adoption-could-increase",
            cue_ref="cue:could",
            modal_force=ModalForce.possible,
            state=EpistemicReviewState.accepted,
            confidence=0.98,
            provenance_ref="prov:epistemic-scopes:reference",
            metadata={"conditional_context": True},
        ),
    ]

    condition_text = "If subsidies were extended"
    cs, ce = _span(content, condition_text)
    conditionals = [ConditionalScope(
        conditional_scope_id="conditional-scope:subsidies-extended",
        source_excerpt_ref=excerpt.source_excerpt_id,
        condition_text=condition_text,
        condition_char_start=cs,
        condition_char_end=ce,
        consequent_proposition_ref="proposition:adoption-could-increase",
        state=EpistemicReviewState.accepted,
        provenance_ref="prov:epistemic-scopes:reference",
    )]

    assessments = [
        EpistemicAssessment(
            assessment_id="assessment:reported-negative-emissions",
            proposition_ref="proposition:measure-no-emissions-reduction",
            epistemic_state=EpistemicState.reported,
            polarity=Polarity.negative,
            certainty_level=CertaintyLevel.source_asserted,
            linguistic_confidence=0.99,
            attribution_ref="attribution:report-states",
            negation_scope_ref="negation-scope:measure-no-emissions-reduction",
            state=EpistemicReviewState.accepted,
            method=InterpretationMethod.manual,
            reviewer_ref="reviewer:epistemic-semantics:v1",
            provenance_ref="prov:epistemic-assessments:reference",
        ),
        EpistemicAssessment(
            assessment_id="assessment:researchers-possible-lower-costs",
            proposition_ref="proposition:may-lower-costs",
            epistemic_state=EpistemicState.attributed,
            polarity=Polarity.positive,
            modal_force=ModalForce.possible,
            certainty_level=CertaintyLevel.low,
            linguistic_confidence=0.98,
            attribution_ref="attribution:researchers-suggest",
            modal_scope_ref="modal-scope:may-lower-costs",
            state=EpistemicReviewState.accepted,
            method=InterpretationMethod.manual,
            reviewer_ref="reviewer:epistemic-semantics:v1",
            provenance_ref="prov:epistemic-assessments:reference",
        ),
        EpistemicAssessment(
            assessment_id="assessment:ministry-explicit-uncertainty",
            proposition_ref="proposition:estimate-uncertain",
            epistemic_state=EpistemicState.uncertain,
            polarity=Polarity.positive,
            certainty_level=CertaintyLevel.explicit_uncertainty,
            linguistic_confidence=0.99,
            attribution_ref="attribution:ministry-says",
            state=EpistemicReviewState.accepted,
            method=InterpretationMethod.manual,
            reviewer_ref="reviewer:epistemic-semantics:v1",
            provenance_ref="prov:epistemic-assessments:reference",
            metadata={"certainty_cue_ref": "cue:uncertain"},
        ),
        EpistemicAssessment(
            assessment_id="assessment:hypothetical-possible-adoption-increase",
            proposition_ref="proposition:adoption-could-increase",
            epistemic_state=EpistemicState.hypothetical,
            polarity=Polarity.positive,
            modal_force=ModalForce.possible,
            certainty_level=CertaintyLevel.low,
            linguistic_confidence=0.98,
            modal_scope_ref="modal-scope:could-increase",
            conditional_scope_ref="conditional-scope:subsidies-extended",
            state=EpistemicReviewState.accepted,
            method=InterpretationMethod.manual,
            reviewer_ref="reviewer:epistemic-semantics:v1",
            provenance_ref="prov:epistemic-assessments:reference",
        ),
    ]

    predecessor_interpretation_ref = predecessor.interpretations[0].interpretation_id
    interpretation = EpistemicInterpretation(
        interpretation_id="epistemic-interpretation:reference:baseline",
        predecessor_grounding_interpretation_ref=predecessor_interpretation_ref,
        source_excerpt_refs=[excerpt.source_excerpt_id],
        proposition_refs=[x.proposition_id for x in propositions],
        assessment_refs=[x.assessment_id for x in assessments],
        unresolved_refs=[],
        state=EpistemicReviewState.accepted,
        confidence=0.98,
        provenance_ref="prov:epistemic-interpretation:reference",
    )

    snapshot_material = {
        "predecessor": predecessor.fingerprint(),
        "excerpt": excerpt.fingerprint(),
        "propositions": [x.fingerprint() for x in propositions],
        "attributions": [x.fingerprint() for x in attributions],
        "cues": [x.fingerprint() for x in cues],
        "negations": [x.fingerprint() for x in negations],
        "modals": [x.fingerprint() for x in modals],
        "conditionals": [x.fingerprint() for x in conditionals],
        "assessments": [x.fingerprint() for x in assessments],
        "interpretation": interpretation.fingerprint(),
    }
    snapshot = EpistemicSemanticSnapshot(
        snapshot_id="snapshot:epistemic-modal-negation-certainty:reference:v1",
        predecessor_fingerprint_sha256=predecessor.fingerprint(),
        interpretation_refs=[interpretation.interpretation_id],
        deterministic_semantic_fingerprint_sha256=canonical_sha256(snapshot_material),
    )

    object_groups = {
        "prov:epistemic-source:reference": [excerpt.source_excerpt_id],
        "prov:epistemic-propositions:reference": [x.proposition_id for x in propositions],
        "prov:epistemic-attribution:reference": [x.attribution_id for x in attributions],
        "prov:epistemic-cues:reference": [x.cue_id for x in cues],
        "prov:epistemic-scopes:reference": [x.negation_scope_id for x in negations] + [x.modal_scope_id for x in modals] + [x.conditional_scope_id for x in conditionals],
        "prov:epistemic-assessments:reference": [x.assessment_id for x in assessments],
        "prov:epistemic-interpretation:reference": [interpretation.interpretation_id, snapshot.snapshot_id],
    }
    provenances = [
        EpistemicProvenanceRecord(
            provenance_id=pid,
            subject_refs=subjects,
            method=InterpretationMethod.manual,
            produced_by_ref="reviewer:epistemic-semantics:v1" if pid != "prov:epistemic-source:reference" else "actor:platform-core-reference-builder",
            source_refs=["source:epistemic-reference-note:v1"],
            reviewer_ref="reviewer:epistemic-semantics:v1" if pid != "prov:epistemic-source:reference" else None,
            transformation_notes=["No source truth, evidence status, or graph identity is changed by this semantic analysis."],
        )
        for pid, subjects in object_groups.items()
    ]

    return EpistemicModalNegationCertaintyBundle(
        extends_contracts=list(EXTENDS_CONTRACTS),
        policy=EpistemicPolicy(policy_id="epistemic-modal-negation-certainty-policy:v4.5"),
        temporal_spatial_grounding=predecessor,
        source_excerpts=[excerpt],
        propositions=propositions,
        attributions=attributions,
        cues=cues,
        negation_scopes=negations,
        modal_scopes=modals,
        conditional_scopes=conditionals,
        assessments=assessments,
        provenance_records=provenances,
        interpretations=[interpretation],
        snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    bundle = reference_epistemic_modal_negation_certainty_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "extends_contracts": list(EXTENDS_CONTRACTS),
        "identity": {
            "product": "Sustainable Catalyst Platform Core",
            "build": "Epistemic, Modal, Negation & Certainty Semantics",
            "major_api": "v4",
        },
        "principles": {
            "propositions_are_distinct_from_truth": True,
            "source_assertion_is_not_platform_assertion": True,
            "attribution_is_first_class": True,
            "negation_scope_is_explicit": True,
            "modal_scope_is_explicit": True,
            "conditional_scope_is_explicit": True,
            "certainty_is_distinct_from_model_confidence": True,
            "epistemic_state_is_provenance_preserving": True,
            "competing_interpretations_may_coexist": True,
            "accepted_interpretation_requires_governed_review": True,
        },
        "boundaries": {
            "reported_claim_establishes_platform_truth": False,
            "source_certainty_establishes_evidence_validity": False,
            "linguistic_confidence_is_claim_probability": False,
            "negated_proposition_is_deleted_from_context": False,
            "modal_possibility_is_prediction_probability": False,
            "conditional_language_establishes_condition_realized": False,
            "surface_source_establishes_canonical_actor_identity": False,
            "accepted_epistemic_analysis_rewrites_v440_predecessor": False,
            "identity_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
            "context_graph_mutation_performed": False,
            "knowledge_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "extends_v440_temporal_spatial_language_grounding": True,
            "prepares_v460_pragmatic_meaning_speech_act_intent": True,
            "prepares_v470_cross_document_context_graph": True,
            "prepares_v480_multilingual_context_alignment": True,
            "prepares_v490_contextual_semantic_evaluation": True,
            "prepares_v4100_unified_contextual_intelligence_runtime": True,
        },
        "reference": {
            "predecessor_release": bundle.temporal_spatial_grounding.release,
            "predecessor_fingerprint_sha256": bundle.temporal_spatial_grounding.fingerprint(),
            "source_excerpts": len(bundle.source_excerpts),
            "propositions": len(bundle.propositions),
            "attributions": len(bundle.attributions),
            "cues": len(bundle.cues),
            "negation_scopes": len(bundle.negation_scopes),
            "modal_scopes": len(bundle.modal_scopes),
            "conditional_scopes": len(bundle.conditional_scopes),
            "assessments": len(bundle.assessments),
            "negative_assessments": sum(x.polarity == Polarity.negative for x in bundle.assessments),
            "possible_modal_assessments": sum(x.modal_force == ModalForce.possible for x in bundle.assessments),
            "explicit_uncertainty_assessments": sum(x.certainty_level == CertaintyLevel.explicit_uncertainty for x in bundle.assessments),
            "hypothetical_assessments": sum(x.epistemic_state == EpistemicState.hypothetical for x in bundle.assessments),
            "canonical_actor_bindings": sum(bool(x.canonical_actor_ref) for x in bundle.attributions),
            "interpretations": len(bundle.interpretations),
            "snapshots": len(bundle.snapshots),
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
        "database_migration": "none",
    }
