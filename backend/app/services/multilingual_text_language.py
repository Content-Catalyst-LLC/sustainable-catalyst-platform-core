from __future__ import annotations

import hashlib
import re
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.65.0"
CONTRACT_VERSION = "sc.core.multilingual-text-language-object.v1"

_BCP47_RE = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
_ISO639_1_RE = re.compile(r"^[a-z]{2}$")
_ISO639_3_RE = re.compile(r"^[a-z]{3}$")
_ISO15924_RE = re.compile(r"^[A-Z][a-z]{3}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _content_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class WritingDirection(str, Enum):
    ltr = "ltr"
    rtl = "rtl"
    vertical_rl = "vertical-rl"
    vertical_lr = "vertical-lr"
    mixed = "mixed"


class TextUnitKind(str, Enum):
    document = "document"
    section = "section"
    paragraph = "paragraph"
    sentence = "sentence"
    passage = "passage"
    utterance = "utterance"
    line = "line"
    verse = "verse"
    title = "title"
    label = "label"


class LanguageAssignmentMethod(str, Enum):
    declared = "declared"
    editorial = "editorial"
    imported = "imported"
    model_assisted = "model-assisted"
    unknown = "unknown"


class LanguageIdentity(BaseModel):
    language_id: str = Field(min_length=2, max_length=500)
    bcp47_tag: str = Field(min_length=2, max_length=80)
    canonical_name: str = Field(min_length=1, max_length=240)
    iso_639_1: str | None = Field(default=None, min_length=2, max_length=2)
    iso_639_3: str | None = Field(default=None, min_length=3, max_length=3)
    endonyms: list[str] = Field(default_factory=list)
    alternate_names: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_language(self):
        if not _BCP47_RE.fullmatch(self.bcp47_tag):
            raise ValueError("bcp47_tag must use a valid BCP 47 language-tag shape")
        if self.iso_639_1 is not None and not _ISO639_1_RE.fullmatch(self.iso_639_1):
            raise ValueError("iso_639_1 must be two lowercase letters")
        if self.iso_639_3 is not None and not _ISO639_3_RE.fullmatch(self.iso_639_3):
            raise ValueError("iso_639_3 must be three lowercase letters")
        _unique(self.endonyms, "language endonyms")
        _unique(self.alternate_names, "language alternate_names")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ScriptIdentity(BaseModel):
    script_id: str = Field(min_length=2, max_length=500)
    iso_15924_code: str = Field(min_length=4, max_length=4)
    canonical_name: str = Field(min_length=1, max_length=240)
    writing_direction: WritingDirection
    unicode_script_property: str | None = Field(default=None, max_length=120)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_script(self):
        if not _ISO15924_RE.fullmatch(self.iso_15924_code):
            raise ValueError("iso_15924_code must use ISO 15924 title-case form such as Latn or Arab")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TextSourceProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=2, max_length=500)
    text_source_ref: str = Field(min_length=2, max_length=500)
    source_object_ref: str = Field(min_length=2, max_length=1000)
    acquisition_method: str = Field(min_length=2, max_length=240)
    source_artifact_ref: str | None = Field(default=None, max_length=1000)
    source_artifact_sha256: str | None = Field(default=None, max_length=64)
    recorded_by_ref: str | None = Field(default=None, max_length=1000)
    recorded_at: str | None = Field(default=None, max_length=80)
    content_replaces_original: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_provenance(self):
        if bool(self.source_artifact_ref) != bool(self.source_artifact_sha256):
            raise ValueError("source artifact ref/hash must be supplied together")
        if self.source_artifact_sha256 is not None and not _SHA256_RE.fullmatch(self.source_artifact_sha256):
            raise ValueError("source_artifact_sha256 must be a lowercase SHA-256 digest")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CanonicalTextSource(BaseModel):
    text_source_id: str = Field(min_length=2, max_length=500)
    source_object_ref: str = Field(min_length=2, max_length=1000)
    source_kind: str = Field(min_length=2, max_length=120)
    primary_language_ref: str = Field(min_length=2, max_length=500)
    primary_script_ref: str = Field(min_length=2, max_length=500)
    provenance_ref: str = Field(min_length=2, max_length=500)
    content: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_encoding: Literal["utf-8"] = "utf-8"
    original_language_is_canonical: Literal[True] = True
    translation_substitution_allowed: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_source(self):
        if self.content_sha256 != _content_sha256(self.content):
            raise ValueError("content_sha256 must match UTF-8 source content")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TextUnitRecord(BaseModel):
    text_unit_id: str = Field(min_length=2, max_length=500)
    source_text_ref: str = Field(min_length=2, max_length=500)
    unit_kind: TextUnitKind
    sequence: int = Field(ge=0)
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    content: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    language_ref: str = Field(min_length=2, max_length=500)
    script_ref: str = Field(min_length=2, max_length=500)
    parent_text_unit_ref: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_unit(self):
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        if self.content_sha256 != _content_sha256(self.content):
            raise ValueError("text-unit content_sha256 must match content")
        if self.parent_text_unit_ref == self.text_unit_id:
            raise ValueError("text unit cannot be its own parent")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class LanguageSpanBinding(BaseModel):
    span_binding_id: str = Field(min_length=2, max_length=500)
    text_unit_ref: str = Field(min_length=2, max_length=500)
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    language_ref: str = Field(min_length=2, max_length=500)
    script_ref: str = Field(min_length=2, max_length=500)
    assignment_method: LanguageAssignmentMethod
    assigned_by_ref: str | None = Field(default=None, max_length=1000)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    machine_assignment_is_advisory: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_span(self):
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        if self.assignment_method == LanguageAssignmentMethod.model_assisted and not self.assigned_by_ref:
            raise ValueError("model-assisted language assignment requires assigned_by_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MultilingualTextLanguageBundle(BaseModel):
    languages: list[LanguageIdentity] = Field(min_length=1)
    scripts: list[ScriptIdentity] = Field(min_length=1)
    provenance_records: list[TextSourceProvenanceRecord] = Field(min_length=1)
    text_sources: list[CanonicalTextSource] = Field(min_length=1)
    text_units: list[TextUnitRecord] = Field(min_length=1)
    language_spans: list[LanguageSpanBinding] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        language_ids = [x.language_id for x in self.languages]
        script_ids = [x.script_id for x in self.scripts]
        provenance_ids = [x.provenance_id for x in self.provenance_records]
        source_ids = [x.text_source_id for x in self.text_sources]
        unit_ids = [x.text_unit_id for x in self.text_units]
        span_ids = [x.span_binding_id for x in self.language_spans]
        for values, label in (
            (language_ids, "language ids"),
            (script_ids, "script ids"),
            (provenance_ids, "provenance ids"),
            (source_ids, "text source ids"),
            (unit_ids, "text unit ids"),
            (span_ids, "language span ids"),
        ):
            _unique(values, label)

        language_set = set(language_ids)
        script_set = set(script_ids)
        provenance_map = {x.provenance_id: x for x in self.provenance_records}
        source_map = {x.text_source_id: x for x in self.text_sources}
        unit_map = {x.text_unit_id: x for x in self.text_units}

        for source in self.text_sources:
            if source.primary_language_ref not in language_set:
                raise ValueError("text source primary_language_ref must resolve")
            if source.primary_script_ref not in script_set:
                raise ValueError("text source primary_script_ref must resolve")
            provenance = provenance_map.get(source.provenance_ref)
            if provenance is None or provenance.text_source_ref != source.text_source_id:
                raise ValueError("text source provenance_ref must resolve back to the same source")

        for provenance in self.provenance_records:
            if provenance.text_source_ref not in source_map:
                raise ValueError("provenance text_source_ref must resolve")

        for unit in self.text_units:
            source = source_map.get(unit.source_text_ref)
            if source is None:
                raise ValueError("text unit source_text_ref must resolve")
            if unit.language_ref not in language_set:
                raise ValueError("text unit language_ref must resolve")
            if unit.script_ref not in script_set:
                raise ValueError("text unit script_ref must resolve")
            if unit.char_end > len(source.content):
                raise ValueError("text unit character range exceeds source content")
            if source.content[unit.char_start:unit.char_end] != unit.content:
                raise ValueError("text unit content must equal its canonical source character slice")
            if unit.parent_text_unit_ref is not None:
                parent = unit_map.get(unit.parent_text_unit_ref)
                if parent is None:
                    raise ValueError("parent_text_unit_ref must resolve")
                if parent.source_text_ref != unit.source_text_ref:
                    raise ValueError("parent and child text units must belong to the same source")
                if not (parent.char_start <= unit.char_start and unit.char_end <= parent.char_end):
                    raise ValueError("child text unit must be contained within parent character range")

        for span in self.language_spans:
            unit = unit_map.get(span.text_unit_ref)
            if unit is None:
                raise ValueError("language span text_unit_ref must resolve")
            if span.language_ref not in language_set:
                raise ValueError("language span language_ref must resolve")
            if span.script_ref not in script_set:
                raise ValueError("language span script_ref must resolve")
            if span.char_end > len(unit.content):
                raise ValueError("language span character range exceeds text unit")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_multilingual_text_language_bundle() -> MultilingualTextLanguageBundle:
    content = "Water 水 systems."
    source_id = "text-source:multilingual-reference-note:v1"
    provenance_id = "text-provenance:multilingual-reference-note:v1"
    unit_id = "text-unit:multilingual-reference-note:document"

    languages = [
        LanguageIdentity(
            language_id="language:mul",
            bcp47_tag="mul",
            canonical_name="Multiple languages",
            iso_639_3="mul",
        ),
        LanguageIdentity(
            language_id="language:en",
            bcp47_tag="en",
            canonical_name="English",
            iso_639_1="en",
            iso_639_3="eng",
            endonyms=["English"],
        ),
        LanguageIdentity(
            language_id="language:zh",
            bcp47_tag="zh",
            canonical_name="Chinese",
            iso_639_1="zh",
            iso_639_3="zho",
            endonyms=["中文"],
        ),
    ]
    scripts = [
        ScriptIdentity(
            script_id="script:Zyyy",
            iso_15924_code="Zyyy",
            canonical_name="Common",
            writing_direction=WritingDirection.mixed,
            unicode_script_property="Common",
        ),
        ScriptIdentity(
            script_id="script:Latn",
            iso_15924_code="Latn",
            canonical_name="Latin",
            writing_direction=WritingDirection.ltr,
            unicode_script_property="Latin",
        ),
        ScriptIdentity(
            script_id="script:Hani",
            iso_15924_code="Hani",
            canonical_name="Han",
            writing_direction=WritingDirection.ltr,
            unicode_script_property="Han",
        ),
    ]
    provenance = TextSourceProvenanceRecord(
        provenance_id=provenance_id,
        text_source_ref=source_id,
        source_object_ref="research-note:multilingual-language-model-reference",
        acquisition_method="direct-authorial-entry",
        recorded_by_ref="actor:sustainable-catalyst-reference-fixture",
        recorded_at="2026-09-28T22:45:00-05:00",
    )
    source = CanonicalTextSource(
        text_source_id=source_id,
        source_object_ref=provenance.source_object_ref,
        source_kind="research-note",
        primary_language_ref="language:mul",
        primary_script_ref="script:Zyyy",
        provenance_ref=provenance_id,
        content=content,
        content_sha256=_content_sha256(content),
    )
    unit = TextUnitRecord(
        text_unit_id=unit_id,
        source_text_ref=source_id,
        unit_kind=TextUnitKind.document,
        sequence=0,
        char_start=0,
        char_end=len(content),
        content=content,
        content_sha256=_content_sha256(content),
        language_ref="language:mul",
        script_ref="script:Zyyy",
    )

    water_start = content.index("Water")
    han_start = content.index("水")
    systems_start = content.index("systems")
    spans = [
        LanguageSpanBinding(
            span_binding_id="language-span:reference:water",
            text_unit_ref=unit_id,
            char_start=water_start,
            char_end=water_start + len("Water"),
            language_ref="language:en",
            script_ref="script:Latn",
            assignment_method=LanguageAssignmentMethod.declared,
        ),
        LanguageSpanBinding(
            span_binding_id="language-span:reference:water-han",
            text_unit_ref=unit_id,
            char_start=han_start,
            char_end=han_start + len("水"),
            language_ref="language:zh",
            script_ref="script:Hani",
            assignment_method=LanguageAssignmentMethod.declared,
        ),
        LanguageSpanBinding(
            span_binding_id="language-span:reference:systems",
            text_unit_ref=unit_id,
            char_start=systems_start,
            char_end=systems_start + len("systems"),
            language_ref="language:en",
            script_ref="script:Latn",
            assignment_method=LanguageAssignmentMethod.declared,
        ),
    ]

    return MultilingualTextLanguageBundle(
        languages=languages,
        scripts=scripts,
        provenance_records=[provenance],
        text_sources=[source],
        text_units=[unit],
        language_spans=spans,
        metadata={
            "purpose": "Platform Core v3.65.0 multilingual text and language contract reference",
            "translation_objects_deferred_to": "v3.67.0",
            "linguistic_annotation_objects_deferred_to": "v3.66.0",
        },
    )


def contract_document() -> dict[str, Any]:
    ref = reference_multilingual_text_language_bundle()
    source = ref.text_sources[0]
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "object_types": [
            "LanguageIdentity",
            "ScriptIdentity",
            "TextSourceProvenanceRecord",
            "CanonicalTextSource",
            "TextUnitRecord",
            "LanguageSpanBinding",
            "MultilingualTextLanguageBundle",
        ],
        "principles": {
            "original_language_is_canonical": True,
            "translation_is_a_derived_representation": True,
            "translation_may_replace_original": False,
            "language_and_script_identity_are_distinct": True,
            "mixed_language_text_preserves_span_level_identity": True,
            "unicode_source_content_is_preserved": True,
            "every_source_requires_provenance": True,
            "machine_language_assignments_are_advisory": True,
        },
        "capabilities": {
            "bcp47_language_identity": True,
            "iso639_language_metadata": True,
            "iso15924_script_identity": True,
            "canonical_utf8_source_text": True,
            "immutable_source_content_hashes": True,
            "hierarchical_text_units": True,
            "character_range_source_binding": True,
            "mixed_language_span_bindings": True,
            "deterministic_object_fingerprints": True,
        },
        "roadmap_integration": {
            "follows_neural_foundation_v3570_through_v3640": True,
            "prepares_v3660_linguistic_annotation_morphology_syntax": True,
            "prepares_v3670_translation_transliteration_parallel_alignment": True,
            "prepares_v3680_historical_language_script_variant_identity": True,
            "prepares_v3690_cross_lingual_semantic_exchange": True,
        },
        "boundaries": {
            "core_performs_ocr_or_htr": False,
            "core_translates_text": False,
            "core_transliterates_text": False,
            "core_tokenizes_or_parses_text": False,
            "core_infers_language_identity": False,
            "core_rewrites_canonical_source_text": False,
            "core_replaces_original_with_translation": False,
            "core_treats_model_language_assignment_as_authoritative": False,
        },
        "reference": {
            "text_source_id": source.text_source_id,
            "content_sha256": source.content_sha256,
            "languages": [x.bcp47_tag for x in ref.languages],
            "scripts": [x.iso_15924_code for x in ref.scripts],
            "language_span_count": len(ref.language_spans),
            "bundle_fingerprint_sha256": ref.fingerprint(),
        },
    }
