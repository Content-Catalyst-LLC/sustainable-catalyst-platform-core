from copy import deepcopy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.routers import context_semantic_frame
from app.services.context_semantic_frame import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    EXTENDS_CONTRACTS,
    ContextObject,
    ContextObjectSemanticFrameBundle,
    ContextScopeKind,
    ContextSemanticProvenanceRecord,
    InterpretationMethod,
    InterpretationReviewState,
    MentionKind,
    ParticipantRoleKind,
    SemanticFrameKind,
    SemanticInterpretation,
    SemanticParticipant,
    SourceContextBinding,
    contract_document,
    reference_context_object_semantic_frame_bundle,
)


def ref():
    return reference_context_object_semantic_frame_bundle()


def payload():
    return ref().model_dump(mode="json", exclude_none=True)


def invalid(mutator):
    p = payload()
    mutator(p)
    with pytest.raises(ValidationError):
        ContextObjectSemanticFrameBundle.model_validate(p)


def test_release_and_contract_identity():
    assert CORE_RELEASE == "4.1.0"
    assert CONTRACT_VERSION == "sc.core.context-object-semantic-frame-foundation.v1"
    assert ref().release == "4.1.0"
    assert ref().contract == CONTRACT_VERSION


def test_backend_version_is_410():
    assert Settings().version == "4.1.0"


def test_extends_required_upstream_contracts():
    assert ref().extends_contracts == EXTENDS_CONTRACTS
    assert EXTENDS_CONTRACTS[0] == "sc.core.sustainable-catalyst-computational-research-core.v1"
    assert "sc.core.multilingual-text-language-object.v1" in EXTENDS_CONTRACTS
    assert "sc.core.linguistic-annotation-provenance.v1" in EXTENDS_CONTRACTS
    assert "sc.core.cross-lingual-semantic-linguistic-exchange.v1" in EXTENDS_CONTRACTS
    assert "sc.core.investigation-session-research-context-runtime.v1" in EXTENDS_CONTRACTS


def test_reference_counts():
    c = contract_document()["reference"]
    assert c["source_bindings"] == 1
    assert c["contexts"] == 3
    assert c["mentions"] == 5
    assert c["frames"] == 3
    assert c["participants"] == 5
    assert c["interpretations"] == 1
    assert c["snapshots"] == 1
    assert c["unresolved_mentions"] == 1


def test_reference_bundle_is_deterministic():
    assert ref().fingerprint() == ref().fingerprint()
    assert len(ref().fingerprint()) == 64


def test_source_hash_verified():
    source = ref().source_bindings[0].model_dump(mode="python")
    source["content_sha256"] = "0" * 64
    with pytest.raises(ValidationError):
        SourceContextBinding.model_validate(source)


def test_context_hash_verified():
    context = ref().contexts[0].model_dump(mode="python")
    context["content_sha256"] = "0" * 64
    with pytest.raises(ValidationError):
        ContextObject.model_validate(context)


def test_context_matches_canonical_source_slice():
    invalid(lambda p: p["contexts"][1].__setitem__("content", "Wrong context"))


def test_context_range_cannot_exceed_source():
    invalid(lambda p: p["contexts"][1].__setitem__("char_end", 999))


def test_context_source_binding_must_resolve():
    invalid(lambda p: p["contexts"][0].__setitem__("source_binding_ref", "context-source:missing"))


def test_context_provenance_must_resolve():
    invalid(lambda p: p["contexts"][0].__setitem__("provenance_ref", "prov:missing"))


def test_parent_context_must_resolve():
    invalid(lambda p: p["contexts"][1].__setitem__("parent_context_ref", "context:missing"))


def test_child_context_must_fit_parent():
    def mutate(p):
        p["contexts"][1]["parent_context_ref"] = p["contexts"][2]["context_id"]
    invalid(mutate)


def test_adjacency_context_must_resolve():
    invalid(lambda p: p["contexts"][1]["following_context_refs"].__setitem__(0, "context:missing"))


def test_context_cannot_reference_itself_as_adjacency():
    c = ref().contexts[1].model_dump(mode="python")
    c["following_context_refs"] = [c["context_id"]]
    with pytest.raises(ValidationError):
        ContextObject.model_validate(c)


def test_mention_surface_must_match_context_slice():
    invalid(lambda p: p["mentions"][0].__setitem__("surface_text", "committee"))


def test_mention_range_cannot_exceed_context():
    invalid(lambda p: p["mentions"][0].__setitem__("char_end", 999))


def test_mention_context_must_resolve():
    invalid(lambda p: p["mentions"][0].__setitem__("context_ref", "context:missing"))


def test_mention_provenance_must_resolve():
    invalid(lambda p: p["mentions"][0].__setitem__("provenance_ref", "prov:missing"))


def test_mention_language_must_match_context():
    invalid(lambda p: p["mentions"][0].__setitem__("language_ref", "language:fr"))


def test_unresolved_reference_is_preserved():
    mention = next(x for x in ref().mentions if x.mention_kind == MentionKind.unresolved_reference)
    assert mention.surface_text == "It"
    assert mention.unresolved_referent_allowed is True
    assert mention.mention_is_not_entity_identity is True
    assert mention.mention_is_not_evidence_fact is True


def test_v41_does_not_resolve_it_reference():
    c = contract_document()
    assert c["boundaries"]["core_resolves_coreference"] is False
    assert ref().interpretations[0].metadata["core_does_not_select_referent"] is True


def test_frame_trigger_must_match_context_slice():
    invalid(lambda p: p["frames"][0].__setitem__("trigger_text", "approved"))


def test_frame_trigger_range_cannot_exceed_context():
    invalid(lambda p: p["frames"][0].__setitem__("trigger_char_end", 999))


def test_frame_context_must_resolve():
    invalid(lambda p: p["frames"][0].__setitem__("context_ref", "context:missing"))


def test_frame_provenance_must_resolve():
    invalid(lambda p: p["frames"][0].__setitem__("provenance_ref", "prov:missing"))


def test_frame_mention_must_resolve():
    invalid(lambda p: p["frames"][0]["mention_refs"].__setitem__(0, "mention:missing"))


def test_frame_mention_must_belong_to_frame_context():
    invalid(lambda p: p["frames"][0]["mention_refs"].__setitem__(0, "mention:it-unresolved"))


def test_frame_participant_must_resolve():
    invalid(lambda p: p["frames"][0]["participant_refs"].__setitem__(0, "participant:missing"))


def test_frame_participant_must_point_back_to_frame():
    invalid(lambda p: p["frames"][0]["participant_refs"].__setitem__(0, "participant:revision-agent"))


def test_participant_requires_exactly_one_binding_target():
    p = ref().participants[0].model_dump(mode="python")
    p["proposition_context_ref"] = ref().contexts[0].context_id
    with pytest.raises(ValidationError):
        SemanticParticipant.model_validate(p)
    p = ref().participants[0].model_dump(mode="python")
    p["mention_ref"] = None
    with pytest.raises(ValidationError):
        SemanticParticipant.model_validate(p)


def test_participant_frame_must_resolve():
    invalid(lambda p: p["participants"][0].__setitem__("frame_ref", "frame:missing"))


def test_participant_mention_must_resolve():
    invalid(lambda p: p["participants"][0].__setitem__("mention_ref", "mention:missing"))


def test_participant_is_not_identity_resolution():
    assert all(x.participant_binding_is_not_identity_resolution for x in ref().participants)


def test_interpretation_frame_must_resolve():
    invalid(lambda p: p["interpretations"][0]["frame_refs"].__setitem__(0, "frame:missing"))


def test_interpretation_mention_must_resolve():
    invalid(lambda p: p["interpretations"][0]["mention_refs"].__setitem__(0, "mention:missing"))


def test_interpretation_context_must_resolve():
    invalid(lambda p: p["interpretations"][0].__setitem__("context_ref", "context:missing"))


def test_interpretation_provenance_must_resolve():
    invalid(lambda p: p["interpretations"][0].__setitem__("provenance_ref", "prov:missing"))


def test_non_candidate_interpretation_requires_reviewer():
    x = ref().interpretations[0].model_dump(mode="python")
    x["review_state"] = InterpretationReviewState.accepted
    with pytest.raises(ValidationError):
        SemanticInterpretation.model_validate(x)


def test_core_never_selects_best_interpretation():
    assert ref().interpretations[0].selected_by_core is False
    assert contract_document()["boundaries"]["core_selects_best_interpretation"] is False


def test_provenance_subject_must_resolve():
    invalid(lambda p: p["provenance_records"][0]["subject_refs"].__setitem__(0, "object:missing"))


def test_model_assisted_provenance_requires_model_ref():
    with pytest.raises(ValidationError):
        ContextSemanticProvenanceRecord(
            provenance_id="prov:test",
            subject_refs=["context:test"],
            method=InterpretationMethod.model_assisted,
            produced_by_ref="runtime:test",
            source_refs=["source:test"],
        )


def test_graph_assisted_provenance_requires_model_ref():
    with pytest.raises(ValidationError):
        ContextSemanticProvenanceRecord(
            provenance_id="prov:test",
            subject_refs=["context:test"],
            method=InterpretationMethod.graph_assisted,
            produced_by_ref="runtime:test",
            source_refs=["source:test"],
        )


def test_snapshot_references_must_resolve():
    invalid(lambda p: p["snapshots"][0]["context_refs"].__setitem__(0, "context:missing"))
    invalid(lambda p: p["snapshots"][0]["interpretation_refs"].__setitem__(0, "interpretation:missing"))


def test_snapshot_is_immutable_but_supersedable():
    s = ref().snapshots[0]
    assert s.immutable is True
    assert s.supersedable is True
    assert s.snapshot_is_not_truth_certification is True
    assert s.snapshot_does_not_mutate_graphs is True


def test_no_database_migration():
    assert ref().database_migration == "none"
    assert contract_document()["database_migration"] == "none"


@pytest.mark.parametrize(
    "field",
    [
        "original_language_remains_primary",
        "translations_remain_derived",
        "context_is_explicit_and_persistent",
        "semantic_interpretation_preserves_provenance",
        "multiple_interpretations_may_coexist",
        "unresolved_reference_may_be_preserved",
        "machine_interpretation_is_advisory",
        "context_selection_does_not_promote_source_authority",
        "semantic_frame_is_not_evidence_fact",
        "interpretation_is_not_truth_verdict",
    ],
)
def test_contract_principles(field):
    assert contract_document()["principles"][field] is True


@pytest.mark.parametrize(
    "field",
    [
        "core_executes_semantic_parser",
        "core_resolves_coreference",
        "core_infers_discourse_relations",
        "core_selects_best_interpretation",
        "semantic_frame_establishes_source_truth",
        "mention_establishes_entity_identity",
        "context_selection_promotes_epistemic_state",
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
        "prepares_v420_discourse_structure_rhetorical_semantics",
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
    app.include_router(context_semantic_frame.public_router)
    with TestClient(app) as client:
        response = client.get("/public/v1/context-semantics/contract")
    assert response.status_code == 200
    body = response.json()
    assert body["release"] == "4.1.0"
    assert body["contract"] == CONTRACT_VERSION
    assert body["principles"]["context_is_explicit_and_persistent"] is True


def test_private_reference_route():
    app = FastAPI()
    app.include_router(context_semantic_frame.router)
    with TestClient(app) as client:
        response = client.get("/v1/context-semantics/reference")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert len(body["bundle_fingerprint_sha256"]) == 64
    assert body["bundle"]["release"] == "4.1.0"


def test_validate_bundle_route():
    app = FastAPI()
    app.include_router(context_semantic_frame.router)
    with TestClient(app) as client:
        response = client.post("/v1/context-semantics/validate-bundle", json=payload())
    assert response.status_code == 200
    assert response.json()["fingerprint_sha256"] == ref().fingerprint()


def test_main_app_mounts_v41_routes():
    from app.main import create_app
    app = create_app(Settings())
    paths = {route.path for route in app.routes}
    assert "/v1/context-semantics/contract" in paths
    assert "/public/v1/context-semantics/contract" in paths
    assert "/v1/context-semantics/reference" in paths


@pytest.mark.parametrize("scope", list(ContextScopeKind))
def test_context_scope_enum(scope):
    assert scope.value


@pytest.mark.parametrize("kind", list(SemanticFrameKind))
def test_semantic_frame_enum(kind):
    assert kind.value


@pytest.mark.parametrize("kind", list(MentionKind))
def test_mention_kind_enum(kind):
    assert kind.value


@pytest.mark.parametrize("role", list(ParticipantRoleKind))
def test_participant_role_enum(role):
    assert role.value


@pytest.mark.parametrize("method", list(InterpretationMethod))
def test_interpretation_method_enum(method):
    assert method.value


@pytest.mark.parametrize("state", list(InterpretationReviewState))
def test_interpretation_review_state_enum(state):
    assert state.value


@pytest.mark.parametrize("i", range(60))
def test_bundle_roundtrip(i):
    b = ref()
    rebuilt = ContextObjectSemanticFrameBundle.model_validate(b.model_dump(mode="python"))
    assert rebuilt.fingerprint() == b.fingerprint()


@pytest.mark.parametrize("i", range(50))
def test_contract_document_stable(i):
    c = contract_document()
    assert c["release"] == "4.1.0"
    assert c["contract"] == CONTRACT_VERSION
    assert c["reference"]["bundle_fingerprint_sha256"] == ref().fingerprint()


@pytest.mark.parametrize("i", range(40))
def test_snapshot_fingerprint_stable(i):
    assert ref().snapshots[0].fingerprint() == ref().snapshots[0].fingerprint()
