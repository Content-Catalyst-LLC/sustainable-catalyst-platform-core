from copy import deepcopy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.main import create_app
from app.routers import coreference_referential_identity
from app.services.coreference_referential_identity import (
    CORE_RELEASE,
    CONTRACT_VERSION,
    EXTENDS_CONTRACTS,
    CoreferenceChain,
    CoreferenceLink,
    CoreferenceReferentialIdentityBundle,
    IdentityBindingState,
    ReferentAnchor,
    ReferentCandidate,
    ReferentCandidateSet,
    ReferenceExpression,
    ReferenceExpressionKind,
    ReferentialIdentityBinding,
    ReferentialIdentityPolicy,
    ReferentialInterpretation,
    ResolutionRelationKind,
    ResolutionState,
    contract_document,
    reference_coreference_referential_identity_bundle,
)
from app.services.discourse_rhetorical_semantics import CONTRACT_VERSION as V42_CONTRACT


def ref():
    return reference_coreference_referential_identity_bundle()


def payload():
    return ref().model_dump(mode="python")


def invalid(mutator):
    p = deepcopy(payload())
    mutator(p)
    with pytest.raises(ValidationError):
        CoreferenceReferentialIdentityBundle.model_validate(p)


def test_release_identity():
    assert CORE_RELEASE == "4.3.0"
    assert CONTRACT_VERSION == "sc.core.coreference-reference-referential-identity-intelligence.v1"
    version = tuple(int(x) for x in Settings().version.split("."))
    assert version >= (4, 3, 0)
    assert ref().release == "4.3.0"


def test_predecessor_is_v42_discourse_semantics():
    assert ref().predecessor_contract == V42_CONTRACT
    assert ref().discourse_semantics.release == "4.2.0"
    assert ref().discourse_semantics.contract == V42_CONTRACT


def test_dependency_order_is_governed():
    assert ref().extends_contracts == EXTENDS_CONTRACTS
    assert "sc.core.entity-resolution-identity-graph-foundation.v1" in EXTENDS_CONTRACTS
    invalid(lambda p: p["extends_contracts"].reverse())


def test_reference_counts():
    c = contract_document()["reference"]
    assert c["reference_expressions"] == 1
    assert c["referents"] == 5
    assert c["candidate_sets"] == 1
    assert c["candidates"] == 3
    assert c["accepted_candidate_sets"] == 1
    assert c["coreference_links"] == 1
    assert c["coreference_chains"] == 1
    assert c["identity_bindings"] == 2
    assert c["deferred_identity_bindings"] == 2
    assert c["resolved_reference_expressions"] == 1
    assert c["unresolved_reference_expressions"] == 0


def test_v41_unresolved_source_mention_is_preserved():
    mentions = {x.mention_id: x for x in ref().discourse_semantics.context_semantics.mentions}
    mention = mentions["mention:it-unresolved"]
    assert mention.mention_kind.value == "unresolved-reference"
    assert mention.surface_text == "It"
    assert contract_document()["reference"]["v410_unresolved_mentions_preserved"] == 1


def test_v43_resolves_by_overlay_not_rewrite():
    interpretation = ref().interpretations[0]
    assert interpretation.unresolved_reference_expression_refs == []
    assert interpretation.interpretation_does_not_rewrite_predecessor_objects is True
    assert interpretation.metadata["resolution_overlays_v4.1_without_rewriting_v4.1"] is True


def test_reference_expression_binds_exact_source_mention():
    expression = ref().reference_expressions[0]
    assert expression.mention_ref == "mention:it-unresolved"
    assert expression.context_ref == "context:policy-note:sentence-2"
    assert expression.surface_text == "It"
    assert expression.expression_kind == ReferenceExpressionKind.pronoun


def test_ranked_candidates_preserve_alternatives():
    candidates = sorted(ref().candidates, key=lambda x: x.rank)
    assert [x.referent_ref for x in candidates] == [
        "referent:proposal",
        "referent:estimate",
        "referent:rejection-event",
    ]
    assert [x.confidence for x in candidates] == [0.82, 0.12, 0.06]


def test_selected_candidate_requires_review():
    candidate_set = ref().candidate_sets[0]
    assert candidate_set.selection_state == ResolutionState.accepted
    assert candidate_set.selected_candidate_ref == "candidate:it:proposal"
    assert candidate_set.reviewer_ref == "reviewer:reference-resolution:v1"


def test_selected_candidate_is_accepted():
    candidates = {x.candidate_id: x for x in ref().candidates}
    selected = candidates[ref().candidate_sets[0].selected_candidate_ref]
    assert selected.state == ResolutionState.accepted
    assert selected.referent_ref == "referent:proposal"


def test_coreference_link_matches_selected_candidate():
    link = ref().coreference_links[0]
    assert link.reference_expression_ref == "reference-expression:it"
    assert link.antecedent_referent_ref == "referent:proposal"
    assert link.relation_kind == ResolutionRelationKind.anaphora
    assert link.state == ResolutionState.accepted
    assert link.reviewer_ref


def test_coreference_chain_preserves_mentions():
    chain = ref().coreference_chains[0]
    assert chain.mention_refs == ["mention:proposal", "mention:it-unresolved"]
    assert chain.referent_refs == ["referent:proposal"]
    assert chain.chain_is_interpretation_not_entity_merge is True


def test_generic_institution_identity_binding_remains_deferred():
    bindings = {x.identity_binding_id: x for x in ref().identity_bindings}
    assert bindings["identity-binding:commission:deferred"].state == IdentityBindingState.deferred
    assert bindings["identity-binding:ministry:deferred"].state == IdentityBindingState.deferred
    assert all(x.selected_entity_ref is None for x in bindings.values())
    assert all(x.identity_graph_mutation_authorized is False for x in bindings.values())


def test_policy_preserves_identity_boundary():
    p = ref().policy
    assert p.coreference_is_distinct_from_canonical_identity is True
    assert p.source_description_does_not_establish_canonical_identity is True
    assert p.identity_binding_requires_upstream_identity_governance is True
    assert p.identity_graph_mutation_authorized is False


def test_contract_boundaries_are_explicit():
    b = contract_document()["boundaries"]
    assert b["core_autonomously_selects_referent"] is False
    assert b["resolution_score_establishes_identity"] is False
    assert b["coreference_link_establishes_canonical_identity"] is False
    assert b["accepted_resolution_rewrites_v410_source"] is False
    assert b["source_description_establishes_entity_identity"] is False
    assert b["referential_identity_binding_merges_entities"] is False
    assert b["identity_graph_mutation_performed"] is False
    assert b["relationship_graph_mutation_performed"] is False
    assert b["evidence_graph_mutation_performed"] is False
    assert b["context_graph_mutation_performed"] is False


def test_no_database_migration():
    assert ref().database_migration == "none"
    assert contract_document()["database_migration"] == "none"


def test_reference_expression_mention_must_resolve():
    invalid(lambda p: p["reference_expressions"][0].__setitem__("mention_ref", "mention:missing"))


def test_reference_expression_context_must_resolve():
    invalid(lambda p: p["reference_expressions"][0].__setitem__("context_ref", "context:missing"))


def test_reference_expression_context_must_match_mention():
    invalid(lambda p: p["reference_expressions"][0].__setitem__("context_ref", "context:policy-note:sentence-1"))


def test_reference_expression_surface_must_preserve_source():
    invalid(lambda p: p["reference_expressions"][0].__setitem__("surface_text", "That"))


def test_reference_expression_candidate_set_must_resolve():
    invalid(lambda p: p["reference_expressions"][0].__setitem__("candidate_set_ref", "candidate-set:missing"))


def test_candidate_set_back_reference_must_match():
    invalid(lambda p: p["candidate_sets"][0].__setitem__("reference_expression_ref", "reference-expression:missing"))


def test_referent_requires_source_anchor():
    p = ref().referents[0].model_dump(mode="python")
    p["source_mention_ref"] = None
    p["source_frame_ref"] = None
    p["source_segment_ref"] = None
    p["canonical_entity_ref"] = None
    with pytest.raises(ValidationError):
        ReferentAnchor.model_validate(p)


def test_referent_source_mention_must_resolve():
    invalid(lambda p: p["referents"][0].__setitem__("source_mention_ref", "mention:missing"))


def test_referent_source_frame_must_resolve():
    invalid(lambda p: p["referents"][2].__setitem__("source_frame_ref", "frame:missing"))


def test_candidate_set_candidate_refs_must_resolve():
    invalid(lambda p: p["candidate_sets"][0]["candidate_refs"].__setitem__(0, "candidate:missing"))


def test_candidate_set_must_enumerate_exact_candidates():
    invalid(lambda p: p["candidate_sets"][0]["candidate_refs"].pop())


def test_candidate_referent_must_resolve():
    invalid(lambda p: p["candidates"][0].__setitem__("referent_ref", "referent:missing"))


def test_candidate_set_ref_must_resolve():
    invalid(lambda p: p["candidates"][0].__setitem__("candidate_set_ref", "candidate-set:missing"))


def test_candidate_ranks_must_be_unique():
    invalid(lambda p: p["candidates"][1].__setitem__("rank", 1))


def test_selected_candidate_must_be_in_candidate_refs():
    p = ref().candidate_sets[0].model_dump(mode="python")
    p["selected_candidate_ref"] = "candidate:missing"
    with pytest.raises(ValidationError):
        ReferentCandidateSet.model_validate(p)


def test_accepted_candidate_set_requires_reviewer():
    p = ref().candidate_sets[0].model_dump(mode="python")
    p["reviewer_ref"] = None
    with pytest.raises(ValidationError):
        ReferentCandidateSet.model_validate(p)


def test_unresolved_candidate_set_cannot_select():
    p = ref().candidate_sets[0].model_dump(mode="python")
    p["selection_state"] = ResolutionState.unresolved
    with pytest.raises(ValidationError):
        ReferentCandidateSet.model_validate(p)


def test_bundle_selected_candidate_must_be_accepted():
    invalid(lambda p: p["candidates"][0].__setitem__("state", "reviewed"))


def test_coreference_link_reference_expression_must_resolve():
    invalid(lambda p: p["coreference_links"][0].__setitem__("reference_expression_ref", "reference-expression:missing"))


def test_coreference_link_referent_must_resolve():
    invalid(lambda p: p["coreference_links"][0].__setitem__("antecedent_referent_ref", "referent:missing"))


def test_accepted_coreference_link_requires_reviewer():
    p = ref().coreference_links[0].model_dump(mode="python")
    p["reviewer_ref"] = None
    with pytest.raises(ValidationError):
        CoreferenceLink.model_validate(p)


def test_accepted_coreference_link_must_match_selected_candidate():
    invalid(lambda p: p["coreference_links"][0].__setitem__("antecedent_referent_ref", "referent:estimate"))


def test_coreference_chain_mentions_must_resolve():
    invalid(lambda p: p["coreference_chains"][0]["mention_refs"].__setitem__(1, "mention:missing"))


def test_coreference_chain_links_must_resolve():
    invalid(lambda p: p["coreference_chains"][0]["coreference_link_refs"].__setitem__(0, "link:missing"))


def test_identity_binding_referent_must_resolve():
    invalid(lambda p: p["identity_bindings"][0].__setitem__("referent_ref", "referent:missing"))


def test_identity_binding_mentions_must_resolve():
    invalid(lambda p: p["identity_bindings"][0]["mention_refs"].__setitem__(0, "mention:missing"))


def test_deferred_identity_binding_cannot_select_entity():
    p = ref().identity_bindings[0].model_dump(mode="python")
    p["candidate_entity_refs"] = ["entity:candidate:1"]
    p["selected_entity_ref"] = "entity:candidate:1"
    with pytest.raises(ValidationError):
        ReferentialIdentityBinding.model_validate(p)


def test_accepted_identity_binding_requires_evidence_and_review():
    p = ref().identity_bindings[0].model_dump(mode="python")
    p["state"] = IdentityBindingState.accepted
    p["candidate_entity_refs"] = ["entity:candidate:1"]
    p["selected_entity_ref"] = "entity:candidate:1"
    with pytest.raises(ValidationError):
        ReferentialIdentityBinding.model_validate(p)


def test_interpretation_discourse_ref_must_resolve():
    invalid(lambda p: p["interpretations"][0].__setitem__("discourse_interpretation_ref", "discourse-interpretation:missing"))


def test_interpretation_reference_refs_must_resolve():
    invalid(lambda p: p["interpretations"][0]["reference_expression_refs"].__setitem__(0, "reference-expression:missing"))


def test_interpretation_candidate_set_refs_must_resolve():
    invalid(lambda p: p["interpretations"][0]["candidate_set_refs"].__setitem__(0, "candidate-set:missing"))


def test_interpretation_link_refs_must_resolve():
    invalid(lambda p: p["interpretations"][0]["coreference_link_refs"].__setitem__(0, "link:missing"))


def test_interpretation_chain_refs_must_resolve():
    invalid(lambda p: p["interpretations"][0]["coreference_chain_refs"].__setitem__(0, "chain:missing"))


def test_interpretation_binding_refs_must_resolve():
    invalid(lambda p: p["interpretations"][0]["identity_binding_refs"].__setitem__(0, "binding:missing"))


def test_provenance_subjects_must_resolve():
    invalid(lambda p: p["provenance_records"][0]["subject_refs"].__setitem__(0, "object:missing"))


def test_snapshot_discourse_fingerprint_must_match():
    invalid(lambda p: p["snapshots"][0].__setitem__("discourse_semantics_fingerprint_sha256", "0" * 64))


def test_snapshot_interpretation_ref_must_resolve():
    invalid(lambda p: p["snapshots"][0]["referential_interpretation_refs"].__setitem__(0, "interpretation:missing"))


def test_reference_fingerprint_is_deterministic():
    assert ref().fingerprint() == reference_coreference_referential_identity_bundle().fingerprint()
    assert len(ref().fingerprint()) == 64


def test_contract_reports_roadmap_handoffs():
    r = contract_document()["roadmap_integration"]
    assert r["closes_v410_v420_reference_deferral"] is True
    assert r["prepares_v440_temporal_spatial_language_grounding"] is True
    assert r["prepares_v470_cross_document_context_graph"] is True


def test_router_contract_surface():
    app = FastAPI()
    app.include_router(coreference_referential_identity.router)
    app.include_router(coreference_referential_identity.public_router)
    client = TestClient(app)
    private = client.get("/v1/referential-identity/contract")
    public = client.get("/public/v1/referential-identity/contract")
    assert private.status_code == 200
    assert public.status_code == 200
    assert private.json()["release"] == "4.3.0"
    assert public.json()["contract"] == CONTRACT_VERSION


def test_router_reference_surface():
    app = FastAPI()
    app.include_router(coreference_referential_identity.router)
    client = TestClient(app)
    body = client.get("/v1/referential-identity/reference").json()
    assert body["ok"] is True
    assert body["bundle"]["release"] == "4.3.0"
    assert body["bundle_fingerprint_sha256"] == ref().fingerprint()


def test_validation_routes_accept_reference_objects():
    app = FastAPI()
    app.include_router(coreference_referential_identity.router)
    client = TestClient(app)
    cases = [
        ("validate-reference-expression", ref().reference_expressions[0]),
        ("validate-candidate", ref().candidates[0]),
        ("validate-candidate-set", ref().candidate_sets[0]),
        ("validate-coreference-link", ref().coreference_links[0]),
        ("validate-coreference-chain", ref().coreference_chains[0]),
        ("validate-identity-binding", ref().identity_bindings[0]),
        ("validate-interpretation", ref().interpretations[0]),
    ]
    for route, obj in cases:
        response = client.post(f"/v1/referential-identity/{route}", json=obj.model_dump(mode="json"))
        assert response.status_code == 200, (route, response.text)
        assert response.json()["ok"] is True


def test_validation_route_accepts_bundle():
    app = FastAPI()
    app.include_router(coreference_referential_identity.router)
    client = TestClient(app)
    response = client.post("/v1/referential-identity/validate-bundle", json=ref().model_dump(mode="json"))
    assert response.status_code == 200
    assert response.json()["fingerprint_sha256"] == ref().fingerprint()


def test_main_app_mounts_v43_routes():
    app = create_app(Settings())
    paths = {route.path for route in app.routes}
    assert "/v1/referential-identity/contract" in paths
    assert "/public/v1/referential-identity/contract" in paths


def test_policy_model_is_strict_about_graph_mutation():
    p = ReferentialIdentityPolicy(policy_id="policy:test")
    assert p.identity_graph_mutation_authorized is False
    with pytest.raises(ValidationError):
        ReferentialIdentityPolicy(policy_id="policy:test", identity_graph_mutation_authorized=True)


def test_reference_expression_model_requires_identity_boundary():
    p = ref().reference_expressions[0].model_dump(mode="python")
    p["expression_is_not_canonical_identity"] = False
    with pytest.raises(ValidationError):
        ReferenceExpression.model_validate(p)


def test_candidate_model_rejects_truth_probability_boundary_change():
    p = ref().candidates[0].model_dump(mode="python")
    p["score_is_not_truth_probability"] = False
    with pytest.raises(ValidationError):
        ReferentCandidate.model_validate(p)


def test_chain_model_rejects_entity_merge_boundary_change():
    p = ref().coreference_chains[0].model_dump(mode="python")
    p["chain_is_interpretation_not_entity_merge"] = False
    with pytest.raises(ValidationError):
        CoreferenceChain.model_validate(p)


def test_identity_binding_model_rejects_graph_mutation_authorization():
    p = ref().identity_bindings[0].model_dump(mode="python")
    p["identity_graph_mutation_authorized"] = True
    with pytest.raises(ValidationError):
        ReferentialIdentityBinding.model_validate(p)
