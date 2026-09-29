from copy import deepcopy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import translation_alignment
from app.services.translation_alignment import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    AlignmentKind,
    DerivationMethod,
    DerivationProvenanceRecord,
    DerivationReviewState,
    DerivedRepresentationKind,
    DerivedTextRepresentation,
    ParallelTextAlignmentRecord,
    RepresentationVariantSet,
    TranslationTransliterationAlignmentBundle,
    contract_document,
    reference_translation_alignment_bundle,
)


def payload():
    return reference_translation_alignment_bundle().model_dump(mode="json", exclude_none=True)


def invalid(mutator):
    p = payload()
    mutator(p)
    with pytest.raises(ValidationError):
        TranslationTransliterationAlignmentBundle.model_validate(p)


def test_release_identity_and_contract():
    assert CORE_RELEASE == "3.67.0"
    assert CONTRACT_VERSION == "sc.core.translation-transliteration-alignment.v1"
    c = contract_document()
    assert c["release"] == "3.67.0"
    assert c["extends_contracts"] == [
        "sc.core.multilingual-text-language-object.v1",
        "sc.core.linguistic-annotation-provenance.v1",
    ]


def test_reference_bundle_is_deterministic():
    a = reference_translation_alignment_bundle()
    b = reference_translation_alignment_bundle()
    assert a.fingerprint() == b.fingerprint()
    assert len(a.fingerprint()) == 64
    assert len(a.representations) == 3
    assert len(a.alignments) == 7
    assert len(a.variant_sets) == 1


def test_translation_and_transliteration_coexist():
    bundle = reference_translation_alignment_bundle()
    kinds = [x.kind for x in bundle.representations]
    assert kinds.count(DerivedRepresentationKind.translation) == 2
    assert kinds.count(DerivedRepresentationKind.transliteration) == 1


def test_original_language_remains_canonical():
    c = contract_document()
    assert c["principles"]["original_language_remains_canonical"] is True
    assert c["principles"]["derived_representation_may_replace_original"] is False


def test_translation_hash_is_verified():
    rep = reference_translation_alignment_bundle().representations[0]
    p = rep.model_dump(mode="json", exclude_none=True)
    p["content_sha256"] = "0" * 64
    with pytest.raises(ValidationError):
        DerivedTextRepresentation.model_validate(p)


def test_transliteration_requires_scheme():
    rep = reference_translation_alignment_bundle().representations[2]
    p = rep.model_dump(mode="json", exclude_none=True)
    p.pop("transliteration_scheme")
    with pytest.raises(ValidationError):
        DerivedTextRepresentation.model_validate(p)


def test_translation_rejects_transliteration_scheme():
    rep = reference_translation_alignment_bundle().representations[0]
    p = rep.model_dump(mode="json", exclude_none=True)
    p["transliteration_scheme"] = "not-applicable"
    with pytest.raises(ValidationError):
        DerivedTextRepresentation.model_validate(p)


def test_model_assisted_provenance_requires_model_ref():
    bundle = reference_translation_alignment_bundle()
    source = bundle.annotation_bundle.text_bundle.text_sources[0]
    with pytest.raises(ValidationError):
        DerivationProvenanceRecord(
            provenance_id="prov:test",
            representation_ref="translation:test",
            source_text_ref=source.text_source_id,
            source_content_sha256=source.content_sha256,
            method=DerivationMethod.model_assisted,
            produced_by_ref="run:test",
        )


def test_reviewed_provenance_requires_reviewer():
    bundle = reference_translation_alignment_bundle()
    source = bundle.annotation_bundle.text_bundle.text_sources[0]
    with pytest.raises(ValidationError):
        DerivationProvenanceRecord(
            provenance_id="prov:test",
            representation_ref="translation:test",
            source_text_ref=source.text_source_id,
            source_content_sha256=source.content_sha256,
            method=DerivationMethod.manual,
            produced_by_ref="actor:test",
            review_state=DerivationReviewState.accepted,
        )


def test_provenance_source_hash_must_match_canonical_source():
    invalid(lambda p: p["provenance_records"][0].__setitem__("source_content_sha256", "0" * 64))


def test_annotation_bundle_fingerprint_is_checked():
    invalid(lambda p: p["provenance_records"][0].__setitem__("source_annotation_bundle_fingerprint_sha256", "0" * 64))


def test_representation_source_text_ref_must_resolve():
    invalid(lambda p: p["representations"][0].__setitem__("source_text_ref", "text-source:missing"))


def test_representation_source_unit_must_resolve():
    invalid(lambda p: p["representations"][0].__setitem__("source_text_unit_ref", "text-unit:missing"))


def test_target_language_must_resolve():
    invalid(lambda p: p["representations"][0].__setitem__("target_language_ref", "language:missing"))


def test_target_script_must_resolve():
    invalid(lambda p: p["representations"][0].__setitem__("target_script_ref", "script:missing"))


def test_representation_provenance_must_resolve():
    invalid(lambda p: p["representations"][0].__setitem__("provenance_ref", "prov:missing"))


def test_provenance_must_point_back_to_representation():
    invalid(lambda p: p["provenance_records"][0].__setitem__("representation_ref", "translation:wrong"))


def test_transliteration_preserves_source_language_identity():
    invalid(lambda p: p["representations"][2].__setitem__("target_language_ref", "language:es"))


def test_alignment_source_hash_is_verified():
    alignment = reference_translation_alignment_bundle().alignments[0]
    p = alignment.model_dump(mode="json", exclude_none=True)
    p["source_content_sha256"] = "0" * 64
    with pytest.raises(ValidationError):
        ParallelTextAlignmentRecord.model_validate(p)


def test_alignment_target_hash_is_verified():
    alignment = reference_translation_alignment_bundle().alignments[0]
    p = alignment.model_dump(mode="json", exclude_none=True)
    p["target_content_sha256"] = "0" * 64
    with pytest.raises(ValidationError):
        ParallelTextAlignmentRecord.model_validate(p)


def test_alignment_source_slice_must_match_canonical_text():
    invalid(lambda p: p["alignments"][0].__setitem__("source_content", "Wrong"))


def test_alignment_target_slice_must_match_representation():
    invalid(lambda p: p["alignments"][0].__setitem__("target_content", "Wrong"))


def test_alignment_target_range_cannot_exceed_representation():
    invalid(lambda p: p["alignments"][0].__setitem__("target_char_end", 999))


def test_alignment_source_range_cannot_exceed_text_unit():
    invalid(lambda p: p["alignments"][0].__setitem__("source_char_end", 999))


def test_alignment_source_token_must_resolve():
    invalid(lambda p: p["alignments"][0]["source_token_refs"].__setitem__(0, "token:missing"))


def test_alignment_source_token_must_be_within_source_span():
    def mutate(p):
        p["alignments"][0]["source_token_refs"] = [p["annotation_bundle"]["tokens"][2]["token_id"]]
    invalid(mutate)


def test_alignment_provenance_must_belong_to_representation():
    invalid(lambda p: p["alignments"][0].__setitem__("provenance_ref", p["provenance_records"][1]["provenance_id"]))


def test_variant_set_requires_unique_representations():
    bundle = reference_translation_alignment_bundle()
    refs = [bundle.representations[0].representation_id] * 2
    with pytest.raises(ValidationError):
        RepresentationVariantSet(
            variant_set_id="variants:test",
            source_text_unit_ref=bundle.annotation_bundle.text_bundle.text_units[0].text_unit_id,
            representation_refs=refs,
            comparison_basis="test",
        )


def test_variant_set_representation_must_resolve():
    invalid(lambda p: p["variant_sets"][0]["representation_refs"].__setitem__(1, "translation:missing"))


def test_variant_set_requires_same_kind():
    def mutate(p):
        p["variant_sets"][0]["representation_refs"][1] = p["representations"][2]["representation_id"]
    invalid(mutate)


def test_variant_set_requires_same_target_language():
    def mutate(p):
        p["representations"][1]["target_language_ref"] = "language:en"
    invalid(mutate)


def test_multiple_translations_can_coexist_without_core_ranking():
    bundle = reference_translation_alignment_bundle()
    assert len(bundle.variant_sets[0].representation_refs) == 2
    assert bundle.variant_sets[0].preferred_representation_selected_by_core is False
    assert bundle.variant_sets[0].disagreement_preserved is True


def test_machine_translation_and_alignment_are_advisory():
    c = contract_document()
    assert c["principles"]["machine_derivations_are_advisory"] is True
    assert c["boundaries"]["core_treats_machine_translation_as_authoritative"] is False
    assert all(x.machine_alignment_is_advisory for x in reference_translation_alignment_bundle().alignments)


def test_core_does_not_execute_translation_or_alignment():
    c = contract_document()
    assert c["boundaries"]["core_translates_text"] is False
    assert c["boundaries"]["core_transliterates_text"] is False
    assert c["boundaries"]["core_infers_parallel_alignment"] is False
    assert c["boundaries"]["core_selects_best_translation"] is False
    assert c["boundaries"]["core_resolves_translation_disagreement"] is False


def test_graph_neural_wave_remains_reserved_and_prediction_not_fact():
    c = contract_document()
    assert c["roadmap_integration"]["preserves_v3700_v3760_graph_neural_wave"] is True
    assert c["roadmap_integration"]["gnn_prediction_is_not_graph_fact"] is True


def test_public_contract_route():
    app = FastAPI()
    app.include_router(translation_alignment.public_router)
    with TestClient(app) as client:
        response = client.get("/public/v1/translation-alignments/contract")
    assert response.status_code == 200
    body = response.json()
    assert body["release"] == "3.67.0"
    assert body["contract"] == CONTRACT_VERSION


def test_private_reference_route():
    app = FastAPI()
    app.include_router(translation_alignment.router)
    with TestClient(app) as client:
        response = client.get("/api/v1/translation-alignments/reference")
    assert response.status_code == 200
    body = response.json()
    assert body["release"] == "3.67.0"
    assert len(body["bundle_fingerprint_sha256"]) == 64
    assert len(body["bundle"]["representations"]) == 3
