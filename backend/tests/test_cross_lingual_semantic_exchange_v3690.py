import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import cross_lingual_semantic_exchange
from app.services.cross_lingual_semantic_exchange import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    CrossLingualConceptSet,
    CrossLingualSemanticAssertion,
    CrossLingualSemanticExchangeBundle,
    ExchangeAssertionState,
    ExchangeMethod,
    LinguisticSemanticAnchor,
    SemanticExchangeProvenanceRecord,
    SemanticRelationKind,
    contract_document,
    reference_cross_lingual_semantic_exchange_bundle,
)


def test_release_and_contract_identity():
    assert CORE_RELEASE == "3.69.0"
    assert CONTRACT_VERSION == "sc.core.cross-lingual-semantic-linguistic-exchange.v1"


def test_reference_bundle_valid_and_deterministic():
    a=reference_cross_lingual_semantic_exchange_bundle(); b=reference_cross_lingual_semantic_exchange_bundle()
    assert a.fingerprint()==b.fingerprint(); assert len(a.fingerprint())==64


def test_reference_languages_cross_three_language_identities():
    bundle=reference_cross_lingual_semantic_exchange_bundle()
    assert set(bundle.concept_sets[0].language_refs)=={"language:en","language:zh","language:es"}


def test_semantic_similarity_does_not_create_equivalence():
    bundle=reference_cross_lingual_semantic_exchange_bundle()
    assert all(x.machine_similarity_is_not_equivalence for x in bundle.assertions)
    assert all(x.assertion_is_not_graph_fact for x in bundle.assertions)


def test_candidate_machine_assertion_stays_non_authoritative():
    bundle=reference_cross_lingual_semantic_exchange_bundle()
    candidate=next(x for x in bundle.assertions if x.assertion_state==ExchangeAssertionState.candidate)
    assert candidate.relation_kind==SemanticRelationKind.translation_correspondence
    prov=next(x for x in bundle.provenance_records if x.assertion_ref==candidate.assertion_id)
    assert prov.method==ExchangeMethod.model_assisted
    assert prov.machine_or_graph_output_is_advisory is True


def test_cross_language_assertion_rejects_same_language_anchors():
    bundle=reference_cross_lingual_semantic_exchange_bundle().model_copy(deep=True)
    bundle.anchors[1].language_ref=bundle.anchors[0].language_ref
    with pytest.raises(ValidationError):
        CrossLingualSemanticExchangeBundle.model_validate(bundle.model_dump(mode="json"))


def test_unresolved_anchor_source_object_is_rejected():
    bundle=reference_cross_lingual_semantic_exchange_bundle().model_copy(deep=True)
    bundle.anchors[0].source_object_ref="missing:object"
    with pytest.raises(ValidationError):
        CrossLingualSemanticExchangeBundle.model_validate(bundle.model_dump(mode="json"))


def test_unresolved_concept_ref_is_rejected():
    bundle=reference_cross_lingual_semantic_exchange_bundle().model_copy(deep=True)
    bundle.anchors[0].concept_ref="concept:missing"
    with pytest.raises(ValidationError):
        CrossLingualSemanticExchangeBundle.model_validate(bundle.model_dump(mode="json"))


def test_reviewed_assertion_requires_reviewer():
    with pytest.raises(ValidationError):
        CrossLingualSemanticAssertion(assertion_id="a", source_anchor_ref="x", target_anchor_ref="y", relation_kind=SemanticRelationKind.related, provenance_ref="p", assertion_state=ExchangeAssertionState.reviewed)


def test_model_assisted_provenance_requires_model():
    with pytest.raises(ValidationError):
        SemanticExchangeProvenanceRecord(provenance_id="p", assertion_ref="a", method=ExchangeMethod.model_assisted, produced_by_ref="run:test")


def test_anchor_range_pairing_is_enforced():
    with pytest.raises(ValidationError):
        LinguisticSemanticAnchor(anchor_id="a", concept_ref="c", language_ref="language:en", surface_form="x", source_object_ref="o", source_object_kind="TokenRecord", char_start=0)


def test_concept_set_language_refs_must_match_anchors():
    bundle=reference_cross_lingual_semantic_exchange_bundle().model_copy(deep=True)
    bundle.concept_sets[0].language_refs=["language:en","language:es"]
    with pytest.raises(ValidationError):
        CrossLingualSemanticExchangeBundle.model_validate(bundle.model_dump(mode="json"))


def test_contract_extends_full_language_block():
    assert contract_document()["extends_contracts"]==[
        "sc.core.multilingual-text-language-object.v1",
        "sc.core.linguistic-annotation-provenance.v1",
        "sc.core.translation-transliteration-alignment.v1",
        "sc.core.historical-language-script-orthography-variant.v1",
    ]


@pytest.mark.parametrize("key", [
    "original_language_remains_canonical",
    "translation_remains_derived",
    "historical_attested_form_remains_preserved",
    "semantic_similarity_is_not_semantic_equivalence",
    "translation_correspondence_is_not_concept_identity",
    "entity_name_correspondence_is_not_entity_identity",
    "machine_cross_lingual_links_are_advisory",
    "cross_lingual_assertion_is_not_graph_fact",
    "unresolved_semantic_disagreement_is_preserved",
])
def test_contract_principles_true(key):
    assert contract_document()["principles"][key] is True


@pytest.mark.parametrize("key", [
    "core_translates_or_transliterates_text",
    "core_computes_embeddings_or_similarity",
    "core_selects_authoritative_translation",
    "core_collapses_semantic_similarity_into_equivalence",
    "core_converts_semantic_assertion_into_graph_fact",
    "core_resolves_entity_identity_from_name_correspondence",
    "core_overwrites_original_or_historical_source_forms",
    "core_treats_model_cross_lingual_match_as_authoritative",
])
def test_contract_boundaries_false(key):
    assert contract_document()["boundaries"][key] is False


def test_language_block_complete_and_gnn_handoff_preserved():
    r=contract_document()["roadmap_integration"]
    assert r["completes_v3650_v3690_language_linguistics_core_block"] is True
    assert r["prepares_v3700_graph_machine_learning_foundation"] is True
    assert r["preserves_v3700_v3760_graph_neural_wave"] is True
    assert r["gnn_prediction_is_not_graph_fact"] is True
    assert r["predicted_relationship_requires_separate_validation_before_evidence_edge"] is True


def test_reference_fixture_is_explicitly_synthetic():
    c=contract_document(); assert c["reference"]["reference_fixture_is_synthetic"] is True
    bundle=reference_cross_lingual_semantic_exchange_bundle()
    assert bundle.concepts[0].metadata["synthetic_reference"] is True


def test_public_contract_route():
    app=FastAPI(); app.include_router(cross_lingual_semantic_exchange.public_router)
    with TestClient(app) as client: response=client.get("/public/v1/cross-lingual-exchange/contract")
    assert response.status_code==200; assert response.json()["release"]=="3.69.0"


def test_private_reference_route():
    app=FastAPI(); app.include_router(cross_lingual_semantic_exchange.router)
    with TestClient(app) as client: response=client.get("/api/v1/cross-lingual-exchange/reference")
    assert response.status_code==200
    body=response.json(); assert body["release"]=="3.69.0"; assert len(body["bundle_fingerprint_sha256"])==64
