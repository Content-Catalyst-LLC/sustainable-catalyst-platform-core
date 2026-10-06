from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .context_semantic_frame import InterpretationMethod
from .epistemic_modal_negation_certainty import (
    EpistemicModalNegationCertaintyBundle,
    reference_epistemic_modal_negation_certainty_bundle,
)

CORE_RELEASE = "4.6.0"
CONTRACT_VERSION = "sc.core.pragmatic-meaning-speech-act-communicative-intent.v1"
PREDECESSOR_CONTRACT = "sc.core.epistemic-modal-negation-certainty-semantics.v1"

EXTENDS_CONTRACTS = [
    PREDECESSOR_CONTRACT,
    "sc.core.temporal-spatial-language-grounding.v1",
    "sc.core.coreference-reference-referential-identity-intelligence.v1",
    "sc.core.discourse-structure-rhetorical-semantics.v1",
    "sc.core.context-object-semantic-frame-foundation.v1",
]


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class SpeechActType(str, Enum):
    assertion = "assertion"
    request = "request"
    recommendation = "recommendation"
    warning = "warning"
    commitment = "commitment"
    question = "question"
    instruction = "instruction"
    denial = "denial"
    qualification = "qualification"
    prediction = "prediction"
    speculation = "speculation"


class CommunicativeIntentType(str, Enum):
    inform = "inform"
    elicit_action = "elicit-action"
    advise = "advise"
    alert = "alert"
    commit = "commit"
    elicit_information = "elicit-information"
    clarify = "clarify"
    qualify = "qualify"
    persuade = "persuade"
    speculate = "speculate"


class ParticipantRole(str, Enum):
    speaker = "speaker"
    audience = "audience"
    addressee = "addressee"
    quoted_speaker = "quoted-speaker"
    unspecified = "unspecified"


class GenreType(str, Enum):
    public_hearing = "public-hearing"
    scientific_paper = "scientific-paper"
    regulatory_notice = "regulatory-notice"
    press_release = "press-release"
    court_filing = "court-filing"
    diplomatic_communication = "diplomatic-communication"
    conversation = "conversation"
    unknown = "unknown"


class RegisterType(str, Enum):
    formal = "formal"
    technical = "technical"
    administrative = "administrative"
    conversational = "conversational"
    persuasive = "persuasive"
    neutral = "neutral"
    unknown = "unknown"


class PragmaticReviewState(str, Enum):
    candidate = "candidate"
    reviewed = "reviewed"
    accepted = "accepted"
    rejected = "rejected"
    disputed = "disputed"
    deferred = "deferred"


class PragmaticPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    source_text_remains_immutable: Literal[True] = True
    speech_act_is_distinct_from_proposition_truth: Literal[True] = True
    communicative_intent_is_distinct_from_outcome: Literal[True] = True
    communicative_intent_does_not_claim_private_mental_state: Literal[True] = True
    surface_speaker_is_distinct_from_canonical_identity: Literal[True] = True
    audience_role_may_remain_unresolved: Literal[True] = True
    genre_and_register_are_interpretations_not_authority_scores: Literal[True] = True
    request_does_not_create_platform_obligation: Literal[True] = True
    recommendation_does_not_establish_normative_correctness: Literal[True] = True
    warning_does_not_establish_risk_as_fact: Literal[True] = True
    commitment_does_not_guarantee_future_performance: Literal[True] = True
    machine_interpretation_is_advisory: Literal[True] = True
    accepted_interpretation_requires_governed_review: Literal[True] = True
    predecessor_epistemic_objects_remain_immutable: Literal[True] = True
    identity_graph_mutation_authorized: Literal[False] = False
    evidence_graph_mutation_authorized: Literal[False] = False
    context_graph_mutation_authorized: Literal[False] = False
    knowledge_graph_mutation_authorized: Literal[False] = False

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class PragmaticSourceExcerpt(BaseModel):
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


class CommunicativeParticipant(BaseModel):
    participant_id: str = Field(min_length=3, max_length=500)
    source_excerpt_ref: str = Field(min_length=3, max_length=500)
    role: ParticipantRole
    surface_forms: list[str] = Field(min_length=1)
    canonical_actor_ref: str | None = Field(default=None, max_length=1000)
    institutional_role: str | None = Field(default=None, max_length=1000)
    provenance_ref: str = Field(min_length=3, max_length=500)
    surface_form_does_not_establish_canonical_identity: Literal[True] = True
    participant_role_is_contextual_interpretation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class PragmaticContentUnit(BaseModel):
    content_unit_id: str = Field(min_length=3, max_length=500)
    source_excerpt_ref: str = Field(min_length=3, max_length=500)
    surface_text: str = Field(min_length=1, max_length=20000)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=1)
    linked_predecessor_proposition_ref: str | None = Field(default=None, max_length=1000)
    provenance_ref: str = Field(min_length=3, max_length=500)
    content_unit_does_not_establish_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_span(self):
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class PragmaticCue(BaseModel):
    cue_id: str = Field(min_length=3, max_length=500)
    source_excerpt_ref: str = Field(min_length=3, max_length=500)
    surface_text: str = Field(min_length=1, max_length=2000)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=1)
    cue_type: Literal["speech-act", "setting", "register", "audience", "politeness", "intent"]
    content_unit_ref: str | None = Field(default=None, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    cue_is_interpretive_evidence_not_world_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_span(self):
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class PragmaticContext(BaseModel):
    context_id: str = Field(min_length=3, max_length=500)
    source_excerpt_ref: str = Field(min_length=3, max_length=500)
    genre: GenreType
    register_type: RegisterType
    setting_text: str | None = Field(default=None, max_length=5000)
    speaker_refs: list[str] = Field(min_length=1)
    audience_refs: list[str] = Field(default_factory=list)
    cue_refs: list[str] = Field(default_factory=list)
    state: PragmaticReviewState
    confidence: float = Field(ge=0.0, le=1.0)
    reviewer_ref: str | None = Field(default=None, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    genre_does_not_establish_source_authority: Literal[True] = True
    register_does_not_establish_credibility: Literal[True] = True

    @model_validator(mode="after")
    def validate_review(self):
        if self.state == PragmaticReviewState.accepted and not self.reviewer_ref:
            raise ValueError("accepted pragmatic context requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SpeechAct(BaseModel):
    speech_act_id: str = Field(min_length=3, max_length=500)
    context_ref: str = Field(min_length=3, max_length=500)
    content_unit_ref: str = Field(min_length=3, max_length=500)
    cue_ref: str = Field(min_length=3, max_length=500)
    act_type: SpeechActType
    speaker_ref: str = Field(min_length=3, max_length=500)
    audience_refs: list[str] = Field(default_factory=list)
    state: PragmaticReviewState
    confidence: float = Field(ge=0.0, le=1.0)
    reviewer_ref: str | None = Field(default=None, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    act_classification_is_not_truth_verdict: Literal[True] = True
    act_classification_does_not_create_legal_or_normative_force: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_review(self):
        if self.state == PragmaticReviewState.accepted and not self.reviewer_ref:
            raise ValueError("accepted speech act requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CommunicativeIntent(BaseModel):
    intent_id: str = Field(min_length=3, max_length=500)
    speech_act_ref: str = Field(min_length=3, max_length=500)
    intent_type: CommunicativeIntentType
    goal_description: str = Field(min_length=1, max_length=5000)
    state: PragmaticReviewState
    confidence: float = Field(ge=0.0, le=1.0)
    reviewer_ref: str | None = Field(default=None, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    intent_is_interpretation_not_private_mental_state: Literal[True] = True
    intent_does_not_establish_communicative_success: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_review(self):
        if self.state == PragmaticReviewState.accepted and not self.reviewer_ref:
            raise ValueError("accepted communicative intent requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class PragmaticInterpretation(BaseModel):
    interpretation_id: str = Field(min_length=3, max_length=500)
    predecessor_epistemic_interpretation_ref: str = Field(min_length=3, max_length=500)
    source_excerpt_refs: list[str] = Field(min_length=1)
    context_refs: list[str] = Field(min_length=1)
    speech_act_refs: list[str] = Field(min_length=1)
    intent_refs: list[str] = Field(min_length=1)
    unresolved_refs: list[str] = Field(default_factory=list)
    state: PragmaticReviewState
    confidence: float = Field(ge=0.0, le=1.0)
    reviewer_ref: str | None = Field(default=None, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    predecessor_objects_remain_immutable: Literal[True] = True
    interpretation_is_not_truth_verdict: Literal[True] = True
    interpretation_does_not_establish_speaker_private_intent: Literal[True] = True

    @model_validator(mode="after")
    def validate_review(self):
        if self.state == PragmaticReviewState.accepted and not self.reviewer_ref:
            raise ValueError("accepted pragmatic interpretation requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class PragmaticProvenanceRecord(BaseModel):
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


class PragmaticSemanticSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    predecessor_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    interpretation_refs: list[str] = Field(min_length=1)
    deterministic_semantic_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_does_not_freeze_truth_or_intent: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class PragmaticMeaningSpeechActIntentBundle(BaseModel):
    release: Literal["4.6.0"] = "4.6.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    extends_contracts: list[str] = Field(min_length=5)
    policy: PragmaticPolicy
    epistemic_semantics: EpistemicModalNegationCertaintyBundle
    source_excerpts: list[PragmaticSourceExcerpt] = Field(min_length=1)
    participants: list[CommunicativeParticipant] = Field(min_length=1)
    content_units: list[PragmaticContentUnit] = Field(min_length=1)
    cues: list[PragmaticCue] = Field(min_length=1)
    contexts: list[PragmaticContext] = Field(min_length=1)
    speech_acts: list[SpeechAct] = Field(min_length=1)
    intents: list[CommunicativeIntent] = Field(min_length=1)
    provenance_records: list[PragmaticProvenanceRecord] = Field(min_length=1)
    interpretations: list[PragmaticInterpretation] = Field(min_length=1)
    snapshots: list[PragmaticSemanticSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.extends_contracts != EXTENDS_CONTRACTS:
            raise ValueError("extends_contracts must preserve declared v4.6 dependency order")
        if self.epistemic_semantics.release != "4.5.0" or self.epistemic_semantics.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.6 must embed governed v4.5 epistemic predecessor")

        groups = (
            ([x.source_excerpt_id for x in self.source_excerpts], "source excerpt ids"),
            ([x.participant_id for x in self.participants], "participant ids"),
            ([x.content_unit_id for x in self.content_units], "content unit ids"),
            ([x.cue_id for x in self.cues], "cue ids"),
            ([x.context_id for x in self.contexts], "context ids"),
            ([x.speech_act_id for x in self.speech_acts], "speech act ids"),
            ([x.intent_id for x in self.intents], "intent ids"),
            ([x.provenance_id for x in self.provenance_records], "provenance ids"),
            ([x.interpretation_id for x in self.interpretations], "interpretation ids"),
            ([x.snapshot_id for x in self.snapshots], "snapshot ids"),
        )
        for values, label in groups:
            _unique(values, label)

        excerpts = {x.source_excerpt_id: x for x in self.source_excerpts}
        participants = {x.participant_id: x for x in self.participants}
        content_units = {x.content_unit_id: x for x in self.content_units}
        cues = {x.cue_id: x for x in self.cues}
        contexts = {x.context_id: x for x in self.contexts}
        acts = {x.speech_act_id: x for x in self.speech_acts}
        intents = {x.intent_id: x for x in self.intents}
        provenances = {x.provenance_id: x for x in self.provenance_records}
        interpretations = {x.interpretation_id: x for x in self.interpretations}
        predecessor_interpretations = {x.interpretation_id for x in self.epistemic_semantics.interpretations}
        predecessor_props = {x.proposition_id for x in self.epistemic_semantics.propositions}

        for participant in self.participants:
            if participant.source_excerpt_ref not in excerpts:
                raise ValueError("participant source_excerpt_ref must resolve")
            excerpt = excerpts[participant.source_excerpt_ref]
            if any(form not in excerpt.content for form in participant.surface_forms):
                raise ValueError("participant surface forms must occur in source excerpt")
            if participant.provenance_ref not in provenances:
                raise ValueError("participant provenance_ref must resolve")

        for unit in self.content_units:
            if unit.source_excerpt_ref not in excerpts:
                raise ValueError("content unit source_excerpt_ref must resolve")
            excerpt = excerpts[unit.source_excerpt_ref]
            if excerpt.content[unit.char_start:unit.char_end] != unit.surface_text:
                raise ValueError("content unit span must reproduce immutable source text")
            if unit.linked_predecessor_proposition_ref and unit.linked_predecessor_proposition_ref not in predecessor_props:
                raise ValueError("linked predecessor proposition ref must resolve")
            if unit.provenance_ref not in provenances:
                raise ValueError("content unit provenance_ref must resolve")

        for cue in self.cues:
            if cue.source_excerpt_ref not in excerpts:
                raise ValueError("cue source excerpt must resolve")
            excerpt = excerpts[cue.source_excerpt_ref]
            if excerpt.content[cue.char_start:cue.char_end] != cue.surface_text:
                raise ValueError("cue span must reproduce immutable source text")
            if cue.content_unit_ref and cue.content_unit_ref not in content_units:
                raise ValueError("cue content_unit_ref must resolve")
            if cue.provenance_ref not in provenances:
                raise ValueError("cue provenance_ref must resolve")

        for context in self.contexts:
            if context.source_excerpt_ref not in excerpts:
                raise ValueError("context source excerpt must resolve")
            if any(ref not in participants for ref in context.speaker_refs + context.audience_refs):
                raise ValueError("context participant refs must resolve")
            if any(ref not in cues for ref in context.cue_refs):
                raise ValueError("context cue refs must resolve")
            if context.provenance_ref not in provenances:
                raise ValueError("context provenance_ref must resolve")

        for act in self.speech_acts:
            if act.context_ref not in contexts or act.content_unit_ref not in content_units or act.cue_ref not in cues:
                raise ValueError("speech act context/content/cue refs must resolve")
            if act.speaker_ref not in participants or any(ref not in participants for ref in act.audience_refs):
                raise ValueError("speech act participant refs must resolve")
            if act.provenance_ref not in provenances:
                raise ValueError("speech act provenance_ref must resolve")

        for intent in self.intents:
            if intent.speech_act_ref not in acts:
                raise ValueError("communicative intent speech_act_ref must resolve")
            if intent.provenance_ref not in provenances:
                raise ValueError("communicative intent provenance_ref must resolve")

        for interpretation in self.interpretations:
            if interpretation.predecessor_epistemic_interpretation_ref not in predecessor_interpretations:
                raise ValueError("pragmatic interpretation predecessor epistemic ref must resolve")
            if any(ref not in excerpts for ref in interpretation.source_excerpt_refs):
                raise ValueError("interpretation source excerpt refs must resolve")
            if any(ref not in contexts for ref in interpretation.context_refs):
                raise ValueError("interpretation context refs must resolve")
            if any(ref not in acts for ref in interpretation.speech_act_refs):
                raise ValueError("interpretation speech act refs must resolve")
            if any(ref not in intents for ref in interpretation.intent_refs):
                raise ValueError("interpretation intent refs must resolve")
            if interpretation.provenance_ref not in provenances:
                raise ValueError("interpretation provenance_ref must resolve")

        object_ids = (
            set(excerpts) | set(participants) | set(content_units) | set(cues) | set(contexts) |
            set(acts) | set(intents) | set(interpretations) | {x.snapshot_id for x in self.snapshots}
        )
        for provenance in self.provenance_records:
            if any(ref not in object_ids for ref in provenance.subject_refs):
                raise ValueError("provenance subject_ref must resolve to a v4.6 object")

        predecessor_fp = self.epistemic_semantics.fingerprint()
        for snapshot in self.snapshots:
            if snapshot.predecessor_fingerprint_sha256 != predecessor_fp:
                raise ValueError("snapshot predecessor fingerprint must match embedded v4.5 bundle")
            if any(ref not in interpretations for ref in snapshot.interpretation_refs):
                raise ValueError("snapshot interpretation refs must resolve")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def _span(text: str, fragment: str, start: int = 0) -> tuple[int, int]:
    i = text.index(fragment, start)
    return i, i + len(fragment)


@lru_cache(maxsize=1)
def reference_pragmatic_meaning_speech_act_intent_bundle() -> PragmaticMeaningSpeechActIntentBundle:
    predecessor = reference_epistemic_modal_negation_certainty_bundle()
    content = (
        "At the public hearing, the agency stated that the measure may reduce emissions. "
        "The agency asked residents to submit comments by Friday, recommended delaying implementation, "
        "warned that immediate adoption could disrupt service, and promised to publish a revised plan next month."
    )
    excerpt = PragmaticSourceExcerpt(
        source_excerpt_id="pragmatic-source:public-hearing-note:v1",
        source_ref="source:pragmatic-public-hearing-note:v1",
        language_ref="language:en",
        content=content,
        content_sha256=canonical_sha256(content),
        provenance_ref="prov:pragmatic-source:reference",
        metadata={"purpose": "reference-only pragmatic meaning, speech-act, and communicative-intent fixture"},
    )

    participants = [
        CommunicativeParticipant(
            participant_id="participant:agency-speaker",
            source_excerpt_ref=excerpt.source_excerpt_id,
            role=ParticipantRole.speaker,
            surface_forms=["the agency", "The agency"],
            institutional_role="institutional-speaker-surface-role",
            provenance_ref="prov:pragmatic-participants:reference",
        ),
        CommunicativeParticipant(
            participant_id="participant:residents-audience",
            source_excerpt_ref=excerpt.source_excerpt_id,
            role=ParticipantRole.audience,
            surface_forms=["residents"],
            provenance_ref="prov:pragmatic-participants:reference",
        ),
    ]

    unit_specs = [
        ("content:measure-may-reduce-emissions", "the measure may reduce emissions"),
        ("content:submit-comments", "submit comments by Friday"),
        ("content:delay-implementation", "delaying implementation"),
        ("content:adoption-disrupt-service", "immediate adoption could disrupt service"),
        ("content:publish-revised-plan", "publish a revised plan next month"),
    ]
    content_units: list[PragmaticContentUnit] = []
    for uid, surface in unit_specs:
        s, e = _span(content, surface)
        content_units.append(PragmaticContentUnit(
            content_unit_id=uid,
            source_excerpt_ref=excerpt.source_excerpt_id,
            surface_text=surface,
            char_start=s,
            char_end=e,
            provenance_ref="prov:pragmatic-content:reference",
        ))

    cue_specs = [
        ("cue:public-hearing", "public hearing", "setting", None),
        ("cue:stated", "stated", "speech-act", "content:measure-may-reduce-emissions"),
        ("cue:asked", "asked", "speech-act", "content:submit-comments"),
        ("cue:recommended", "recommended", "speech-act", "content:delay-implementation"),
        ("cue:warned", "warned", "speech-act", "content:adoption-disrupt-service"),
        ("cue:promised", "promised", "speech-act", "content:publish-revised-plan"),
    ]
    cues: list[PragmaticCue] = []
    for cid, surface, ctype, uref in cue_specs:
        s, e = _span(content, surface)
        cues.append(PragmaticCue(
            cue_id=cid,
            source_excerpt_ref=excerpt.source_excerpt_id,
            surface_text=surface,
            char_start=s,
            char_end=e,
            cue_type=ctype,
            content_unit_ref=uref,
            provenance_ref="prov:pragmatic-cues:reference",
        ))

    context = PragmaticContext(
        context_id="pragmatic-context:public-hearing:reference",
        source_excerpt_ref=excerpt.source_excerpt_id,
        genre=GenreType.public_hearing,
        register_type=RegisterType.formal,
        setting_text="public hearing",
        speaker_refs=["participant:agency-speaker"],
        audience_refs=["participant:residents-audience"],
        cue_refs=["cue:public-hearing"],
        state=PragmaticReviewState.accepted,
        confidence=0.99,
        reviewer_ref="reviewer:pragmatic-semantics:v1",
        provenance_ref="prov:pragmatic-context:reference",
    )

    act_specs = [
        ("speech-act:assert-measure", "content:measure-may-reduce-emissions", "cue:stated", SpeechActType.assertion, []),
        ("speech-act:request-comments", "content:submit-comments", "cue:asked", SpeechActType.request, ["participant:residents-audience"]),
        ("speech-act:recommend-delay", "content:delay-implementation", "cue:recommended", SpeechActType.recommendation, ["participant:residents-audience"]),
        ("speech-act:warn-disruption", "content:adoption-disrupt-service", "cue:warned", SpeechActType.warning, ["participant:residents-audience"]),
        ("speech-act:commit-revised-plan", "content:publish-revised-plan", "cue:promised", SpeechActType.commitment, ["participant:residents-audience"]),
    ]
    acts = [
        SpeechAct(
            speech_act_id=aid,
            context_ref=context.context_id,
            content_unit_ref=uref,
            cue_ref=cref,
            act_type=atype,
            speaker_ref="participant:agency-speaker",
            audience_refs=aud,
            state=PragmaticReviewState.accepted,
            confidence=0.99,
            reviewer_ref="reviewer:pragmatic-semantics:v1",
            provenance_ref="prov:pragmatic-speech-acts:reference",
        )
        for aid, uref, cref, atype, aud in act_specs
    ]

    intent_specs = [
        ("intent:inform-measure", "speech-act:assert-measure", CommunicativeIntentType.inform, "present the measure-emissions proposition as information"),
        ("intent:elicit-comments", "speech-act:request-comments", CommunicativeIntentType.elicit_action, "seek submission of public comments by the stated deadline"),
        ("intent:advise-delay", "speech-act:recommend-delay", CommunicativeIntentType.advise, "advise delaying implementation"),
        ("intent:alert-disruption", "speech-act:warn-disruption", CommunicativeIntentType.alert, "alert the audience to a stated potential service disruption"),
        ("intent:commit-plan", "speech-act:commit-revised-plan", CommunicativeIntentType.commit, "express a commitment to publish a revised plan"),
    ]
    intents = [
        CommunicativeIntent(
            intent_id=iid,
            speech_act_ref=aref,
            intent_type=itype,
            goal_description=goal,
            state=PragmaticReviewState.accepted,
            confidence=0.98,
            reviewer_ref="reviewer:pragmatic-semantics:v1",
            provenance_ref="prov:pragmatic-intents:reference",
        )
        for iid, aref, itype, goal in intent_specs
    ]

    interpretation = PragmaticInterpretation(
        interpretation_id="pragmatic-interpretation:public-hearing:baseline",
        predecessor_epistemic_interpretation_ref=predecessor.interpretations[0].interpretation_id,
        source_excerpt_refs=[excerpt.source_excerpt_id],
        context_refs=[context.context_id],
        speech_act_refs=[x.speech_act_id for x in acts],
        intent_refs=[x.intent_id for x in intents],
        unresolved_refs=["canonical-actor:agency", "canonical-actor:residents"],
        state=PragmaticReviewState.accepted,
        confidence=0.98,
        reviewer_ref="reviewer:pragmatic-semantics:v1",
        provenance_ref="prov:pragmatic-interpretation:reference",
    )

    snapshot_material = {
        "predecessor": predecessor.fingerprint(),
        "excerpt": excerpt.fingerprint(),
        "participants": [x.fingerprint() for x in participants],
        "content_units": [x.fingerprint() for x in content_units],
        "cues": [x.fingerprint() for x in cues],
        "context": context.fingerprint(),
        "speech_acts": [x.fingerprint() for x in acts],
        "intents": [x.fingerprint() for x in intents],
        "interpretation": interpretation.fingerprint(),
    }
    snapshot = PragmaticSemanticSnapshot(
        snapshot_id="snapshot:pragmatic-semantics:public-hearing:v1",
        predecessor_fingerprint_sha256=predecessor.fingerprint(),
        interpretation_refs=[interpretation.interpretation_id],
        deterministic_semantic_fingerprint_sha256=canonical_sha256(snapshot_material),
    )

    object_groups = {
        "prov:pragmatic-source:reference": [excerpt.source_excerpt_id],
        "prov:pragmatic-participants:reference": [x.participant_id for x in participants],
        "prov:pragmatic-content:reference": [x.content_unit_id for x in content_units],
        "prov:pragmatic-cues:reference": [x.cue_id for x in cues],
        "prov:pragmatic-context:reference": [context.context_id],
        "prov:pragmatic-speech-acts:reference": [x.speech_act_id for x in acts],
        "prov:pragmatic-intents:reference": [x.intent_id for x in intents],
        "prov:pragmatic-interpretation:reference": [interpretation.interpretation_id, snapshot.snapshot_id],
    }
    provenances = [
        PragmaticProvenanceRecord(
            provenance_id=pid,
            subject_refs=subjects,
            method=InterpretationMethod.manual,
            produced_by_ref="reviewer:pragmatic-semantics:v1" if pid != "prov:pragmatic-source:reference" else "actor:platform-core-reference-builder",
            source_refs=["source:pragmatic-public-hearing-note:v1"],
            reviewer_ref="reviewer:pragmatic-semantics:v1" if pid != "prov:pragmatic-source:reference" else None,
            transformation_notes=["Pragmatic classification does not establish proposition truth, source authority, private mental state, normative force, or communicative success."],
        )
        for pid, subjects in object_groups.items()
    ]

    return PragmaticMeaningSpeechActIntentBundle(
        extends_contracts=list(EXTENDS_CONTRACTS),
        policy=PragmaticPolicy(policy_id="pragmatic-meaning-speech-act-intent-policy:v4.6"),
        epistemic_semantics=predecessor,
        source_excerpts=[excerpt],
        participants=participants,
        content_units=content_units,
        cues=cues,
        contexts=[context],
        speech_acts=acts,
        intents=intents,
        provenance_records=provenances,
        interpretations=[interpretation],
        snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    bundle = reference_pragmatic_meaning_speech_act_intent_bundle()
    act_counts = {kind.value: sum(x.act_type == kind for x in bundle.speech_acts) for kind in SpeechActType}
    intent_counts = {kind.value: sum(x.intent_type == kind for x in bundle.intents) for kind in CommunicativeIntentType}
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "extends_contracts": list(EXTENDS_CONTRACTS),
        "identity": {
            "product": "Sustainable Catalyst Platform Core",
            "build": "Pragmatic Meaning, Speech Act & Communicative Intent",
            "major_api": "v4",
        },
        "principles": {
            "speech_act_is_distinct_from_proposition_truth": True,
            "communicative_intent_is_contextual_interpretation": True,
            "speaker_and_audience_roles_are_first_class": True,
            "genre_and_register_are_explicit_context": True,
            "pragmatic_cues_preserve_source_spans": True,
            "competing_interpretations_may_coexist": True,
            "accepted_interpretation_requires_governed_review": True,
            "predecessor_epistemic_objects_remain_immutable": True,
        },
        "boundaries": {
            "assertion_establishes_platform_truth": False,
            "request_creates_platform_obligation": False,
            "recommendation_establishes_normative_correctness": False,
            "warning_establishes_risk_as_fact": False,
            "commitment_guarantees_future_performance": False,
            "communicative_intent_reveals_private_mental_state": False,
            "genre_or_register_establishes_source_authority": False,
            "surface_speaker_establishes_canonical_actor_identity": False,
            "accepted_pragmatic_analysis_rewrites_v450_predecessor": False,
            "identity_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
            "context_graph_mutation_performed": False,
            "knowledge_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "extends_v450_epistemic_modal_negation_certainty": True,
            "prepares_v470_cross_document_context_graph": True,
            "prepares_v480_multilingual_context_alignment": True,
            "prepares_v490_contextual_semantic_evaluation": True,
            "prepares_v4100_unified_contextual_intelligence_runtime": True,
        },
        "reference": {
            "predecessor_release": bundle.epistemic_semantics.release,
            "predecessor_fingerprint_sha256": bundle.epistemic_semantics.fingerprint(),
            "source_excerpts": len(bundle.source_excerpts),
            "participants": len(bundle.participants),
            "content_units": len(bundle.content_units),
            "cues": len(bundle.cues),
            "contexts": len(bundle.contexts),
            "speech_acts": len(bundle.speech_acts),
            "intents": len(bundle.intents),
            "assertions": act_counts[SpeechActType.assertion.value],
            "requests": act_counts[SpeechActType.request.value],
            "recommendations": act_counts[SpeechActType.recommendation.value],
            "warnings": act_counts[SpeechActType.warning.value],
            "commitments": act_counts[SpeechActType.commitment.value],
            "inform_intents": intent_counts[CommunicativeIntentType.inform.value],
            "elicit_action_intents": intent_counts[CommunicativeIntentType.elicit_action.value],
            "advise_intents": intent_counts[CommunicativeIntentType.advise.value],
            "alert_intents": intent_counts[CommunicativeIntentType.alert.value],
            "commit_intents": intent_counts[CommunicativeIntentType.commit.value],
            "canonical_actor_bindings": sum(bool(x.canonical_actor_ref) for x in bundle.participants),
            "interpretations": len(bundle.interpretations),
            "snapshots": len(bundle.snapshots),
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
        "database_migration": "none",
    }
