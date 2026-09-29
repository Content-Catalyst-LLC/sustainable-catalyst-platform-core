from copy import deepcopy
import hashlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import multilingual_text_language
from app.services.multilingual_text_language import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    CanonicalTextSource,
    LanguageAssignmentMethod,
    LanguageIdentity,
    LanguageSpanBinding,
    MultilingualTextLanguageBundle,
    ScriptIdentity,
    WritingDirection,
    contract_document,
    reference_multilingual_text_language_bundle,
)


def payload():
    return reference_multilingual_text_language_bundle().model_dump(mode="json", exclude_none=True)


def invalid(mutator):
    p = payload()
    mutator(p)
    with pytest.raises(ValidationError):
        MultilingualTextLanguageBundle.model_validate(p)


def test_release_identity_and_contract():
    assert CORE_RELEASE == "3.65.0"
    assert CONTRACT_VERSION == "sc.core.multilingual-text-language-object.v1"
    c = contract_document()
    assert c["release"] == "3.65.0"
    assert c["principles"]["original_language_is_canonical"] is True
    assert c["principles"]["translation_may_replace_original"] is False


def test_reference_bundle_is_deterministic_and_multilingual():
    a = reference_multilingual_text_language_bundle()
    b = reference_multilingual_text_language_bundle()
    assert a.fingerprint() == b.fingerprint()
    assert len(a.fingerprint()) == 64
    assert {x.bcp47_tag for x in a.languages} == {"mul", "en", "zh"}
    assert {x.iso_15924_code for x in a.scripts} == {"Zyyy", "Latn", "Hani"}
    assert len(a.language_spans) == 3


def test_source_content_hash_is_verified():
    content = "Original language text"
    source = CanonicalTextSource(
        text_source_id="text-source:test",
        source_object_ref="source:test",
        source_kind="note",
        primary_language_ref="language:en",
        primary_script_ref="script:Latn",
        provenance_ref="provenance:test",
        content=content,
        content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )
    assert source.original_language_is_canonical is True
    bad = source.model_dump()
    bad["content_sha256"] = "0" * 64
    with pytest.raises(ValidationError):
        CanonicalTextSource.model_validate(bad)


def test_language_identifier_shapes_are_validated():
    LanguageIdentity(language_id="language:en-us", bcp47_tag="en-US", canonical_name="English (US)", iso_639_1="en", iso_639_3="eng")
    with pytest.raises(ValidationError):
        LanguageIdentity(language_id="language:bad", bcp47_tag="e_123", canonical_name="Bad")


def test_script_identifier_shape_is_validated():
    ScriptIdentity(script_id="script:Arab", iso_15924_code="Arab", canonical_name="Arabic", writing_direction=WritingDirection.rtl)
    with pytest.raises(ValidationError):
        ScriptIdentity(script_id="script:bad", iso_15924_code="ARAB", canonical_name="Bad", writing_direction=WritingDirection.rtl)


def test_unresolved_source_language_is_rejected():
    invalid(lambda p: p["text_sources"][0].__setitem__("primary_language_ref", "language:missing"))


def test_unresolved_source_script_is_rejected():
    invalid(lambda p: p["text_sources"][0].__setitem__("primary_script_ref", "script:missing"))


def test_source_provenance_must_resolve_back_to_source():
    invalid(lambda p: p["provenance_records"][0].__setitem__("text_source_ref", "text-source:missing"))


def test_text_unit_must_match_canonical_source_slice():
    invalid(lambda p: p["text_units"][0].__setitem__("content", "Water X systems."))


def test_text_unit_range_cannot_exceed_source():
    invalid(lambda p: p["text_units"][0].__setitem__("char_end", 999))


def test_language_span_references_must_resolve():
    invalid(lambda p: p["language_spans"][0].__setitem__("language_ref", "language:missing"))


def test_language_span_range_must_fit_unit():
    invalid(lambda p: p["language_spans"][0].__setitem__("char_end", 999))


def test_model_assisted_language_assignment_requires_provenance():
    with pytest.raises(ValidationError):
        LanguageSpanBinding(
            span_binding_id="span:test",
            text_unit_ref="unit:test",
            char_start=0,
            char_end=4,
            language_ref="language:en",
            script_ref="script:Latn",
            assignment_method=LanguageAssignmentMethod.model_assisted,
        )


def test_translation_cannot_replace_original_in_contract():
    c = contract_document()
    assert c["principles"]["translation_is_a_derived_representation"] is True
    assert c["principles"]["translation_may_replace_original"] is False
    assert c["boundaries"]["core_replaces_original_with_translation"] is False


def test_v366_and_v367_scope_is_reserved():
    c = contract_document()
    assert c["roadmap_integration"]["prepares_v3660_linguistic_annotation_morphology_syntax"] is True
    assert c["roadmap_integration"]["prepares_v3670_translation_transliteration_parallel_alignment"] is True
    assert c["boundaries"]["core_tokenizes_or_parses_text"] is False
    assert c["boundaries"]["core_translates_text"] is False


def test_public_contract_route():
    app = FastAPI()
    app.include_router(multilingual_text_language.public_router)
    response = TestClient(app).get("/public/v1/language-text/contract")
    assert response.status_code == 200
    body = response.json()
    assert body["release"] == "3.65.0"
    assert body["contract"] == CONTRACT_VERSION
    assert body["principles"]["original_language_is_canonical"] is True


def test_private_reference_route():
    app = FastAPI()
    app.include_router(multilingual_text_language.router)
    response = TestClient(app).get("/api/v1/language-text/reference")
    assert response.status_code == 200
    body = response.json()
    assert body["release"] == "3.65.0"
    assert len(body["bundle_fingerprint_sha256"]) == 64
    assert body["bundle"]["text_sources"][0]["translation_substitution_allowed"] is False
