from __future__ import annotations

import hashlib
from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .context_semantic_frame import InterpretationMethod
from .cross_document_context_graph import (
    CrossDocumentContextGraphBundle,
    GraphReviewState,
    reference_cross_document_context_graph_bundle,
)
from .cross_lingual_semantic_exchange import (
    CONTRACT_VERSION as CROSS_LINGUAL_CONTRACT_VERSION,
    CrossLingualSemanticExchangeBundle,
    reference_cross_lingual_semantic_exchange_bundle,
)

CORE_RELEASE = "4.8.0"
CONTRACT_VERSION = "sc.core.multilingual-context-semantic-alignment.v1"
PREDECESSOR_CONTRACT = "sc.core.cross-document-context-graph.v1"

EXTENDS_CONTRACTS = [
    PREDECESSOR_CONTRACT,
    "sc.core.cross-lingual-semantic-linguistic-exchange.v1",
    "sc.core.translation-transliteration-alignment.v1",
    "sc.core.multilingual-text-language-object.v1",
    "sc.core.pragmatic-meaning-speech-act-communicative-intent.v1",
    "sc.core.epistemic-modal-negation-certainty-semantics.v1",
    "sc.core.temporal-spatial-language-grounding.v1",
    "sc.core.coreference-reference-referential-identity-intelligence.v1",
    "sc.core.discourse-structure-rhetorical-semantics.v1",
    "sc.core.context-object-semantic-frame-foundation.v1",
]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class ContextRepresentationRole(str, Enum):
    original = "original"
    translation = "translation"
    transliteration = "transliteration"


class AlignmentReviewState(str, Enum):
    candidate = "candidate"
    reviewed = "reviewed"
    rejected = "rejected"
    superseded = "superseded"


class ContextAlignmentRelation(str, Enum):
    exact_context_equivalence = "exact-context-equivalence"
    near_equivalent = "near-equivalent"
    translation_correspondence = "translation-correspondence"
    pragmatic_shift = "pragmatic-shift"
    epistemic_shift = "epistemic-shift"
    discourse_shift = "discourse-shift"
    referential_shift = "referential-shift"
    culturally_conditioned = "culturally-conditioned"
    historically_conditioned = "historically-conditioned"
    non_equivalent = "non-equivalent"
    unresolved = "unresolved"


class DivergenceDimension(str, Enum):
    lexical = "lexical"
    semantic = "semantic"
    discourse = "discourse"
    pragmatic = "pragmatic"
    epistemic = "epistemic"
    referential = "referential"
    temporal = "temporal"
    spatial = "spatial"
    cultural = "cultural"
    historical = "historical"


class ContextUnitKind(str, Enum):
    proposition = "proposition"
    discourse_segment = "discourse-segment"
    pragmatic_unit = "pragmatic-unit"
    contextual_concept = "contextual-concept"


class MultilingualContextPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    original_language_is_authoritative_representation: Literal[True] = True
    translation_is_derived_representation: Literal[True] = True
    contextual_alignment_preserves_source_spans: Literal[True] = True
    multiple_translations_may_coexist: Literal[True] = True
    culturally_conditioned_meaning_may_remain_unresolved: Literal[True] = True
    historically_conditioned_meaning_may_remain_unresolved: Literal[True] = True
    machine_alignment_is_advisory: Literal[True] = True
    accepted_alignment_requires_governed_review: Literal[True] = True
    semantic_similarity_is_not_equivalence: Literal[True] = True
    translation_correspondence_is_not_identity: Literal[True] = True
    cross_language_context_projection_is_not_graph_fact: Literal[True] = True
    predecessor_context_graph_rewrite_authorized: Literal[False] = False
    identity_graph_mutation_authorized: Literal[False] = False
    evidence_graph_mutation_authorized: Literal[False] = False
    knowledge_graph_mutation_authorized: Literal[False] = False


class ContextLanguageRepresentation(BaseModel):
    representation_id: str = Field(min_length=3, max_length=500)
    role: ContextRepresentationRole
    language_ref: str = Field(min_length=3, max_length=200)
    script_ref: str = Field(min_length=3, max_length=200)
    source_ref: str = Field(min_length=3, max_length=1000)
    content: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    derived_from_representation_ref: str | None = Field(default=None, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    original_language_is_authoritative: bool
    derived_representation_replaces_original: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_representation(self):
        if self.content_sha256 != _sha256_text(self.content):
            raise ValueError("content_sha256 must match UTF-8 content")
        if self.role == ContextRepresentationRole.original:
            if self.derived_from_representation_ref is not None:
                raise ValueError("original representation cannot derive from another representation")
            if not self.original_language_is_authoritative:
                raise ValueError("original representation must remain authoritative")
        else:
            if not self.derived_from_representation_ref:
                raise ValueError("derived context representation requires derived_from_representation_ref")
            if self.original_language_is_authoritative:
                raise ValueError("derived representation cannot be marked authoritative")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextSemanticUnit(BaseModel):
    unit_id: str = Field(min_length=3, max_length=500)
    representation_ref: str = Field(min_length=3, max_length=500)
    unit_kind: ContextUnitKind
    sequence: int = Field(ge=0)
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    surface_text: str = Field(min_length=1, max_length=8000)
    semantic_summary: str = Field(min_length=1, max_length=4000)
    modality: str | None = Field(default=None, max_length=200)
    epistemic_status: str | None = Field(default=None, max_length=200)
    pragmatic_function: str | None = Field(default=None, max_length=200)
    context_graph_refs: list[str] = Field(default_factory=list)
    source_span_is_immutable: Literal[True] = True
    semantic_summary_is_interpretive: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_unit(self):
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        _unique(self.context_graph_refs, "context_graph_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SemanticDivergenceRecord(BaseModel):
    divergence_id: str = Field(min_length=3, max_length=500)
    source_unit_ref: str = Field(min_length=3, max_length=500)
    target_unit_ref: str = Field(min_length=3, max_length=500)
    dimensions: list[DivergenceDimension] = Field(min_length=1)
    description: str = Field(min_length=3, max_length=5000)
    severity: float = Field(ge=0.0, le=1.0)
    state: AlignmentReviewState
    provenance_ref: str = Field(min_length=3, max_length=500)
    reviewer_ref: str | None = Field(default=None, max_length=500)
    divergence_is_not_translation_error_by_default: Literal[True] = True
    unresolved_divergence_is_preserved: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_divergence(self):
        _unique([x.value for x in self.dimensions], "divergence dimensions")
        if self.state == AlignmentReviewState.reviewed and not self.reviewer_ref:
            raise ValueError("reviewed divergence requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MultilingualContextAlignment(BaseModel):
    alignment_id: str = Field(min_length=3, max_length=500)
    source_unit_ref: str = Field(min_length=3, max_length=500)
    target_unit_ref: str = Field(min_length=3, max_length=500)
    relation: ContextAlignmentRelation
    confidence: float = Field(ge=0.0, le=1.0)
    state: AlignmentReviewState
    aligned_dimensions: list[str] = Field(min_length=1)
    divergence_refs: list[str] = Field(default_factory=list)
    provenance_ref: str = Field(min_length=3, max_length=500)
    reviewer_ref: str | None = Field(default=None, max_length=500)
    direction_is_significant: Literal[True] = True
    alignment_is_not_lexical_identity: Literal[True] = True
    alignment_is_not_claim_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_alignment(self):
        if self.source_unit_ref == self.target_unit_ref:
            raise ValueError("multilingual alignment requires distinct source and target units")
        _unique(self.aligned_dimensions, "aligned_dimensions")
        _unique(self.divergence_refs, "divergence_refs")
        if self.state == AlignmentReviewState.reviewed and not self.reviewer_ref:
            raise ValueError("reviewed context alignment requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextGraphProjectionBinding(BaseModel):
    projection_id: str = Field(min_length=3, max_length=500)
    semantic_unit_ref: str = Field(min_length=3, max_length=500)
    context_graph_thread_ref: str = Field(min_length=3, max_length=500)
    relation_label: str = Field(min_length=3, max_length=500)
    confidence: float = Field(ge=0.0, le=1.0)
    state: AlignmentReviewState
    provenance_ref: str = Field(min_length=3, max_length=500)
    reviewer_ref: str | None = Field(default=None, max_length=500)
    projection_is_contextual_hypothesis: Literal[True] = True
    projection_does_not_mutate_context_graph: Literal[True] = True
    projection_does_not_establish_object_identity: Literal[True] = True

    @model_validator(mode="after")
    def validate_projection(self):
        if self.state == AlignmentReviewState.reviewed and not self.reviewer_ref:
            raise ValueError("reviewed graph projection requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MultilingualContextProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3, max_length=500)
    subject_refs: list[str] = Field(min_length=1)
    method: InterpretationMethod
    produced_by_ref: str = Field(min_length=3, max_length=500)
    source_refs: list[str] = Field(min_length=1)
    reviewer_ref: str | None = Field(default=None, max_length=500)
    transformation_notes: list[str] = Field(default_factory=list)
    machine_or_translation_output_is_advisory: Literal[True] = True
    provenance_does_not_establish_equivalence_or_truth: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MultilingualContextInterpretation(BaseModel):
    interpretation_id: str = Field(min_length=3, max_length=500)
    predecessor_context_graph_interpretation_refs: list[str] = Field(min_length=1)
    representation_refs: list[str] = Field(min_length=2)
    semantic_unit_refs: list[str] = Field(min_length=2)
    alignment_refs: list[str] = Field(min_length=1)
    divergence_refs: list[str] = Field(default_factory=list)
    projection_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    state: AlignmentReviewState
    confidence: float = Field(ge=0.0, le=1.0)
    reviewer_ref: str | None = Field(default=None, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    accepted_interpretation_does_not_establish_universal_equivalence: Literal[True] = True

    @model_validator(mode="after")
    def validate_interpretation(self):
        for values, label in (
            (self.representation_refs, "representation_refs"),
            (self.semantic_unit_refs, "semantic_unit_refs"),
            (self.alignment_refs, "alignment_refs"),
            (self.divergence_refs, "divergence_refs"),
            (self.projection_refs, "projection_refs"),
            (self.unresolved_refs, "unresolved_refs"),
        ):
            _unique(values, label)
        if self.state == AlignmentReviewState.reviewed and not self.reviewer_ref:
            raise ValueError("reviewed multilingual context interpretation requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MultilingualContextSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    predecessor_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    cross_lingual_exchange_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    interpretation_refs: list[str] = Field(min_length=1)
    deterministic_alignment_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_does_not_freeze_semantic_equivalence: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MultilingualContextSemanticAlignmentBundle(BaseModel):
    release: Literal["4.8.0"] = "4.8.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    extends_contracts: list[str] = Field(min_length=10)
    policy: MultilingualContextPolicy
    context_graph: CrossDocumentContextGraphBundle
    cross_lingual_exchange: CrossLingualSemanticExchangeBundle
    representations: list[ContextLanguageRepresentation] = Field(min_length=2)
    semantic_units: list[ContextSemanticUnit] = Field(min_length=2)
    alignments: list[MultilingualContextAlignment] = Field(min_length=1)
    divergences: list[SemanticDivergenceRecord] = Field(default_factory=list)
    graph_projections: list[ContextGraphProjectionBinding] = Field(default_factory=list)
    provenance_records: list[MultilingualContextProvenanceRecord] = Field(min_length=1)
    interpretations: list[MultilingualContextInterpretation] = Field(min_length=1)
    snapshots: list[MultilingualContextSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.extends_contracts != EXTENDS_CONTRACTS:
            raise ValueError("extends_contracts must preserve v4.8 dependency order")
        if self.context_graph.release != "4.7.0" or self.context_graph.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.8 must embed governed v4.7 context graph predecessor")
        if CROSS_LINGUAL_CONTRACT_VERSION != "sc.core.cross-lingual-semantic-linguistic-exchange.v1":
            raise ValueError("v4.8 requires governed cross-lingual semantic exchange contract")

        for values, label in (
            ([x.representation_id for x in self.representations], "representation ids"),
            ([x.unit_id for x in self.semantic_units], "semantic unit ids"),
            ([x.alignment_id for x in self.alignments], "alignment ids"),
            ([x.divergence_id for x in self.divergences], "divergence ids"),
            ([x.projection_id for x in self.graph_projections], "projection ids"),
            ([x.provenance_id for x in self.provenance_records], "provenance ids"),
            ([x.interpretation_id for x in self.interpretations], "interpretation ids"),
            ([x.snapshot_id for x in self.snapshots], "snapshot ids"),
        ):
            _unique(values, label)

        reps = {x.representation_id: x for x in self.representations}
        units = {x.unit_id: x for x in self.semantic_units}
        alignments = {x.alignment_id: x for x in self.alignments}
        divergences = {x.divergence_id: x for x in self.divergences}
        projections = {x.projection_id: x for x in self.graph_projections}
        provenances = {x.provenance_id: x for x in self.provenance_records}
        interpretations = {x.interpretation_id: x for x in self.interpretations}

        originals = [x for x in self.representations if x.role == ContextRepresentationRole.original]
        if len(originals) != 1:
            raise ValueError("reference multilingual context bundle requires exactly one authoritative original representation")
        original = originals[0]
        for rep in self.representations:
            if rep.provenance_ref not in provenances:
                raise ValueError("representation provenance_ref must resolve")
            if rep.role != ContextRepresentationRole.original and rep.derived_from_representation_ref != original.representation_id:
                raise ValueError("derived context representations must derive from authoritative original")

        for unit in self.semantic_units:
            if unit.representation_ref not in reps:
                raise ValueError("semantic unit representation_ref must resolve")
            for graph_ref in unit.context_graph_refs:
                known_graph_refs = {x.node_id for x in self.context_graph.nodes} | {x.thread_id for x in self.context_graph.threads}
                if graph_ref not in known_graph_refs:
                    raise ValueError("semantic unit context_graph_ref must resolve")

        for divergence in self.divergences:
            if divergence.source_unit_ref not in units or divergence.target_unit_ref not in units:
                raise ValueError("divergence unit refs must resolve")
            if divergence.provenance_ref not in provenances:
                raise ValueError("divergence provenance_ref must resolve")

        for alignment in self.alignments:
            if alignment.source_unit_ref not in units or alignment.target_unit_ref not in units:
                raise ValueError("alignment unit refs must resolve")
            srep = reps[units[alignment.source_unit_ref].representation_ref]
            trep = reps[units[alignment.target_unit_ref].representation_ref]
            if srep.language_ref == trep.language_ref:
                raise ValueError("multilingual context alignment must cross language identities")
            if srep.role != ContextRepresentationRole.original:
                raise ValueError("reference v4.8 alignments must be directed from authoritative original")
            if any(ref not in divergences for ref in alignment.divergence_refs):
                raise ValueError("alignment divergence refs must resolve")
            if alignment.provenance_ref not in provenances:
                raise ValueError("alignment provenance_ref must resolve")

        graph_threads = {x.thread_id for x in self.context_graph.threads}
        for projection in self.graph_projections:
            if projection.semantic_unit_ref not in units:
                raise ValueError("graph projection semantic_unit_ref must resolve")
            if projection.context_graph_thread_ref not in graph_threads:
                raise ValueError("graph projection thread ref must resolve")
            if projection.provenance_ref not in provenances:
                raise ValueError("graph projection provenance_ref must resolve")

        local_subjects = set(reps) | set(units) | set(alignments) | set(divergences) | set(projections) | set(interpretations) | {x.snapshot_id for x in self.snapshots}
        for provenance in self.provenance_records:
            if any(ref not in local_subjects for ref in provenance.subject_refs):
                raise ValueError("provenance subject ref must resolve to v4.8 object")

        predecessor_interpretations = {x.interpretation_id for x in self.context_graph.interpretations}
        for interpretation in self.interpretations:
            if any(ref not in predecessor_interpretations for ref in interpretation.predecessor_context_graph_interpretation_refs):
                raise ValueError("predecessor context graph interpretation ref must resolve")
            if any(ref not in reps for ref in interpretation.representation_refs):
                raise ValueError("interpretation representation refs must resolve")
            if any(ref not in units for ref in interpretation.semantic_unit_refs):
                raise ValueError("interpretation semantic unit refs must resolve")
            if any(ref not in alignments for ref in interpretation.alignment_refs):
                raise ValueError("interpretation alignment refs must resolve")
            if any(ref not in divergences for ref in interpretation.divergence_refs):
                raise ValueError("interpretation divergence refs must resolve")
            if any(ref not in projections for ref in interpretation.projection_refs):
                raise ValueError("interpretation projection refs must resolve")
            if interpretation.provenance_ref not in provenances:
                raise ValueError("interpretation provenance_ref must resolve")

        pred_fp = self.context_graph.fingerprint()
        exch_fp = self.cross_lingual_exchange.fingerprint()
        for snapshot in self.snapshots:
            if snapshot.predecessor_fingerprint_sha256 != pred_fp:
                raise ValueError("snapshot predecessor fingerprint must match embedded v4.7 graph")
            if snapshot.cross_lingual_exchange_fingerprint_sha256 != exch_fp:
                raise ValueError("snapshot cross-lingual exchange fingerprint must match embedded v3.69 contract")
            if any(ref not in interpretations for ref in snapshot.interpretation_refs):
                raise ValueError("snapshot interpretation refs must resolve")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


@lru_cache(maxsize=1)
def reference_multilingual_context_semantic_alignment_bundle() -> MultilingualContextSemanticAlignmentBundle:
    graph = reference_cross_document_context_graph_bundle()
    exchange = reference_cross_lingual_semantic_exchange_bundle()

    original_text = "该提案可能降低成本。治理需要问责。"
    english_text = "The proposal may reduce costs. Governance requires accountability."
    spanish_text = "La propuesta podría reducir los costos. La gobernanza requiere rendición de cuentas."

    prov_rep = "prov:multilingual-context:representations:v1"
    prov_align = "prov:multilingual-context:alignments:v1"
    prov_div = "prov:multilingual-context:divergence:v1"
    prov_projection = "prov:multilingual-context:projection:v1"
    prov_interpretation = "prov:multilingual-context:interpretation:v1"

    reps = [
        ContextLanguageRepresentation(
            representation_id="context-representation:zh:original:v1",
            role=ContextRepresentationRole.original,
            language_ref="language:zh",
            script_ref="script:Hani",
            source_ref="source:multilingual-context:synthetic-policy:v1",
            content=original_text,
            content_sha256=_sha256_text(original_text),
            provenance_ref=prov_rep,
            original_language_is_authoritative=True,
            metadata={"synthetic_reference": True, "analysis_order": 1},
        ),
        ContextLanguageRepresentation(
            representation_id="context-representation:en:derived:v1",
            role=ContextRepresentationRole.translation,
            language_ref="language:en",
            script_ref="script:Latn",
            source_ref="source:multilingual-context:synthetic-policy:v1",
            content=english_text,
            content_sha256=_sha256_text(english_text),
            derived_from_representation_ref="context-representation:zh:original:v1",
            provenance_ref=prov_rep,
            original_language_is_authoritative=False,
            metadata={"synthetic_reference": True, "analysis_order": 2},
        ),
        ContextLanguageRepresentation(
            representation_id="context-representation:es:derived:v1",
            role=ContextRepresentationRole.translation,
            language_ref="language:es",
            script_ref="script:Latn",
            source_ref="source:multilingual-context:synthetic-policy:v1",
            content=spanish_text,
            content_sha256=_sha256_text(spanish_text),
            derived_from_representation_ref="context-representation:zh:original:v1",
            provenance_ref=prov_rep,
            original_language_is_authoritative=False,
            metadata={"synthetic_reference": True, "analysis_order": 3},
        ),
    ]

    units = [
        ContextSemanticUnit(unit_id="context-unit:zh:proposal-cost:v1", representation_ref=reps[0].representation_id, unit_kind=ContextUnitKind.proposition, sequence=0, char_start=0, char_end=10, surface_text="该提案可能降低成本。", semantic_summary="A proposal is presented as possibly lowering costs.", modality="possibility", epistemic_status="source-proposition", context_graph_refs=["thread:policy-topic-continuity:candidate"], metadata={"original_language_unit": True}),
        ContextSemanticUnit(unit_id="context-unit:zh:governance:v1", representation_ref=reps[0].representation_id, unit_kind=ContextUnitKind.contextual_concept, sequence=1, char_start=10, char_end=len(original_text), surface_text="治理需要问责。", semantic_summary="治理 is presented in a context linking governance/order with accountability.", context_graph_refs=[], metadata={"original_language_unit": True, "context_sensitive_term": "治理"}),
        ContextSemanticUnit(unit_id="context-unit:en:proposal-cost:v1", representation_ref=reps[1].representation_id, unit_kind=ContextUnitKind.proposition, sequence=0, char_start=0, char_end=30, surface_text="The proposal may reduce costs.", semantic_summary="A proposal is presented as possibly lowering costs.", modality="possibility", epistemic_status="derived-translation", context_graph_refs=["thread:policy-topic-continuity:candidate"]),
        ContextSemanticUnit(unit_id="context-unit:en:governance:v1", representation_ref=reps[1].representation_id, unit_kind=ContextUnitKind.contextual_concept, sequence=1, char_start=31, char_end=len(english_text), surface_text="Governance requires accountability.", semantic_summary="Governance is rendered as requiring accountability.", context_graph_refs=[], metadata={"translation_term": "governance"}),
        ContextSemanticUnit(unit_id="context-unit:es:proposal-cost:v1", representation_ref=reps[2].representation_id, unit_kind=ContextUnitKind.proposition, sequence=0, char_start=0, char_end=39, surface_text="La propuesta podría reducir los costos.", semantic_summary="A proposal is presented as possibly lowering costs.", modality="possibility", epistemic_status="derived-translation", context_graph_refs=["thread:policy-topic-continuity:candidate"]),
        ContextSemanticUnit(unit_id="context-unit:es:governance:v1", representation_ref=reps[2].representation_id, unit_kind=ContextUnitKind.contextual_concept, sequence=1, char_start=40, char_end=len(spanish_text), surface_text="La gobernanza requiere rendición de cuentas.", semantic_summary="Gobernanza is rendered as requiring accountability.", context_graph_refs=[], metadata={"translation_term": "gobernanza"}),
    ]

    divergences = [
        SemanticDivergenceRecord(
            divergence_id="divergence:zh-en:governance:v1",
            source_unit_ref="context-unit:zh:governance:v1",
            target_unit_ref="context-unit:en:governance:v1",
            dimensions=[DivergenceDimension.semantic, DivergenceDimension.cultural],
            description="治理 and governance overlap in this synthetic context but are not treated as universally interchangeable concepts across institutional, historical, or political settings.",
            severity=0.42,
            state=AlignmentReviewState.reviewed,
            provenance_ref=prov_div,
            reviewer_ref="reviewer:multilingual-context:v1",
        ),
        SemanticDivergenceRecord(
            divergence_id="divergence:zh-es:governance:v1",
            source_unit_ref="context-unit:zh:governance:v1",
            target_unit_ref="context-unit:es:governance:v1",
            dimensions=[DivergenceDimension.semantic, DivergenceDimension.cultural],
            description="治理 and gobernanza are contextually related here, while culturally and institutionally conditioned differences remain unresolved.",
            severity=0.46,
            state=AlignmentReviewState.candidate,
            provenance_ref=prov_div,
        ),
    ]

    alignments = [
        MultilingualContextAlignment(alignment_id="context-alignment:zh-en:proposal-cost:v1", source_unit_ref="context-unit:zh:proposal-cost:v1", target_unit_ref="context-unit:en:proposal-cost:v1", relation=ContextAlignmentRelation.translation_correspondence, confidence=0.95, state=AlignmentReviewState.reviewed, aligned_dimensions=["proposition", "modality", "topic"], provenance_ref=prov_align, reviewer_ref="reviewer:multilingual-context:v1"),
        MultilingualContextAlignment(alignment_id="context-alignment:zh-es:proposal-cost:v1", source_unit_ref="context-unit:zh:proposal-cost:v1", target_unit_ref="context-unit:es:proposal-cost:v1", relation=ContextAlignmentRelation.near_equivalent, confidence=0.90, state=AlignmentReviewState.candidate, aligned_dimensions=["proposition", "modality", "topic"], provenance_ref=prov_align),
        MultilingualContextAlignment(alignment_id="context-alignment:zh-en:governance:v1", source_unit_ref="context-unit:zh:governance:v1", target_unit_ref="context-unit:en:governance:v1", relation=ContextAlignmentRelation.culturally_conditioned, confidence=0.72, state=AlignmentReviewState.reviewed, aligned_dimensions=["contextual-concept", "accountability-relation"], divergence_refs=["divergence:zh-en:governance:v1"], provenance_ref=prov_align, reviewer_ref="reviewer:multilingual-context:v1"),
        MultilingualContextAlignment(alignment_id="context-alignment:zh-es:governance:v1", source_unit_ref="context-unit:zh:governance:v1", target_unit_ref="context-unit:es:governance:v1", relation=ContextAlignmentRelation.culturally_conditioned, confidence=0.68, state=AlignmentReviewState.candidate, aligned_dimensions=["contextual-concept", "accountability-relation"], divergence_refs=["divergence:zh-es:governance:v1"], provenance_ref=prov_align),
    ]

    projections = [
        ContextGraphProjectionBinding(
            projection_id="projection:zh-proposal-to-v47-topic-thread:v1",
            semantic_unit_ref="context-unit:zh:proposal-cost:v1",
            context_graph_thread_ref="thread:policy-topic-continuity:candidate",
            relation_label="candidate multilingual policy-topic continuity",
            confidence=0.60,
            state=AlignmentReviewState.candidate,
            provenance_ref=prov_projection,
        )
    ]

    interpretation = MultilingualContextInterpretation(
        interpretation_id="multilingual-context-interpretation:reference:v1",
        predecessor_context_graph_interpretation_refs=[graph.interpretations[0].interpretation_id],
        representation_refs=[x.representation_id for x in reps],
        semantic_unit_refs=[x.unit_id for x in units],
        alignment_refs=[x.alignment_id for x in alignments],
        divergence_refs=[x.divergence_id for x in divergences],
        projection_refs=[x.projection_id for x in projections],
        unresolved_refs=["universal-equivalence:治理-governance-gobernanza", "same-policy-object:v48-v47"],
        state=AlignmentReviewState.reviewed,
        confidence=0.91,
        reviewer_ref="reviewer:multilingual-context:v1",
        provenance_ref=prov_interpretation,
    )

    snapshot_material = {
        "predecessor": graph.fingerprint(),
        "exchange": exchange.fingerprint(),
        "representations": [x.fingerprint() for x in reps],
        "units": [x.fingerprint() for x in units],
        "alignments": [x.fingerprint() for x in alignments],
        "divergences": [x.fingerprint() for x in divergences],
        "projections": [x.fingerprint() for x in projections],
        "interpretation": interpretation.fingerprint(),
    }
    snapshot = MultilingualContextSnapshot(
        snapshot_id="snapshot:multilingual-context-alignment:reference:v1",
        predecessor_fingerprint_sha256=graph.fingerprint(),
        cross_lingual_exchange_fingerprint_sha256=exchange.fingerprint(),
        interpretation_refs=[interpretation.interpretation_id],
        deterministic_alignment_fingerprint_sha256=canonical_sha256(snapshot_material),
    )

    provenances = [
        MultilingualContextProvenanceRecord(provenance_id=prov_rep, subject_refs=[x.representation_id for x in reps], method=InterpretationMethod.manual, produced_by_ref="curator:multilingual-context:v1", source_refs=["source:multilingual-context:synthetic-policy:v1"], reviewer_ref="reviewer:multilingual-context:v1", transformation_notes=["Chinese source is authoritative; English and Spanish are derived reference translations and do not replace it."]),
        MultilingualContextProvenanceRecord(provenance_id=prov_align, subject_refs=[x.alignment_id for x in alignments], method=InterpretationMethod.manual, produced_by_ref="curator:multilingual-context:v1", source_refs=[x.representation_id for x in reps], reviewer_ref="reviewer:multilingual-context:v1", transformation_notes=["Context alignment is directional and preserves modality, discourse, pragmatic, and cultural qualifications rather than flattening to lexical similarity."]),
        MultilingualContextProvenanceRecord(provenance_id=prov_div, subject_refs=[x.divergence_id for x in divergences], method=InterpretationMethod.manual, produced_by_ref="curator:multilingual-context:v1", source_refs=["context-unit:zh:governance:v1", "context-unit:en:governance:v1", "context-unit:es:governance:v1"], reviewer_ref="reviewer:multilingual-context:v1", transformation_notes=["Culturally conditioned differences are recorded as first-class semantic divergence, not discarded as translation noise."]),
        MultilingualContextProvenanceRecord(provenance_id=prov_projection, subject_refs=[x.projection_id for x in projections], method=InterpretationMethod.manual, produced_by_ref="curator:multilingual-context:v1", source_refs=[graph.threads[1].thread_id], transformation_notes=["Projection links multilingual context to v4.7 topic continuity only as a candidate contextual hypothesis and performs no graph mutation."]),
        MultilingualContextProvenanceRecord(provenance_id=prov_interpretation, subject_refs=[interpretation.interpretation_id, snapshot.snapshot_id], method=InterpretationMethod.manual, produced_by_ref="reviewer:multilingual-context:v1", source_refs=[graph.fingerprint(), exchange.fingerprint()], reviewer_ref="reviewer:multilingual-context:v1", transformation_notes=["Reviewed packaging certifies an alignment interpretation; it does not establish universal equivalence, source authority, evidence validity, or world truth."]),
    ]

    return MultilingualContextSemanticAlignmentBundle(
        extends_contracts=list(EXTENDS_CONTRACTS),
        policy=MultilingualContextPolicy(policy_id="multilingual-context-semantic-alignment-policy:v4.8"),
        context_graph=graph,
        cross_lingual_exchange=exchange,
        representations=reps,
        semantic_units=units,
        alignments=alignments,
        divergences=divergences,
        graph_projections=projections,
        provenance_records=provenances,
        interpretations=[interpretation],
        snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    bundle = reference_multilingual_context_semantic_alignment_bundle()
    original = [x for x in bundle.representations if x.role == ContextRepresentationRole.original]
    derived = [x for x in bundle.representations if x.role != ContextRepresentationRole.original]
    reviewed = [x for x in bundle.alignments if x.state == AlignmentReviewState.reviewed]
    candidate = [x for x in bundle.alignments if x.state == AlignmentReviewState.candidate]
    culturally_conditioned = [x for x in bundle.alignments if x.relation == ContextAlignmentRelation.culturally_conditioned]
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "extends_contracts": list(EXTENDS_CONTRACTS),
        "identity": {"product": "Sustainable Catalyst Platform Core", "build": "Multilingual Context & Semantic Alignment", "major_api": "v4"},
        "principles": {
            "original_language_is_analyzed_first": True,
            "translation_is_derived_representation": True,
            "contextual_meaning_is_aligned_not_flattened": True,
            "semantic_divergence_is_first_class": True,
            "cultural_and_historical_conditioning_may_remain_unresolved": True,
            "multiple_translation_interpretations_may_coexist": True,
            "cross_language_alignment_preserves_provenance": True,
            "predecessor_context_graph_remains_immutable": True,
        },
        "boundaries": {
            "translation_replaces_original_source": False,
            "semantic_similarity_establishes_equivalence": False,
            "translation_correspondence_establishes_concept_identity": False,
            "culturally_conditioned_alignment_establishes_universal_equivalence": False,
            "reviewed_alignment_establishes_claim_truth": False,
            "multilingual_projection_mutates_v470_context_graph": False,
            "cross_language_context_link_establishes_canonical_identity": False,
            "identity_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
            "knowledge_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "extends_v470_cross_document_context_graph": True,
            "integrates_v3650_through_v3690_language_linguistics_core": True,
            "integrates_v410_through_v470_contextual_semantics": True,
            "prepares_v490_contextual_semantic_evaluation": True,
            "prepares_v4100_unified_contextual_intelligence_runtime": True,
        },
        "reference": {
            "predecessor_release": bundle.context_graph.release,
            "predecessor_fingerprint_sha256": bundle.context_graph.fingerprint(),
            "cross_lingual_exchange_fingerprint_sha256": bundle.cross_lingual_exchange.fingerprint(),
            "representations": len(bundle.representations),
            "original_representations": len(original),
            "derived_representations": len(derived),
            "languages": sorted({x.language_ref for x in bundle.representations}),
            "semantic_units": len(bundle.semantic_units),
            "alignments": len(bundle.alignments),
            "reviewed_alignments": len(reviewed),
            "candidate_alignments": len(candidate),
            "culturally_conditioned_alignments": len(culturally_conditioned),
            "divergences": len(bundle.divergences),
            "context_graph_projections": len(bundle.graph_projections),
            "context_graph_mutations_created": 0,
            "interpretations": len(bundle.interpretations),
            "snapshots": len(bundle.snapshots),
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
        "database_migration": "none",
    }
