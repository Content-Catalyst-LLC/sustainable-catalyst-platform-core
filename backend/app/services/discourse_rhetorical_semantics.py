from __future__ import annotations

import hashlib
from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .context_semantic_frame import (
    CONTRACT_VERSION as CONTEXT_SEMANTIC_CONTRACT,
    ContextObjectSemanticFrameBundle,
    InterpretationMethod,
    reference_context_object_semantic_frame_bundle,
)

CORE_RELEASE = "4.2.0"
CONTRACT_VERSION = "sc.core.discourse-structure-rhetorical-semantics.v1"
PREDECESSOR_CONTRACT = CONTEXT_SEMANTIC_CONTRACT

EXTENDS_CONTRACTS = [
    PREDECESSOR_CONTRACT,
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


class DiscourseSegmentKind(str, Enum):
    clause = "clause"
    sentence = "sentence"
    paragraph = "paragraph"
    section = "section"
    quotation = "quotation"
    turn = "turn"
    proposition = "proposition"
    other = "other"


class RhetoricalRelationKind(str, Enum):
    elaboration = "elaboration"
    contrast = "contrast"
    cause = "cause"
    consequence = "consequence"
    condition = "condition"
    concession = "concession"
    background = "background"
    evidence = "evidence"
    example = "example"
    explanation = "explanation"
    restatement = "restatement"
    sequence = "sequence"
    temporal_sequence = "temporal-sequence"
    purpose = "purpose"
    attribution = "attribution"
    question_answer = "question-answer"
    claim_support = "claim-support"
    rebuttal = "rebuttal"
    comparison = "comparison"
    other = "other"


class RhetoricalNuclearity(str, Enum):
    nucleus_satellite = "nucleus-satellite"
    satellite_nucleus = "satellite-nucleus"
    multinuclear = "multinuclear"
    unspecified = "unspecified"


class DiscourseReviewState(str, Enum):
    candidate = "candidate"
    reviewed = "reviewed"
    accepted = "accepted"
    rejected = "rejected"
    disputed = "disputed"


class ArgumentRole(str, Enum):
    claim = "claim"
    premise = "premise"
    evidence = "evidence"
    warrant = "warrant"
    rebuttal = "rebuttal"
    qualification = "qualification"
    background = "background"
    other = "other"


class ArgumentRelationKind(str, Enum):
    supports = "supports"
    challenges = "challenges"
    rebuts = "rebuts"
    qualifies = "qualifies"
    warrants = "warrants"
    contextualizes = "contextualizes"
    evidences = "evidences"
    other = "other"


class DiscourseRhetoricalPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    discourse_structure_is_explicit_and_persistent: Literal[True] = True
    discourse_analysis_preserves_source_text: Literal[True] = True
    rhetorical_relations_preserve_provenance: Literal[True] = True
    multiple_discourse_interpretations_may_coexist: Literal[True] = True
    unresolved_reference_remains_unresolved: Literal[True] = True
    machine_discourse_output_is_advisory: Literal[True] = True
    rhetorical_relation_is_not_source_fact: Literal[True] = True
    causal_rhetorical_relation_is_not_causal_proof: Literal[True] = True
    evidence_relation_is_not_evidence_grade: Literal[True] = True
    argument_role_is_not_truth_or_credibility_rating: Literal[True] = True
    discourse_interpretation_is_not_truth_verdict: Literal[True] = True
    context_graph_mutation_authorized: Literal[False] = False
    identity_graph_mutation_authorized: Literal[False] = False
    relationship_graph_mutation_authorized: Literal[False] = False
    evidence_graph_mutation_authorized: Literal[False] = False

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DiscourseSegment(BaseModel):
    segment_id: str = Field(min_length=3, max_length=500)
    context_ref: str = Field(min_length=3, max_length=500)
    segment_kind: DiscourseSegmentKind
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    content: str = Field(min_length=1, max_length=100000)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    language_ref: str = Field(min_length=2, max_length=500)
    parent_segment_ref: str | None = Field(default=None, max_length=500)
    frame_refs: list[str] = Field(default_factory=list)
    mention_refs: list[str] = Field(default_factory=list)
    provenance_ref: str = Field(min_length=3, max_length=500)
    segment_is_interpretive_structure_not_source_fact: Literal[True] = True
    source_text_remains_canonical: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_segment(self):
        if self.char_end <= self.char_start:
            raise ValueError("segment char_end must be greater than char_start")
        if _sha256_text(self.content) != self.content_sha256:
            raise ValueError("segment content_sha256 must match content")
        _unique(self.frame_refs, "segment frame_refs")
        _unique(self.mention_refs, "segment mention_refs")
        if self.parent_segment_ref == self.segment_id:
            raise ValueError("segment cannot be its own parent")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DiscourseSignal(BaseModel):
    signal_id: str = Field(min_length=3, max_length=500)
    context_ref: str = Field(min_length=3, max_length=500)
    host_segment_ref: str | None = Field(default=None, max_length=500)
    signal_text: str = Field(min_length=1, max_length=10000)
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    relation_hint_kinds: list[RhetoricalRelationKind] = Field(default_factory=list)
    provenance_ref: str = Field(min_length=3, max_length=500)
    lexical_signal_does_not_force_relation: Literal[True] = True
    signal_is_not_truth_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_signal(self):
        if self.char_end <= self.char_start:
            raise ValueError("signal char_end must be greater than char_start")
        _unique([x.value for x in self.relation_hint_kinds], "signal relation_hint_kinds")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RhetoricalRelation(BaseModel):
    relation_id: str = Field(min_length=3, max_length=500)
    relation_kind: RhetoricalRelationKind
    source_segment_refs: list[str] = Field(min_length=1)
    target_segment_refs: list[str] = Field(min_length=1)
    signal_refs: list[str] = Field(default_factory=list)
    nuclearity: RhetoricalNuclearity = RhetoricalNuclearity.unspecified
    provenance_ref: str = Field(min_length=3, max_length=500)
    review_state: DiscourseReviewState = DiscourseReviewState.candidate
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    relation_is_interpretation_not_source_fact: Literal[True] = True
    relation_does_not_establish_real_world_causality: Literal[True] = True
    relation_does_not_establish_evidence_strength: Literal[True] = True
    selected_by_core: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_relation(self):
        _unique(self.source_segment_refs, "relation source_segment_refs")
        _unique(self.target_segment_refs, "relation target_segment_refs")
        _unique(self.signal_refs, "relation signal_refs")
        if set(self.source_segment_refs) == set(self.target_segment_refs):
            raise ValueError("rhetorical relation source and target sets cannot be identical")
        if self.review_state != DiscourseReviewState.candidate and not self.reviewer_ref:
            raise ValueError("reviewed rhetorical relation requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ArgumentUnit(BaseModel):
    argument_unit_id: str = Field(min_length=3, max_length=500)
    segment_ref: str = Field(min_length=3, max_length=500)
    role: ArgumentRole
    frame_refs: list[str] = Field(default_factory=list)
    provenance_ref: str = Field(min_length=3, max_length=500)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    argument_role_is_interpretive: Literal[True] = True
    argument_role_does_not_establish_truth: Literal[True] = True
    argument_role_does_not_establish_source_credibility: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_argument_unit(self):
        _unique(self.frame_refs, "argument unit frame_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ArgumentRelation(BaseModel):
    argument_relation_id: str = Field(min_length=3, max_length=500)
    relation_kind: ArgumentRelationKind
    from_argument_unit_ref: str = Field(min_length=3, max_length=500)
    to_argument_unit_ref: str = Field(min_length=3, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    relation_is_rhetorical_not_evidence_grade: Literal[True] = True
    relation_does_not_establish_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_argument_relation(self):
        if self.from_argument_unit_ref == self.to_argument_unit_ref:
            raise ValueError("argument relation cannot point from an argument unit to itself")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DiscourseProvenanceRecord(BaseModel):
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
    machine_output_is_advisory: Literal[True] = True
    provenance_does_not_establish_rhetorical_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_provenance(self):
        _unique(self.subject_refs, "discourse provenance subject_refs")
        _unique(self.source_refs, "discourse provenance source_refs")
        if self.method in {InterpretationMethod.model_assisted, InterpretationMethod.graph_assisted} and not self.model_ref:
            raise ValueError("model/graph-assisted discourse provenance requires model_ref")
        if self.model_version and not self.model_ref:
            raise ValueError("model_version requires model_ref")
        if self.tool_version and not self.tool_ref:
            raise ValueError("tool_version requires tool_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DiscourseInterpretation(BaseModel):
    interpretation_id: str = Field(min_length=3, max_length=500)
    context_ref: str = Field(min_length=3, max_length=500)
    segment_refs: list[str] = Field(min_length=1)
    signal_refs: list[str] = Field(default_factory=list)
    rhetorical_relation_refs: list[str] = Field(default_factory=list)
    argument_unit_refs: list[str] = Field(default_factory=list)
    argument_relation_refs: list[str] = Field(default_factory=list)
    provenance_ref: str = Field(min_length=3, max_length=500)
    review_state: DiscourseReviewState = DiscourseReviewState.candidate
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    alternative_interpretation_refs: list[str] = Field(default_factory=list)
    selected_by_core: Literal[False] = False
    unresolved_reference_preserved: Literal[True] = True
    interpretation_is_not_truth_verdict: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_interpretation(self):
        for values, label in (
            (self.segment_refs, "discourse interpretation segment_refs"),
            (self.signal_refs, "discourse interpretation signal_refs"),
            (self.rhetorical_relation_refs, "discourse interpretation rhetorical_relation_refs"),
            (self.argument_unit_refs, "discourse interpretation argument_unit_refs"),
            (self.argument_relation_refs, "discourse interpretation argument_relation_refs"),
            (self.alternative_interpretation_refs, "discourse interpretation alternative_interpretation_refs"),
        ):
            _unique(values, label)
        if self.interpretation_id in self.alternative_interpretation_refs:
            raise ValueError("discourse interpretation cannot list itself as an alternative")
        if self.review_state != DiscourseReviewState.candidate and not self.reviewer_ref:
            raise ValueError("reviewed discourse interpretation requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DiscourseSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    context_semantics_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    discourse_interpretation_refs: list[str] = Field(min_length=1)
    deterministic_discourse_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_is_not_truth_certification: Literal[True] = True
    snapshot_does_not_mutate_graphs: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        _unique(self.discourse_interpretation_refs, "snapshot discourse_interpretation_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DiscourseStructureRhetoricalSemanticsBundle(BaseModel):
    release: Literal["4.2.0"] = "4.2.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    extends_contracts: list[str] = Field(min_length=5)
    policy: DiscourseRhetoricalPolicy
    context_semantics: ContextObjectSemanticFrameBundle
    segments: list[DiscourseSegment] = Field(min_length=1)
    signals: list[DiscourseSignal] = Field(default_factory=list)
    rhetorical_relations: list[RhetoricalRelation] = Field(default_factory=list)
    argument_units: list[ArgumentUnit] = Field(default_factory=list)
    argument_relations: list[ArgumentRelation] = Field(default_factory=list)
    provenance_records: list[DiscourseProvenanceRecord] = Field(min_length=1)
    interpretations: list[DiscourseInterpretation] = Field(min_length=1)
    snapshots: list[DiscourseSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.extends_contracts != EXTENDS_CONTRACTS:
            raise ValueError("extends_contracts must preserve the declared v4.2 dependency order")
        if self.context_semantics.release != "4.1.0" or self.context_semantics.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.2 requires an intact v4.1 contextual-semantics bundle")

        for values, label in (
            ([x.segment_id for x in self.segments], "discourse segment ids"),
            ([x.signal_id for x in self.signals], "discourse signal ids"),
            ([x.relation_id for x in self.rhetorical_relations], "rhetorical relation ids"),
            ([x.argument_unit_id for x in self.argument_units], "argument unit ids"),
            ([x.argument_relation_id for x in self.argument_relations], "argument relation ids"),
            ([x.provenance_id for x in self.provenance_records], "discourse provenance ids"),
            ([x.interpretation_id for x in self.interpretations], "discourse interpretation ids"),
            ([x.snapshot_id for x in self.snapshots], "discourse snapshot ids"),
        ):
            _unique(values, label)

        contexts = {x.context_id: x for x in self.context_semantics.contexts}
        frames = {x.frame_id: x for x in self.context_semantics.frames}
        mentions = {x.mention_id: x for x in self.context_semantics.mentions}
        segments = {x.segment_id: x for x in self.segments}
        signals = {x.signal_id: x for x in self.signals}
        relations = {x.relation_id: x for x in self.rhetorical_relations}
        argument_units = {x.argument_unit_id: x for x in self.argument_units}
        argument_relations = {x.argument_relation_id: x for x in self.argument_relations}
        provenances = {x.provenance_id: x for x in self.provenance_records}
        interpretations = {x.interpretation_id: x for x in self.interpretations}

        for segment in self.segments:
            if segment.context_ref not in contexts:
                raise ValueError("discourse segment context_ref must resolve to v4.1 context")
            if segment.provenance_ref not in provenances:
                raise ValueError("discourse segment provenance_ref must resolve")
            context = contexts[segment.context_ref]
            if segment.char_end > len(context.content):
                raise ValueError("discourse segment range cannot exceed context")
            if context.content[segment.char_start:segment.char_end] != segment.content:
                raise ValueError("discourse segment content must match v4.1 context slice")
            if segment.language_ref != context.language_ref:
                raise ValueError("discourse segment language must match v4.1 context language")
            if segment.parent_segment_ref:
                if segment.parent_segment_ref not in segments:
                    raise ValueError("parent_segment_ref must resolve")
                parent = segments[segment.parent_segment_ref]
                if parent.context_ref != segment.context_ref:
                    raise ValueError("parent and child discourse segments must share context")
                if segment.char_start < parent.char_start or segment.char_end > parent.char_end:
                    raise ValueError("child discourse segment must fit inside parent segment")
            for ref in segment.frame_refs:
                if ref not in frames:
                    raise ValueError("discourse segment frame_ref must resolve")
                frame = frames[ref]
                if frame.context_ref != segment.context_ref:
                    raise ValueError("discourse segment frame must share context")
                if frame.trigger_char_start < segment.char_start or frame.trigger_char_end > segment.char_end:
                    raise ValueError("discourse segment must contain referenced frame trigger")
            for ref in segment.mention_refs:
                if ref not in mentions:
                    raise ValueError("discourse segment mention_ref must resolve")
                mention = mentions[ref]
                if mention.context_ref != segment.context_ref:
                    raise ValueError("discourse segment mention must share context")
                if mention.char_start < segment.char_start or mention.char_end > segment.char_end:
                    raise ValueError("discourse segment must contain referenced mention")

        for signal in self.signals:
            if signal.context_ref not in contexts:
                raise ValueError("discourse signal context_ref must resolve")
            if signal.provenance_ref not in provenances:
                raise ValueError("discourse signal provenance_ref must resolve")
            context = contexts[signal.context_ref]
            if signal.char_end > len(context.content):
                raise ValueError("discourse signal range cannot exceed context")
            if context.content[signal.char_start:signal.char_end] != signal.signal_text:
                raise ValueError("discourse signal_text must match context slice")
            if signal.host_segment_ref:
                if signal.host_segment_ref not in segments:
                    raise ValueError("discourse signal host_segment_ref must resolve")
                host = segments[signal.host_segment_ref]
                if host.context_ref != signal.context_ref:
                    raise ValueError("discourse signal and host segment must share context")
                if signal.char_start < host.char_start or signal.char_end > host.char_end:
                    raise ValueError("discourse signal must fit inside host segment")

        for relation in self.rhetorical_relations:
            if relation.provenance_ref not in provenances:
                raise ValueError("rhetorical relation provenance_ref must resolve")
            if any(ref not in segments for ref in relation.source_segment_refs + relation.target_segment_refs):
                raise ValueError("rhetorical relation segment_ref must resolve")
            for ref in relation.signal_refs:
                if ref not in signals:
                    raise ValueError("rhetorical relation signal_ref must resolve")
                hints = signals[ref].relation_hint_kinds
                if hints and relation.relation_kind not in hints:
                    raise ValueError("rhetorical relation kind must be compatible with signal hints")

        for unit in self.argument_units:
            if unit.segment_ref not in segments:
                raise ValueError("argument unit segment_ref must resolve")
            if unit.provenance_ref not in provenances:
                raise ValueError("argument unit provenance_ref must resolve")
            for ref in unit.frame_refs:
                if ref not in frames:
                    raise ValueError("argument unit frame_ref must resolve")
                if ref not in segments[unit.segment_ref].frame_refs:
                    raise ValueError("argument unit frame_ref must be represented by its discourse segment")

        for relation in self.argument_relations:
            if relation.from_argument_unit_ref not in argument_units or relation.to_argument_unit_ref not in argument_units:
                raise ValueError("argument relation unit refs must resolve")
            if relation.provenance_ref not in provenances:
                raise ValueError("argument relation provenance_ref must resolve")

        for interpretation in self.interpretations:
            if interpretation.context_ref not in contexts:
                raise ValueError("discourse interpretation context_ref must resolve")
            if interpretation.provenance_ref not in provenances:
                raise ValueError("discourse interpretation provenance_ref must resolve")
            if any(ref not in segments for ref in interpretation.segment_refs):
                raise ValueError("discourse interpretation segment_ref must resolve")
            if any(ref not in signals for ref in interpretation.signal_refs):
                raise ValueError("discourse interpretation signal_ref must resolve")
            if any(ref not in relations for ref in interpretation.rhetorical_relation_refs):
                raise ValueError("discourse interpretation rhetorical_relation_ref must resolve")
            if any(ref not in argument_units for ref in interpretation.argument_unit_refs):
                raise ValueError("discourse interpretation argument_unit_ref must resolve")
            if any(ref not in argument_relations for ref in interpretation.argument_relation_refs):
                raise ValueError("discourse interpretation argument_relation_ref must resolve")
            if any(ref not in interpretations for ref in interpretation.alternative_interpretation_refs):
                raise ValueError("discourse interpretation alternative_interpretation_ref must resolve")

        object_ids = (
            set(segments) | set(signals) | set(relations) | set(argument_units) |
            set(argument_relations) | set(interpretations) | {x.snapshot_id for x in self.snapshots}
        )
        for provenance in self.provenance_records:
            for ref in provenance.subject_refs:
                if ref not in object_ids:
                    raise ValueError("discourse provenance subject_ref must resolve to a v4.2 object")

        context_fingerprint = self.context_semantics.fingerprint()
        for snapshot in self.snapshots:
            if snapshot.context_semantics_fingerprint_sha256 != context_fingerprint:
                raise ValueError("snapshot must bind to exact v4.1 contextual-semantics fingerprint")
            if any(ref not in interpretations for ref in snapshot.discourse_interpretation_refs):
                raise ValueError("snapshot discourse_interpretation_ref must resolve")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


@lru_cache(maxsize=1)
def reference_discourse_structure_rhetorical_semantics_bundle() -> DiscourseStructureRhetoricalSemanticsBundle:
    context_bundle = reference_context_object_semantic_frame_bundle()
    contexts = {x.context_id: x for x in context_bundle.contexts}
    s1 = contexts["context:policy-note:sentence-1"]
    s2 = contexts["context:policy-note:sentence-2"]

    segments = [
        DiscourseSegment(
            segment_id="discourse-segment:sentence-1",
            context_ref=s1.context_id,
            segment_kind=DiscourseSegmentKind.sentence,
            char_start=0,
            char_end=len(s1.content),
            content=s1.content,
            content_sha256=_sha256_text(s1.content),
            language_ref=s1.language_ref,
            frame_refs=["frame:rejection", "frame:revision"],
            mention_refs=["mention:commission", "mention:proposal", "mention:ministry", "mention:estimate"],
            provenance_ref="prov:discourse-segments:reference",
        ),
        DiscourseSegment(
            segment_id="discourse-segment:rejection-clause",
            context_ref=s1.context_id,
            segment_kind=DiscourseSegmentKind.clause,
            char_start=0,
            char_end=36,
            content=s1.content[0:36],
            content_sha256=_sha256_text(s1.content[0:36]),
            language_ref=s1.language_ref,
            parent_segment_ref="discourse-segment:sentence-1",
            frame_refs=["frame:rejection"],
            mention_refs=["mention:commission", "mention:proposal"],
            provenance_ref="prov:discourse-segments:reference",
        ),
        DiscourseSegment(
            segment_id="discourse-segment:revision-clause",
            context_ref=s1.context_id,
            segment_kind=DiscourseSegmentKind.clause,
            char_start=43,
            char_end=76,
            content=s1.content[43:76],
            content_sha256=_sha256_text(s1.content[43:76]),
            language_ref=s1.language_ref,
            parent_segment_ref="discourse-segment:sentence-1",
            frame_refs=["frame:revision"],
            mention_refs=["mention:ministry", "mention:estimate"],
            provenance_ref="prov:discourse-segments:reference",
        ),
        DiscourseSegment(
            segment_id="discourse-segment:sentence-2",
            context_ref=s2.context_id,
            segment_kind=DiscourseSegmentKind.sentence,
            char_start=0,
            char_end=len(s2.content),
            content=s2.content,
            content_sha256=_sha256_text(s2.content),
            language_ref=s2.language_ref,
            frame_refs=["frame:viability"],
            mention_refs=["mention:it-unresolved"],
            provenance_ref="prov:discourse-segments:reference",
            metadata={"unresolved_reference_preserved": "mention:it-unresolved"},
        ),
    ]

    signals = [
        DiscourseSignal(
            signal_id="discourse-signal:after",
            context_ref=s1.context_id,
            host_segment_ref="discourse-segment:sentence-1",
            signal_text="after",
            char_start=37,
            char_end=42,
            relation_hint_kinds=[RhetoricalRelationKind.temporal_sequence],
            provenance_ref="prov:discourse-signals:reference",
        ),
        DiscourseSignal(
            signal_id="discourse-signal:nevertheless",
            context_ref=s2.context_id,
            host_segment_ref="discourse-segment:sentence-2",
            signal_text="nevertheless",
            char_start=3,
            char_end=15,
            relation_hint_kinds=[RhetoricalRelationKind.concession, RhetoricalRelationKind.contrast],
            provenance_ref="prov:discourse-signals:reference",
        ),
    ]

    relations = [
        RhetoricalRelation(
            relation_id="rhetorical-relation:revision-before-rejection",
            relation_kind=RhetoricalRelationKind.temporal_sequence,
            source_segment_refs=["discourse-segment:revision-clause"],
            target_segment_refs=["discourse-segment:rejection-clause"],
            signal_refs=["discourse-signal:after"],
            nuclearity=RhetoricalNuclearity.multinuclear,
            provenance_ref="prov:rhetorical-relations:reference",
            confidence=1.0,
            metadata={"surface_order_differs_from_event_order": True},
        ),
        RhetoricalRelation(
            relation_id="rhetorical-relation:concession-viability",
            relation_kind=RhetoricalRelationKind.concession,
            source_segment_refs=["discourse-segment:sentence-1"],
            target_segment_refs=["discourse-segment:sentence-2"],
            signal_refs=["discourse-signal:nevertheless"],
            nuclearity=RhetoricalNuclearity.nucleus_satellite,
            provenance_ref="prov:rhetorical-relations:reference",
            confidence=1.0,
            metadata={"coreference_resolution_required": False, "referent_selection_deferred_to_v4.3": True},
        ),
    ]

    argument_units = [
        ArgumentUnit(
            argument_unit_id="argument-unit:rejection",
            segment_ref="discourse-segment:rejection-clause",
            role=ArgumentRole.claim,
            frame_refs=["frame:rejection"],
            provenance_ref="prov:argument-structure:reference",
            confidence=1.0,
            metadata={"role_describes_discourse_function_only": True},
        ),
        ArgumentUnit(
            argument_unit_id="argument-unit:revision-background",
            segment_ref="discourse-segment:revision-clause",
            role=ArgumentRole.background,
            frame_refs=["frame:revision"],
            provenance_ref="prov:argument-structure:reference",
            confidence=1.0,
            metadata={"role_describes_discourse_function_only": True},
        ),
    ]

    argument_relations = [
        ArgumentRelation(
            argument_relation_id="argument-relation:revision-contextualizes-rejection",
            relation_kind=ArgumentRelationKind.contextualizes,
            from_argument_unit_ref="argument-unit:revision-background",
            to_argument_unit_ref="argument-unit:rejection",
            provenance_ref="prov:argument-structure:reference",
            confidence=1.0,
        )
    ]

    interpretation = DiscourseInterpretation(
        interpretation_id="discourse-interpretation:policy-note:baseline",
        context_ref="context:policy-note:document",
        segment_refs=[x.segment_id for x in segments],
        signal_refs=[x.signal_id for x in signals],
        rhetorical_relation_refs=[x.relation_id for x in relations],
        argument_unit_refs=[x.argument_unit_id for x in argument_units],
        argument_relation_refs=[x.argument_relation_id for x in argument_relations],
        provenance_ref="prov:discourse-interpretation:reference",
        confidence=1.0,
        metadata={
            "unresolved_reference": "mention:it-unresolved",
            "core_does_not_select_referent": True,
            "coreference_resolution_deferred_to_v4.3": True,
        },
    )

    snapshot_material = {
        "context_semantics": context_bundle.fingerprint(),
        "segments": [x.fingerprint() for x in segments],
        "signals": [x.fingerprint() for x in signals],
        "relations": [x.fingerprint() for x in relations],
        "argument_units": [x.fingerprint() for x in argument_units],
        "argument_relations": [x.fingerprint() for x in argument_relations],
        "interpretation": interpretation.fingerprint(),
    }
    snapshot = DiscourseSnapshot(
        snapshot_id="snapshot:discourse-rhetorical-semantics:reference:v1",
        context_semantics_fingerprint_sha256=context_bundle.fingerprint(),
        discourse_interpretation_refs=[interpretation.interpretation_id],
        deterministic_discourse_fingerprint_sha256=canonical_sha256(snapshot_material),
    )

    provenances = [
        DiscourseProvenanceRecord(
            provenance_id="prov:discourse-segments:reference",
            subject_refs=[x.segment_id for x in segments],
            method=InterpretationMethod.manual,
            produced_by_ref="actor:platform-core-reference-builder",
            source_refs=["source:policy-note:v1"],
        ),
        DiscourseProvenanceRecord(
            provenance_id="prov:discourse-signals:reference",
            subject_refs=[x.signal_id for x in signals],
            method=InterpretationMethod.manual,
            produced_by_ref="actor:platform-core-reference-builder",
            source_refs=["source:policy-note:v1"],
        ),
        DiscourseProvenanceRecord(
            provenance_id="prov:rhetorical-relations:reference",
            subject_refs=[x.relation_id for x in relations],
            method=InterpretationMethod.manual,
            produced_by_ref="actor:platform-core-reference-builder",
            source_refs=["source:policy-note:v1"],
        ),
        DiscourseProvenanceRecord(
            provenance_id="prov:argument-structure:reference",
            subject_refs=[x.argument_unit_id for x in argument_units] + [x.argument_relation_id for x in argument_relations],
            method=InterpretationMethod.manual,
            produced_by_ref="actor:platform-core-reference-builder",
            source_refs=["source:policy-note:v1"],
        ),
        DiscourseProvenanceRecord(
            provenance_id="prov:discourse-interpretation:reference",
            subject_refs=[interpretation.interpretation_id, snapshot.snapshot_id],
            method=InterpretationMethod.manual,
            produced_by_ref="actor:platform-core-reference-builder",
            source_refs=["source:policy-note:v1"],
        ),
    ]

    return DiscourseStructureRhetoricalSemanticsBundle(
        extends_contracts=list(EXTENDS_CONTRACTS),
        policy=DiscourseRhetoricalPolicy(policy_id="discourse-rhetorical-policy:v4.2"),
        context_semantics=context_bundle,
        segments=segments,
        signals=signals,
        rhetorical_relations=relations,
        argument_units=argument_units,
        argument_relations=argument_relations,
        provenance_records=provenances,
        interpretations=[interpretation],
        snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    bundle = reference_discourse_structure_rhetorical_semantics_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "extends_contracts": list(EXTENDS_CONTRACTS),
        "identity": {
            "product": "Sustainable Catalyst Platform Core",
            "build": "Discourse Structure & Rhetorical Semantics",
            "major_api": "v4",
        },
        "principles": {
            "discourse_structure_is_explicit_and_persistent": True,
            "discourse_analysis_preserves_source_text": True,
            "rhetorical_relations_preserve_provenance": True,
            "multiple_discourse_interpretations_may_coexist": True,
            "unresolved_reference_remains_unresolved": True,
            "machine_discourse_output_is_advisory": True,
            "rhetorical_relation_is_not_source_fact": True,
            "causal_rhetorical_relation_is_not_causal_proof": True,
            "evidence_relation_is_not_evidence_grade": True,
            "argument_role_is_not_truth_or_credibility_rating": True,
            "discourse_interpretation_is_not_truth_verdict": True,
        },
        "boundaries": {
            "core_executes_discourse_parser": False,
            "core_autonomously_infers_discourse_relations": False,
            "core_resolves_coreference": False,
            "core_selects_best_discourse_interpretation": False,
            "rhetorical_cause_establishes_real_world_causality": False,
            "rhetorical_evidence_establishes_evidence_strength": False,
            "argument_role_establishes_truth": False,
            "argument_role_establishes_source_credibility": False,
            "identity_graph_mutation_performed": False,
            "relationship_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
            "context_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "extends_v410_context_object_semantic_frame_foundation": True,
            "prepares_v430_coreference_reference_identity": True,
            "prepares_v440_temporal_spatial_language_grounding": True,
            "prepares_v450_epistemic_modal_negation_certainty": True,
            "prepares_v460_pragmatic_meaning_speech_act_intent": True,
            "prepares_v470_cross_document_context_graph": True,
            "prepares_v480_multilingual_context_alignment": True,
            "prepares_v490_contextual_semantic_evaluation": True,
        },
        "reference": {
            "context_semantics_release": bundle.context_semantics.release,
            "context_semantics_fingerprint_sha256": bundle.context_semantics.fingerprint(),
            "segments": len(bundle.segments),
            "signals": len(bundle.signals),
            "rhetorical_relations": len(bundle.rhetorical_relations),
            "argument_units": len(bundle.argument_units),
            "argument_relations": len(bundle.argument_relations),
            "interpretations": len(bundle.interpretations),
            "snapshots": len(bundle.snapshots),
            "unresolved_mentions": sum(
                x.mention_kind.value == "unresolved-reference" for x in bundle.context_semantics.mentions
            ),
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
        "database_migration": "none",
    }
