import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.services.entity_resolution_identity_graph import *
from app.routers import entity_resolution_identity_graph


def ref():
    return reference_entity_resolution_identity_graph_bundle()


def test_release():
    assert CORE_RELEASE == "3.77.0"


def test_contract():
    assert CONTRACT_VERSION == "sc.core.entity-resolution-identity-graph-foundation.v1"


def test_roundtrip():
    b = ref()
    rebuilt = EntityResolutionIdentityGraphBundle.model_validate(b.model_dump(mode="json"))
    assert rebuilt.fingerprint() == b.fingerprint()


def test_fingerprint_deterministic():
    assert ref().fingerprint() == ref().fingerprint()


def test_reference_has_two_pre_resolution_entities():
    assert len(ref().entities) == 2


def test_reference_has_aliases():
    assert len(ref().aliases) == 3


def test_reference_has_verified_identifiers():
    assert len(ref().identifier_assertions) == 2
    assert all(x.verification_state == IdentifierState.verified for x in ref().identifier_assertions)


def test_reference_shared_identifier_value():
    values = {x.identifier_value for x in ref().identifier_assertions}
    assert values == {"SYN-NRC-001"}


def test_shared_identifier_not_auto_identity():
    assert all(x.shared_identifier_is_not_automatically_same_entity for x in ref().identifier_assertions)


def test_source_assertion_not_canonical_identity():
    assert all(x.source_assertion_is_not_canonical_identity for x in ref().source_identity_assertions)


def test_alias_not_identity_proof():
    assert all(x.alias_is_not_identity_proof for x in ref().aliases)


def test_canonical_record_preserves_disagreement():
    assert all(x.canonical_record_does_not_imply_all_sources_agree for x in ref().entities)


def test_identity_evidence_independent_of_model():
    assert all(x.independent_of_match_model for x in ref().identity_evidence_items)


def test_model_score_not_identity_evidence():
    assert all(x.model_score_is_not_identity_evidence for x in ref().identity_evidence_items)


def test_policy_blocks_probability_identity():
    assert ref().resolution_policies[0].match_probability_can_establish_identity is False


def test_policy_blocks_name_identity():
    assert ref().resolution_policies[0].shared_name_can_establish_identity is False


def test_policy_blocks_identifier_review_bypass():
    assert ref().resolution_policies[0].shared_identifier_can_bypass_review is False


def test_policy_blocks_automatic_merge():
    assert ref().resolution_policies[0].automatic_merge_allowed is False


def test_policy_blocks_automatic_split():
    assert ref().resolution_policies[0].automatic_split_allowed is False


def test_candidate_is_not_identity_fact():
    assert ref().candidate_matches[0].is_identity_fact is False


def test_candidate_is_not_equivalence_edge():
    assert ref().candidate_matches[0].is_canonical_equivalence_edge is False


def test_match_probability_not_identity_fact():
    assert ref().candidate_matches[0].match_probability_is_not_identity_fact is True


def test_same_name_not_identity_fact():
    assert ref().candidate_matches[0].same_name_is_not_identity_fact is True


def test_automated_resolver_cannot_merge():
    assert ref().candidate_matches[0].automated_resolution_may_not_merge_entities is True


def test_candidate_supported_has_two_reviews():
    assert len(ref().candidate_matches[0].review_refs) == 2


def test_two_independent_reviewers():
    assert len({x.reviewer_ref for x in ref().identity_reviews}) == 2


def test_reviews_independent_of_model():
    assert all(x.reviewer_independent_of_match_model for x in ref().identity_reviews)


def test_reviews_model_signal_context_only():
    assert all(x.model_scores_are_context_not_identity_evidence for x in ref().identity_reviews)


def test_review_does_not_merge():
    assert all(x.review_does_not_itself_merge_entities for x in ref().identity_reviews)


def test_merge_authorized():
    a = ref().mutation_authorizations[0]
    assert a.operation == IdentityMutationKind.merge
    assert a.decision == IdentityMutationDecision.authorized


def test_merge_requires_two_sources_one_result():
    a = ref().mutation_authorizations[0]
    assert len(a.source_entity_refs) == 2
    assert len(a.proposed_result_entity_refs) == 1


def test_authorization_model_output_not_evidence():
    assert ref().mutation_authorizations[0].model_outputs_counted_as_identity_evidence is False


def test_authorization_model_output_cannot_authorize():
    assert ref().mutation_authorizations[0].model_outputs_can_authorize_identity_mutation is False


def test_authorization_is_not_mutation():
    assert ref().mutation_authorizations[0].actual_identity_graph_mutation_performed is False


def test_authorization_requires_downstream_mutation():
    assert ref().mutation_authorizations[0].authorization_requires_downstream_audited_mutation is True


def test_snapshot_immutable():
    assert ref().identity_graph_snapshots[0].immutable_snapshot is True


def test_snapshot_candidate_not_equivalence_edge():
    assert ref().identity_graph_snapshots[0].candidate_matches_are_not_canonical_equivalence_edges is True


def test_snapshot_identity_graph_distinct_from_evidence_graph():
    assert ref().identity_graph_snapshots[0].identity_graph_is_distinct_from_evidence_graph is True


def test_snapshot_authorization_not_applied():
    assert ref().identity_graph_snapshots[0].authorized_mutation_is_not_applied_in_snapshot is True


def test_audit_append_only():
    assert all(x.append_only_audit_event for x in ref().audit_records)


def test_bad_alias_entity_rejected():
    b = ref().model_copy(deep=True)
    b.aliases[0].entity_ref = "entity:missing"
    with pytest.raises(ValidationError):
        EntityResolutionIdentityGraphBundle.model_validate(b.model_dump(mode="json"))


def test_bad_identifier_entity_rejected():
    b = ref().model_copy(deep=True)
    b.identifier_assertions[0].entity_ref = "entity:missing"
    with pytest.raises(ValidationError):
        EntityResolutionIdentityGraphBundle.model_validate(b.model_dump(mode="json"))


def test_verified_identifier_without_verifier_rejected():
    d = ref().identifier_assertions[0].model_dump()
    d["verified_by_refs"] = []
    with pytest.raises(ValidationError):
        ExternalIdentifierAssertion.model_validate(d)


def test_bad_source_assertion_alias_rejected():
    b = ref().model_copy(deep=True)
    b.source_identity_assertions[0].alias_refs = ["alias:missing"]
    with pytest.raises(ValidationError):
        EntityResolutionIdentityGraphBundle.model_validate(b.model_dump(mode="json"))


def test_bad_entity_alias_ref_rejected():
    b = ref().model_copy(deep=True)
    b.entities[0].alias_refs = ["alias:missing"]
    with pytest.raises(ValidationError):
        EntityResolutionIdentityGraphBundle.model_validate(b.model_dump(mode="json"))


def test_candidate_self_match_rejected():
    d = ref().candidate_matches[0].model_dump()
    d["right_entity_ref"] = d["left_entity_ref"]
    with pytest.raises(ValidationError):
        CandidateEntityMatch.model_validate(d)


def test_supported_candidate_without_reviews_rejected():
    d = ref().candidate_matches[0].model_dump()
    d["review_refs"] = []
    with pytest.raises(ValidationError):
        CandidateEntityMatch.model_validate(d)


def test_support_review_without_evidence_rejected():
    d = ref().identity_reviews[0].model_dump()
    d["supporting_identity_evidence_refs"] = []
    with pytest.raises(ValidationError):
        IndependentIdentityReview.model_validate(d)


def test_authorized_merge_without_candidate_rejected():
    d = ref().mutation_authorizations[0].model_dump()
    d["candidate_match_ref"] = None
    with pytest.raises(ValidationError):
        IdentityMutationAuthorization.model_validate(d)


def test_authorized_merge_without_governance_gate_rejected():
    d = ref().mutation_authorizations[0].model_dump()
    d["identifier_provenance_verified"] = False
    with pytest.raises(ValidationError):
        IdentityMutationAuthorization.model_validate(d)


def test_authorized_merge_without_evidence_rejected():
    d = ref().mutation_authorizations[0].model_dump()
    d["supporting_identity_evidence_refs"] = []
    with pytest.raises(ValidationError):
        IdentityMutationAuthorization.model_validate(d)


def test_split_shape_contract():
    d = ref().mutation_authorizations[0].model_dump()
    d.update({
        "identity_mutation_authorization_id": "identity-mutation-authorization:split:test",
        "operation": "split",
        "decision": "deferred",
        "candidate_match_ref": None,
        "source_entity_refs": [ref().entities[0].entity_id],
        "proposed_result_entity_refs": ["entity:proposed:one", "entity:proposed:two"],
        "supporting_identity_evidence_refs": [],
        "reviewer_refs": [],
        "identifier_provenance_verified": False,
        "source_assertion_provenance_verified": False,
        "contradictory_evidence_review_completed": False,
        "independent_review_completed": False,
    })
    x = IdentityMutationAuthorization.model_validate(d)
    assert x.operation == IdentityMutationKind.split


def test_invalid_split_shape_rejected():
    d = ref().mutation_authorizations[0].model_dump()
    d.update({
        "operation": "split",
        "decision": "deferred",
        "candidate_match_ref": None,
        "source_entity_refs": [ref().entities[0].entity_id, ref().entities[1].entity_id],
        "proposed_result_entity_refs": ["entity:proposed:one", "entity:proposed:two"],
    })
    with pytest.raises(ValidationError):
        IdentityMutationAuthorization.model_validate(d)


def test_bad_merge_pair_rejected():
    b = ref().model_copy(deep=True)
    b.mutation_authorizations[0].source_entity_refs = [ref().entities[0].entity_id, "entity:missing"]
    with pytest.raises(ValidationError):
        EntityResolutionIdentityGraphBundle.model_validate(b.model_dump(mode="json"))


def test_bad_snapshot_match_ref_rejected():
    b = ref().model_copy(deep=True)
    b.identity_graph_snapshots[0].candidate_match_refs = ["candidate:missing"]
    with pytest.raises(ValidationError):
        EntityResolutionIdentityGraphBundle.model_validate(b.model_dump(mode="json"))


def test_public_route():
    app = FastAPI()
    app.include_router(entity_resolution_identity_graph.public_router)
    with TestClient(app) as client:
        response = client.get("/public/v1/entity-resolution/contract")
    assert response.status_code == 200
    assert response.json()["release"] == "3.77.0"


def test_private_reference_route():
    app = FastAPI()
    app.include_router(entity_resolution_identity_graph.router)
    with TestClient(app) as client:
        response = client.get("/v1/entity-resolution/reference")
    assert response.status_code == 200
    assert response.json()["contract"] == CONTRACT_VERSION


@pytest.mark.parametrize(
    "key",
    [
        "match_probability_is_not_identity_fact",
        "same_name_is_not_identity_fact",
        "shared_identifier_requires_provenance_and_review",
        "source_identity_assertion_is_not_canonical_identity",
        "alias_is_not_identity_proof",
        "candidate_match_is_not_canonical_equivalence_edge",
        "automated_resolution_may_not_silently_merge_entities",
        "automated_resolution_may_not_silently_split_entities",
        "identity_mutation_requires_independent_evidence",
        "identity_mutation_requires_provenance",
        "authorization_is_not_identity_graph_mutation",
        "identity_graph_is_distinct_from_evidence_graph",
        "gnn_prediction_is_not_graph_fact",
    ],
)
def test_principles(key):
    assert contract_document()["principles"][key] is True


@pytest.mark.parametrize(
    "key",
    [
        "core_auto_merges_entities_from_match_score",
        "core_auto_splits_entities_from_model_output",
        "core_treats_alias_match_as_identity_proof",
        "core_treats_shared_identifier_as_unreviewed_identity_fact",
        "core_mutates_identity_graph_during_authorization",
        "runtime_may_create_canonical_equivalence_edge_from_probability",
        "identity_authorization_itself_creates_or_deletes_entity_records",
    ],
)
def test_boundaries(key):
    assert contract_document()["boundaries"][key] is False


def test_begins_new_block():
    assert contract_document()["roadmap_integration"]["begins_entity_evidence_connection_intelligence_block_v3770_through_v3900"] is True


def test_follows_gnn_wave():
    assert contract_document()["roadmap_integration"]["follows_graph_neural_wave_v3700_through_v3760"] is True


def test_prepares_v3780():
    assert contract_document()["roadmap_integration"]["prepares_temporal_identity_alias_name_variant_intelligence_v3780"] is True


def test_schema_generation():
    assert EntityResolutionIdentityGraphBundle.model_json_schema()["title"] == "EntityResolutionIdentityGraphBundle"
