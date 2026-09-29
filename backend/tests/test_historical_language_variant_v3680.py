import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import historical_language_variant
from app.services.historical_language_variant import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    HistoricalLanguageStageIdentity,
    HistoricalLanguageVariantBundle,
    HistoricalVariantAttestation,
    HistoricalIdentityMethod,
    NormalizationMethod,
    OrthographicNormalizationRecord,
    TemporalCertainty,
    VariantReviewState,
    contract_document,
    reference_historical_language_variant_bundle,
)
from app.services.multilingual_text_language import _content_sha256


def test_release_and_contract_identity():
    assert CORE_RELEASE == "3.68.0"
    assert CONTRACT_VERSION == "sc.core.historical-language-script-orthography-variant.v1"


def test_reference_bundle_is_valid_and_deterministic():
    a = reference_historical_language_variant_bundle()
    b = reference_historical_language_variant_bundle()
    assert a.fingerprint() == b.fingerprint()
    assert len(a.fingerprint()) == 64


def test_reference_fixture_preserves_canonical_source():
    bundle = reference_historical_language_variant_bundle()
    source = bundle.text_bundle.text_sources[0]
    assert source.content == "Publick knowledge preserves the original forme."
    assert source.original_language_is_canonical is True
    assert source.translation_substitution_allowed is False


def test_historical_variant_exactly_matches_source_span():
    bundle = reference_historical_language_variant_bundle()
    source = bundle.text_bundle.text_sources[0]
    for variant in bundle.variants:
        assert source.content[variant.char_start:variant.char_end] == variant.attested_form


def test_normalizations_are_derived_and_source_unchanged():
    bundle = reference_historical_language_variant_bundle()
    source_before = bundle.text_bundle.text_sources[0].content
    assert [x.normalized_form for x in bundle.normalizations] == ["Public", "form"]
    for n in bundle.normalizations:
        assert n.normalized_form_is_derived is True
        assert n.canonical_source_unchanged is True
        assert n.normalization_is_authoritative is False
    assert bundle.text_bundle.text_sources[0].content == source_before


def test_variant_range_mismatch_is_rejected():
    bundle = reference_historical_language_variant_bundle()
    bad = bundle.model_copy(deep=True)
    bad.variants[0].char_start = 1
    with pytest.raises(ValidationError):
        HistoricalLanguageVariantBundle.model_validate(bad.model_dump(mode="json"))


def test_variant_hash_mismatch_is_rejected():
    with pytest.raises(ValidationError):
        HistoricalVariantAttestation(
            variant_id="v", source_text_ref="s", text_unit_ref="u", char_start=0, char_end=2,
            attested_form="ab", attested_form_sha256="0"*64,
            language_stage_ref="ls", script_variant_ref="sv", orthography_profile_ref="op"
        )


def test_normalization_hash_mismatch_is_rejected():
    with pytest.raises(ValidationError):
        OrthographicNormalizationRecord(
            normalization_id="n", variant_ref="v", source_form="ab",
            source_form_sha256=_content_sha256("ab"), normalized_form="a",
            normalized_form_sha256="0"*64, method=NormalizationMethod.manual,
            produced_by_ref="actor:test"
        )


def test_model_assisted_normalization_requires_model_ref():
    with pytest.raises(ValidationError):
        OrthographicNormalizationRecord(
            normalization_id="n", variant_ref="v", source_form="ab",
            source_form_sha256=_content_sha256("ab"), normalized_form="a",
            normalized_form_sha256=_content_sha256("a"), method=NormalizationMethod.model_assisted,
            produced_by_ref="actor:test"
        )


def test_model_assisted_historical_identity_requires_assignee():
    with pytest.raises(ValidationError):
        HistoricalLanguageStageIdentity(
            stage_id="stage:test", language_ref="language:en", canonical_label="Test",
            identity_method=HistoricalIdentityMethod.model_assisted
        )


def test_reversed_stage_date_range_is_rejected():
    with pytest.raises(ValidationError):
        HistoricalLanguageStageIdentity(
            stage_id="stage:test", language_ref="language:en", canonical_label="Test",
            start_year=1500, end_year=1400, temporal_certainty=TemporalCertainty.approximate
        )


def test_reviewed_variant_requires_reviewer():
    with pytest.raises(ValidationError):
        HistoricalVariantAttestation(
            variant_id="v", source_text_ref="s", text_unit_ref="u", char_start=0, char_end=2,
            attested_form="ab", attested_form_sha256=_content_sha256("ab"),
            language_stage_ref="ls", script_variant_ref="sv", orthography_profile_ref="op",
            review_state=VariantReviewState.reviewed
        )


def test_contract_extends_prior_language_contracts():
    c = contract_document()
    assert c["extends_contracts"] == [
        "sc.core.multilingual-text-language-object.v1",
        "sc.core.linguistic-annotation-provenance.v1",
        "sc.core.translation-transliteration-alignment.v1",
    ]


@pytest.mark.parametrize("key", [
    "original_attested_form_is_preserved",
    "normalization_is_a_derived_representation",
    "historical_language_stage_is_distinct_from_base_language_identity",
    "historical_script_variant_is_distinct_from_iso15924_script_identity",
    "orthographic_variants_remain_traceable_to_exact_source_spans",
    "historical_dates_may_preserve_uncertainty",
    "machine_historical_identity_is_advisory",
])
def test_contract_principles_true(key):
    assert contract_document()["principles"][key] is True


def test_normalization_cannot_replace_attested_source():
    assert contract_document()["principles"]["normalization_may_replace_attested_source"] is False


@pytest.mark.parametrize("key", [
    "core_modernizes_or_normalizes_source_text",
    "core_rewrites_attested_source_text",
    "core_infers_historical_periodization",
    "core_infers_historical_script_identity",
    "core_resolves_orthographic_variant_authority",
    "core_treats_model_normalization_as_authoritative",
    "core_treats_uncertain_dates_as_exact",
])
def test_contract_boundaries_false(key):
    assert contract_document()["boundaries"][key] is False


def test_v369_and_gnn_roadmap_are_preserved():
    r = contract_document()["roadmap_integration"]
    assert r["prepares_v3690_cross_lingual_semantic_exchange"] is True
    assert r["preserves_v3700_v3760_graph_neural_wave"] is True
    assert r["gnn_prediction_is_not_graph_fact"] is True


def test_reference_fixture_is_explicitly_synthetic():
    c = contract_document()
    assert c["reference"]["reference_fixture_is_synthetic"] is True
    source = reference_historical_language_variant_bundle().text_bundle.text_sources[0]
    assert source.metadata["historical_claim"] is False


def test_public_contract_route():
    app = FastAPI(); app.include_router(historical_language_variant.public_router)
    with TestClient(app) as client:
        response = client.get("/public/v1/historical-language/contract")
    assert response.status_code == 200
    assert response.json()["release"] == "3.68.0"


def test_private_reference_route():
    app = FastAPI(); app.include_router(historical_language_variant.router)
    with TestClient(app) as client:
        response = client.get("/api/v1/historical-language/reference")
    assert response.status_code == 200
    body=response.json()
    assert body["release"] == "3.68.0"
    assert len(body["bundle_fingerprint_sha256"]) == 64
    assert len(body["bundle"]["variants"]) == 2
