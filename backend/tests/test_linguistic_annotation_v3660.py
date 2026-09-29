from copy import deepcopy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import linguistic_annotation
from app.services.linguistic_annotation import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    AnnotationMethod,
    AnnotationProvenanceRecord,
    AnnotationReviewState,
    DependencyRelation,
    LinguisticAnnotationBundle,
    PartOfSpeechAnnotation,
    TokenRecord,
    UniversalPartOfSpeech,
    contract_document,
    reference_linguistic_annotation_bundle,
)


def payload():
    return reference_linguistic_annotation_bundle().model_dump(mode="json", exclude_none=True)


def invalid(mutator):
    p = payload()
    mutator(p)
    with pytest.raises(ValidationError):
        LinguisticAnnotationBundle.model_validate(p)


def test_release_identity_and_contract():
    assert CORE_RELEASE == "3.66.0"
    assert CONTRACT_VERSION == "sc.core.linguistic-annotation-provenance.v1"
    c = contract_document()
    assert c["release"] == "3.66.0"
    assert c["extends_contract"] == "sc.core.multilingual-text-language-object.v1"


def test_reference_bundle_is_deterministic():
    a = reference_linguistic_annotation_bundle()
    b = reference_linguistic_annotation_bundle()
    assert a.fingerprint() == b.fingerprint()
    assert len(a.fingerprint()) == 64
    assert len(a.tokens) == 4
    assert len(a.dependency_relations) == 4
    assert len(a.constituency_nodes) == 3


def test_tokens_bind_exactly_to_v365_canonical_text():
    bundle = reference_linguistic_annotation_bundle()
    unit = bundle.text_bundle.text_units[0]
    for token in bundle.tokens:
        assert unit.content[token.char_start:token.char_end] == token.surface


def test_token_surface_hash_is_verified():
    p = payload()["tokens"][0]
    p["surface_sha256"] = "0" * 64
    with pytest.raises(ValidationError):
        TokenRecord.model_validate(p)


def test_unresolved_text_unit_is_rejected():
    invalid(lambda p: p["tokens"][0].__setitem__("text_unit_ref", "text-unit:missing"))


def test_token_surface_must_match_canonical_slice():
    invalid(lambda p: p["tokens"][0].__setitem__("surface", "WATER"))


def test_token_range_cannot_exceed_text_unit():
    invalid(lambda p: p["tokens"][0].__setitem__("char_end", 999))


def test_tokenization_membership_must_resolve():
    invalid(lambda p: p["tokenizations"][0]["token_refs"].__setitem__(0, "token:missing"))


def test_overlapping_tokens_are_rejected():
    def mutate(p):
        p["tokens"][1]["char_start"] = 4
        p["tokens"][1]["char_end"] = 5
        p["tokens"][1]["surface"] = "r"
        import hashlib
        p["tokens"][1]["surface_sha256"] = hashlib.sha256(b"r").hexdigest()
    invalid(mutate)


def test_complete_tokenization_requires_contiguous_sequence_numbers():
    invalid(lambda p: p["tokens"][3].__setitem__("sequence", 8))


def test_model_assisted_provenance_requires_model_ref():
    source = reference_linguistic_annotation_bundle().text_bundle.text_sources[0]
    with pytest.raises(ValidationError):
        AnnotationProvenanceRecord(
            provenance_id="prov:test",
            source_text_ref=source.text_source_id,
            source_content_sha256=source.content_sha256,
            method=AnnotationMethod.model_assisted,
            produced_by_ref="run:test",
        )


def test_reviewed_provenance_requires_reviewer():
    source = reference_linguistic_annotation_bundle().text_bundle.text_sources[0]
    with pytest.raises(ValidationError):
        AnnotationProvenanceRecord(
            provenance_id="prov:test",
            source_text_ref=source.text_source_id,
            source_content_sha256=source.content_sha256,
            method=AnnotationMethod.manual,
            produced_by_ref="actor:test",
            review_state=AnnotationReviewState.accepted,
        )


def test_annotation_provenance_hash_must_match_canonical_source():
    invalid(lambda p: p["provenance_records"][0].__setitem__("source_content_sha256", "0" * 64))


def test_morpheme_surface_must_match_parent_token():
    invalid(lambda p: p["morphemes"][0].__setitem__("surface", "systeX"))


def test_morphology_morpheme_must_belong_to_same_token():
    invalid(lambda p: p["morphology_annotations"][0]["morpheme_refs"].append("morpheme:reference:systems:stem"))


def test_pos_requires_upos_or_xpos():
    bundle = reference_linguistic_annotation_bundle()
    token = bundle.tokens[0]
    prov = bundle.provenance_records[0]
    with pytest.raises(ValidationError):
        PartOfSpeechAnnotation(
            annotation_id="pos:test",
            token_ref=token.token_id,
            tagset="custom",
            provenance_ref=prov.provenance_id,
        )


def test_custom_xpos_is_allowed():
    bundle = reference_linguistic_annotation_bundle()
    token = bundle.tokens[0]
    prov = bundle.provenance_records[0]
    ann = PartOfSpeechAnnotation(
        annotation_id="pos:test",
        token_ref=token.token_id,
        xpos="NN",
        tagset="Penn Treebank",
        provenance_ref=prov.provenance_id,
    )
    assert ann.xpos == "NN"


def test_dependency_root_semantics_are_enforced():
    bundle = reference_linguistic_annotation_bundle()
    with pytest.raises(ValidationError):
        DependencyRelation(
            relation_id="dep:test",
            parse_ref=bundle.dependency_parses[0].parse_id,
            dependent_token_ref=bundle.tokens[0].token_id,
            head_token_ref=None,
            relation="nsubj",
            provenance_ref=bundle.provenance_records[0].provenance_id,
        )


def test_complete_dependency_parse_requires_every_token_once():
    invalid(lambda p: p["dependency_parses"][0]["relation_refs"].pop())


def test_complete_dependency_parse_requires_exactly_one_root():
    def mutate(p):
        p["dependency_relations"][1]["head_token_ref"] = None
        p["dependency_relations"][1]["relation"] = "root"
    invalid(mutate)


def test_dependency_cycles_are_rejected():
    def mutate(p):
        # systems -> water while water -> systems, leaving one root converted to period
        p["dependency_relations"][0]["head_token_ref"] = p["tokens"][0]["token_id"]
        p["dependency_relations"][0]["relation"] = "dep"
        p["dependency_relations"][3]["head_token_ref"] = None
        p["dependency_relations"][3]["relation"] = "root"
    invalid(mutate)


def test_constituency_unknown_child_is_rejected():
    invalid(lambda p: p["constituency_nodes"][0]["child_node_refs"].append("node:missing"))


def test_constituency_cycles_are_rejected():
    def mutate(p):
        p["constituency_nodes"][1]["child_node_refs"] = [p["constituency_nodes"][0]["node_id"]]
    invalid(mutate)


def test_machine_annotations_remain_advisory_and_non_authoritative():
    c = contract_document()
    assert c["principles"]["machine_annotations_are_advisory"] is True
    assert c["boundaries"]["core_promotes_model_annotation_to_truth"] is False
    assert c["boundaries"]["core_resolves_annotation_disagreement"] is False


def test_core_defines_annotations_but_does_not_execute_nlp():
    c = contract_document()
    assert c["boundaries"]["core_tokenizes_text"] is False
    assert c["boundaries"]["core_performs_morphological_analysis"] is False
    assert c["boundaries"]["core_assigns_pos_tags"] is False
    assert c["boundaries"]["core_parses_dependency_syntax"] is False
    assert c["boundaries"]["core_parses_constituency_syntax"] is False


def test_v367_v369_scope_is_preserved():
    c = contract_document()
    assert c["roadmap_integration"]["prepares_v3670_translation_transliteration_parallel_alignment"] is True
    assert c["roadmap_integration"]["prepares_v3680_historical_language_script_variant_identity"] is True
    assert c["roadmap_integration"]["prepares_v3690_cross_lingual_semantic_exchange"] is True
    assert c["roadmap_integration"]["preserves_v3700_v3760_graph_neural_wave"] is True


def test_public_contract_route():
    app = FastAPI()
    app.include_router(linguistic_annotation.public_router)
    with TestClient(app) as client:
        response = client.get("/public/v1/linguistic-annotations/contract")
    assert response.status_code == 200
    body = response.json()
    assert body["release"] == "3.66.0"
    assert body["contract"] == CONTRACT_VERSION


def test_private_reference_route():
    app = FastAPI()
    app.include_router(linguistic_annotation.router)
    with TestClient(app) as client:
        response = client.get("/api/v1/linguistic-annotations/reference")
    assert response.status_code == 200
    body = response.json()
    assert body["release"] == "3.66.0"
    assert len(body["bundle_fingerprint_sha256"]) == 64
    assert len(body["bundle"]["tokens"]) == 4
