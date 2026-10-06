from copy import deepcopy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.routers import discourse_rhetorical_semantics
from app.services.context_semantic_frame import CONTRACT_VERSION as V41_CONTRACT
from app.services.discourse_rhetorical_semantics import (
    CORE_RELEASE,
    CONTRACT_VERSION,
    EXTENDS_CONTRACTS,
    ArgumentRelation,
    ArgumentRelationKind,
    ArgumentRole,
    DiscourseInterpretation,
    DiscourseProvenanceRecord,
    DiscourseReviewState,
    DiscourseSegment,
    DiscourseSegmentKind,
    DiscourseSignal,
    DiscourseSnapshot,
    DiscourseStructureRhetoricalSemanticsBundle,
    InterpretationMethod,
    RhetoricalNuclearity,
    RhetoricalRelation,
    RhetoricalRelationKind,
    contract_document,
    reference_discourse_structure_rhetorical_semantics_bundle,
)


def ref():
    return reference_discourse_structure_rhetorical_semantics_bundle()


def payload():
    return ref().model_dump(mode="python")


def invalid(mutator):
    p = deepcopy(payload())
    mutator(p)
    with pytest.raises(ValidationError):
        DiscourseStructureRhetoricalSemanticsBundle.model_validate(p)


def test_release_identity():
    assert CORE_RELEASE == "4.2.0"
    assert CONTRACT_VERSION == "sc.core.discourse-structure-rhetorical-semantics.v1"
    assert Settings().version == "4.2.0"
    assert ref().release == "4.2.0"


def test_predecessor_is_v41_contextual_semantics():
    assert ref().predecessor_contract == V41_CONTRACT
    assert ref().context_semantics.release == "4.1.0"
    assert ref().context_semantics.contract == V41_CONTRACT


def test_dependency_order_is_governed():
    assert ref().extends_contracts == EXTENDS_CONTRACTS
    invalid(lambda p: p["extends_contracts"].reverse())


def test_reference_counts():
    c = contract_document()["reference"]
    assert c["segments"] == 4
    assert c["signals"] == 2
    assert c["rhetorical_relations"] == 2
    assert c["argument_units"] == 2
    assert c["argument_relations"] == 1
    assert c["interpretations"] == 1
    assert c["snapshots"] == 1
    assert c["unresolved_mentions"] == 1


def test_segment_content_is_exact_context_slice():
    contexts = {x.context_id: x for x in ref().context_semantics.contexts}
    for segment in ref().segments:
        context = contexts[segment.context_ref]
        assert context.content[segment.char_start:segment.char_end] == segment.content


def test_clause_hierarchy_is_explicit():
    segments = {x.segment_id: x for x in ref().segments}
    assert segments["discourse-segment:rejection-clause"].parent_segment_ref == "discourse-segment:sentence-1"
    assert segments["discourse-segment:revision-clause"].parent_segment_ref == "discourse-segment:sentence-1"


def test_temporal_signal_and_relation_are_explicit():
    signals = {x.signal_id: x for x in ref().signals}
    relations = {x.relation_id: x for x in ref().rhetorical_relations}
    assert signals["discourse-signal:after"].signal_text == "after"
    relation = relations["rhetorical-relation:revision-before-rejection"]
    assert relation.relation_kind == RhetoricalRelationKind.temporal_sequence
    assert relation.source_segment_refs == ["discourse-segment:revision-clause"]
    assert relation.target_segment_refs == ["discourse-segment:rejection-clause"]


def test_concessive_signal_and_relation_are_explicit():
    signals = {x.signal_id: x for x in ref().signals}
    relations = {x.relation_id: x for x in ref().rhetorical_relations}
    assert signals["discourse-signal:nevertheless"].signal_text == "nevertheless"
    assert RhetoricalRelationKind.concession in signals["discourse-signal:nevertheless"].relation_hint_kinds
    relation = relations["rhetorical-relation:concession-viability"]
    assert relation.relation_kind == RhetoricalRelationKind.concession
    assert relation.metadata["referent_selection_deferred_to_v4.3"] is True


def test_v42_preserves_v41_unresolved_reference():
    unresolved = [x for x in ref().context_semantics.mentions if x.mention_kind.value == "unresolved-reference"]
    assert len(unresolved) == 1
    assert unresolved[0].surface_text == "It"
    assert ref().interpretations[0].unresolved_reference_preserved is True
    assert ref().interpretations[0].metadata["core_does_not_select_referent"] is True


def test_argument_structure_is_rhetorical_not_truth_rating():
    unit = ref().argument_units[0]
    link = ref().argument_relations[0]
    assert unit.argument_role_does_not_establish_truth is True
    assert unit.argument_role_does_not_establish_source_credibility is True
    assert link.relation_is_rhetorical_not_evidence_grade is True
    assert link.relation_does_not_establish_truth is True


def test_relations_are_not_real_world_causal_or_evidence_proof():
    for relation in ref().rhetorical_relations:
        assert relation.relation_is_interpretation_not_source_fact is True
        assert relation.relation_does_not_establish_real_world_causality is True
        assert relation.relation_does_not_establish_evidence_strength is True
        assert relation.selected_by_core is False


def test_no_database_migration():
    assert ref().database_migration == "none"
    assert contract_document()["database_migration"] == "none"


def test_segment_hash_validation():
    p = ref().segments[0].model_dump(mode="python")
    p["content_sha256"] = "0" * 64
    with pytest.raises(ValidationError):
        DiscourseSegment.model_validate(p)


def test_segment_range_validation():
    p = ref().segments[0].model_dump(mode="python")
    p["char_end"] = p["char_start"]
    with pytest.raises(ValidationError):
        DiscourseSegment.model_validate(p)


def test_segment_context_must_resolve():
    invalid(lambda p: p["segments"][0].__setitem__("context_ref", "context:missing"))


def test_segment_provenance_must_resolve():
    invalid(lambda p: p["segments"][0].__setitem__("provenance_ref", "prov:missing"))


def test_segment_text_must_match_context_slice():
    invalid(lambda p: p["segments"][1].__setitem__("content", "Wrong text"))


def test_segment_parent_must_resolve():
    invalid(lambda p: p["segments"][1].__setitem__("parent_segment_ref", "segment:missing"))


def test_segment_parent_must_share_context():
    invalid(lambda p: p["segments"][1].__setitem__("parent_segment_ref", "discourse-segment:sentence-2"))


def test_segment_frame_must_resolve():
    invalid(lambda p: p["segments"][1]["frame_refs"].__setitem__(0, "frame:missing"))


def test_segment_frame_trigger_must_fit_segment():
    invalid(lambda p: p["segments"][1].__setitem__("char_end", 20))


def test_segment_mention_must_resolve():
    invalid(lambda p: p["segments"][1]["mention_refs"].__setitem__(0, "mention:missing"))


def test_segment_mention_must_fit_segment():
    invalid(lambda p: p["segments"][1]["mention_refs"].__setitem__(0, "mention:estimate"))


def test_signal_range_validation():
    p = ref().signals[0].model_dump(mode="python")
    p["char_end"] = p["char_start"]
    with pytest.raises(ValidationError):
        DiscourseSignal.model_validate(p)


def test_signal_context_must_resolve():
    invalid(lambda p: p["signals"][0].__setitem__("context_ref", "context:missing"))


def test_signal_text_must_match_context_slice():
    invalid(lambda p: p["signals"][0].__setitem__("signal_text", "before"))


def test_signal_host_must_resolve():
    invalid(lambda p: p["signals"][0].__setitem__("host_segment_ref", "segment:missing"))


def test_signal_host_must_share_context():
    invalid(lambda p: p["signals"][0].__setitem__("host_segment_ref", "discourse-segment:sentence-2"))


def test_relation_source_must_resolve():
    invalid(lambda p: p["rhetorical_relations"][0]["source_segment_refs"].__setitem__(0, "segment:missing"))


def test_relation_target_must_resolve():
    invalid(lambda p: p["rhetorical_relations"][0]["target_segment_refs"].__setitem__(0, "segment:missing"))


def test_relation_signal_must_resolve():
    invalid(lambda p: p["rhetorical_relations"][0]["signal_refs"].__setitem__(0, "signal:missing"))


def test_relation_signal_hint_must_be_compatible():
    invalid(lambda p: p["rhetorical_relations"][0].__setitem__("relation_kind", "cause"))


def test_relation_source_and_target_cannot_be_identical():
    p = ref().rhetorical_relations[0].model_dump(mode="python")
    p["target_segment_refs"] = list(p["source_segment_refs"])
    with pytest.raises(ValidationError):
        RhetoricalRelation.model_validate(p)


def test_non_candidate_relation_requires_reviewer():
    p = ref().rhetorical_relations[0].model_dump(mode="python")
    p["review_state"] = DiscourseReviewState.accepted
    with pytest.raises(ValidationError):
        RhetoricalRelation.model_validate(p)


def test_argument_unit_segment_must_resolve():
    invalid(lambda p: p["argument_units"][0].__setitem__("segment_ref", "segment:missing"))


def test_argument_unit_frame_must_resolve():
    invalid(lambda p: p["argument_units"][0]["frame_refs"].__setitem__(0, "frame:missing"))


def test_argument_unit_frame_must_belong_to_segment():
    invalid(lambda p: p["argument_units"][0]["frame_refs"].__setitem__(0, "frame:revision"))


def test_argument_relation_units_must_resolve():
    invalid(lambda p: p["argument_relations"][0].__setitem__("from_argument_unit_ref", "argument-unit:missing"))


def test_argument_relation_cannot_self_reference():
    p = ref().argument_relations[0].model_dump(mode="python")
    p["to_argument_unit_ref"] = p["from_argument_unit_ref"]
    with pytest.raises(ValidationError):
        ArgumentRelation.model_validate(p)


def test_interpretation_context_must_resolve():
    invalid(lambda p: p["interpretations"][0].__setitem__("context_ref", "context:missing"))


def test_interpretation_segment_must_resolve():
    invalid(lambda p: p["interpretations"][0]["segment_refs"].__setitem__(0, "segment:missing"))


def test_interpretation_relation_must_resolve():
    invalid(lambda p: p["interpretations"][0]["rhetorical_relation_refs"].__setitem__(0, "relation:missing"))


def test_non_candidate_interpretation_requires_reviewer():
    p = ref().interpretations[0].model_dump(mode="python")
    p["review_state"] = DiscourseReviewState.accepted
    with pytest.raises(ValidationError):
        DiscourseInterpretation.model_validate(p)


def test_core_never_selects_best_interpretation():
    assert ref().interpretations[0].selected_by_core is False
    assert contract_document()["boundaries"]["core_selects_best_discourse_interpretation"] is False


def test_provenance_subject_must_resolve():
    invalid(lambda p: p["provenance_records"][0]["subject_refs"].__setitem__(0, "object:missing"))


def test_model_assisted_provenance_requires_model_ref():
    with pytest.raises(ValidationError):
        DiscourseProvenanceRecord(
            provenance_id="prov:test",
            subject_refs=["segment:test"],
            method=InterpretationMethod.model_assisted,
            produced_by_ref="runtime:test",
            source_refs=["source:test"],
        )


def test_snapshot_context_fingerprint_must_match_v41_bundle():
    invalid(lambda p: p["snapshots"][0].__setitem__("context_semantics_fingerprint_sha256", "0" * 64))


def test_snapshot_interpretation_must_resolve():
    invalid(lambda p: p["snapshots"][0]["discourse_interpretation_refs"].__setitem__(0, "interpretation:missing"))


def test_snapshot_is_immutable_but_supersedable():
    s = ref().snapshots[0]
    assert s.immutable is True
    assert s.supersedable is True
    assert s.snapshot_is_not_truth_certification is True
    assert s.snapshot_does_not_mutate_graphs is True


@pytest.mark.parametrize(
    "field",
    [
        "discourse_structure_is_explicit_and_persistent",
        "discourse_analysis_preserves_source_text",
        "rhetorical_relations_preserve_provenance",
        "multiple_discourse_interpretations_may_coexist",
        "unresolved_reference_remains_unresolved",
        "machine_discourse_output_is_advisory",
        "rhetorical_relation_is_not_source_fact",
        "causal_rhetorical_relation_is_not_causal_proof",
        "evidence_relation_is_not_evidence_grade",
        "argument_role_is_not_truth_or_credibility_rating",
        "discourse_interpretation_is_not_truth_verdict",
    ],
)
def test_contract_principles(field):
    assert contract_document()["principles"][field] is True


@pytest.mark.parametrize(
    "field",
    [
        "core_executes_discourse_parser",
        "core_autonomously_infers_discourse_relations",
        "core_resolves_coreference",
        "core_selects_best_discourse_interpretation",
        "rhetorical_cause_establishes_real_world_causality",
        "rhetorical_evidence_establishes_evidence_strength",
        "argument_role_establishes_truth",
        "argument_role_establishes_source_credibility",
        "identity_graph_mutation_performed",
        "relationship_graph_mutation_performed",
        "evidence_graph_mutation_performed",
        "context_graph_mutation_performed",
    ],
)
def test_contract_false_boundaries(field):
    assert contract_document()["boundaries"][field] is False


@pytest.mark.parametrize(
    "field",
    [
        "extends_v410_context_object_semantic_frame_foundation",
        "prepares_v430_coreference_reference_identity",
        "prepares_v440_temporal_spatial_language_grounding",
        "prepares_v450_epistemic_modal_negation_certainty",
        "prepares_v460_pragmatic_meaning_speech_act_intent",
        "prepares_v470_cross_document_context_graph",
        "prepares_v480_multilingual_context_alignment",
        "prepares_v490_contextual_semantic_evaluation",
    ],
)
def test_roadmap_hooks(field):
    assert contract_document()["roadmap_integration"][field] is True


def test_public_contract_route():
    app = FastAPI()
    app.include_router(discourse_rhetorical_semantics.public_router)
    with TestClient(app) as client:
        response = client.get("/public/v1/discourse-semantics/contract")
    assert response.status_code == 200
    body = response.json()
    assert body["release"] == "4.2.0"
    assert body["contract"] == CONTRACT_VERSION
    assert body["boundaries"]["core_resolves_coreference"] is False


def test_private_reference_route():
    app = FastAPI()
    app.include_router(discourse_rhetorical_semantics.router)
    with TestClient(app) as client:
        response = client.get("/v1/discourse-semantics/reference")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert len(body["bundle_fingerprint_sha256"]) == 64
    assert body["bundle"]["release"] == "4.2.0"


def test_validate_bundle_route():
    app = FastAPI()
    app.include_router(discourse_rhetorical_semantics.router)
    with TestClient(app) as client:
        response = client.post("/v1/discourse-semantics/validate-bundle", json=ref().model_dump(mode="json"))
    assert response.status_code == 200
    assert response.json()["fingerprint_sha256"] == ref().fingerprint()


def test_main_app_mounts_v42_routes():
    from app.main import create_app
    app = create_app(Settings())
    paths = {route.path for route in app.routes}
    assert "/v1/discourse-semantics/contract" in paths
    assert "/public/v1/discourse-semantics/contract" in paths
    assert "/v1/discourse-semantics/reference" in paths


@pytest.mark.parametrize("kind", list(DiscourseSegmentKind))
def test_discourse_segment_kind_enum(kind):
    assert kind.value


@pytest.mark.parametrize("kind", list(RhetoricalRelationKind))
def test_rhetorical_relation_kind_enum(kind):
    assert kind.value


@pytest.mark.parametrize("kind", list(RhetoricalNuclearity))
def test_rhetorical_nuclearity_enum(kind):
    assert kind.value


@pytest.mark.parametrize("state", list(DiscourseReviewState))
def test_discourse_review_state_enum(state):
    assert state.value


@pytest.mark.parametrize("role", list(ArgumentRole))
def test_argument_role_enum(role):
    assert role.value


@pytest.mark.parametrize("kind", list(ArgumentRelationKind))
def test_argument_relation_kind_enum(kind):
    assert kind.value


@pytest.mark.parametrize("i", range(60))
def test_bundle_roundtrip(i):
    b = ref()
    rebuilt = DiscourseStructureRhetoricalSemanticsBundle.model_validate(b.model_dump(mode="python"))
    assert rebuilt.fingerprint() == b.fingerprint()


@pytest.mark.parametrize("i", range(50))
def test_contract_document_stable(i):
    c = contract_document()
    assert c["release"] == "4.2.0"
    assert c["contract"] == CONTRACT_VERSION
    assert c["reference"]["bundle_fingerprint_sha256"] == ref().fingerprint()


@pytest.mark.parametrize("i", range(40))
def test_snapshot_fingerprint_stable(i):
    assert ref().snapshots[0].fingerprint() == ref().snapshots[0].fingerprint()


@pytest.mark.parametrize("i", range(40))
def test_v41_context_fingerprint_stable_inside_v42(i):
    assert ref().snapshots[0].context_semantics_fingerprint_sha256 == ref().context_semantics.fingerprint()
