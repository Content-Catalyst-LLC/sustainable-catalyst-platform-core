from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.routers import multilingual_context_semantic_alignment as api
from app.services.cross_lingual_semantic_exchange import CONTRACT_VERSION as CROSS_LINGUAL_CONTRACT_VERSION
from app.services.multilingual_context_semantic_alignment import (
    AlignmentReviewState,
    ContextAlignmentRelation,
    ContextLanguageRepresentation,
    ContextRepresentationRole,
    DivergenceDimension,
    MultilingualContextSemanticAlignmentBundle,
    contract_document,
    reference_multilingual_context_semantic_alignment_bundle,
)


def ref():
    return reference_multilingual_context_semantic_alignment_bundle()


def payload():
    return ref().model_dump(mode="json")


def invalid(mutator):
    p = payload()
    mutator(p)
    with pytest.raises((ValidationError, ValueError)):
        MultilingualContextSemanticAlignmentBundle.model_validate(p)


def test_release_identity():
    assert tuple(map(int, Settings().version.split("."))) >= (4, 8, 0)
    assert ref().release == "4.8.0"
    assert ref().contract == "sc.core.multilingual-context-semantic-alignment.v1"
    assert ref().predecessor_contract == "sc.core.cross-document-context-graph.v1"


def test_predecessor_context_graph_is_preserved():
    assert ref().context_graph.release == "4.7.0"
    assert ref().context_graph.contract == "sc.core.cross-document-context-graph.v1"


def test_cross_lingual_exchange_contract_is_embedded():
    assert CROSS_LINGUAL_CONTRACT_VERSION == "sc.core.cross-lingual-semantic-linguistic-exchange.v1"


def test_original_language_is_authoritative():
    originals = [x for x in ref().representations if x.role == ContextRepresentationRole.original]
    assert len(originals) == 1
    assert originals[0].language_ref == "language:zh"
    assert originals[0].original_language_is_authoritative is True
    assert originals[0].derived_from_representation_ref is None


def test_translations_are_derived_and_do_not_replace_original():
    derived = [x for x in ref().representations if x.role == ContextRepresentationRole.translation]
    assert len(derived) == 2
    assert {x.language_ref for x in derived} == {"language:en", "language:es"}
    assert all(x.derived_from_representation_ref == "context-representation:zh:original:v1" for x in derived)
    assert all(x.derived_representation_replaces_original is False for x in derived)
    assert all(x.original_language_is_authoritative is False for x in derived)


def test_three_languages_are_present():
    assert {x.language_ref for x in ref().representations} == {"language:zh", "language:en", "language:es"}


def test_semantic_units_preserve_source_spans():
    assert len(ref().semantic_units) == 6
    assert all(x.source_span_is_immutable for x in ref().semantic_units)
    assert all(x.char_end > x.char_start for x in ref().semantic_units)


def test_original_proposition_retains_possibility_modality():
    unit = next(x for x in ref().semantic_units if x.unit_id == "context-unit:zh:proposal-cost:v1")
    assert unit.modality == "possibility"
    assert unit.context_graph_refs == ["thread:policy-topic-continuity:candidate"]


def test_derived_propositions_retain_modality():
    units = [x for x in ref().semantic_units if x.unit_id in {"context-unit:en:proposal-cost:v1", "context-unit:es:proposal-cost:v1"}]
    assert all(x.modality == "possibility" for x in units)


def test_proposal_alignments_are_directional_from_original():
    a = next(x for x in ref().alignments if x.alignment_id == "context-alignment:zh-en:proposal-cost:v1")
    assert a.relation == ContextAlignmentRelation.translation_correspondence
    assert a.state == AlignmentReviewState.reviewed
    assert a.source_unit_ref.startswith("context-unit:zh:")
    assert a.target_unit_ref.startswith("context-unit:en:")
    assert a.direction_is_significant is True


def test_spanish_proposal_alignment_may_remain_candidate():
    a = next(x for x in ref().alignments if x.alignment_id == "context-alignment:zh-es:proposal-cost:v1")
    assert a.state == AlignmentReviewState.candidate
    assert a.relation == ContextAlignmentRelation.near_equivalent


def test_governance_alignment_is_culturally_conditioned_not_exact_equivalence():
    a = next(x for x in ref().alignments if x.alignment_id == "context-alignment:zh-en:governance:v1")
    assert a.relation == ContextAlignmentRelation.culturally_conditioned
    assert a.relation != ContextAlignmentRelation.exact_context_equivalence
    assert a.divergence_refs == ["divergence:zh-en:governance:v1"]


def test_governance_divergence_preserves_semantic_and_cultural_dimensions():
    d = next(x for x in ref().divergences if x.divergence_id == "divergence:zh-en:governance:v1")
    assert set(d.dimensions) == {DivergenceDimension.semantic, DivergenceDimension.cultural}
    assert d.unresolved_divergence_is_preserved is True
    assert d.divergence_is_not_translation_error_by_default is True


def test_candidate_governance_divergence_may_remain_unresolved():
    d = next(x for x in ref().divergences if x.divergence_id == "divergence:zh-es:governance:v1")
    assert d.state == AlignmentReviewState.candidate
    assert d.reviewer_ref is None


def test_reviewed_alignment_requires_reviewer():
    p = payload()
    p["alignments"][0]["reviewer_ref"] = None
    with pytest.raises((ValidationError, ValueError)):
        MultilingualContextSemanticAlignmentBundle.model_validate(p)


def test_reviewed_divergence_requires_reviewer():
    p = payload()
    p["divergences"][0]["reviewer_ref"] = None
    with pytest.raises((ValidationError, ValueError)):
        MultilingualContextSemanticAlignmentBundle.model_validate(p)


def test_original_cannot_derive_from_translation():
    invalid(lambda p: p["representations"][0].__setitem__("derived_from_representation_ref", "context-representation:en:derived:v1"))


def test_derived_representation_requires_original_parent():
    invalid(lambda p: p["representations"][1].__setitem__("derived_from_representation_ref", None))


def test_derived_representation_cannot_be_authoritative():
    invalid(lambda p: p["representations"][1].__setitem__("original_language_is_authoritative", True))


def test_content_hash_is_enforced():
    invalid(lambda p: p["representations"][0].__setitem__("content_sha256", "0" * 64))


def test_alignment_must_cross_languages():
    p = payload()
    p["alignments"][0]["target_unit_ref"] = "context-unit:zh:governance:v1"
    with pytest.raises((ValidationError, ValueError)):
        MultilingualContextSemanticAlignmentBundle.model_validate(p)


def test_reference_alignment_must_start_from_original():
    p = payload()
    p["alignments"][0]["source_unit_ref"] = "context-unit:en:proposal-cost:v1"
    p["alignments"][0]["target_unit_ref"] = "context-unit:es:proposal-cost:v1"
    with pytest.raises((ValidationError, ValueError)):
        MultilingualContextSemanticAlignmentBundle.model_validate(p)


def test_context_graph_projection_is_candidate_and_non_mutating():
    projection = ref().graph_projections[0]
    assert projection.state == AlignmentReviewState.candidate
    assert projection.context_graph_thread_ref == "thread:policy-topic-continuity:candidate"
    assert projection.projection_is_contextual_hypothesis is True
    assert projection.projection_does_not_mutate_context_graph is True
    assert projection.projection_does_not_establish_object_identity is True


def test_projection_thread_must_resolve():
    invalid(lambda p: p["graph_projections"][0].__setitem__("context_graph_thread_ref", "thread:missing"))


def test_semantic_unit_context_graph_ref_must_resolve():
    invalid(lambda p: p["semantic_units"][0].__setitem__("context_graph_refs", ["thread:missing"]))


def test_interpretation_preserves_unresolved_universal_equivalence():
    unresolved = ref().interpretations[0].unresolved_refs
    assert "universal-equivalence:治理-governance-gobernanza" in unresolved
    assert "same-policy-object:v48-v47" in unresolved


def test_reviewed_interpretation_requires_reviewer():
    p = payload()
    p["interpretations"][0]["reviewer_ref"] = None
    with pytest.raises((ValidationError, ValueError)):
        MultilingualContextSemanticAlignmentBundle.model_validate(p)


def test_snapshot_preserves_both_predecessor_fingerprints():
    s = ref().snapshots[0]
    assert s.predecessor_fingerprint_sha256 == ref().context_graph.fingerprint()
    assert s.cross_lingual_exchange_fingerprint_sha256 == ref().cross_lingual_exchange.fingerprint()
    assert s.snapshot_does_not_freeze_semantic_equivalence is True


def test_snapshot_predecessor_fingerprint_must_match():
    invalid(lambda p: p["snapshots"][0].__setitem__("predecessor_fingerprint_sha256", "0" * 64))


def test_snapshot_exchange_fingerprint_must_match():
    invalid(lambda p: p["snapshots"][0].__setitem__("cross_lingual_exchange_fingerprint_sha256", "0" * 64))


def test_policy_preserves_original_and_divergence():
    policy = ref().policy
    assert policy.original_language_is_authoritative_representation is True
    assert policy.translation_is_derived_representation is True
    assert policy.culturally_conditioned_meaning_may_remain_unresolved is True
    assert policy.semantic_similarity_is_not_equivalence is True


def test_policy_forbids_graph_and_truth_promotion():
    policy = ref().policy
    assert policy.cross_language_context_projection_is_not_graph_fact is True
    assert policy.predecessor_context_graph_rewrite_authorized is False
    assert policy.identity_graph_mutation_authorized is False
    assert policy.evidence_graph_mutation_authorized is False
    assert policy.knowledge_graph_mutation_authorized is False


def test_contract_boundaries_are_explicit():
    b = contract_document()["boundaries"]
    assert b["translation_replaces_original_source"] is False
    assert b["semantic_similarity_establishes_equivalence"] is False
    assert b["translation_correspondence_establishes_concept_identity"] is False
    assert b["culturally_conditioned_alignment_establishes_universal_equivalence"] is False
    assert b["reviewed_alignment_establishes_claim_truth"] is False
    assert b["multilingual_projection_mutates_v470_context_graph"] is False
    assert b["cross_language_context_link_establishes_canonical_identity"] is False


def test_contract_graph_mutation_boundaries_are_false():
    b = contract_document()["boundaries"]
    assert b["identity_graph_mutation_performed"] is False
    assert b["evidence_graph_mutation_performed"] is False
    assert b["knowledge_graph_mutation_performed"] is False


def test_contract_principles_preserve_contextual_meaning():
    p = contract_document()["principles"]
    assert p["original_language_is_analyzed_first"] is True
    assert p["contextual_meaning_is_aligned_not_flattened"] is True
    assert p["semantic_divergence_is_first_class"] is True
    assert p["multiple_translation_interpretations_may_coexist"] is True


def test_roadmap_handoff_is_explicit():
    r = contract_document()["roadmap_integration"]
    assert r["extends_v470_cross_document_context_graph"] is True
    assert r["integrates_v3650_through_v3690_language_linguistics_core"] is True
    assert r["integrates_v410_through_v470_contextual_semantics"] is True
    assert r["prepares_v490_contextual_semantic_evaluation"] is True
    assert r["prepares_v4100_unified_contextual_intelligence_runtime"] is True


def test_reference_counts():
    r = contract_document()["reference"]
    assert r["representations"] == 3
    assert r["original_representations"] == 1
    assert r["derived_representations"] == 2
    assert r["languages"] == ["language:en", "language:es", "language:zh"]
    assert r["semantic_units"] == 6
    assert r["alignments"] == 4
    assert r["reviewed_alignments"] == 2
    assert r["candidate_alignments"] == 2
    assert r["culturally_conditioned_alignments"] == 2
    assert r["divergences"] == 2
    assert r["context_graph_projections"] == 1
    assert r["context_graph_mutations_created"] == 0
    assert r["interpretations"] == 1
    assert r["snapshots"] == 1


def test_fingerprint_is_deterministic():
    assert ref().fingerprint() == reference_multilingual_context_semantic_alignment_bundle().fingerprint()
    assert len(ref().fingerprint()) == 64


def test_contract_fingerprint_matches_bundle():
    assert contract_document()["reference"]["bundle_fingerprint_sha256"] == ref().fingerprint()


def test_all_ids_are_unique():
    assert len({x.representation_id for x in ref().representations}) == len(ref().representations)
    assert len({x.unit_id for x in ref().semantic_units}) == len(ref().semantic_units)
    assert len({x.alignment_id for x in ref().alignments}) == len(ref().alignments)
    assert len({x.divergence_id for x in ref().divergences}) == len(ref().divergences)


def test_duplicate_alignment_id_rejected():
    invalid(lambda p: p["alignments"].append(deepcopy(p["alignments"][0])))


def test_duplicate_representation_id_rejected():
    invalid(lambda p: p["representations"].append(deepcopy(p["representations"][0])))


def test_direct_router_contract_matches_service_contract():
    assert api.public_contract() == contract_document()
    assert api.contract() == contract_document()


def test_direct_router_reference_returns_bundle():
    out = api.reference()
    assert out["ok"] is True
    assert out["bundle"]["release"] == "4.8.0"
    assert out["bundle_fingerprint_sha256"] == ref().fingerprint()


def test_direct_router_representation_filter():
    out = api.reference_representations(role=ContextRepresentationRole.original)
    assert out["count"] == 1
    assert out["items"][0]["language_ref"] == "language:zh"


def test_direct_router_language_filter():
    out = api.reference_representations(language_ref="language:es")
    assert out["count"] == 1


def test_direct_router_alignment_filter():
    out = api.reference_alignments(relation=ContextAlignmentRelation.culturally_conditioned)
    assert out["count"] == 2


def test_direct_router_state_filter():
    out = api.reference_alignments(state=AlignmentReviewState.reviewed)
    assert out["count"] == 2


def test_direct_router_divergence_filter():
    out = api.reference_divergences(state=AlignmentReviewState.candidate)
    assert out["count"] == 1


def test_direct_router_validation_endpoints():
    assert api.validate_representation(ref().representations[0])["ok"] is True
    assert api.validate_alignment(ref().alignments[0])["ok"] is True
    assert api.validate_divergence(ref().divergences[0])["ok"] is True
    assert api.validate_projection(ref().graph_projections[0])["ok"] is True
    assert api.validate_interpretation(ref().interpretations[0])["ok"] is True
    assert api.validate_bundle(ref())["fingerprint_sha256"] == ref().fingerprint()


def test_model_schema_includes_core_v48_objects():
    defs = MultilingualContextSemanticAlignmentBundle.model_json_schema()["$defs"]
    for name in [
        "ContextLanguageRepresentation",
        "ContextSemanticUnit",
        "MultilingualContextAlignment",
        "SemanticDivergenceRecord",
        "ContextGraphProjectionBinding",
        "MultilingualContextInterpretation",
        "MultilingualContextSnapshot",
    ]:
        assert name in defs


def test_main_app_mounts_v48_routes():
    from app.main import create_app
    paths = {route.path for route in create_app().routes}
    assert "/v1/multilingual-context/contract" in paths
    assert "/public/v1/multilingual-context/contract" in paths
    assert "/v1/multilingual-context/reference" in paths
