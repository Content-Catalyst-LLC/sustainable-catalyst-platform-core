from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .multilingual_text_language import (
    CanonicalTextSource,
    LanguageIdentity,
    MultilingualTextLanguageBundle,
    ScriptIdentity,
    TextSourceProvenanceRecord,
    TextUnitKind,
    TextUnitRecord,
    WritingDirection,
    _content_sha256,
)

CORE_RELEASE = "3.68.0"
CONTRACT_VERSION = "sc.core.historical-language-script-orthography-variant.v1"


class TemporalCertainty(str, Enum):
    exact = "exact"
    approximate = "approximate"
    uncertain = "uncertain"
    unknown = "unknown"


class HistoricalIdentityMethod(str, Enum):
    declared = "declared"
    editorial = "editorial"
    imported = "imported"
    scholarly = "scholarly"
    model_assisted = "model-assisted"


class NormalizationMethod(str, Enum):
    manual = "manual"
    editorial = "editorial"
    rule_based = "rule-based"
    imported = "imported"
    model_assisted = "model-assisted"


class VariantReviewState(str, Enum):
    unreviewed = "unreviewed"
    reviewed = "reviewed"
    accepted = "accepted"
    rejected = "rejected"
    disputed = "disputed"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class HistoricalLanguageStageIdentity(BaseModel):
    stage_id: str = Field(min_length=2, max_length=500)
    language_ref: str = Field(min_length=2, max_length=500)
    canonical_label: str = Field(min_length=1, max_length=500)
    parent_stage_ref: str | None = Field(default=None, max_length=500)
    start_year: int | None = Field(default=None, ge=-10000, le=10000)
    end_year: int | None = Field(default=None, ge=-10000, le=10000)
    temporal_certainty: TemporalCertainty = TemporalCertainty.unknown
    chronology_source_refs: list[str] = Field(default_factory=list)
    identity_method: HistoricalIdentityMethod = HistoricalIdentityMethod.declared
    assigned_by_ref: str | None = Field(default=None, max_length=1000)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    machine_identity_is_advisory: Literal[True] = True
    identity_is_authoritative: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_stage(self):
        if self.start_year is not None and self.end_year is not None and self.end_year < self.start_year:
            raise ValueError("end_year must not precede start_year")
        if self.identity_method == HistoricalIdentityMethod.model_assisted and not self.assigned_by_ref:
            raise ValueError("model-assisted historical identity requires assigned_by_ref")
        _unique(self.chronology_source_refs, "chronology_source_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class HistoricalScriptVariantIdentity(BaseModel):
    script_variant_id: str = Field(min_length=2, max_length=500)
    base_script_ref: str = Field(min_length=2, max_length=500)
    language_stage_ref: str | None = Field(default=None, max_length=500)
    canonical_label: str = Field(min_length=1, max_length=500)
    variant_label: str = Field(min_length=1, max_length=500)
    parent_script_variant_ref: str | None = Field(default=None, max_length=500)
    chronology_source_refs: list[str] = Field(default_factory=list)
    identity_method: HistoricalIdentityMethod = HistoricalIdentityMethod.declared
    assigned_by_ref: str | None = Field(default=None, max_length=1000)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    machine_identity_is_advisory: Literal[True] = True
    identity_is_authoritative: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_script_variant(self):
        if self.parent_script_variant_ref == self.script_variant_id:
            raise ValueError("script variant cannot be its own parent")
        if self.identity_method == HistoricalIdentityMethod.model_assisted and not self.assigned_by_ref:
            raise ValueError("model-assisted historical script identity requires assigned_by_ref")
        _unique(self.chronology_source_refs, "script chronology_source_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class OrthographyProfile(BaseModel):
    orthography_profile_id: str = Field(min_length=2, max_length=500)
    language_stage_ref: str = Field(min_length=2, max_length=500)
    script_variant_ref: str = Field(min_length=2, max_length=500)
    canonical_label: str = Field(min_length=1, max_length=500)
    convention_notes: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    identity_method: HistoricalIdentityMethod = HistoricalIdentityMethod.declared
    assigned_by_ref: str | None = Field(default=None, max_length=1000)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    machine_profile_is_advisory: Literal[True] = True
    profile_is_authoritative: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_profile(self):
        if self.identity_method == HistoricalIdentityMethod.model_assisted and not self.assigned_by_ref:
            raise ValueError("model-assisted orthography profile requires assigned_by_ref")
        _unique(self.source_refs, "orthography source_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class HistoricalVariantAttestation(BaseModel):
    variant_id: str = Field(min_length=2, max_length=500)
    source_text_ref: str = Field(min_length=2, max_length=500)
    text_unit_ref: str = Field(min_length=2, max_length=500)
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    attested_form: str = Field(min_length=1)
    attested_form_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    language_stage_ref: str = Field(min_length=2, max_length=500)
    script_variant_ref: str = Field(min_length=2, max_length=500)
    orthography_profile_ref: str = Field(min_length=2, max_length=500)
    attestation_source_refs: list[str] = Field(default_factory=list)
    temporal_label: str | None = Field(default=None, max_length=500)
    start_year: int | None = Field(default=None, ge=-10000, le=10000)
    end_year: int | None = Field(default=None, ge=-10000, le=10000)
    temporal_certainty: TemporalCertainty = TemporalCertainty.unknown
    review_state: VariantReviewState = VariantReviewState.unreviewed
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    machine_assignment_is_advisory: Literal[True] = True
    attestation_is_authoritative: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_attestation(self):
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        if self.attested_form_sha256 != _content_sha256(self.attested_form):
            raise ValueError("attested_form_sha256 must match attested_form")
        if self.start_year is not None and self.end_year is not None and self.end_year < self.start_year:
            raise ValueError("attestation end_year must not precede start_year")
        if self.review_state != VariantReviewState.unreviewed and not self.reviewer_ref:
            raise ValueError("reviewed historical attestation requires reviewer_ref")
        _unique(self.attestation_source_refs, "attestation_source_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class OrthographicNormalizationRecord(BaseModel):
    normalization_id: str = Field(min_length=2, max_length=500)
    variant_ref: str = Field(min_length=2, max_length=500)
    source_form: str = Field(min_length=1)
    source_form_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    normalized_form: str = Field(min_length=1)
    normalized_form_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    method: NormalizationMethod
    produced_by_ref: str = Field(min_length=2, max_length=1000)
    ruleset_ref: str | None = Field(default=None, max_length=1000)
    tool_ref: str | None = Field(default=None, max_length=1000)
    tool_version: str | None = Field(default=None, max_length=240)
    model_ref: str | None = Field(default=None, max_length=1000)
    model_version: str | None = Field(default=None, max_length=240)
    reversible: bool = False
    review_state: VariantReviewState = VariantReviewState.unreviewed
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    normalized_form_is_derived: Literal[True] = True
    canonical_source_unchanged: Literal[True] = True
    machine_normalization_is_advisory: Literal[True] = True
    normalization_is_authoritative: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_normalization(self):
        if self.source_form_sha256 != _content_sha256(self.source_form):
            raise ValueError("source_form_sha256 must match source_form")
        if self.normalized_form_sha256 != _content_sha256(self.normalized_form):
            raise ValueError("normalized_form_sha256 must match normalized_form")
        if self.method == NormalizationMethod.model_assisted and not self.model_ref:
            raise ValueError("model-assisted normalization requires model_ref")
        if self.model_version and not self.model_ref:
            raise ValueError("model_version requires model_ref")
        if self.tool_version and not self.tool_ref:
            raise ValueError("tool_version requires tool_ref")
        if self.review_state != VariantReviewState.unreviewed and not self.reviewer_ref:
            raise ValueError("reviewed normalization requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class HistoricalLanguageVariantBundle(BaseModel):
    text_bundle: MultilingualTextLanguageBundle
    language_stages: list[HistoricalLanguageStageIdentity] = Field(min_length=1)
    script_variants: list[HistoricalScriptVariantIdentity] = Field(min_length=1)
    orthography_profiles: list[OrthographyProfile] = Field(min_length=1)
    variants: list[HistoricalVariantAttestation] = Field(min_length=1)
    normalizations: list[OrthographicNormalizationRecord] = Field(default_factory=list)
    linguistic_annotation_refs: list[str] = Field(default_factory=list)
    derived_representation_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        for values, label in (
            ([x.stage_id for x in self.language_stages], "language stage ids"),
            ([x.script_variant_id for x in self.script_variants], "script variant ids"),
            ([x.orthography_profile_id for x in self.orthography_profiles], "orthography profile ids"),
            ([x.variant_id for x in self.variants], "historical variant ids"),
            ([x.normalization_id for x in self.normalizations], "normalization ids"),
            (self.linguistic_annotation_refs, "linguistic annotation refs"),
            (self.derived_representation_refs, "derived representation refs"),
        ):
            _unique(values, label)

        language_ids = {x.language_id for x in self.text_bundle.languages}
        script_ids = {x.script_id for x in self.text_bundle.scripts}
        source_map = {x.text_source_id: x for x in self.text_bundle.text_sources}
        unit_map = {x.text_unit_id: x for x in self.text_bundle.text_units}
        stage_map = {x.stage_id: x for x in self.language_stages}
        script_variant_map = {x.script_variant_id: x for x in self.script_variants}
        profile_map = {x.orthography_profile_id: x for x in self.orthography_profiles}
        variant_map = {x.variant_id: x for x in self.variants}

        for stage in self.language_stages:
            if stage.language_ref not in language_ids:
                raise ValueError("historical language stage language_ref must resolve")
            if stage.parent_stage_ref is not None and stage.parent_stage_ref not in stage_map:
                raise ValueError("historical language stage parent_stage_ref must resolve")
            if stage.parent_stage_ref == stage.stage_id:
                raise ValueError("historical language stage cannot be its own parent")

        for script_variant in self.script_variants:
            if script_variant.base_script_ref not in script_ids:
                raise ValueError("historical script base_script_ref must resolve")
            if script_variant.language_stage_ref is not None and script_variant.language_stage_ref not in stage_map:
                raise ValueError("historical script language_stage_ref must resolve")
            if script_variant.parent_script_variant_ref is not None and script_variant.parent_script_variant_ref not in script_variant_map:
                raise ValueError("historical script parent_script_variant_ref must resolve")

        for profile in self.orthography_profiles:
            if profile.language_stage_ref not in stage_map:
                raise ValueError("orthography profile language_stage_ref must resolve")
            if profile.script_variant_ref not in script_variant_map:
                raise ValueError("orthography profile script_variant_ref must resolve")

        for variant in self.variants:
            source = source_map.get(variant.source_text_ref)
            unit = unit_map.get(variant.text_unit_ref)
            if source is None or unit is None:
                raise ValueError("historical variant source/text unit refs must resolve")
            if unit.source_text_ref != source.text_source_id:
                raise ValueError("historical variant unit must belong to source")
            if variant.language_stage_ref not in stage_map:
                raise ValueError("historical variant language_stage_ref must resolve")
            if variant.script_variant_ref not in script_variant_map:
                raise ValueError("historical variant script_variant_ref must resolve")
            if variant.orthography_profile_ref not in profile_map:
                raise ValueError("historical variant orthography_profile_ref must resolve")
            if variant.char_end > len(source.content):
                raise ValueError("historical variant range exceeds canonical source")
            if source.content[variant.char_start:variant.char_end] != variant.attested_form:
                raise ValueError("historical variant attested_form must equal canonical source slice")

        for normalization in self.normalizations:
            variant = variant_map.get(normalization.variant_ref)
            if variant is None:
                raise ValueError("normalization variant_ref must resolve")
            if normalization.source_form != variant.attested_form:
                raise ValueError("normalization source_form must equal attested historical form")
            if normalization.source_form_sha256 != variant.attested_form_sha256:
                raise ValueError("normalization source hash must match attested historical form")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_historical_language_variant_bundle() -> HistoricalLanguageVariantBundle:
    content = "Publick knowledge preserves the original forme."
    source_id = "text-source:historical-orthography-reference:v1"
    provenance_id = "text-provenance:historical-orthography-reference:v1"
    unit_id = "text-unit:historical-orthography-reference:document"

    language = LanguageIdentity(
        language_id="language:en",
        bcp47_tag="en",
        canonical_name="English",
        iso_639_1="en",
        iso_639_3="eng",
        endonyms=["English"],
    )
    script = ScriptIdentity(
        script_id="script:Latn",
        iso_15924_code="Latn",
        canonical_name="Latin",
        writing_direction=WritingDirection.ltr,
        unicode_script_property="Latin",
    )
    provenance = TextSourceProvenanceRecord(
        provenance_id=provenance_id,
        text_source_ref=source_id,
        source_object_ref="reference-fixture:historical-orthography:v1",
        acquisition_method="synthetic-reference-fixture",
        recorded_by_ref="actor:sustainable-catalyst-reference-fixture",
        recorded_at="2026-09-29T01:20:00-05:00",
        metadata={"historical_claim": False, "purpose": "schema-validation-only"},
    )
    source = CanonicalTextSource(
        text_source_id=source_id,
        source_object_ref=provenance.source_object_ref,
        source_kind="reference-fixture",
        primary_language_ref=language.language_id,
        primary_script_ref=script.script_id,
        provenance_ref=provenance_id,
        content=content,
        content_sha256=_content_sha256(content),
        metadata={"synthetic": True, "historical_claim": False},
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
        language_ref=language.language_id,
        script_ref=script.script_id,
    )
    text_bundle = MultilingualTextLanguageBundle(
        languages=[language], scripts=[script], provenance_records=[provenance],
        text_sources=[source], text_units=[unit], language_spans=[],
        metadata={"purpose": "v3.68 synthetic historical-identity reference fixture"},
    )

    stage = HistoricalLanguageStageIdentity(
        stage_id="language-stage:en:historical-reference",
        language_ref=language.language_id,
        canonical_label="Historical English reference stage",
        temporal_certainty=TemporalCertainty.unknown,
        chronology_source_refs=[],
        identity_method=HistoricalIdentityMethod.declared,
        metadata={"synthetic_reference": True, "asserts_real_periodization": False},
    )
    script_variant = HistoricalScriptVariantIdentity(
        script_variant_id="script-variant:latn:historical-reference",
        base_script_ref=script.script_id,
        language_stage_ref=stage.stage_id,
        canonical_label="Latin script historical reference variant",
        variant_label="Reference historical Latin-script usage",
        identity_method=HistoricalIdentityMethod.declared,
        metadata={"synthetic_reference": True},
    )
    profile = OrthographyProfile(
        orthography_profile_id="orthography:en:historical-reference",
        language_stage_ref=stage.stage_id,
        script_variant_ref=script_variant.script_variant_id,
        canonical_label="Historical English orthography reference profile",
        convention_notes=["Reference fixture retains attested spellings exactly."],
        identity_method=HistoricalIdentityMethod.declared,
        metadata={"synthetic_reference": True},
    )

    variants=[]
    normalizations=[]
    for idx, (attested, normalized) in enumerate((("Publick", "Public"), ("forme", "form")), start=1):
        start=content.index(attested)
        variant=HistoricalVariantAttestation(
            variant_id=f"historical-variant:reference:{idx}",
            source_text_ref=source_id,
            text_unit_ref=unit_id,
            char_start=start,
            char_end=start+len(attested),
            attested_form=attested,
            attested_form_sha256=_content_sha256(attested),
            language_stage_ref=stage.stage_id,
            script_variant_ref=script_variant.script_variant_id,
            orthography_profile_ref=profile.orthography_profile_id,
            temporal_label="synthetic historical reference",
            temporal_certainty=TemporalCertainty.unknown,
            metadata={"synthetic_reference": True, "historical_claim": False},
        )
        normalization=OrthographicNormalizationRecord(
            normalization_id=f"normalization:reference:{idx}",
            variant_ref=variant.variant_id,
            source_form=attested,
            source_form_sha256=_content_sha256(attested),
            normalized_form=normalized,
            normalized_form_sha256=_content_sha256(normalized),
            method=NormalizationMethod.editorial,
            produced_by_ref="actor:sustainable-catalyst-reference-fixture",
            reversible=True,
            metadata={"purpose": "demonstrate derived normalization lineage"},
        )
        variants.append(variant); normalizations.append(normalization)

    return HistoricalLanguageVariantBundle(
        text_bundle=text_bundle,
        language_stages=[stage],
        script_variants=[script_variant],
        orthography_profiles=[profile],
        variants=variants,
        normalizations=normalizations,
        metadata={
            "purpose": "Platform Core v3.68 historical language/script/orthography contract reference",
            "prepares_cross_lingual_exchange": "v3.69.0",
            "preserves_graph_neural_wave": "v3.70.0-v3.76.0",
        },
    )


def contract_document() -> dict[str, Any]:
    ref = reference_historical_language_variant_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contracts": [
            "sc.core.multilingual-text-language-object.v1",
            "sc.core.linguistic-annotation-provenance.v1",
            "sc.core.translation-transliteration-alignment.v1",
        ],
        "object_types": [
            "HistoricalLanguageStageIdentity",
            "HistoricalScriptVariantIdentity",
            "OrthographyProfile",
            "HistoricalVariantAttestation",
            "OrthographicNormalizationRecord",
            "HistoricalLanguageVariantBundle",
        ],
        "principles": {
            "original_attested_form_is_preserved": True,
            "normalization_is_a_derived_representation": True,
            "normalization_may_replace_attested_source": False,
            "historical_language_stage_is_distinct_from_base_language_identity": True,
            "historical_script_variant_is_distinct_from_iso15924_script_identity": True,
            "orthographic_variants_remain_traceable_to_exact_source_spans": True,
            "historical_dates_may_preserve_uncertainty": True,
            "machine_historical_identity_is_advisory": True,
        },
        "capabilities": {
            "historical_language_stage_identity": True,
            "historical_script_variant_identity": True,
            "orthography_profile_identity": True,
            "attested_variant_source_binding": True,
            "derived_normalization_lineage": True,
            "temporal_certainty_and_chronology_sources": True,
            "review_state_and_provenance": True,
            "deterministic_object_fingerprints": True,
            "v366_linguistic_annotation_reference_hooks": True,
            "v367_derived_representation_reference_hooks": True,
        },
        "roadmap_integration": {
            "follows_v3650_multilingual_text": True,
            "follows_v3660_linguistic_annotations": True,
            "follows_v3670_translation_alignment": True,
            "prepares_v3690_cross_lingual_semantic_exchange": True,
            "preserves_v3700_v3760_graph_neural_wave": True,
            "gnn_prediction_is_not_graph_fact": True,
        },
        "boundaries": {
            "core_modernizes_or_normalizes_source_text": False,
            "core_rewrites_attested_source_text": False,
            "core_infers_historical_periodization": False,
            "core_infers_historical_script_identity": False,
            "core_resolves_orthographic_variant_authority": False,
            "core_treats_model_normalization_as_authoritative": False,
            "core_treats_uncertain_dates_as_exact": False,
        },
        "reference": {
            "text_source_id": ref.text_bundle.text_sources[0].text_source_id,
            "language_stage_count": len(ref.language_stages),
            "script_variant_count": len(ref.script_variants),
            "orthography_profile_count": len(ref.orthography_profiles),
            "variant_count": len(ref.variants),
            "normalization_count": len(ref.normalizations),
            "canonical_source_content_sha256": ref.text_bundle.text_sources[0].content_sha256,
            "bundle_fingerprint_sha256": ref.fingerprint(),
            "reference_fixture_is_synthetic": True,
        },
    }
