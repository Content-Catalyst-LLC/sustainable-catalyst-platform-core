from __future__ import annotations

import hashlib
from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "4.1.0"
CONTRACT_VERSION = "sc.core.context-object-semantic-frame-foundation.v1"
PREDECESSOR_CORE_CONTRACT = "sc.core.sustainable-catalyst-computational-research-core.v1"

EXTENDS_CONTRACTS = [
    PREDECESSOR_CORE_CONTRACT,
    "sc.core.multilingual-text-language-object.v1",
    "sc.core.linguistic-annotation-provenance.v1",
    "sc.core.cross-lingual-semantic-linguistic-exchange.v1",
    "sc.core.investigation-session-research-context-runtime.v1",
]


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class ContextScopeKind(str, Enum):
    sentence = "sentence"
    paragraph = "paragraph"
    section = "section"
    document = "document"
    conversation = "conversation"
    research_session = "research-session"
    cross_document = "cross-document"


class SemanticFrameKind(str, Enum):
    event = "event"
    state = "state"
    relation = "relation"
    communication = "communication"
    cognition = "cognition"
    evaluation = "evaluation"
    causation = "causation"
    possession = "possession"
    motion = "motion"
    other = "other"


class MentionKind(str, Enum):
    entity = "entity"
    event = "event"
    concept = "concept"
    proposition = "proposition"
    time = "time"
    place = "place"
    quantity = "quantity"
    unresolved_reference = "unresolved-reference"
    other = "other"


class ParticipantRoleKind(str, Enum):
    agent = "agent"
    patient = "patient"
    theme = "theme"
    experiencer = "experiencer"
    stimulus = "stimulus"
    instrument = "instrument"
    beneficiary = "beneficiary"
    source = "source"
    goal = "goal"
    location = "location"
    time = "time"
    manner = "manner"
    proposition = "proposition"
    other = "other"


class InterpretationMethod(str, Enum):
    manual = "manual"
    scholarly = "scholarly"
    imported = "imported"
    rule_based = "rule-based"
    model_assisted = "model-assisted"
    graph_assisted = "graph-assisted"


class InterpretationReviewState(str, Enum):
    candidate = "candidate"
    reviewed = "reviewed"
    accepted = "accepted"
    rejected = "rejected"
    disputed = "disputed"


class ContextSemanticPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    original_language_remains_primary: Literal[True] = True
    translations_remain_derived: Literal[True] = True
    context_is_explicit_and_persistent: Literal[True] = True
    semantic_interpretation_preserves_provenance: Literal[True] = True
    multiple_interpretations_may_coexist: Literal[True] = True
    unresolved_reference_may_be_preserved: Literal[True] = True
    machine_interpretation_is_advisory: Literal[True] = True
    context_selection_does_not_promote_source_authority: Literal[True] = True
    semantic_frame_is_not_evidence_fact: Literal[True] = True
    interpretation_is_not_truth_verdict: Literal[True] = True
    context_graph_mutation_authorized: Literal[False] = False
    identity_graph_mutation_authorized: Literal[False] = False
    evidence_graph_mutation_authorized: Literal[False] = False

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SourceContextBinding(BaseModel):
    source_binding_id: str = Field(min_length=3, max_length=500)
    source_object_ref: str = Field(min_length=3, max_length=1000)
    source_contract: str = Field(min_length=10, max_length=500)
    source_text_ref: str = Field(min_length=3, max_length=1000)
    source_text_unit_ref: str | None = Field(default=None, max_length=1000)
    language_ref: str = Field(min_length=2, max_length=500)
    script_ref: str | None = Field(default=None, max_length=500)
    content: str = Field(min_length=1, max_length=100000)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_provenance_refs: list[str] = Field(min_length=1)
    original_language_is_canonical: Literal[True] = True
    translation_is_derived_representation: Literal[True] = True
    source_binding_does_not_change_source_authority: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_source(self):
        if _sha256_text(self.content) != self.content_sha256:
            raise ValueError("content_sha256 must match source content")
        _unique(self.source_provenance_refs, "source_provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextObject(BaseModel):
    context_id: str = Field(min_length=3, max_length=500)
    source_binding_ref: str = Field(min_length=3, max_length=500)
    scope_kind: ContextScopeKind
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    content: str = Field(min_length=1, max_length=100000)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    language_ref: str = Field(min_length=2, max_length=500)
    parent_context_ref: str | None = Field(default=None, max_length=500)
    preceding_context_refs: list[str] = Field(default_factory=list)
    following_context_refs: list[str] = Field(default_factory=list)
    provenance_ref: str = Field(min_length=3, max_length=500)
    context_is_interpretive_container_not_evidence: Literal[True] = True
    source_authority_unchanged_by_context_selection: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_context(self):
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        if _sha256_text(self.content) != self.content_sha256:
            raise ValueError("content_sha256 must match context content")
        _unique(self.preceding_context_refs, "preceding_context_refs")
        _unique(self.following_context_refs, "following_context_refs")
        if self.context_id in self.preceding_context_refs or self.context_id in self.following_context_refs:
            raise ValueError("context cannot precede or follow itself")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SemanticMention(BaseModel):
    mention_id: str = Field(min_length=3, max_length=500)
    context_ref: str = Field(min_length=3, max_length=500)
    mention_kind: MentionKind
    surface_text: str = Field(min_length=1, max_length=10000)
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    language_ref: str = Field(min_length=2, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    unresolved_referent_allowed: Literal[True] = True
    mention_is_not_entity_identity: Literal[True] = True
    mention_is_not_evidence_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_mention(self):
        if self.char_end <= self.char_start:
            raise ValueError("mention char_end must be greater than char_start")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextSemanticProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3, max_length=500)
    subject_refs: list[str] = Field(min_length=1)
    method: InterpretationMethod
    produced_by_ref: str = Field(min_length=3, max_length=1000)
    source_refs: list[str] = Field(min_length=1)
    model_ref: str | None = Field(default=None, max_length=1000)
    model_version: str | None = Field(default=None, max_length=240)
    tool_ref: str | None = Field(default=None, max_length=1000)
    tool_version: str | None = Field(default=None, max_length=240)
    created_at: str | None = Field(default=None, max_length=80)
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    review_note: str | None = Field(default=None, max_length=5000)
    machine_or_graph_output_is_advisory: Literal[True] = True
    provenance_does_not_establish_semantic_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_provenance(self):
        _unique(self.subject_refs, "provenance subject_refs")
        _unique(self.source_refs, "provenance source_refs")
        if self.method in {InterpretationMethod.model_assisted, InterpretationMethod.graph_assisted} and not self.model_ref:
            raise ValueError("model/graph-assisted semantic provenance requires model_ref")
        if self.model_version and not self.model_ref:
            raise ValueError("model_version requires model_ref")
        if self.tool_version and not self.tool_ref:
            raise ValueError("tool_version requires tool_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SemanticParticipant(BaseModel):
    participant_id: str = Field(min_length=3, max_length=500)
    frame_ref: str = Field(min_length=3, max_length=500)
    role_kind: ParticipantRoleKind
    mention_ref: str | None = Field(default=None, max_length=500)
    proposition_context_ref: str | None = Field(default=None, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    participant_binding_is_interpretive: Literal[True] = True
    participant_binding_is_not_identity_resolution: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_participant(self):
        if (self.mention_ref is None) == (self.proposition_context_ref is None):
            raise ValueError("participant requires exactly one of mention_ref or proposition_context_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SemanticFrame(BaseModel):
    frame_id: str = Field(min_length=3, max_length=500)
    context_ref: str = Field(min_length=3, max_length=500)
    frame_kind: SemanticFrameKind
    trigger_text: str = Field(min_length=1, max_length=10000)
    trigger_char_start: int = Field(ge=0)
    trigger_char_end: int = Field(gt=0)
    predicate_lemma: str | None = Field(default=None, max_length=1000)
    mention_refs: list[str] = Field(default_factory=list)
    participant_refs: list[str] = Field(default_factory=list)
    provenance_ref: str = Field(min_length=3, max_length=500)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    frame_is_interpretation_not_source_fact: Literal[True] = True
    machine_frame_is_advisory: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_frame(self):
        if self.trigger_char_end <= self.trigger_char_start:
            raise ValueError("trigger_char_end must be greater than trigger_char_start")
        _unique(self.mention_refs, "frame mention_refs")
        _unique(self.participant_refs, "frame participant_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SemanticInterpretation(BaseModel):
    interpretation_id: str = Field(min_length=3, max_length=500)
    context_ref: str = Field(min_length=3, max_length=500)
    frame_refs: list[str] = Field(min_length=1)
    mention_refs: list[str] = Field(default_factory=list)
    provenance_ref: str = Field(min_length=3, max_length=500)
    review_state: InterpretationReviewState = InterpretationReviewState.candidate
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    alternative_interpretation_refs: list[str] = Field(default_factory=list)
    selected_by_core: Literal[False] = False
    unresolved_ambiguity_preserved: Literal[True] = True
    interpretation_is_not_truth_verdict: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_interpretation(self):
        _unique(self.frame_refs, "interpretation frame_refs")
        _unique(self.mention_refs, "interpretation mention_refs")
        _unique(self.alternative_interpretation_refs, "alternative_interpretation_refs")
        if self.interpretation_id in self.alternative_interpretation_refs:
            raise ValueError("interpretation cannot list itself as an alternative")
        if self.review_state != InterpretationReviewState.candidate and not self.reviewer_ref:
            raise ValueError("reviewed semantic interpretation requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextSemanticSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    source_binding_refs: list[str] = Field(min_length=1)
    context_refs: list[str] = Field(min_length=1)
    interpretation_refs: list[str] = Field(min_length=1)
    deterministic_context_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_is_not_truth_certification: Literal[True] = True
    snapshot_does_not_mutate_graphs: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        _unique(self.source_binding_refs, "snapshot source_binding_refs")
        _unique(self.context_refs, "snapshot context_refs")
        _unique(self.interpretation_refs, "snapshot interpretation_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextObjectSemanticFrameBundle(BaseModel):
    release: Literal["4.1.0"] = "4.1.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_core_contract: Literal[PREDECESSOR_CORE_CONTRACT] = PREDECESSOR_CORE_CONTRACT
    extends_contracts: list[str] = Field(min_length=5)
    policy: ContextSemanticPolicy
    source_bindings: list[SourceContextBinding] = Field(min_length=1)
    contexts: list[ContextObject] = Field(min_length=1)
    mentions: list[SemanticMention] = Field(default_factory=list)
    provenance_records: list[ContextSemanticProvenanceRecord] = Field(min_length=1)
    participants: list[SemanticParticipant] = Field(default_factory=list)
    frames: list[SemanticFrame] = Field(min_length=1)
    interpretations: list[SemanticInterpretation] = Field(min_length=1)
    snapshots: list[ContextSemanticSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.extends_contracts != EXTENDS_CONTRACTS:
            raise ValueError("extends_contracts must preserve the declared v4.1 dependency order")

        for values, label in (
            ([x.source_binding_id for x in self.source_bindings], "source binding ids"),
            ([x.context_id for x in self.contexts], "context ids"),
            ([x.mention_id for x in self.mentions], "mention ids"),
            ([x.provenance_id for x in self.provenance_records], "provenance ids"),
            ([x.participant_id for x in self.participants], "participant ids"),
            ([x.frame_id for x in self.frames], "frame ids"),
            ([x.interpretation_id for x in self.interpretations], "interpretation ids"),
            ([x.snapshot_id for x in self.snapshots], "snapshot ids"),
        ):
            _unique(values, label)

        sources = {x.source_binding_id: x for x in self.source_bindings}
        contexts = {x.context_id: x for x in self.contexts}
        mentions = {x.mention_id: x for x in self.mentions}
        provenances = {x.provenance_id: x for x in self.provenance_records}
        participants = {x.participant_id: x for x in self.participants}
        frames = {x.frame_id: x for x in self.frames}
        interpretations = {x.interpretation_id: x for x in self.interpretations}

        for context in self.contexts:
            if context.source_binding_ref not in sources:
                raise ValueError("context source_binding_ref must resolve")
            if context.provenance_ref not in provenances:
                raise ValueError("context provenance_ref must resolve")
            source = sources[context.source_binding_ref]
            if context.char_end > len(source.content):
                raise ValueError("context range cannot exceed source content")
            if source.content[context.char_start:context.char_end] != context.content:
                raise ValueError("context content must match canonical source slice")
            if context.language_ref != source.language_ref:
                raise ValueError("v4.1 reference context language must preserve source language identity")
            if context.parent_context_ref:
                if context.parent_context_ref not in contexts:
                    raise ValueError("parent_context_ref must resolve")
                parent = contexts[context.parent_context_ref]
                if parent.source_binding_ref != context.source_binding_ref:
                    raise ValueError("parent and child contexts must bind to the same source")
                if context.char_start < parent.char_start or context.char_end > parent.char_end:
                    raise ValueError("child context must fit inside parent context")
            for ref in context.preceding_context_refs + context.following_context_refs:
                if ref not in contexts:
                    raise ValueError("context adjacency reference must resolve")

        for mention in self.mentions:
            if mention.context_ref not in contexts:
                raise ValueError("mention context_ref must resolve")
            if mention.provenance_ref not in provenances:
                raise ValueError("mention provenance_ref must resolve")
            context = contexts[mention.context_ref]
            if mention.char_end > len(context.content):
                raise ValueError("mention range cannot exceed context")
            if context.content[mention.char_start:mention.char_end] != mention.surface_text:
                raise ValueError("mention surface_text must match context slice")
            if mention.language_ref != context.language_ref:
                raise ValueError("mention language must match context language")

        for participant in self.participants:
            if participant.frame_ref not in frames:
                raise ValueError("participant frame_ref must resolve")
            if participant.provenance_ref not in provenances:
                raise ValueError("participant provenance_ref must resolve")
            if participant.mention_ref:
                if participant.mention_ref not in mentions:
                    raise ValueError("participant mention_ref must resolve")
                if mentions[participant.mention_ref].context_ref != frames[participant.frame_ref].context_ref:
                    raise ValueError("participant mention must belong to frame context")
            if participant.proposition_context_ref and participant.proposition_context_ref not in contexts:
                raise ValueError("participant proposition_context_ref must resolve")

        for frame in self.frames:
            if frame.context_ref not in contexts:
                raise ValueError("frame context_ref must resolve")
            if frame.provenance_ref not in provenances:
                raise ValueError("frame provenance_ref must resolve")
            context = contexts[frame.context_ref]
            if frame.trigger_char_end > len(context.content):
                raise ValueError("frame trigger range cannot exceed context")
            if context.content[frame.trigger_char_start:frame.trigger_char_end] != frame.trigger_text:
                raise ValueError("frame trigger_text must match context slice")
            for ref in frame.mention_refs:
                if ref not in mentions:
                    raise ValueError("frame mention_ref must resolve")
                if mentions[ref].context_ref != frame.context_ref:
                    raise ValueError("frame mention must belong to frame context")
            for ref in frame.participant_refs:
                if ref not in participants:
                    raise ValueError("frame participant_ref must resolve")
                if participants[ref].frame_ref != frame.frame_id:
                    raise ValueError("frame participant must point back to frame")

        for interpretation in self.interpretations:
            if interpretation.context_ref not in contexts:
                raise ValueError("interpretation context_ref must resolve")
            if interpretation.provenance_ref not in provenances:
                raise ValueError("interpretation provenance_ref must resolve")
            for ref in interpretation.frame_refs:
                if ref not in frames:
                    raise ValueError("interpretation frame_ref must resolve")
            for ref in interpretation.mention_refs:
                if ref not in mentions:
                    raise ValueError("interpretation mention_ref must resolve")
            for ref in interpretation.alternative_interpretation_refs:
                if ref not in interpretations:
                    raise ValueError("alternative interpretation_ref must resolve")

        object_ids = (
            set(sources) | set(contexts) | set(mentions) | set(participants) |
            set(frames) | set(interpretations) | {x.snapshot_id for x in self.snapshots}
        )
        for provenance in self.provenance_records:
            for ref in provenance.subject_refs:
                if ref not in object_ids:
                    raise ValueError("provenance subject_ref must resolve to a v4.1 object")

        for snapshot in self.snapshots:
            if any(ref not in sources for ref in snapshot.source_binding_refs):
                raise ValueError("snapshot source_binding_ref must resolve")
            if any(ref not in contexts for ref in snapshot.context_refs):
                raise ValueError("snapshot context_ref must resolve")
            if any(ref not in interpretations for ref in snapshot.interpretation_refs):
                raise ValueError("snapshot interpretation_ref must resolve")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


@lru_cache(maxsize=1)
def reference_context_object_semantic_frame_bundle() -> ContextObjectSemanticFrameBundle:
    text = (
        "The commission rejected the proposal after the ministry revised its estimate. "
        "It nevertheless remained politically viable."
    )
    source = SourceContextBinding(
        source_binding_id="context-source:policy-note:v1",
        source_object_ref="source:policy-note:v1",
        source_contract="sc.core.multilingual-text-language-object.v1",
        source_text_ref="text-source:policy-note:v1",
        source_text_unit_ref="text-unit:policy-note:document",
        language_ref="language:en",
        script_ref="script:Latn",
        content=text,
        content_sha256=_sha256_text(text),
        source_provenance_refs=["provenance:source-policy-note:v1"],
    )

    doc = ContextObject(
        context_id="context:policy-note:document",
        source_binding_ref=source.source_binding_id,
        scope_kind=ContextScopeKind.document,
        char_start=0,
        char_end=len(text),
        content=text,
        content_sha256=_sha256_text(text),
        language_ref="language:en",
        provenance_ref="prov:context:reference",
    )
    sentence_1_text = text[0:77]
    sentence_2_text = text[78:]
    sentence_1 = ContextObject(
        context_id="context:policy-note:sentence-1",
        source_binding_ref=source.source_binding_id,
        scope_kind=ContextScopeKind.sentence,
        char_start=0,
        char_end=77,
        content=sentence_1_text,
        content_sha256=_sha256_text(sentence_1_text),
        language_ref="language:en",
        parent_context_ref=doc.context_id,
        following_context_refs=["context:policy-note:sentence-2"],
        provenance_ref="prov:context:reference",
    )
    sentence_2 = ContextObject(
        context_id="context:policy-note:sentence-2",
        source_binding_ref=source.source_binding_id,
        scope_kind=ContextScopeKind.sentence,
        char_start=78,
        char_end=len(text),
        content=sentence_2_text,
        content_sha256=_sha256_text(sentence_2_text),
        language_ref="language:en",
        parent_context_ref=doc.context_id,
        preceding_context_refs=[sentence_1.context_id],
        provenance_ref="prov:context:reference",
    )

    mentions = [
        SemanticMention(mention_id="mention:commission", context_ref=sentence_1.context_id, mention_kind=MentionKind.entity,
                        surface_text="commission", char_start=4, char_end=14, language_ref="language:en", provenance_ref="prov:mention:reference"),
        SemanticMention(mention_id="mention:proposal", context_ref=sentence_1.context_id, mention_kind=MentionKind.concept,
                        surface_text="proposal", char_start=28, char_end=36, language_ref="language:en", provenance_ref="prov:mention:reference"),
        SemanticMention(mention_id="mention:ministry", context_ref=sentence_1.context_id, mention_kind=MentionKind.entity,
                        surface_text="ministry", char_start=47, char_end=55, language_ref="language:en", provenance_ref="prov:mention:reference"),
        SemanticMention(mention_id="mention:estimate", context_ref=sentence_1.context_id, mention_kind=MentionKind.concept,
                        surface_text="estimate", char_start=68, char_end=76, language_ref="language:en", provenance_ref="prov:mention:reference"),
        SemanticMention(mention_id="mention:it-unresolved", context_ref=sentence_2.context_id, mention_kind=MentionKind.unresolved_reference,
                        surface_text="It", char_start=0, char_end=2, language_ref="language:en", provenance_ref="prov:mention:reference"),
    ]

    frames = [
        SemanticFrame(frame_id="frame:rejection", context_ref=sentence_1.context_id, frame_kind=SemanticFrameKind.event,
                      trigger_text="rejected", trigger_char_start=15, trigger_char_end=23, predicate_lemma="reject",
                      mention_refs=["mention:commission", "mention:proposal"], participant_refs=["participant:rejection-agent", "participant:rejection-theme"],
                      provenance_ref="prov:frame:reference", confidence=1.0),
        SemanticFrame(frame_id="frame:revision", context_ref=sentence_1.context_id, frame_kind=SemanticFrameKind.event,
                      trigger_text="revised", trigger_char_start=56, trigger_char_end=63, predicate_lemma="revise",
                      mention_refs=["mention:ministry", "mention:estimate"], participant_refs=["participant:revision-agent", "participant:revision-theme"],
                      provenance_ref="prov:frame:reference", confidence=1.0),
        SemanticFrame(frame_id="frame:viability", context_ref=sentence_2.context_id, frame_kind=SemanticFrameKind.state,
                      trigger_text="remained", trigger_char_start=16, trigger_char_end=24, predicate_lemma="remain",
                      mention_refs=["mention:it-unresolved"], participant_refs=["participant:viability-theme"],
                      provenance_ref="prov:frame:reference", confidence=1.0,
                      metadata={"complement": "politically viable", "coreference_resolution_deferred_to_v4.3": True}),
    ]

    participants = [
        SemanticParticipant(participant_id="participant:rejection-agent", frame_ref="frame:rejection", role_kind=ParticipantRoleKind.agent,
                            mention_ref="mention:commission", provenance_ref="prov:frame:reference", confidence=1.0),
        SemanticParticipant(participant_id="participant:rejection-theme", frame_ref="frame:rejection", role_kind=ParticipantRoleKind.theme,
                            mention_ref="mention:proposal", provenance_ref="prov:frame:reference", confidence=1.0),
        SemanticParticipant(participant_id="participant:revision-agent", frame_ref="frame:revision", role_kind=ParticipantRoleKind.agent,
                            mention_ref="mention:ministry", provenance_ref="prov:frame:reference", confidence=1.0),
        SemanticParticipant(participant_id="participant:revision-theme", frame_ref="frame:revision", role_kind=ParticipantRoleKind.theme,
                            mention_ref="mention:estimate", provenance_ref="prov:frame:reference", confidence=1.0),
        SemanticParticipant(participant_id="participant:viability-theme", frame_ref="frame:viability", role_kind=ParticipantRoleKind.theme,
                            mention_ref="mention:it-unresolved", provenance_ref="prov:frame:reference", confidence=1.0),
    ]

    interpretation = SemanticInterpretation(
        interpretation_id="interpretation:policy-note:baseline",
        context_ref=doc.context_id,
        frame_refs=[x.frame_id for x in frames],
        mention_refs=[x.mention_id for x in mentions],
        provenance_ref="prov:interpretation:reference",
        review_state=InterpretationReviewState.candidate,
        confidence=1.0,
        metadata={
            "unresolved_reference": "mention:it-unresolved",
            "core_does_not_select_referent": True,
            "discourse_relation_inference_deferred_to_v4.2": True,
        },
    )

    snapshot_material = {
        "source": source.fingerprint(),
        "contexts": [doc.fingerprint(), sentence_1.fingerprint(), sentence_2.fingerprint()],
        "interpretation": interpretation.fingerprint(),
    }
    snapshot = ContextSemanticSnapshot(
        snapshot_id="snapshot:context-semantics:reference:v1",
        source_binding_refs=[source.source_binding_id],
        context_refs=[doc.context_id, sentence_1.context_id, sentence_2.context_id],
        interpretation_refs=[interpretation.interpretation_id],
        deterministic_context_fingerprint_sha256=canonical_sha256(snapshot_material),
    )

    provenances = [
        ContextSemanticProvenanceRecord(
            provenance_id="prov:context:reference",
            subject_refs=[doc.context_id, sentence_1.context_id, sentence_2.context_id],
            method=InterpretationMethod.manual,
            produced_by_ref="actor:platform-core-reference-builder",
            source_refs=[source.source_object_ref],
        ),
        ContextSemanticProvenanceRecord(
            provenance_id="prov:mention:reference",
            subject_refs=[x.mention_id for x in mentions],
            method=InterpretationMethod.manual,
            produced_by_ref="actor:platform-core-reference-builder",
            source_refs=[source.source_object_ref],
        ),
        ContextSemanticProvenanceRecord(
            provenance_id="prov:frame:reference",
            subject_refs=[x.frame_id for x in frames] + [x.participant_id for x in participants],
            method=InterpretationMethod.manual,
            produced_by_ref="actor:platform-core-reference-builder",
            source_refs=[source.source_object_ref],
        ),
        ContextSemanticProvenanceRecord(
            provenance_id="prov:interpretation:reference",
            subject_refs=[interpretation.interpretation_id, snapshot.snapshot_id],
            method=InterpretationMethod.manual,
            produced_by_ref="actor:platform-core-reference-builder",
            source_refs=[source.source_object_ref],
        ),
    ]

    return ContextObjectSemanticFrameBundle(
        extends_contracts=list(EXTENDS_CONTRACTS),
        policy=ContextSemanticPolicy(policy_id="context-semantic-policy:v4.1"),
        source_bindings=[source],
        contexts=[doc, sentence_1, sentence_2],
        mentions=mentions,
        provenance_records=provenances,
        participants=participants,
        frames=frames,
        interpretations=[interpretation],
        snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    bundle = reference_context_object_semantic_frame_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contracts": list(EXTENDS_CONTRACTS),
        "identity": {
            "product": "Sustainable Catalyst Platform Core",
            "build": "Context Object & Semantic Frame Foundation",
            "major_api": "v4",
        },
        "principles": {
            "original_language_remains_primary": True,
            "translations_remain_derived": True,
            "context_is_explicit_and_persistent": True,
            "semantic_interpretation_preserves_provenance": True,
            "multiple_interpretations_may_coexist": True,
            "unresolved_reference_may_be_preserved": True,
            "machine_interpretation_is_advisory": True,
            "context_selection_does_not_promote_source_authority": True,
            "semantic_frame_is_not_evidence_fact": True,
            "interpretation_is_not_truth_verdict": True,
        },
        "boundaries": {
            "core_executes_semantic_parser": False,
            "core_resolves_coreference": False,
            "core_infers_discourse_relations": False,
            "core_selects_best_interpretation": False,
            "semantic_frame_establishes_source_truth": False,
            "mention_establishes_entity_identity": False,
            "context_selection_promotes_epistemic_state": False,
            "identity_graph_mutation_performed": False,
            "relationship_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
            "context_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "prepares_v420_discourse_structure_rhetorical_semantics": True,
            "prepares_v430_coreference_reference_identity": True,
            "prepares_v440_temporal_spatial_language_grounding": True,
            "prepares_v450_epistemic_modal_negation_certainty": True,
            "prepares_v460_pragmatic_meaning_speech_act_intent": True,
            "prepares_v470_cross_document_context_graph": True,
            "prepares_v480_multilingual_context_alignment": True,
            "prepares_v490_contextual_semantic_evaluation": True,
        },
        "reference": {
            "source_bindings": len(bundle.source_bindings),
            "contexts": len(bundle.contexts),
            "mentions": len(bundle.mentions),
            "frames": len(bundle.frames),
            "participants": len(bundle.participants),
            "interpretations": len(bundle.interpretations),
            "snapshots": len(bundle.snapshots),
            "unresolved_mentions": sum(x.mention_kind == MentionKind.unresolved_reference for x in bundle.mentions),
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
        "database_migration": "none",
    }
