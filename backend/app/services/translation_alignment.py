from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .linguistic_annotation import (
    LinguisticAnnotationBundle,
    reference_linguistic_annotation_bundle,
)
from .multilingual_text_language import (
    LanguageIdentity,
    MultilingualTextLanguageBundle,
    _content_sha256,
)

CORE_RELEASE = "3.67.0"
CONTRACT_VERSION = "sc.core.translation-transliteration-alignment.v1"


class DerivedRepresentationKind(str, Enum):
    translation = "translation"
    transliteration = "transliteration"


class DerivationMethod(str, Enum):
    manual = "manual"
    editorial = "editorial"
    imported = "imported"
    model_assisted = "model-assisted"
    pipeline = "pipeline"


class DerivationReviewState(str, Enum):
    unreviewed = "unreviewed"
    reviewed = "reviewed"
    accepted = "accepted"
    rejected = "rejected"
    disputed = "disputed"


class AlignmentKind(str, Enum):
    one_to_one = "one-to-one"
    one_to_many = "one-to-many"
    many_to_one = "many-to-one"
    many_to_many = "many-to-many"
    partial = "partial"
    omission = "omission"
    insertion = "insertion"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class DerivationProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=2, max_length=500)
    representation_ref: str = Field(min_length=2, max_length=500)
    source_text_ref: str = Field(min_length=2, max_length=500)
    source_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_annotation_bundle_fingerprint_sha256: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    method: DerivationMethod
    produced_by_ref: str = Field(min_length=2, max_length=1000)
    translator_ref: str | None = Field(default=None, max_length=1000)
    tool_ref: str | None = Field(default=None, max_length=1000)
    tool_version: str | None = Field(default=None, max_length=240)
    model_ref: str | None = Field(default=None, max_length=1000)
    model_version: str | None = Field(default=None, max_length=240)
    created_at: str | None = Field(default=None, max_length=80)
    review_state: DerivationReviewState = DerivationReviewState.unreviewed
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    review_note: str | None = Field(default=None, max_length=4000)
    machine_output_is_advisory: Literal[True] = True
    interpretation_is_authoritative: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_provenance(self):
        if self.method == DerivationMethod.model_assisted and not self.model_ref:
            raise ValueError("model-assisted derivation provenance requires model_ref")
        if self.model_version and not self.model_ref:
            raise ValueError("model_version requires model_ref")
        if self.tool_version and not self.tool_ref:
            raise ValueError("tool_version requires tool_ref")
        if self.review_state != DerivationReviewState.unreviewed and not self.reviewer_ref:
            raise ValueError("reviewed derivation provenance requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DerivedTextRepresentation(BaseModel):
    representation_id: str = Field(min_length=2, max_length=500)
    kind: DerivedRepresentationKind
    source_text_ref: str = Field(min_length=2, max_length=500)
    source_text_unit_ref: str = Field(min_length=2, max_length=500)
    target_language_ref: str = Field(min_length=2, max_length=500)
    target_script_ref: str = Field(min_length=2, max_length=500)
    content: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    provenance_ref: str = Field(min_length=2, max_length=500)
    transliteration_scheme: str | None = Field(default=None, max_length=500)
    derived_from_original: Literal[True] = True
    is_canonical_source: Literal[False] = False
    replaces_original: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_representation(self):
        if self.content_sha256 != _content_sha256(self.content):
            raise ValueError("content_sha256 must match UTF-8 derived content")
        if self.kind == DerivedRepresentationKind.transliteration and not self.transliteration_scheme:
            raise ValueError("transliteration representation requires transliteration_scheme")
        if self.kind == DerivedRepresentationKind.translation and self.transliteration_scheme:
            raise ValueError("translation representation cannot declare transliteration_scheme")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ParallelTextAlignmentRecord(BaseModel):
    alignment_id: str = Field(min_length=2, max_length=500)
    representation_ref: str = Field(min_length=2, max_length=500)
    source_text_unit_ref: str = Field(min_length=2, max_length=500)
    source_char_start: int = Field(ge=0)
    source_char_end: int = Field(gt=0)
    source_content: str = Field(min_length=1)
    source_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_char_start: int = Field(ge=0)
    target_char_end: int = Field(gt=0)
    target_content: str = Field(min_length=1)
    target_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    alignment_kind: AlignmentKind
    provenance_ref: str = Field(min_length=2, max_length=500)
    source_token_refs: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    machine_alignment_is_advisory: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_alignment(self):
        if self.source_char_end <= self.source_char_start:
            raise ValueError("source_char_end must be greater than source_char_start")
        if self.target_char_end <= self.target_char_start:
            raise ValueError("target_char_end must be greater than target_char_start")
        if self.source_content_sha256 != _content_sha256(self.source_content):
            raise ValueError("source_content_sha256 must match source_content")
        if self.target_content_sha256 != _content_sha256(self.target_content):
            raise ValueError("target_content_sha256 must match target_content")
        _unique(self.source_token_refs, "alignment source_token_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RepresentationVariantSet(BaseModel):
    variant_set_id: str = Field(min_length=2, max_length=500)
    source_text_unit_ref: str = Field(min_length=2, max_length=500)
    representation_refs: list[str] = Field(min_length=2)
    comparison_basis: str = Field(min_length=2, max_length=1000)
    disagreement_preserved: Literal[True] = True
    preferred_representation_selected_by_core: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_variant_set(self):
        _unique(self.representation_refs, "variant-set representation_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TranslationTransliterationAlignmentBundle(BaseModel):
    annotation_bundle: LinguisticAnnotationBundle
    provenance_records: list[DerivationProvenanceRecord] = Field(min_length=1)
    representations: list[DerivedTextRepresentation] = Field(min_length=1)
    alignments: list[ParallelTextAlignmentRecord] = Field(default_factory=list)
    variant_sets: list[RepresentationVariantSet] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        for values, label in (
            ([x.provenance_id for x in self.provenance_records], "derivation provenance ids"),
            ([x.representation_id for x in self.representations], "representation ids"),
            ([x.alignment_id for x in self.alignments], "alignment ids"),
            ([x.variant_set_id for x in self.variant_sets], "variant-set ids"),
        ):
            _unique(values, label)

        text_bundle = self.annotation_bundle.text_bundle
        source_map = {x.text_source_id: x for x in text_bundle.text_sources}
        unit_map = {x.text_unit_id: x for x in text_bundle.text_units}
        language_ids = {x.language_id for x in text_bundle.languages}
        script_ids = {x.script_id for x in text_bundle.scripts}
        provenance_map = {x.provenance_id: x for x in self.provenance_records}
        representation_map = {x.representation_id: x for x in self.representations}
        token_map = {x.token_id: x for x in self.annotation_bundle.tokens}
        annotation_fingerprint = self.annotation_bundle.fingerprint()

        for provenance in self.provenance_records:
            source = source_map.get(provenance.source_text_ref)
            if source is None:
                raise ValueError("derivation provenance source_text_ref must resolve")
            if provenance.source_content_sha256 != source.content_sha256:
                raise ValueError("derivation provenance source_content_sha256 must match canonical source")
            if (
                provenance.source_annotation_bundle_fingerprint_sha256 is not None
                and provenance.source_annotation_bundle_fingerprint_sha256 != annotation_fingerprint
            ):
                raise ValueError("derivation provenance annotation-bundle fingerprint must match")

        for representation in self.representations:
            source = source_map.get(representation.source_text_ref)
            if source is None:
                raise ValueError("representation source_text_ref must resolve")
            unit = unit_map.get(representation.source_text_unit_ref)
            if unit is None:
                raise ValueError("representation source_text_unit_ref must resolve")
            if unit.source_text_ref != representation.source_text_ref:
                raise ValueError("representation source unit must belong to source text")
            if representation.target_language_ref not in language_ids:
                raise ValueError("representation target_language_ref must resolve")
            if representation.target_script_ref not in script_ids:
                raise ValueError("representation target_script_ref must resolve")
            provenance = provenance_map.get(representation.provenance_ref)
            if provenance is None:
                raise ValueError("representation provenance_ref must resolve")
            if provenance.representation_ref != representation.representation_id:
                raise ValueError("representation provenance must point back to representation")
            if provenance.source_text_ref != representation.source_text_ref:
                raise ValueError("representation and provenance must reference the same source text")
            if representation.kind == DerivedRepresentationKind.transliteration:
                source_languages = {unit.language_ref}
                source_languages.update(
                    x.language_ref for x in text_bundle.language_spans if x.text_unit_ref == unit.text_unit_id
                )
                if representation.target_language_ref not in source_languages:
                    raise ValueError("transliteration must preserve a source-language identity")

        for alignment in self.alignments:
            representation = representation_map.get(alignment.representation_ref)
            if representation is None:
                raise ValueError("alignment representation_ref must resolve")
            unit = unit_map.get(alignment.source_text_unit_ref)
            if unit is None:
                raise ValueError("alignment source_text_unit_ref must resolve")
            if unit.text_unit_id != representation.source_text_unit_ref:
                raise ValueError("alignment source unit must match representation source unit")
            provenance = provenance_map.get(alignment.provenance_ref)
            if provenance is None:
                raise ValueError("alignment provenance_ref must resolve")
            if provenance.representation_ref != representation.representation_id:
                raise ValueError("alignment provenance must belong to its representation")
            if alignment.source_char_end > len(unit.content):
                raise ValueError("alignment source range exceeds canonical text unit")
            if unit.content[alignment.source_char_start:alignment.source_char_end] != alignment.source_content:
                raise ValueError("alignment source_content must equal canonical source slice")
            if alignment.target_char_end > len(representation.content):
                raise ValueError("alignment target range exceeds derived representation")
            if representation.content[alignment.target_char_start:alignment.target_char_end] != alignment.target_content:
                raise ValueError("alignment target_content must equal derived representation slice")
            for ref in alignment.source_token_refs:
                token = token_map.get(ref)
                if token is None:
                    raise ValueError("alignment source_token_ref must resolve")
                if token.text_unit_ref != unit.text_unit_id:
                    raise ValueError("alignment source token must belong to alignment source unit")
                if not (
                    alignment.source_char_start <= token.char_start
                    and token.char_end <= alignment.source_char_end
                ):
                    raise ValueError("alignment source token must fall within source alignment span")

        for variant_set in self.variant_sets:
            unit = unit_map.get(variant_set.source_text_unit_ref)
            if unit is None:
                raise ValueError("variant-set source_text_unit_ref must resolve")
            members: list[DerivedTextRepresentation] = []
            for ref in variant_set.representation_refs:
                representation = representation_map.get(ref)
                if representation is None:
                    raise ValueError("variant-set representation_ref must resolve")
                if representation.source_text_unit_ref != unit.text_unit_id:
                    raise ValueError("variant-set representations must share one source text unit")
                members.append(representation)
            if len({x.kind for x in members}) != 1:
                raise ValueError("variant-set representations must share representation kind")
            if len({x.target_language_ref for x in members}) != 1:
                raise ValueError("variant-set representations must share target language")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def _alignment(
    alignment_id: str,
    representation: DerivedTextRepresentation,
    unit,
    source_surface: str,
    target_surface: str,
    provenance_ref: str,
    *,
    source_token_refs: list[str] | None = None,
    source_occurrence_start: int = 0,
    target_occurrence_start: int = 0,
    kind: AlignmentKind = AlignmentKind.one_to_one,
) -> ParallelTextAlignmentRecord:
    ss = unit.content.index(source_surface, source_occurrence_start)
    ts = representation.content.index(target_surface, target_occurrence_start)
    return ParallelTextAlignmentRecord(
        alignment_id=alignment_id,
        representation_ref=representation.representation_id,
        source_text_unit_ref=unit.text_unit_id,
        source_char_start=ss,
        source_char_end=ss + len(source_surface),
        source_content=source_surface,
        source_content_sha256=_content_sha256(source_surface),
        target_char_start=ts,
        target_char_end=ts + len(target_surface),
        target_content=target_surface,
        target_content_sha256=_content_sha256(target_surface),
        alignment_kind=kind,
        provenance_ref=provenance_ref,
        source_token_refs=source_token_refs or [],
    )


def reference_translation_alignment_bundle() -> TranslationTransliterationAlignmentBundle:
    base = reference_linguistic_annotation_bundle()
    text_payload = base.text_bundle.model_dump(mode="json", exclude_none=True)
    text_payload["languages"].append(
        LanguageIdentity(
            language_id="language:es",
            bcp47_tag="es",
            canonical_name="Spanish",
            iso_639_1="es",
            iso_639_3="spa",
            endonyms=["español"],
        ).model_dump(mode="json", exclude_none=True)
    )
    text_bundle = MultilingualTextLanguageBundle.model_validate(text_payload)
    annotation_payload = base.model_dump(mode="json", exclude_none=True)
    annotation_payload["text_bundle"] = text_bundle.model_dump(mode="json", exclude_none=True)
    annotation_bundle = LinguisticAnnotationBundle.model_validate(annotation_payload)

    source = annotation_bundle.text_bundle.text_sources[0]
    unit = annotation_bundle.text_bundle.text_units[0]
    annotation_fp = annotation_bundle.fingerprint()

    translation_a = DerivedTextRepresentation(
        representation_id="translation:reference:es:a",
        kind=DerivedRepresentationKind.translation,
        source_text_ref=source.text_source_id,
        source_text_unit_ref=unit.text_unit_id,
        target_language_ref="language:es",
        target_script_ref="script:Latn",
        content="Agua agua sistemas.",
        content_sha256=_content_sha256("Agua agua sistemas."),
        provenance_ref="derivation-provenance:translation:reference:es:a",
        metadata={"variant_label": "A"},
    )
    translation_b = DerivedTextRepresentation(
        representation_id="translation:reference:es:b",
        kind=DerivedRepresentationKind.translation,
        source_text_ref=source.text_source_id,
        source_text_unit_ref=unit.text_unit_id,
        target_language_ref="language:es",
        target_script_ref="script:Latn",
        content="Agua, agua y sistemas.",
        content_sha256=_content_sha256("Agua, agua y sistemas."),
        provenance_ref="derivation-provenance:translation:reference:es:b",
        metadata={"variant_label": "B"},
    )
    transliteration = DerivedTextRepresentation(
        representation_id="transliteration:reference:zh-latn:shui",
        kind=DerivedRepresentationKind.transliteration,
        source_text_ref=source.text_source_id,
        source_text_unit_ref=unit.text_unit_id,
        target_language_ref="language:zh",
        target_script_ref="script:Latn",
        content="shuǐ",
        content_sha256=_content_sha256("shuǐ"),
        provenance_ref="derivation-provenance:transliteration:reference:zh-latn:shui",
        transliteration_scheme="Hanyu Pinyin with tone marks",
    )

    provenance_records = [
        DerivationProvenanceRecord(
            provenance_id=translation_a.provenance_ref,
            representation_ref=translation_a.representation_id,
            source_text_ref=source.text_source_id,
            source_content_sha256=source.content_sha256,
            source_annotation_bundle_fingerprint_sha256=annotation_fp,
            method=DerivationMethod.manual,
            produced_by_ref="actor:sustainable-catalyst-reference-translator-a",
            translator_ref="actor:sustainable-catalyst-reference-translator-a",
            created_at="2026-09-29T00:00:00-05:00",
            review_state=DerivationReviewState.reviewed,
            reviewer_ref="actor:sustainable-catalyst-reference-reviewer",
            review_note="Reference translation A; retained as one interpretation, not canonical text.",
        ),
        DerivationProvenanceRecord(
            provenance_id=translation_b.provenance_ref,
            representation_ref=translation_b.representation_id,
            source_text_ref=source.text_source_id,
            source_content_sha256=source.content_sha256,
            source_annotation_bundle_fingerprint_sha256=annotation_fp,
            method=DerivationMethod.model_assisted,
            produced_by_ref="run:reference-translation-model",
            model_ref="model:reference-translation-model",
            model_version="1.0",
            created_at="2026-09-29T00:01:00-05:00",
            review_state=DerivationReviewState.unreviewed,
        ),
        DerivationProvenanceRecord(
            provenance_id=transliteration.provenance_ref,
            representation_ref=transliteration.representation_id,
            source_text_ref=source.text_source_id,
            source_content_sha256=source.content_sha256,
            source_annotation_bundle_fingerprint_sha256=annotation_fp,
            method=DerivationMethod.editorial,
            produced_by_ref="actor:sustainable-catalyst-reference-editor",
            created_at="2026-09-29T00:02:00-05:00",
        ),
    ]

    token_by_surface = {x.surface: x.token_id for x in annotation_bundle.tokens}
    alignments = [
        _alignment("alignment:es-a:water", translation_a, unit, "Water", "Agua", translation_a.provenance_ref, source_token_refs=[token_by_surface["Water"]]),
        _alignment("alignment:es-a:han", translation_a, unit, "水", "agua", translation_a.provenance_ref, source_token_refs=[token_by_surface["水"]], target_occurrence_start=1),
        _alignment("alignment:es-a:systems", translation_a, unit, "systems", "sistemas", translation_a.provenance_ref, source_token_refs=[token_by_surface["systems"]]),
        _alignment("alignment:es-b:water", translation_b, unit, "Water", "Agua", translation_b.provenance_ref, source_token_refs=[token_by_surface["Water"]]),
        _alignment("alignment:es-b:han", translation_b, unit, "水", "agua", translation_b.provenance_ref, source_token_refs=[token_by_surface["水"]], target_occurrence_start=1),
        _alignment("alignment:es-b:systems", translation_b, unit, "systems", "sistemas", translation_b.provenance_ref, source_token_refs=[token_by_surface["systems"]]),
        _alignment("alignment:zh-latn:han", transliteration, unit, "水", "shuǐ", transliteration.provenance_ref, source_token_refs=[token_by_surface["水"]]),
    ]

    variant_set = RepresentationVariantSet(
        variant_set_id="translation-variants:reference:es",
        source_text_unit_ref=unit.text_unit_id,
        representation_refs=[translation_a.representation_id, translation_b.representation_id],
        comparison_basis="Alternative Spanish renderings of the same canonical source text unit",
        metadata={"core_ranking": "none"},
    )

    return TranslationTransliterationAlignmentBundle(
        annotation_bundle=annotation_bundle,
        provenance_records=provenance_records,
        representations=[translation_a, translation_b, transliteration],
        alignments=alignments,
        variant_sets=[variant_set],
        metadata={
            "purpose": "Platform Core v3.67.0 translation, transliteration, and parallel-text alignment reference",
            "original_language_is_canonical": True,
            "translation_disagreement_is_preserved": True,
        },
    )


def contract_document() -> dict[str, Any]:
    ref = reference_translation_alignment_bundle()
    kinds = [x.kind.value for x in ref.representations]
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contracts": [
            "sc.core.multilingual-text-language-object.v1",
            "sc.core.linguistic-annotation-provenance.v1",
        ],
        "object_types": [
            "DerivationProvenanceRecord",
            "DerivedTextRepresentation",
            "ParallelTextAlignmentRecord",
            "RepresentationVariantSet",
            "TranslationTransliterationAlignmentBundle",
        ],
        "principles": {
            "original_language_remains_canonical": True,
            "translation_is_a_derived_representation": True,
            "transliteration_is_a_derived_representation": True,
            "derived_representation_may_replace_original": False,
            "alignment_preserves_source_and_target_spans": True,
            "multiple_translations_may_coexist": True,
            "translation_disagreement_is_preserved": True,
            "machine_derivations_are_advisory": True,
            "core_selects_authoritative_translation": False,
        },
        "capabilities": {
            "translation_objects": True,
            "transliteration_objects": True,
            "transliteration_scheme_identity": True,
            "parallel_text_character_alignment": True,
            "source_token_alignment_refs": True,
            "translator_model_tool_provenance": True,
            "human_review_state": True,
            "translation_variant_sets": True,
            "deterministic_object_fingerprints": True,
        },
        "roadmap_integration": {
            "extends_v3650_original_language_text_objects": True,
            "extends_v3660_linguistic_annotation_objects": True,
            "prepares_v3680_historical_language_script_variant_identity": True,
            "prepares_v3690_cross_lingual_semantic_exchange": True,
            "preserves_v3700_v3760_graph_neural_wave": True,
            "gnn_prediction_is_not_graph_fact": True,
        },
        "boundaries": {
            "core_translates_text": False,
            "core_transliterates_text": False,
            "core_infers_parallel_alignment": False,
            "core_rewrites_canonical_source_text": False,
            "core_replaces_original_with_translation": False,
            "core_selects_best_translation": False,
            "core_resolves_translation_disagreement": False,
            "core_treats_machine_translation_as_authoritative": False,
        },
        "reference": {
            "canonical_source_id": ref.annotation_bundle.text_bundle.text_sources[0].text_source_id,
            "representation_count": len(ref.representations),
            "representation_kinds": kinds,
            "alignment_count": len(ref.alignments),
            "variant_set_count": len(ref.variant_sets),
            "bundle_fingerprint_sha256": ref.fingerprint(),
        },
    }
