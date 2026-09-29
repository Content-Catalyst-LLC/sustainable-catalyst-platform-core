from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .historical_language_variant import (
    HistoricalLanguageVariantBundle,
    reference_historical_language_variant_bundle,
)
from .translation_alignment import (
    TranslationTransliterationAlignmentBundle,
    reference_translation_alignment_bundle,
)

CORE_RELEASE = "3.69.0"
CONTRACT_VERSION = "sc.core.cross-lingual-semantic-linguistic-exchange.v1"


class SemanticRelationKind(str, Enum):
    exact_equivalent = "exact-equivalent"
    near_equivalent = "near-equivalent"
    broader = "broader"
    narrower = "narrower"
    related = "related"
    lexical_correspondence = "lexical-correspondence"
    translation_correspondence = "translation-correspondence"
    transliteration_correspondence = "transliteration-correspondence"
    historical_variant_correspondence = "historical-variant-correspondence"
    entity_name_correspondence = "entity-name-correspondence"


class ExchangeAssertionState(str, Enum):
    candidate = "candidate"
    reviewed = "reviewed"
    accepted = "accepted"
    rejected = "rejected"
    disputed = "disputed"


class ExchangeMethod(str, Enum):
    manual = "manual"
    scholarly = "scholarly"
    imported = "imported"
    rule_based = "rule-based"
    model_assisted = "model-assisted"
    graph_assisted = "graph-assisted"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class SemanticConceptIdentity(BaseModel):
    concept_id: str = Field(min_length=2, max_length=500)
    canonical_label: str = Field(min_length=1, max_length=500)
    definition: str | None = Field(default=None, max_length=5000)
    domain_refs: list[str] = Field(default_factory=list)
    external_concept_refs: list[str] = Field(default_factory=list)
    concept_identity_is_language_neutral: Literal[True] = True
    concept_is_not_source_text: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_concept(self):
        _unique(self.domain_refs, "concept domain_refs")
        _unique(self.external_concept_refs, "external_concept_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class LinguisticSemanticAnchor(BaseModel):
    anchor_id: str = Field(min_length=2, max_length=500)
    concept_ref: str = Field(min_length=2, max_length=500)
    language_ref: str = Field(min_length=2, max_length=500)
    script_ref: str | None = Field(default=None, max_length=500)
    surface_form: str = Field(min_length=1, max_length=4000)
    source_object_ref: str = Field(min_length=2, max_length=1000)
    source_object_kind: str = Field(min_length=2, max_length=200)
    text_source_ref: str | None = Field(default=None, max_length=500)
    text_unit_ref: str | None = Field(default=None, max_length=500)
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, gt=0)
    historical_language_stage_ref: str | None = Field(default=None, max_length=500)
    orthography_profile_ref: str | None = Field(default=None, max_length=500)
    translation_representation_ref: str | None = Field(default=None, max_length=500)
    anchor_is_evidence_of_concept_identity: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_anchor(self):
        if (self.char_start is None) != (self.char_end is None):
            raise ValueError("char_start and char_end must be supplied together")
        if self.char_start is not None and self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SemanticExchangeProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=2, max_length=500)
    assertion_ref: str = Field(min_length=2, max_length=500)
    method: ExchangeMethod
    produced_by_ref: str = Field(min_length=2, max_length=1000)
    model_ref: str | None = Field(default=None, max_length=1000)
    model_version: str | None = Field(default=None, max_length=240)
    tool_ref: str | None = Field(default=None, max_length=1000)
    tool_version: str | None = Field(default=None, max_length=240)
    source_refs: list[str] = Field(default_factory=list)
    created_at: str | None = Field(default=None, max_length=80)
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    review_note: str | None = Field(default=None, max_length=5000)
    machine_or_graph_output_is_advisory: Literal[True] = True
    provenance_does_not_establish_semantic_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_provenance(self):
        if self.method in {ExchangeMethod.model_assisted, ExchangeMethod.graph_assisted} and not self.model_ref:
            raise ValueError("model/graph-assisted exchange provenance requires model_ref")
        if self.model_version and not self.model_ref:
            raise ValueError("model_version requires model_ref")
        if self.tool_version and not self.tool_ref:
            raise ValueError("tool_version requires tool_ref")
        _unique(self.source_refs, "semantic exchange source_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossLingualSemanticAssertion(BaseModel):
    assertion_id: str = Field(min_length=2, max_length=500)
    source_anchor_ref: str = Field(min_length=2, max_length=500)
    target_anchor_ref: str = Field(min_length=2, max_length=500)
    relation_kind: SemanticRelationKind
    provenance_ref: str = Field(min_length=2, max_length=500)
    assertion_state: ExchangeAssertionState = ExchangeAssertionState.candidate
    semantic_similarity_score: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    supporting_evidence_refs: list[str] = Field(default_factory=list)
    contradicting_evidence_refs: list[str] = Field(default_factory=list)
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    machine_similarity_is_not_equivalence: Literal[True] = True
    assertion_is_not_graph_fact: Literal[True] = True
    assertion_is_not_entity_identity: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_assertion(self):
        if self.source_anchor_ref == self.target_anchor_ref:
            raise ValueError("cross-lingual assertion requires distinct source and target anchors")
        if self.assertion_state != ExchangeAssertionState.candidate and not self.reviewer_ref:
            raise ValueError("reviewed semantic assertion requires reviewer_ref")
        _unique(self.supporting_evidence_refs, "supporting_evidence_refs")
        _unique(self.contradicting_evidence_refs, "contradicting_evidence_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossLingualConceptSet(BaseModel):
    concept_set_id: str = Field(min_length=2, max_length=500)
    concept_ref: str = Field(min_length=2, max_length=500)
    anchor_refs: list[str] = Field(min_length=2)
    assertion_refs: list[str] = Field(default_factory=list)
    language_refs: list[str] = Field(min_length=2)
    unresolved_disagreement_preserved: Literal[True] = True
    preferred_language_form_selected_by_core: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_set(self):
        _unique(self.anchor_refs, "concept-set anchor_refs")
        _unique(self.assertion_refs, "concept-set assertion_refs")
        _unique(self.language_refs, "concept-set language_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossLingualSemanticExchangeBundle(BaseModel):
    translation_bundle: TranslationTransliterationAlignmentBundle
    historical_bundle: HistoricalLanguageVariantBundle
    concepts: list[SemanticConceptIdentity] = Field(min_length=1)
    anchors: list[LinguisticSemanticAnchor] = Field(min_length=2)
    provenance_records: list[SemanticExchangeProvenanceRecord] = Field(min_length=1)
    assertions: list[CrossLingualSemanticAssertion] = Field(min_length=1)
    concept_sets: list[CrossLingualConceptSet] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        for values, label in (
            ([x.concept_id for x in self.concepts], "concept ids"),
            ([x.anchor_id for x in self.anchors], "anchor ids"),
            ([x.provenance_id for x in self.provenance_records], "exchange provenance ids"),
            ([x.assertion_id for x in self.assertions], "semantic assertion ids"),
            ([x.concept_set_id for x in self.concept_sets], "concept-set ids"),
        ):
            _unique(values, label)

        concepts = {x.concept_id for x in self.concepts}
        anchors = {x.anchor_id: x for x in self.anchors}
        provenances = {x.provenance_id: x for x in self.provenance_records}
        assertions = {x.assertion_id: x for x in self.assertions}

        translation_representation_ids = {x.representation_id for x in self.translation_bundle.representations}
        historical_variant_ids = {x.variant_id for x in self.historical_bundle.variants}
        historical_normalization_ids = {x.normalization_id for x in self.historical_bundle.normalizations}
        translation_token_ids = {x.token_id for x in self.translation_bundle.annotation_bundle.tokens}

        known_source_objects = translation_representation_ids | historical_variant_ids | historical_normalization_ids | translation_token_ids

        for anchor in self.anchors:
            if anchor.concept_ref not in concepts:
                raise ValueError("anchor concept_ref must resolve")
            if anchor.source_object_ref not in known_source_objects:
                raise ValueError("anchor source_object_ref must resolve to governed linguistic object")
            if anchor.translation_representation_ref and anchor.translation_representation_ref not in translation_representation_ids:
                raise ValueError("translation_representation_ref must resolve")

        for provenance in self.provenance_records:
            if provenance.assertion_ref not in assertions:
                raise ValueError("exchange provenance assertion_ref must resolve")

        for assertion in self.assertions:
            if assertion.source_anchor_ref not in anchors or assertion.target_anchor_ref not in anchors:
                raise ValueError("semantic assertion anchors must resolve")
            if assertion.provenance_ref not in provenances:
                raise ValueError("semantic assertion provenance_ref must resolve")
            if anchors[assertion.source_anchor_ref].language_ref == anchors[assertion.target_anchor_ref].language_ref:
                raise ValueError("cross-lingual semantic assertion must cross language identities")

        for concept_set in self.concept_sets:
            if concept_set.concept_ref not in concepts:
                raise ValueError("concept-set concept_ref must resolve")
            if any(ref not in anchors for ref in concept_set.anchor_refs):
                raise ValueError("concept-set anchor_refs must resolve")
            if any(ref not in assertions for ref in concept_set.assertion_refs):
                raise ValueError("concept-set assertion_refs must resolve")
            actual_languages = {anchors[ref].language_ref for ref in concept_set.anchor_refs}
            if set(concept_set.language_refs) != actual_languages:
                raise ValueError("concept-set language_refs must match anchor languages")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_cross_lingual_semantic_exchange_bundle() -> CrossLingualSemanticExchangeBundle:
    translation_bundle = reference_translation_alignment_bundle()
    historical_bundle = reference_historical_language_variant_bundle()

    token_by_surface = {x.surface: x for x in translation_bundle.annotation_bundle.tokens}
    water_en = token_by_surface["Water"]
    water_zh = token_by_surface["水"]
    es_translation = next(x for x in translation_bundle.representations if x.representation_id == "translation:reference:es:a")

    concept = SemanticConceptIdentity(
        concept_id="concept:reference:water",
        canonical_label="water",
        definition="Synthetic reference concept used only to demonstrate cross-lingual exchange contracts.",
        domain_refs=["domain:reference:environment"],
        metadata={"synthetic_reference": True, "scientific_claim": False},
    )

    anchors = [
        LinguisticSemanticAnchor(
            anchor_id="anchor:reference:water:en",
            concept_ref=concept.concept_id,
            language_ref="language:en",
            script_ref="script:Latn",
            surface_form="Water",
            source_object_ref=water_en.token_id,
            source_object_kind="TokenRecord",
            text_source_ref=translation_bundle.annotation_bundle.text_bundle.text_sources[0].text_source_id,
            text_unit_ref=translation_bundle.annotation_bundle.text_bundle.text_units[0].text_unit_id,
            char_start=water_en.char_start,
            char_end=water_en.char_end,
        ),
        LinguisticSemanticAnchor(
            anchor_id="anchor:reference:water:zh",
            concept_ref=concept.concept_id,
            language_ref="language:zh",
            script_ref="script:Hani",
            surface_form="水",
            source_object_ref=water_zh.token_id,
            source_object_kind="TokenRecord",
            text_source_ref=translation_bundle.annotation_bundle.text_bundle.text_sources[0].text_source_id,
            text_unit_ref=translation_bundle.annotation_bundle.text_bundle.text_units[0].text_unit_id,
            char_start=water_zh.char_start,
            char_end=water_zh.char_end,
        ),
        LinguisticSemanticAnchor(
            anchor_id="anchor:reference:water:es",
            concept_ref=concept.concept_id,
            language_ref="language:es",
            script_ref="script:Latn",
            surface_form="Agua",
            source_object_ref=es_translation.representation_id,
            source_object_kind="DerivedTextRepresentation",
            translation_representation_ref=es_translation.representation_id,
        ),
    ]

    assertions = [
        CrossLingualSemanticAssertion(
            assertion_id="semantic-assertion:reference:water:en-zh",
            source_anchor_ref=anchors[0].anchor_id,
            target_anchor_ref=anchors[1].anchor_id,
            relation_kind=SemanticRelationKind.near_equivalent,
            provenance_ref="exchange-provenance:reference:water:en-zh",
            assertion_state=ExchangeAssertionState.reviewed,
            semantic_similarity_score=0.96,
            confidence=0.9,
            reviewer_ref="actor:sustainable-catalyst-reference-reviewer",
            supporting_evidence_refs=["alignment:zh-latn:han"],
            metadata={"synthetic_reference": True, "does_not_establish_lexical_universality": True},
        ),
        CrossLingualSemanticAssertion(
            assertion_id="semantic-assertion:reference:water:en-es",
            source_anchor_ref=anchors[0].anchor_id,
            target_anchor_ref=anchors[2].anchor_id,
            relation_kind=SemanticRelationKind.translation_correspondence,
            provenance_ref="exchange-provenance:reference:water:en-es",
            assertion_state=ExchangeAssertionState.candidate,
            semantic_similarity_score=0.94,
            confidence=0.86,
            supporting_evidence_refs=["alignment:es-a:water"],
            metadata={"synthetic_reference": True},
        ),
    ]

    provenance = [
        SemanticExchangeProvenanceRecord(
            provenance_id="exchange-provenance:reference:water:en-zh",
            assertion_ref=assertions[0].assertion_id,
            method=ExchangeMethod.manual,
            produced_by_ref="actor:sustainable-catalyst-reference-curator",
            reviewer_ref="actor:sustainable-catalyst-reference-reviewer",
            source_refs=[water_en.token_id, water_zh.token_id],
            created_at="2026-09-29T01:00:00-05:00",
        ),
        SemanticExchangeProvenanceRecord(
            provenance_id="exchange-provenance:reference:water:en-es",
            assertion_ref=assertions[1].assertion_id,
            method=ExchangeMethod.model_assisted,
            produced_by_ref="run:reference-cross-lingual-model",
            model_ref="model:reference-cross-lingual-encoder",
            model_version="1.0",
            source_refs=[water_en.token_id, es_translation.representation_id, "alignment:es-a:water"],
            created_at="2026-09-29T01:01:00-05:00",
        ),
    ]

    concept_set = CrossLingualConceptSet(
        concept_set_id="concept-set:reference:water",
        concept_ref=concept.concept_id,
        anchor_refs=[x.anchor_id for x in anchors],
        assertion_refs=[x.assertion_id for x in assertions],
        language_refs=["language:en", "language:zh", "language:es"],
        metadata={"synthetic_reference": True, "core_ranking": "none"},
    )

    return CrossLingualSemanticExchangeBundle(
        translation_bundle=translation_bundle,
        historical_bundle=historical_bundle,
        concepts=[concept],
        anchors=anchors,
        provenance_records=provenance,
        assertions=assertions,
        concept_sets=[concept_set],
        metadata={
            "purpose": "Platform Core v3.69 cross-lingual semantic and linguistic exchange reference",
            "semantic_similarity_is_not_equivalence": True,
            "cross_lingual_assertion_is_not_graph_fact": True,
            "prepares_graph_machine_learning_foundation": "v3.70.0",
        },
    )


def contract_document() -> dict[str, Any]:
    ref = reference_cross_lingual_semantic_exchange_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contracts": [
            "sc.core.multilingual-text-language-object.v1",
            "sc.core.linguistic-annotation-provenance.v1",
            "sc.core.translation-transliteration-alignment.v1",
            "sc.core.historical-language-script-orthography-variant.v1",
        ],
        "object_types": [
            "SemanticConceptIdentity",
            "LinguisticSemanticAnchor",
            "SemanticExchangeProvenanceRecord",
            "CrossLingualSemanticAssertion",
            "CrossLingualConceptSet",
            "CrossLingualSemanticExchangeBundle",
        ],
        "principles": {
            "original_language_remains_canonical": True,
            "translation_remains_derived": True,
            "historical_attested_form_remains_preserved": True,
            "semantic_similarity_is_not_semantic_equivalence": True,
            "translation_correspondence_is_not_concept_identity": True,
            "entity_name_correspondence_is_not_entity_identity": True,
            "machine_cross_lingual_links_are_advisory": True,
            "cross_lingual_assertion_is_not_graph_fact": True,
            "unresolved_semantic_disagreement_is_preserved": True,
        },
        "capabilities": {
            "language_neutral_concept_identity": True,
            "language_specific_semantic_anchors": True,
            "cross_language_semantic_assertions": True,
            "translation_aware_semantic_exchange": True,
            "transliteration_aware_semantic_exchange": True,
            "historical_variant_aware_semantic_exchange": True,
            "semantic_similarity_scores_with_provenance": True,
            "supporting_and_contradicting_evidence_refs": True,
            "review_state_and_human_validation": True,
            "cross_lingual_concept_sets": True,
            "deterministic_object_fingerprints": True,
        },
        "roadmap_integration": {
            "completes_v3650_v3690_language_linguistics_core_block": True,
            "prepares_v3700_graph_machine_learning_foundation": True,
            "preserves_v3700_v3760_graph_neural_wave": True,
            "gnn_prediction_is_not_graph_fact": True,
            "predicted_relationship_requires_separate_validation_before_evidence_edge": True,
        },
        "boundaries": {
            "core_translates_or_transliterates_text": False,
            "core_computes_embeddings_or_similarity": False,
            "core_selects_authoritative_translation": False,
            "core_collapses_semantic_similarity_into_equivalence": False,
            "core_converts_semantic_assertion_into_graph_fact": False,
            "core_resolves_entity_identity_from_name_correspondence": False,
            "core_overwrites_original_or_historical_source_forms": False,
            "core_treats_model_cross_lingual_match_as_authoritative": False,
        },
        "reference": {
            "concept_count": len(ref.concepts),
            "anchor_count": len(ref.anchors),
            "assertion_count": len(ref.assertions),
            "concept_set_count": len(ref.concept_sets),
            "languages": ref.concept_sets[0].language_refs,
            "bundle_fingerprint_sha256": ref.fingerprint(),
            "reference_fixture_is_synthetic": True,
        },
    }
