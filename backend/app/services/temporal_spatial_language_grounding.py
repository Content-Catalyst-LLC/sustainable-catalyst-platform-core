from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .context_semantic_frame import InterpretationMethod
from .coreference_referential_identity import (
    CoreferenceReferentialIdentityBundle,
    reference_coreference_referential_identity_bundle,
)

CORE_RELEASE = "4.4.0"
CONTRACT_VERSION = "sc.core.temporal-spatial-language-grounding.v1"
PREDECESSOR_CONTRACT = "sc.core.coreference-reference-referential-identity-intelligence.v1"

EXTENDS_CONTRACTS = [
    PREDECESSOR_CONTRACT,
    "sc.core.discourse-structure-rhetorical-semantics.v1",
    "sc.core.context-object-semantic-frame-foundation.v1",
    "sc.core.temporal-identity-alias-name-variant-intelligence.v1",
    "sc.core.spatial-temporal-visual-reasoning.v1",
]


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class GroundingDomain(str, Enum):
    temporal = "temporal"
    spatial = "spatial"


class GroundingState(str, Enum):
    candidate = "candidate"
    reviewed = "reviewed"
    accepted = "accepted"
    rejected = "rejected"
    disputed = "disputed"
    unresolved = "unresolved"
    deferred = "deferred"


class TemporalExpressionKind(str, Enum):
    absolute_year = "absolute-year"
    absolute_date = "absolute-date"
    absolute_datetime = "absolute-datetime"
    relative_time = "relative-time"
    deictic_time = "deictic-time"
    event_relative = "event-relative"
    duration = "duration"
    frequency = "frequency"
    temporal_relation_signal = "temporal-relation-signal"
    other = "other"


class SpatialExpressionKind(str, Enum):
    named_place = "named-place"
    spatial_deixis = "spatial-deixis"
    relative_location = "relative-location"
    region = "region"
    address = "address"
    coordinate_literal = "coordinate-literal"
    route_or_path = "route-or-path"
    other = "other"


class TemporalAnchorKind(str, Enum):
    instant = "instant"
    interval = "interval"
    calendar_period = "calendar-period"
    event = "event"
    derived = "derived"
    unresolved = "unresolved"


class SpatialAnchorKind(str, Enum):
    source_named_place = "source-named-place"
    canonical_place = "canonical-place"
    region = "region"
    geometry = "geometry"
    coordinate = "coordinate"
    route_or_path = "route-or-path"
    unresolved = "unresolved"


class TemporalRelationKind(str, Enum):
    before = "before"
    after = "after"
    during = "during"
    overlaps = "overlaps"
    contains = "contains"
    starts = "starts"
    finishes = "finishes"
    simultaneous = "simultaneous"


class GroundingPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    source_text_remains_immutable: Literal[True] = True
    linguistic_expression_is_distinct_from_grounded_anchor: Literal[True] = True
    competing_groundings_may_coexist: Literal[True] = True
    normalization_preserves_uncertainty: Literal[True] = True
    relative_grounding_preserves_base_anchor: Literal[True] = True
    spatial_deixis_requires_explicit_antecedent_or_candidate_set: Literal[True] = True
    temporal_relation_is_source_semantics_not_world_truth: Literal[True] = True
    place_name_does_not_establish_canonical_geographic_identity: Literal[True] = True
    geocoder_output_is_advisory: Literal[True] = True
    model_output_is_advisory: Literal[True] = True
    accepted_grounding_requires_governed_review: Literal[True] = True
    temporal_graph_mutation_authorized: Literal[False] = False
    spatial_graph_mutation_authorized: Literal[False] = False
    identity_graph_mutation_authorized: Literal[False] = False
    evidence_graph_mutation_authorized: Literal[False] = False
    context_graph_mutation_authorized: Literal[False] = False

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GroundingSourceExcerpt(BaseModel):
    source_excerpt_id: str = Field(min_length=3, max_length=500)
    source_ref: str = Field(min_length=3, max_length=1000)
    language_ref: str = Field(min_length=3, max_length=500)
    content: str = Field(min_length=1, max_length=50000)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    provenance_ref: str = Field(min_length=3, max_length=500)
    source_excerpt_is_immutable: Literal[True] = True
    source_excerpt_is_not_evidence_validation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_content_hash(self):
        if self.content_sha256 != canonical_sha256(self.content):
            raise ValueError("content_sha256 must match immutable source excerpt content")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TemporalExpression(BaseModel):
    temporal_expression_id: str = Field(min_length=3, max_length=500)
    source_excerpt_ref: str | None = Field(default=None, max_length=500)
    predecessor_signal_ref: str | None = Field(default=None, max_length=500)
    expression_kind: TemporalExpressionKind
    surface_text: str = Field(min_length=1, max_length=10000)
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=1)
    candidate_set_ref: str = Field(min_length=3, max_length=500)
    base_temporal_expression_ref: str | None = Field(default=None, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    source_expression_preserved: Literal[True] = True
    normalized_time_is_interpretation_not_source_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_source_locator(self):
        if not self.source_excerpt_ref and not self.predecessor_signal_ref:
            raise ValueError("temporal expression requires source_excerpt_ref or predecessor_signal_ref")
        if self.source_excerpt_ref and (self.char_start is None or self.char_end is None):
            raise ValueError("source excerpt temporal expression requires char offsets")
        if self.char_start is not None and self.char_end is not None and self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SpatialExpression(BaseModel):
    spatial_expression_id: str = Field(min_length=3, max_length=500)
    source_excerpt_ref: str = Field(min_length=3, max_length=500)
    expression_kind: SpatialExpressionKind
    surface_text: str = Field(min_length=1, max_length=10000)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=1)
    candidate_set_ref: str = Field(min_length=3, max_length=500)
    antecedent_expression_ref: str | None = Field(default=None, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    source_expression_preserved: Literal[True] = True
    spatial_grounding_is_interpretation_not_source_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_span(self):
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TemporalAnchor(BaseModel):
    temporal_anchor_id: str = Field(min_length=3, max_length=500)
    anchor_kind: TemporalAnchorKind
    normalized_start: str | None = Field(default=None, max_length=100)
    normalized_end: str | None = Field(default=None, max_length=100)
    precision: str = Field(min_length=2, max_length=100)
    calendar: str = Field(default="gregorian", min_length=2, max_length=100)
    timezone: str | None = Field(default=None, max_length=100)
    base_anchor_ref: str | None = Field(default=None, max_length=500)
    derivation_operation: str | None = Field(default=None, max_length=500)
    event_ref: str | None = Field(default=None, max_length=1000)
    authoritative_temporal_ref: str | None = Field(default=None, max_length=1000)
    provenance_ref: str = Field(min_length=3, max_length=500)
    normalized_value_is_interpretation_not_source_fact: Literal[True] = True
    external_temporal_identity_not_assumed: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_anchor(self):
        if self.anchor_kind == TemporalAnchorKind.derived:
            if not self.base_anchor_ref or not self.derivation_operation:
                raise ValueError("derived temporal anchor requires base_anchor_ref and derivation_operation")
        if self.anchor_kind == TemporalAnchorKind.event and not self.event_ref:
            raise ValueError("event temporal anchor requires event_ref")
        if self.anchor_kind not in {TemporalAnchorKind.event, TemporalAnchorKind.unresolved}:
            if not self.normalized_start and not self.normalized_end:
                raise ValueError("temporal anchor requires a normalized bound")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SpatialAnchor(BaseModel):
    spatial_anchor_id: str = Field(min_length=3, max_length=500)
    anchor_kind: SpatialAnchorKind
    label: str = Field(min_length=1, max_length=1000)
    source_expression_ref: str | None = Field(default=None, max_length=500)
    canonical_place_ref: str | None = Field(default=None, max_length=1000)
    geometry_ref: str | None = Field(default=None, max_length=1000)
    jurisdiction_hints: list[str] = Field(default_factory=list)
    coordinate: dict[str, float] | None = None
    provenance_ref: str = Field(min_length=3, max_length=500)
    canonical_geographic_identity_established: Literal[False] = False
    coordinate_is_not_implicitly_geocoded: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_anchor(self):
        _unique(self.jurisdiction_hints, "jurisdiction_hints")
        if self.anchor_kind == SpatialAnchorKind.canonical_place and not self.canonical_place_ref:
            raise ValueError("canonical place anchor requires canonical_place_ref")
        if self.anchor_kind == SpatialAnchorKind.geometry and not self.geometry_ref:
            raise ValueError("geometry anchor requires geometry_ref")
        if self.anchor_kind == SpatialAnchorKind.coordinate and not self.coordinate:
            raise ValueError("coordinate anchor requires coordinate")
        if self.coordinate:
            if set(self.coordinate) != {"lat", "lon"}:
                raise ValueError("coordinate must contain exactly lat and lon")
            if not -90 <= self.coordinate["lat"] <= 90 or not -180 <= self.coordinate["lon"] <= 180:
                raise ValueError("coordinate is outside valid latitude/longitude bounds")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GroundingCandidate(BaseModel):
    candidate_id: str = Field(min_length=3, max_length=500)
    candidate_set_ref: str = Field(min_length=3, max_length=500)
    domain: GroundingDomain
    expression_ref: str = Field(min_length=3, max_length=500)
    anchor_ref: str = Field(min_length=3, max_length=500)
    rank: int = Field(ge=1)
    score: float | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    state: GroundingState = GroundingState.candidate
    supporting_signal_refs: list[str] = Field(default_factory=list)
    contradicting_signal_refs: list[str] = Field(default_factory=list)
    provenance_ref: str = Field(min_length=3, max_length=500)
    score_is_not_truth_probability: Literal[True] = True
    candidate_is_not_canonical_grounding_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_candidate(self):
        _unique(self.supporting_signal_refs, "supporting_signal_refs")
        _unique(self.contradicting_signal_refs, "contradicting_signal_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GroundingCandidateSet(BaseModel):
    candidate_set_id: str = Field(min_length=3, max_length=500)
    domain: GroundingDomain
    expression_ref: str = Field(min_length=3, max_length=500)
    candidate_refs: list[str] = Field(min_length=1)
    selected_candidate_ref: str | None = Field(default=None, max_length=500)
    state: GroundingState = GroundingState.candidate
    method: InterpretationMethod
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    rationale: str | None = Field(default=None, max_length=8000)
    provenance_ref: str = Field(min_length=3, max_length=500)
    competing_candidates_preserved: Literal[True] = True
    selected_candidate_is_interpretation_not_world_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_candidate_set(self):
        _unique(self.candidate_refs, "candidate_refs")
        if self.selected_candidate_ref and self.selected_candidate_ref not in self.candidate_refs:
            raise ValueError("selected_candidate_ref must be present in candidate_refs")
        if self.state == GroundingState.accepted:
            if not self.selected_candidate_ref or not self.reviewer_ref:
                raise ValueError("accepted candidate set requires selection and reviewer")
        if self.state == GroundingState.unresolved and self.selected_candidate_ref:
            raise ValueError("unresolved candidate set cannot select a candidate")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TemporalGrounding(BaseModel):
    temporal_grounding_id: str = Field(min_length=3, max_length=500)
    temporal_expression_ref: str = Field(min_length=3, max_length=500)
    temporal_anchor_ref: str = Field(min_length=3, max_length=500)
    selected_candidate_ref: str = Field(min_length=3, max_length=500)
    state: GroundingState = GroundingState.candidate
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    provenance_ref: str = Field(min_length=3, max_length=500)
    grounding_is_interpretation_not_world_truth: Literal[True] = True
    grounding_does_not_mutate_temporal_graph: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_grounding(self):
        if self.state == GroundingState.accepted and not self.reviewer_ref:
            raise ValueError("accepted temporal grounding requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SpatialGrounding(BaseModel):
    spatial_grounding_id: str = Field(min_length=3, max_length=500)
    spatial_expression_ref: str = Field(min_length=3, max_length=500)
    spatial_anchor_ref: str = Field(min_length=3, max_length=500)
    selected_candidate_ref: str = Field(min_length=3, max_length=500)
    state: GroundingState = GroundingState.candidate
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    provenance_ref: str = Field(min_length=3, max_length=500)
    grounding_is_interpretation_not_world_truth: Literal[True] = True
    grounding_does_not_establish_canonical_place_identity: Literal[True] = True
    grounding_does_not_mutate_spatial_graph: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_grounding(self):
        if self.state == GroundingState.accepted and not self.reviewer_ref:
            raise ValueError("accepted spatial grounding requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TemporalRelationGrounding(BaseModel):
    temporal_relation_grounding_id: str = Field(min_length=3, max_length=500)
    predecessor_rhetorical_relation_ref: str = Field(min_length=3, max_length=500)
    predecessor_signal_ref: str = Field(min_length=3, max_length=500)
    source_event_ref: str = Field(min_length=3, max_length=500)
    target_event_ref: str = Field(min_length=3, max_length=500)
    relation_kind: TemporalRelationKind
    state: GroundingState = GroundingState.candidate
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    provenance_ref: str = Field(min_length=3, max_length=500)
    relation_represents_reported_language_semantics: Literal[True] = True
    relation_does_not_establish_real_world_event_order: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_relation(self):
        if self.state == GroundingState.accepted and not self.reviewer_ref:
            raise ValueError("accepted temporal relation grounding requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GroundingProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3, max_length=500)
    subject_refs: list[str] = Field(min_length=1)
    method: InterpretationMethod
    produced_by_ref: str = Field(min_length=3, max_length=1000)
    source_refs: list[str] = Field(min_length=1)
    model_ref: str | None = Field(default=None, max_length=1000)
    model_version: str | None = Field(default=None, max_length=240)
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    created_at: str | None = Field(default=None, max_length=80)
    external_geocoder_ref: str | None = Field(default=None, max_length=1000)
    external_gazetteer_ref: str | None = Field(default=None, max_length=1000)
    machine_or_external_output_is_advisory: Literal[True] = True
    provenance_does_not_establish_world_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_provenance(self):
        _unique(self.subject_refs, "provenance subject_refs")
        _unique(self.source_refs, "provenance source_refs")
        if self.method in {InterpretationMethod.model_assisted, InterpretationMethod.graph_assisted} and not self.model_ref:
            raise ValueError("model/graph-assisted grounding provenance requires model_ref")
        if self.model_version and not self.model_ref:
            raise ValueError("model_version requires model_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TemporalSpatialGroundingInterpretation(BaseModel):
    interpretation_id: str = Field(min_length=3, max_length=500)
    referential_interpretation_ref: str = Field(min_length=3, max_length=500)
    source_excerpt_refs: list[str] = Field(default_factory=list)
    temporal_expression_refs: list[str] = Field(default_factory=list)
    spatial_expression_refs: list[str] = Field(default_factory=list)
    candidate_set_refs: list[str] = Field(default_factory=list)
    temporal_grounding_refs: list[str] = Field(default_factory=list)
    spatial_grounding_refs: list[str] = Field(default_factory=list)
    temporal_relation_grounding_refs: list[str] = Field(default_factory=list)
    unresolved_expression_refs: list[str] = Field(default_factory=list)
    provenance_ref: str = Field(min_length=3, max_length=500)
    state: GroundingState = GroundingState.candidate
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    interpretation_does_not_rewrite_predecessor_objects: Literal[True] = True
    interpretation_is_not_world_truth_verdict: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_interpretation(self):
        for values, label in (
            (self.source_excerpt_refs, "source_excerpt_refs"),
            (self.temporal_expression_refs, "temporal_expression_refs"),
            (self.spatial_expression_refs, "spatial_expression_refs"),
            (self.candidate_set_refs, "candidate_set_refs"),
            (self.temporal_grounding_refs, "temporal_grounding_refs"),
            (self.spatial_grounding_refs, "spatial_grounding_refs"),
            (self.temporal_relation_grounding_refs, "temporal_relation_grounding_refs"),
            (self.unresolved_expression_refs, "unresolved_expression_refs"),
        ):
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TemporalSpatialGroundingSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    predecessor_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    interpretation_refs: list[str] = Field(min_length=1)
    deterministic_grounding_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        _unique(self.interpretation_refs, "interpretation_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TemporalSpatialLanguageGroundingBundle(BaseModel):
    release: Literal["4.4.0"] = "4.4.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    extends_contracts: list[str] = Field(min_length=5)
    policy: GroundingPolicy
    referential_identity: CoreferenceReferentialIdentityBundle
    source_excerpts: list[GroundingSourceExcerpt] = Field(min_length=1)
    temporal_expressions: list[TemporalExpression] = Field(min_length=1)
    spatial_expressions: list[SpatialExpression] = Field(min_length=1)
    temporal_anchors: list[TemporalAnchor] = Field(min_length=1)
    spatial_anchors: list[SpatialAnchor] = Field(min_length=1)
    candidate_sets: list[GroundingCandidateSet] = Field(min_length=1)
    candidates: list[GroundingCandidate] = Field(min_length=1)
    temporal_groundings: list[TemporalGrounding] = Field(min_length=1)
    spatial_groundings: list[SpatialGrounding] = Field(min_length=1)
    temporal_relation_groundings: list[TemporalRelationGrounding] = Field(min_length=1)
    provenance_records: list[GroundingProvenanceRecord] = Field(min_length=1)
    interpretations: list[TemporalSpatialGroundingInterpretation] = Field(min_length=1)
    snapshots: list[TemporalSpatialGroundingSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.extends_contracts != EXTENDS_CONTRACTS:
            raise ValueError("extends_contracts must preserve the declared v4.4 dependency order")
        if self.referential_identity.release != "4.3.0" or self.referential_identity.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.4 must embed the governed v4.3 referential-identity predecessor")

        groups = (
            ([x.source_excerpt_id for x in self.source_excerpts], "source excerpt ids"),
            ([x.temporal_expression_id for x in self.temporal_expressions], "temporal expression ids"),
            ([x.spatial_expression_id for x in self.spatial_expressions], "spatial expression ids"),
            ([x.temporal_anchor_id for x in self.temporal_anchors], "temporal anchor ids"),
            ([x.spatial_anchor_id for x in self.spatial_anchors], "spatial anchor ids"),
            ([x.candidate_set_id for x in self.candidate_sets], "candidate set ids"),
            ([x.candidate_id for x in self.candidates], "candidate ids"),
            ([x.temporal_grounding_id for x in self.temporal_groundings], "temporal grounding ids"),
            ([x.spatial_grounding_id for x in self.spatial_groundings], "spatial grounding ids"),
            ([x.temporal_relation_grounding_id for x in self.temporal_relation_groundings], "temporal relation grounding ids"),
            ([x.provenance_id for x in self.provenance_records], "provenance ids"),
            ([x.interpretation_id for x in self.interpretations], "interpretation ids"),
            ([x.snapshot_id for x in self.snapshots], "snapshot ids"),
        )
        for values, label in groups:
            _unique(values, label)

        excerpts = {x.source_excerpt_id: x for x in self.source_excerpts}
        temporal_expressions = {x.temporal_expression_id: x for x in self.temporal_expressions}
        spatial_expressions = {x.spatial_expression_id: x for x in self.spatial_expressions}
        temporal_anchors = {x.temporal_anchor_id: x for x in self.temporal_anchors}
        spatial_anchors = {x.spatial_anchor_id: x for x in self.spatial_anchors}
        sets = {x.candidate_set_id: x for x in self.candidate_sets}
        candidates = {x.candidate_id: x for x in self.candidates}
        temporal_groundings = {x.temporal_grounding_id: x for x in self.temporal_groundings}
        spatial_groundings = {x.spatial_grounding_id: x for x in self.spatial_groundings}
        temporal_relations = {x.temporal_relation_grounding_id: x for x in self.temporal_relation_groundings}
        provenances = {x.provenance_id: x for x in self.provenance_records}
        interpretations = {x.interpretation_id: x for x in self.interpretations}

        predecessor_signals = {x.signal_id for x in self.referential_identity.discourse_semantics.signals}
        predecessor_relations = {x.relation_id for x in self.referential_identity.discourse_semantics.rhetorical_relations}
        predecessor_frames = {x.frame_id for x in self.referential_identity.discourse_semantics.context_semantics.frames}
        predecessor_interpretations = {x.interpretation_id for x in self.referential_identity.interpretations}

        for expression in self.temporal_expressions:
            if expression.source_excerpt_ref:
                if expression.source_excerpt_ref not in excerpts:
                    raise ValueError("temporal expression source_excerpt_ref must resolve")
                excerpt = excerpts[expression.source_excerpt_ref]
                if excerpt.content[expression.char_start:expression.char_end] != expression.surface_text:
                    raise ValueError("temporal expression span must reproduce immutable source text")
            if expression.predecessor_signal_ref and expression.predecessor_signal_ref not in predecessor_signals:
                raise ValueError("temporal expression predecessor_signal_ref must resolve")
            if expression.candidate_set_ref not in sets:
                raise ValueError("temporal expression candidate_set_ref must resolve")
            if expression.base_temporal_expression_ref and expression.base_temporal_expression_ref not in temporal_expressions:
                raise ValueError("base_temporal_expression_ref must resolve")
            if expression.provenance_ref not in provenances:
                raise ValueError("temporal expression provenance_ref must resolve")

        for expression in self.spatial_expressions:
            if expression.source_excerpt_ref not in excerpts:
                raise ValueError("spatial expression source_excerpt_ref must resolve")
            excerpt = excerpts[expression.source_excerpt_ref]
            if excerpt.content[expression.char_start:expression.char_end] != expression.surface_text:
                raise ValueError("spatial expression span must reproduce immutable source text")
            if expression.candidate_set_ref not in sets:
                raise ValueError("spatial expression candidate_set_ref must resolve")
            if expression.antecedent_expression_ref and expression.antecedent_expression_ref not in spatial_expressions:
                raise ValueError("antecedent_expression_ref must resolve")
            if expression.provenance_ref not in provenances:
                raise ValueError("spatial expression provenance_ref must resolve")

        for anchor in self.temporal_anchors:
            if anchor.base_anchor_ref and anchor.base_anchor_ref not in temporal_anchors:
                raise ValueError("temporal anchor base_anchor_ref must resolve")
            if anchor.event_ref and anchor.event_ref not in predecessor_frames:
                raise ValueError("temporal anchor event_ref must resolve to predecessor semantic frame")
            if anchor.provenance_ref not in provenances:
                raise ValueError("temporal anchor provenance_ref must resolve")

        for anchor in self.spatial_anchors:
            if anchor.source_expression_ref and anchor.source_expression_ref not in spatial_expressions:
                raise ValueError("spatial anchor source_expression_ref must resolve")
            if anchor.provenance_ref not in provenances:
                raise ValueError("spatial anchor provenance_ref must resolve")

        all_expressions = {**temporal_expressions, **spatial_expressions}
        all_anchors: dict[str, Any] = {**temporal_anchors, **spatial_anchors}
        for candidate_set in self.candidate_sets:
            if candidate_set.expression_ref not in all_expressions:
                raise ValueError("candidate set expression_ref must resolve")
            expression_domain = GroundingDomain.temporal if candidate_set.expression_ref in temporal_expressions else GroundingDomain.spatial
            if candidate_set.domain != expression_domain:
                raise ValueError("candidate set domain must match expression domain")
            if any(ref not in candidates for ref in candidate_set.candidate_refs):
                raise ValueError("candidate set candidate_refs must resolve")
            exact = [c.candidate_id for c in self.candidates if c.candidate_set_ref == candidate_set.candidate_set_id]
            if set(exact) != set(candidate_set.candidate_refs):
                raise ValueError("candidate set must enumerate exactly its grounding candidates")
            ranks = [c.rank for c in self.candidates if c.candidate_set_ref == candidate_set.candidate_set_id]
            if len(ranks) != len(set(ranks)):
                raise ValueError("candidate ranks must be unique within candidate set")
            if candidate_set.provenance_ref not in provenances:
                raise ValueError("candidate set provenance_ref must resolve")

        for candidate in self.candidates:
            if candidate.candidate_set_ref not in sets:
                raise ValueError("candidate candidate_set_ref must resolve")
            candidate_set = sets[candidate.candidate_set_ref]
            if candidate.expression_ref != candidate_set.expression_ref or candidate.domain != candidate_set.domain:
                raise ValueError("candidate must match candidate-set expression and domain")
            if candidate.anchor_ref not in all_anchors:
                raise ValueError("candidate anchor_ref must resolve")
            expected_domain = GroundingDomain.temporal if candidate.anchor_ref in temporal_anchors else GroundingDomain.spatial
            if candidate.domain != expected_domain:
                raise ValueError("candidate domain must match anchor domain")
            if candidate.provenance_ref not in provenances:
                raise ValueError("candidate provenance_ref must resolve")

        for grounding in self.temporal_groundings:
            if grounding.temporal_expression_ref not in temporal_expressions or grounding.temporal_anchor_ref not in temporal_anchors:
                raise ValueError("temporal grounding expression/anchor refs must resolve")
            if grounding.selected_candidate_ref not in candidates:
                raise ValueError("temporal grounding selected_candidate_ref must resolve")
            candidate = candidates[grounding.selected_candidate_ref]
            if candidate.domain != GroundingDomain.temporal or candidate.expression_ref != grounding.temporal_expression_ref or candidate.anchor_ref != grounding.temporal_anchor_ref:
                raise ValueError("temporal grounding must agree with selected candidate")
            if grounding.state == GroundingState.accepted and candidate.state != GroundingState.accepted:
                raise ValueError("accepted temporal grounding requires accepted candidate")
            if grounding.provenance_ref not in provenances:
                raise ValueError("temporal grounding provenance_ref must resolve")

        for grounding in self.spatial_groundings:
            if grounding.spatial_expression_ref not in spatial_expressions or grounding.spatial_anchor_ref not in spatial_anchors:
                raise ValueError("spatial grounding expression/anchor refs must resolve")
            if grounding.selected_candidate_ref not in candidates:
                raise ValueError("spatial grounding selected_candidate_ref must resolve")
            candidate = candidates[grounding.selected_candidate_ref]
            if candidate.domain != GroundingDomain.spatial or candidate.expression_ref != grounding.spatial_expression_ref or candidate.anchor_ref != grounding.spatial_anchor_ref:
                raise ValueError("spatial grounding must agree with selected candidate")
            if grounding.state == GroundingState.accepted and candidate.state != GroundingState.accepted:
                raise ValueError("accepted spatial grounding requires accepted candidate")
            if grounding.provenance_ref not in provenances:
                raise ValueError("spatial grounding provenance_ref must resolve")

        for relation in self.temporal_relation_groundings:
            if relation.predecessor_rhetorical_relation_ref not in predecessor_relations:
                raise ValueError("temporal relation predecessor rhetorical relation must resolve")
            if relation.predecessor_signal_ref not in predecessor_signals:
                raise ValueError("temporal relation predecessor signal must resolve")
            if relation.source_event_ref not in predecessor_frames or relation.target_event_ref not in predecessor_frames:
                raise ValueError("temporal relation event refs must resolve")
            if relation.provenance_ref not in provenances:
                raise ValueError("temporal relation provenance_ref must resolve")

        for interpretation in self.interpretations:
            if interpretation.referential_interpretation_ref not in predecessor_interpretations:
                raise ValueError("grounding interpretation referential_interpretation_ref must resolve")
            if any(ref not in excerpts for ref in interpretation.source_excerpt_refs):
                raise ValueError("interpretation source excerpt ref must resolve")
            if any(ref not in temporal_expressions for ref in interpretation.temporal_expression_refs):
                raise ValueError("interpretation temporal expression ref must resolve")
            if any(ref not in spatial_expressions for ref in interpretation.spatial_expression_refs):
                raise ValueError("interpretation spatial expression ref must resolve")
            if any(ref not in sets for ref in interpretation.candidate_set_refs):
                raise ValueError("interpretation candidate set ref must resolve")
            if any(ref not in temporal_groundings for ref in interpretation.temporal_grounding_refs):
                raise ValueError("interpretation temporal grounding ref must resolve")
            if any(ref not in spatial_groundings for ref in interpretation.spatial_grounding_refs):
                raise ValueError("interpretation spatial grounding ref must resolve")
            if any(ref not in temporal_relations for ref in interpretation.temporal_relation_grounding_refs):
                raise ValueError("interpretation temporal relation grounding ref must resolve")
            known_expressions = set(temporal_expressions) | set(spatial_expressions)
            if any(ref not in known_expressions for ref in interpretation.unresolved_expression_refs):
                raise ValueError("interpretation unresolved expression ref must resolve")
            if interpretation.provenance_ref not in provenances:
                raise ValueError("interpretation provenance_ref must resolve")

        object_ids = (
            set(excerpts) | set(temporal_expressions) | set(spatial_expressions) |
            set(temporal_anchors) | set(spatial_anchors) | set(sets) | set(candidates) |
            set(temporal_groundings) | set(spatial_groundings) | set(temporal_relations) |
            set(interpretations) | {x.snapshot_id for x in self.snapshots}
        )
        for provenance in self.provenance_records:
            if any(ref not in object_ids for ref in provenance.subject_refs):
                raise ValueError("provenance subject_ref must resolve to a v4.4 object")

        predecessor_fp = self.referential_identity.fingerprint()
        for snapshot in self.snapshots:
            if snapshot.predecessor_fingerprint_sha256 != predecessor_fp:
                raise ValueError("snapshot predecessor fingerprint must match embedded v4.3 bundle")
            if any(ref not in interpretations for ref in snapshot.interpretation_refs):
                raise ValueError("snapshot interpretation ref must resolve")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


@lru_cache(maxsize=1)
def reference_temporal_spatial_language_grounding_bundle() -> TemporalSpatialLanguageGroundingBundle:
    predecessor = reference_coreference_referential_identity_bundle()
    source_text = "In 2025, the ministry opened an office in Brussels. The commission met there the following year."

    excerpt = GroundingSourceExcerpt(
        source_excerpt_id="grounding-source:reference-note:v1",
        source_ref="source:grounding-reference-note:v1",
        language_ref="language:en",
        content=source_text,
        content_sha256=canonical_sha256(source_text),
        provenance_ref="prov:grounding-source:reference",
        metadata={"purpose": "v4.4 temporal and spatial grounding reference case"},
    )

    temporal_expressions = [
        TemporalExpression(
            temporal_expression_id="temporal-expression:2025",
            source_excerpt_ref=excerpt.source_excerpt_id,
            expression_kind=TemporalExpressionKind.absolute_year,
            surface_text="2025",
            char_start=3,
            char_end=7,
            candidate_set_ref="grounding-candidate-set:temporal:2025",
            provenance_ref="prov:grounding-expressions:reference",
        ),
        TemporalExpression(
            temporal_expression_id="temporal-expression:following-year",
            source_excerpt_ref=excerpt.source_excerpt_id,
            expression_kind=TemporalExpressionKind.relative_time,
            surface_text="the following year",
            char_start=77,
            char_end=95,
            candidate_set_ref="grounding-candidate-set:temporal:following-year",
            base_temporal_expression_ref="temporal-expression:2025",
            provenance_ref="prov:grounding-expressions:reference",
            metadata={"relative_operation": "+P1Y"},
        ),
        TemporalExpression(
            temporal_expression_id="temporal-expression:after",
            predecessor_signal_ref="discourse-signal:after",
            expression_kind=TemporalExpressionKind.temporal_relation_signal,
            surface_text="after",
            candidate_set_ref="grounding-candidate-set:temporal:after",
            provenance_ref="prov:grounding-expressions:reference",
            metadata={"predecessor_relation": "rhetorical-relation:revision-before-rejection"},
        ),
    ]

    spatial_expressions = [
        SpatialExpression(
            spatial_expression_id="spatial-expression:brussels",
            source_excerpt_ref=excerpt.source_excerpt_id,
            expression_kind=SpatialExpressionKind.named_place,
            surface_text="Brussels",
            char_start=42,
            char_end=50,
            candidate_set_ref="grounding-candidate-set:spatial:brussels",
            provenance_ref="prov:grounding-expressions:reference",
        ),
        SpatialExpression(
            spatial_expression_id="spatial-expression:there",
            source_excerpt_ref=excerpt.source_excerpt_id,
            expression_kind=SpatialExpressionKind.spatial_deixis,
            surface_text="there",
            char_start=71,
            char_end=76,
            candidate_set_ref="grounding-candidate-set:spatial:there",
            antecedent_expression_ref="spatial-expression:brussels",
            provenance_ref="prov:grounding-expressions:reference",
        ),
    ]

    temporal_anchors = [
        TemporalAnchor(
            temporal_anchor_id="temporal-anchor:calendar-year:2025",
            anchor_kind=TemporalAnchorKind.calendar_period,
            normalized_start="2025-01-01",
            normalized_end="2025-12-31",
            precision="year",
            provenance_ref="prov:grounding-anchors:reference",
        ),
        TemporalAnchor(
            temporal_anchor_id="temporal-anchor:calendar-year:2026",
            anchor_kind=TemporalAnchorKind.derived,
            normalized_start="2026-01-01",
            normalized_end="2026-12-31",
            precision="year",
            base_anchor_ref="temporal-anchor:calendar-year:2025",
            derivation_operation="+P1Y",
            provenance_ref="prov:grounding-anchors:reference",
        ),
        TemporalAnchor(
            temporal_anchor_id="temporal-anchor:revision-event",
            anchor_kind=TemporalAnchorKind.event,
            precision="event",
            event_ref="frame:revision",
            provenance_ref="prov:grounding-anchors:reference",
        ),
    ]

    spatial_anchors = [
        SpatialAnchor(
            spatial_anchor_id="spatial-anchor:brussels-source-place",
            anchor_kind=SpatialAnchorKind.source_named_place,
            label="Brussels",
            source_expression_ref="spatial-expression:brussels",
            jurisdiction_hints=["Belgium"],
            provenance_ref="prov:grounding-anchors:reference",
            metadata={"canonical_place_resolution": "deferred"},
        )
    ]

    candidates = [
        GroundingCandidate(
            candidate_id="grounding-candidate:2025:calendar-year",
            candidate_set_ref="grounding-candidate-set:temporal:2025",
            domain=GroundingDomain.temporal,
            expression_ref="temporal-expression:2025",
            anchor_ref="temporal-anchor:calendar-year:2025",
            rank=1,
            confidence=1.0,
            state=GroundingState.accepted,
            supporting_signal_refs=["surface-form:four-digit-year"],
            provenance_ref="prov:grounding-candidates:reference",
        ),
        GroundingCandidate(
            candidate_id="grounding-candidate:following-year:2026",
            candidate_set_ref="grounding-candidate-set:temporal:following-year",
            domain=GroundingDomain.temporal,
            expression_ref="temporal-expression:following-year",
            anchor_ref="temporal-anchor:calendar-year:2026",
            rank=1,
            confidence=0.99,
            state=GroundingState.accepted,
            supporting_signal_refs=["temporal-expression:2025", "relative-operation:+P1Y"],
            provenance_ref="prov:grounding-candidates:reference",
        ),
        GroundingCandidate(
            candidate_id="grounding-candidate:after:revision-event",
            candidate_set_ref="grounding-candidate-set:temporal:after",
            domain=GroundingDomain.temporal,
            expression_ref="temporal-expression:after",
            anchor_ref="temporal-anchor:revision-event",
            rank=1,
            confidence=1.0,
            state=GroundingState.accepted,
            supporting_signal_refs=["rhetorical-relation:revision-before-rejection"],
            provenance_ref="prov:grounding-candidates:reference",
        ),
        GroundingCandidate(
            candidate_id="grounding-candidate:brussels:source-place",
            candidate_set_ref="grounding-candidate-set:spatial:brussels",
            domain=GroundingDomain.spatial,
            expression_ref="spatial-expression:brussels",
            anchor_ref="spatial-anchor:brussels-source-place",
            rank=1,
            confidence=1.0,
            state=GroundingState.accepted,
            supporting_signal_refs=["surface-form:named-place"],
            provenance_ref="prov:grounding-candidates:reference",
        ),
        GroundingCandidate(
            candidate_id="grounding-candidate:there:brussels",
            candidate_set_ref="grounding-candidate-set:spatial:there",
            domain=GroundingDomain.spatial,
            expression_ref="spatial-expression:there",
            anchor_ref="spatial-anchor:brussels-source-place",
            rank=1,
            confidence=0.96,
            state=GroundingState.accepted,
            supporting_signal_refs=["spatial-expression:brussels", "discourse-proximity:previous-sentence"],
            provenance_ref="prov:grounding-candidates:reference",
        ),
    ]

    candidate_sets = [
        GroundingCandidateSet(
            candidate_set_id="grounding-candidate-set:temporal:2025",
            domain=GroundingDomain.temporal,
            expression_ref="temporal-expression:2025",
            candidate_refs=["grounding-candidate:2025:calendar-year"],
            selected_candidate_ref="grounding-candidate:2025:calendar-year",
            state=GroundingState.accepted,
            method=InterpretationMethod.manual,
            reviewer_ref="reviewer:language-grounding:v1",
            provenance_ref="prov:grounding-candidates:reference",
        ),
        GroundingCandidateSet(
            candidate_set_id="grounding-candidate-set:temporal:following-year",
            domain=GroundingDomain.temporal,
            expression_ref="temporal-expression:following-year",
            candidate_refs=["grounding-candidate:following-year:2026"],
            selected_candidate_ref="grounding-candidate:following-year:2026",
            state=GroundingState.accepted,
            method=InterpretationMethod.manual,
            reviewer_ref="reviewer:language-grounding:v1",
            provenance_ref="prov:grounding-candidates:reference",
            rationale="Relative year is normalized against the explicitly grounded 2025 base expression; the derivation is preserved rather than flattened.",
        ),
        GroundingCandidateSet(
            candidate_set_id="grounding-candidate-set:temporal:after",
            domain=GroundingDomain.temporal,
            expression_ref="temporal-expression:after",
            candidate_refs=["grounding-candidate:after:revision-event"],
            selected_candidate_ref="grounding-candidate:after:revision-event",
            state=GroundingState.accepted,
            method=InterpretationMethod.manual,
            reviewer_ref="reviewer:language-grounding:v1",
            provenance_ref="prov:grounding-candidates:reference",
        ),
        GroundingCandidateSet(
            candidate_set_id="grounding-candidate-set:spatial:brussels",
            domain=GroundingDomain.spatial,
            expression_ref="spatial-expression:brussels",
            candidate_refs=["grounding-candidate:brussels:source-place"],
            selected_candidate_ref="grounding-candidate:brussels:source-place",
            state=GroundingState.accepted,
            method=InterpretationMethod.manual,
            reviewer_ref="reviewer:language-grounding:v1",
            provenance_ref="prov:grounding-candidates:reference",
            rationale="Source text names Brussels; canonical gazetteer identity remains deliberately deferred.",
        ),
        GroundingCandidateSet(
            candidate_set_id="grounding-candidate-set:spatial:there",
            domain=GroundingDomain.spatial,
            expression_ref="spatial-expression:there",
            candidate_refs=["grounding-candidate:there:brussels"],
            selected_candidate_ref="grounding-candidate:there:brussels",
            state=GroundingState.accepted,
            method=InterpretationMethod.manual,
            reviewer_ref="reviewer:language-grounding:v1",
            provenance_ref="prov:grounding-candidates:reference",
            rationale="Spatial deixis is resolved to the explicit Brussels source-place anchor while preserving that this is linguistic interpretation rather than canonical geocoding.",
        ),
    ]

    temporal_groundings = [
        TemporalGrounding(
            temporal_grounding_id="temporal-grounding:2025",
            temporal_expression_ref="temporal-expression:2025",
            temporal_anchor_ref="temporal-anchor:calendar-year:2025",
            selected_candidate_ref="grounding-candidate:2025:calendar-year",
            state=GroundingState.accepted,
            confidence=1.0,
            reviewer_ref="reviewer:language-grounding:v1",
            provenance_ref="prov:groundings:reference",
        ),
        TemporalGrounding(
            temporal_grounding_id="temporal-grounding:following-year",
            temporal_expression_ref="temporal-expression:following-year",
            temporal_anchor_ref="temporal-anchor:calendar-year:2026",
            selected_candidate_ref="grounding-candidate:following-year:2026",
            state=GroundingState.accepted,
            confidence=0.99,
            reviewer_ref="reviewer:language-grounding:v1",
            provenance_ref="prov:groundings:reference",
        ),
        TemporalGrounding(
            temporal_grounding_id="temporal-grounding:after-signal",
            temporal_expression_ref="temporal-expression:after",
            temporal_anchor_ref="temporal-anchor:revision-event",
            selected_candidate_ref="grounding-candidate:after:revision-event",
            state=GroundingState.accepted,
            confidence=1.0,
            reviewer_ref="reviewer:language-grounding:v1",
            provenance_ref="prov:groundings:reference",
            metadata={"anchor_role": "reference event for reported after relation"},
        ),
    ]

    spatial_groundings = [
        SpatialGrounding(
            spatial_grounding_id="spatial-grounding:brussels",
            spatial_expression_ref="spatial-expression:brussels",
            spatial_anchor_ref="spatial-anchor:brussels-source-place",
            selected_candidate_ref="grounding-candidate:brussels:source-place",
            state=GroundingState.accepted,
            confidence=1.0,
            reviewer_ref="reviewer:language-grounding:v1",
            provenance_ref="prov:groundings:reference",
        ),
        SpatialGrounding(
            spatial_grounding_id="spatial-grounding:there-to-brussels",
            spatial_expression_ref="spatial-expression:there",
            spatial_anchor_ref="spatial-anchor:brussels-source-place",
            selected_candidate_ref="grounding-candidate:there:brussels",
            state=GroundingState.accepted,
            confidence=0.96,
            reviewer_ref="reviewer:language-grounding:v1",
            provenance_ref="prov:groundings:reference",
        ),
    ]

    relation = TemporalRelationGrounding(
        temporal_relation_grounding_id="temporal-relation-grounding:revision-before-rejection",
        predecessor_rhetorical_relation_ref="rhetorical-relation:revision-before-rejection",
        predecessor_signal_ref="discourse-signal:after",
        source_event_ref="frame:revision",
        target_event_ref="frame:rejection",
        relation_kind=TemporalRelationKind.before,
        state=GroundingState.accepted,
        confidence=1.0,
        reviewer_ref="reviewer:language-grounding:v1",
        provenance_ref="prov:groundings:reference",
        metadata={"surface_form": "rejected ... after ... revised"},
    )

    interpretation = TemporalSpatialGroundingInterpretation(
        interpretation_id="grounding-interpretation:reference:baseline",
        referential_interpretation_ref="referential-interpretation:policy-note:baseline",
        source_excerpt_refs=[excerpt.source_excerpt_id],
        temporal_expression_refs=[x.temporal_expression_id for x in temporal_expressions],
        spatial_expression_refs=[x.spatial_expression_id for x in spatial_expressions],
        candidate_set_refs=[x.candidate_set_id for x in candidate_sets],
        temporal_grounding_refs=[x.temporal_grounding_id for x in temporal_groundings],
        spatial_grounding_refs=[x.spatial_grounding_id for x in spatial_groundings],
        temporal_relation_grounding_refs=[relation.temporal_relation_grounding_id],
        unresolved_expression_refs=[],
        provenance_ref="prov:grounding-interpretation:reference",
        state=GroundingState.accepted,
        confidence=0.96,
        metadata={
            "predecessor_objects_are_embedded_unchanged": True,
            "canonical_geographic_identity_for_brussels_is_deferred": True,
        },
    )

    snapshot_material = {
        "predecessor": predecessor.fingerprint(),
        "source_excerpt": excerpt.fingerprint(),
        "temporal_expressions": [x.fingerprint() for x in temporal_expressions],
        "spatial_expressions": [x.fingerprint() for x in spatial_expressions],
        "temporal_anchors": [x.fingerprint() for x in temporal_anchors],
        "spatial_anchors": [x.fingerprint() for x in spatial_anchors],
        "candidate_sets": [x.fingerprint() for x in candidate_sets],
        "candidates": [x.fingerprint() for x in candidates],
        "temporal_groundings": [x.fingerprint() for x in temporal_groundings],
        "spatial_groundings": [x.fingerprint() for x in spatial_groundings],
        "temporal_relation": relation.fingerprint(),
        "interpretation": interpretation.fingerprint(),
    }
    snapshot = TemporalSpatialGroundingSnapshot(
        snapshot_id="snapshot:temporal-spatial-language-grounding:reference:v1",
        predecessor_fingerprint_sha256=predecessor.fingerprint(),
        interpretation_refs=[interpretation.interpretation_id],
        deterministic_grounding_fingerprint_sha256=canonical_sha256(snapshot_material),
    )

    object_groups = {
        "prov:grounding-source:reference": [excerpt.source_excerpt_id],
        "prov:grounding-expressions:reference": [x.temporal_expression_id for x in temporal_expressions] + [x.spatial_expression_id for x in spatial_expressions],
        "prov:grounding-anchors:reference": [x.temporal_anchor_id for x in temporal_anchors] + [x.spatial_anchor_id for x in spatial_anchors],
        "prov:grounding-candidates:reference": [x.candidate_set_id for x in candidate_sets] + [x.candidate_id for x in candidates],
        "prov:groundings:reference": [x.temporal_grounding_id for x in temporal_groundings] + [x.spatial_grounding_id for x in spatial_groundings] + [relation.temporal_relation_grounding_id],
        "prov:grounding-interpretation:reference": [interpretation.interpretation_id, snapshot.snapshot_id],
    }
    provenances = [
        GroundingProvenanceRecord(
            provenance_id=prov_id,
            subject_refs=subjects,
            method=InterpretationMethod.manual,
            produced_by_ref="reviewer:language-grounding:v1" if prov_id != "prov:grounding-source:reference" else "actor:platform-core-reference-builder",
            source_refs=["source:grounding-reference-note:v1", "source:policy-note:v1"] if prov_id == "prov:groundings:reference" else ["source:grounding-reference-note:v1"],
            reviewer_ref="reviewer:language-grounding:v1" if prov_id != "prov:grounding-source:reference" else None,
        )
        for prov_id, subjects in object_groups.items()
    ]

    return TemporalSpatialLanguageGroundingBundle(
        extends_contracts=list(EXTENDS_CONTRACTS),
        policy=GroundingPolicy(policy_id="temporal-spatial-language-grounding-policy:v4.4"),
        referential_identity=predecessor,
        source_excerpts=[excerpt],
        temporal_expressions=temporal_expressions,
        spatial_expressions=spatial_expressions,
        temporal_anchors=temporal_anchors,
        spatial_anchors=spatial_anchors,
        candidate_sets=candidate_sets,
        candidates=candidates,
        temporal_groundings=temporal_groundings,
        spatial_groundings=spatial_groundings,
        temporal_relation_groundings=[relation],
        provenance_records=provenances,
        interpretations=[interpretation],
        snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    bundle = reference_temporal_spatial_language_grounding_bundle()
    unresolved = sum(len(x.unresolved_expression_refs) for x in bundle.interpretations)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "extends_contracts": list(EXTENDS_CONTRACTS),
        "identity": {
            "product": "Sustainable Catalyst Platform Core",
            "build": "Temporal & Spatial Language Grounding",
            "major_api": "v4",
        },
        "principles": {
            "temporal_and_spatial_expressions_are_first_class": True,
            "grounding_is_explicit_and_provenance_preserving": True,
            "relative_time_preserves_base_anchor_and_derivation": True,
            "spatial_deixis_preserves_antecedent_expression": True,
            "competing_groundings_may_coexist": True,
            "accepted_grounding_requires_governed_review": True,
            "temporal_relation_is_source_semantics_not_world_truth": True,
            "named_place_grounding_is_distinct_from_canonical_geographic_identity": True,
            "geocoder_and_model_outputs_are_advisory": True,
            "grounding_overlays_without_rewriting_predecessor_objects": True,
        },
        "boundaries": {
            "core_autonomously_geocodes_named_place": False,
            "core_autonomously_selects_grounding": False,
            "grounding_score_establishes_world_truth": False,
            "named_place_establishes_canonical_geographic_identity": False,
            "temporal_relation_establishes_real_world_event_order": False,
            "relative_time_flattens_derivation_history": False,
            "accepted_grounding_rewrites_v430_predecessor": False,
            "temporal_graph_mutation_performed": False,
            "spatial_graph_mutation_performed": False,
            "identity_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
            "context_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "extends_v430_coreference_reference_identity": True,
            "grounds_v420_temporal_discourse_signal": True,
            "prepares_v450_epistemic_modal_negation_certainty": True,
            "prepares_v460_pragmatic_meaning_speech_act_intent": True,
            "prepares_v470_cross_document_context_graph": True,
            "prepares_v480_multilingual_context_alignment": True,
            "prepares_v490_contextual_semantic_evaluation": True,
        },
        "reference": {
            "predecessor_release": bundle.referential_identity.release,
            "predecessor_fingerprint_sha256": bundle.referential_identity.fingerprint(),
            "source_excerpts": len(bundle.source_excerpts),
            "temporal_expressions": len(bundle.temporal_expressions),
            "spatial_expressions": len(bundle.spatial_expressions),
            "temporal_anchors": len(bundle.temporal_anchors),
            "spatial_anchors": len(bundle.spatial_anchors),
            "candidate_sets": len(bundle.candidate_sets),
            "candidates": len(bundle.candidates),
            "accepted_candidate_sets": sum(x.state == GroundingState.accepted for x in bundle.candidate_sets),
            "temporal_groundings": len(bundle.temporal_groundings),
            "spatial_groundings": len(bundle.spatial_groundings),
            "temporal_relation_groundings": len(bundle.temporal_relation_groundings),
            "unresolved_expressions": unresolved,
            "relative_time_groundings": sum(x.expression_kind == TemporalExpressionKind.relative_time for x in bundle.temporal_expressions),
            "spatial_deictic_groundings": sum(x.expression_kind == SpatialExpressionKind.spatial_deixis for x in bundle.spatial_expressions),
            "canonical_place_bindings": sum(bool(x.canonical_place_ref) for x in bundle.spatial_anchors),
            "interpretations": len(bundle.interpretations),
            "snapshots": len(bundle.snapshots),
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
        "database_migration": "none",
    }
