import pytest
from pydantic import ValidationError

from app.services.relationship_discovery_hypotheses import (
    CONTRACT_VERSION,
    ConnectionCandidate,
    ConnectionCandidateState,
    ConnectionHypothesis,
    ConnectionHypothesisEvidencePosition,
    ConnectionHypothesisState,
    RelationshipDiscoveryHypothesisBundle,
    RelationshipDiscoverySignal,
    RelationshipSignalKind,
    SourceObservedRelationship,
    contract_document,
    reference_relationship_discovery_hypothesis_bundle,
)


def ref():
    return reference_relationship_discovery_hypothesis_bundle()


def invalid(mutator):
    b = ref().model_copy(deep=True)
    mutator(b)
    with pytest.raises(ValidationError):
        RelationshipDiscoveryHypothesisBundle.model_validate(b.model_dump(mode="json"))


def test_contract_version(): assert CONTRACT_VERSION == "sc.core.relationship-discovery-connection-hypothesis.v1"
def test_release(): assert contract_document()["release"] == "3.82.0"
def test_reference_policy_count(): assert len(ref().policies) == 1
def test_reference_signal_count(): assert len(ref().signals) == 2
def test_reference_observed_count(): assert len(ref().source_observed_relationships) == 1
def test_reference_candidate_count(): assert len(ref().connection_candidates) == 1
def test_reference_hypothesis_count(): assert len(ref().connection_hypotheses) == 1
def test_reference_position_count(): assert len(ref().evidence_positions) == 2
def test_reference_review_count(): assert len(ref().reviews) == 2
def test_reference_gate_count(): assert len(ref().promotion_gates) == 1
def test_reference_snapshot_count(): assert len(ref().snapshots) == 1
def test_hypothesis_supported_for_validation(): assert ref().connection_hypotheses[0].state == ConnectionHypothesisState.supported_for_validation
def test_gate_eligible_for_validation(): assert ref().promotion_gates[0].gate_state == "eligible-for-evidence-validation"
def test_bundle_fingerprint_stable(): assert ref().fingerprint() == ref().fingerprint()
def test_bundle_fingerprint_length(): assert len(ref().fingerprint()) == 64
def test_contract_fingerprint_length(): assert len(contract_document()["reference"]["bundle_fingerprint_sha256"]) == 64


@pytest.mark.parametrize("field", [
    "cooccurrence_is_not_relationship",
    "shared_attribute_is_not_relationship",
    "graph_proximity_is_not_relationship",
    "model_score_is_not_relationship_fact",
    "source_observation_is_not_canonical_relationship_fact",
    "hypothesis_is_not_graph_fact",
])
def test_bundle_principle_flags(field):
    assert getattr(ref(), field) is True


@pytest.mark.parametrize("field", [
    "relationship_graph_mutation_performed",
    "evidence_graph_mutation_performed",
    "identity_graph_mutation_performed",
])
def test_bundle_mutations_false(field):
    assert getattr(ref(), field) is False


@pytest.mark.parametrize("field", [
    "core_infers_relationship_truth_from_cooccurrence",
    "core_infers_relationship_truth_from_shared_attribute",
    "core_infers_relationship_truth_from_graph_proximity",
    "core_infers_relationship_truth_from_embedding_similarity",
    "core_treats_model_score_as_relationship_evidence",
    "core_treats_source_count_as_relationship_evidence",
    "core_auto_promotes_connection_candidate",
    "core_auto_promotes_connection_hypothesis",
    "core_creates_evidence_edge_in_v382",
    "core_mutates_relationship_graph_during_discovery",
    "core_mutates_evidence_graph_during_discovery",
    "core_mutates_identity_graph_during_discovery",
])
def test_contract_boundaries_false(field):
    assert contract_document()["boundaries"][field] is False


@pytest.mark.parametrize("field", [
    "cooccurrence_is_not_relationship",
    "shared_attribute_is_not_relationship",
    "graph_proximity_is_not_relationship",
    "embedding_similarity_is_not_relationship",
    "model_score_is_not_relationship_fact",
    "source_observation_is_not_canonical_relationship_fact",
    "hypothesis_is_not_graph_fact",
    "relationship_promotion_requires_separate_evidence_validation",
])
def test_contract_principles_true(field):
    assert contract_document()["principles"][field] is True


@pytest.mark.parametrize("field", [
    "source_bound_relationship_observations",
    "multi_signal_connection_discovery",
    "explicit_connection_candidates",
    "connection_hypothesis_objects",
    "supporting_contradicting_contextual_evidence_positions",
    "independence_group_tracking",
    "independent_hypothesis_review",
    "governed_promotion_gates",
    "immutable_relationship_discovery_snapshots",
    "deterministic_object_fingerprints",
])
def test_capabilities_true(field):
    assert contract_document()["capabilities"][field] is True


@pytest.mark.parametrize("field", [
    "extends_v3770_entity_resolution_foundation",
    "extends_v3800_cross_source_entity_reconciliation",
    "extends_v3810_documentary_source_model",
    "prepares_v3830_network_structure_community_motif_intelligence",
    "prepares_v3840_explainable_connection_paths_evidence_chains",
    "prepares_v3850_multihop_research_investigation_graph_reasoning",
    "preserves_v3760_evidence_validation_boundary",
])
def test_roadmap_flags(field):
    assert contract_document()["roadmap_integration"][field] is True


def test_signal_self_reference_rejected():
    d = ref().signals[0].model_dump(); d["object_entity_ref"] = d["subject_entity_ref"]
    with pytest.raises(ValidationError): RelationshipDiscoverySignal.model_validate(d)


def test_signal_score_requires_semantics():
    d = ref().signals[0].model_dump(); d["score_semantics"] = None
    with pytest.raises(ValidationError): RelationshipDiscoverySignal.model_validate(d)


def test_documentary_signal_requires_source_context():
    d = ref().signals[0].model_dump(); d["source_refs"] = []; d["documentary_interpretation_refs"] = []
    with pytest.raises(ValidationError): RelationshipDiscoverySignal.model_validate(d)


def test_signal_time_order_enforced():
    d = ref().signals[0].model_dump(); d["valid_from"] = "2026-01-02"; d["valid_to"] = "2026-01-01"
    with pytest.raises(ValidationError): RelationshipDiscoverySignal.model_validate(d)


def test_observed_relationship_self_reference_rejected():
    d = ref().source_observed_relationships[0].model_dump(); d["object_entity_ref"] = d["subject_entity_ref"]
    with pytest.raises(ValidationError): SourceObservedRelationship.model_validate(d)


def test_observed_relationship_time_order_enforced():
    d = ref().source_observed_relationships[0].model_dump(); d["valid_from"] = "2026-01-02"; d["valid_to"] = "2026-01-01"
    with pytest.raises(ValidationError): SourceObservedRelationship.model_validate(d)


def test_candidate_self_reference_rejected():
    d = ref().connection_candidates[0].model_dump(); d["object_entity_ref"] = d["subject_entity_ref"]
    with pytest.raises(ValidationError): ConnectionCandidate.model_validate(d)


def test_candidate_score_requires_semantics():
    d = ref().connection_candidates[0].model_dump(); d["candidate_score_semantics"] = None
    with pytest.raises(ValidationError): ConnectionCandidate.model_validate(d)


def test_supported_candidate_requires_observed_context():
    d = ref().connection_candidates[0].model_dump(); d["source_observed_relationship_refs"] = []
    with pytest.raises(ValidationError): ConnectionCandidate.model_validate(d)


def test_hypothesis_self_reference_rejected():
    d = ref().connection_hypotheses[0].model_dump(); d["object_entity_ref"] = d["subject_entity_ref"]
    with pytest.raises(ValidationError): ConnectionHypothesis.model_validate(d)


def test_supported_hypothesis_requires_positions():
    d = ref().connection_hypotheses[0].model_dump(); d["evidence_position_refs"] = []
    with pytest.raises(ValidationError): ConnectionHypothesis.model_validate(d)


def test_supported_hypothesis_requires_reviews():
    d = ref().connection_hypotheses[0].model_dump(); d["review_refs"] = []
    with pytest.raises(ValidationError): ConnectionHypothesis.model_validate(d)


def test_evidence_position_requires_material():
    d = ref().evidence_positions[0].model_dump();
    d["identity_evidence_refs"] = []; d["documentary_interpretation_refs"] = []; d["document_segment_refs"] = []; d["source_observed_relationship_refs"] = []
    with pytest.raises(ValidationError): ConnectionHypothesisEvidencePosition.model_validate(d)


@pytest.mark.parametrize("mutator", [
    lambda b: setattr(b.signals[0], "subject_entity_ref", "entity:missing"),
    lambda b: setattr(b.signals[0], "object_entity_ref", "entity:missing"),
    lambda b: setattr(b.signals[0], "source_refs", ["documentary-source:missing"]),
    lambda b: setattr(b.signals[0], "document_segment_refs", ["segment:missing"]),
    lambda b: setattr(b.signals[0], "documentary_interpretation_refs", ["interpretation:missing"]),
    lambda b: setattr(b.signals[0], "identity_evidence_refs", ["evidence:missing"]),
    lambda b: setattr(b.source_observed_relationships[0], "subject_entity_ref", "entity:missing"),
    lambda b: setattr(b.source_observed_relationships[0], "source_refs", ["documentary-source:missing"]),
    lambda b: setattr(b.source_observed_relationships[0], "document_segment_refs", ["segment:missing"]),
    lambda b: setattr(b.source_observed_relationships[0], "documentary_interpretation_refs", ["interpretation:missing"]),
    lambda b: setattr(b.source_observed_relationships[0], "identity_evidence_refs", ["evidence:missing"]),
    lambda b: setattr(b.connection_candidates[0], "signal_refs", ["signal:missing"]),
    lambda b: setattr(b.connection_candidates[0], "source_observed_relationship_refs", ["observed:missing"]),
    lambda b: setattr(b.connection_hypotheses[0], "connection_candidate_ref", "candidate:missing"),
    lambda b: setattr(b.connection_hypotheses[0], "evidence_position_refs", ["position:missing"]),
    lambda b: setattr(b.connection_hypotheses[0], "review_refs", ["review:missing"]),
    lambda b: setattr(b.evidence_positions[0], "connection_hypothesis_ref", "hypothesis:missing"),
    lambda b: setattr(b.evidence_positions[0], "identity_evidence_refs", ["evidence:missing"]),
    lambda b: setattr(b.evidence_positions[0], "documentary_interpretation_refs", ["interpretation:missing"]),
    lambda b: setattr(b.evidence_positions[0], "document_segment_refs", ["segment:missing"]),
    lambda b: setattr(b.evidence_positions[0], "source_refs", ["documentary-source:missing"]),
    lambda b: setattr(b.evidence_positions[0], "source_observed_relationship_refs", ["observed:missing"]),
    lambda b: setattr(b.reviews[0], "connection_hypothesis_ref", "hypothesis:missing"),
    lambda b: setattr(b.reviews[0], "considered_evidence_position_refs", ["position:missing"]),
    lambda b: setattr(b.reviews[0], "considered_signal_refs", ["signal:missing"]),
    lambda b: setattr(b.promotion_gates[0], "connection_hypothesis_ref", "hypothesis:missing"),
    lambda b: setattr(b.promotion_gates[0], "relationship_discovery_policy_ref", "policy:missing"),
    lambda b: setattr(b.promotion_gates[0], "required_evidence_position_refs", ["position:missing"]),
    lambda b: setattr(b.promotion_gates[0], "required_review_refs", ["review:missing"]),
    lambda b: setattr(b.snapshots[0], "policy_refs", ["policy:missing"]),
    lambda b: setattr(b.snapshots[0], "signal_refs", ["signal:missing"]),
    lambda b: setattr(b.snapshots[0], "source_observed_relationship_refs", ["observed:missing"]),
    lambda b: setattr(b.snapshots[0], "connection_candidate_refs", ["candidate:missing"]),
    lambda b: setattr(b.snapshots[0], "connection_hypothesis_refs", ["hypothesis:missing"]),
    lambda b: setattr(b.snapshots[0], "evidence_position_refs", ["position:missing"]),
    lambda b: setattr(b.snapshots[0], "review_refs", ["review:missing"]),
    lambda b: setattr(b.snapshots[0], "promotion_gate_refs", ["gate:missing"]),
    lambda b: setattr(b.snapshots[0], "unresolved_hypothesis_refs", ["hypothesis:missing"]),
])
def test_bundle_rejects_unresolved_references(mutator):
    invalid(mutator)


def test_candidate_signal_endpoint_mismatch_rejected():
    invalid(lambda b: setattr(b.connection_candidates[0], "object_entity_ref", b.connection_candidates[0].subject_entity_ref))


def test_hypothesis_candidate_endpoint_mismatch_rejected():
    b=ref().model_copy(deep=True)
    b.connection_hypotheses[0].subject_entity_ref, b.connection_hypotheses[0].object_entity_ref = b.connection_hypotheses[0].object_entity_ref, b.connection_hypotheses[0].subject_entity_ref
    with pytest.raises(ValidationError): RelationshipDiscoveryHypothesisBundle.model_validate(b.model_dump(mode="json"))


def test_hypothesis_relationship_type_mismatch_rejected():
    invalid(lambda b: setattr(b.connection_hypotheses[0], "relationship_type_hypothesis", "different-relationship"))


def test_duplicate_policy_ids_rejected():
    b=ref().model_copy(deep=True); b.policies.append(b.policies[0].model_copy(deep=True))
    with pytest.raises(ValidationError): RelationshipDiscoveryHypothesisBundle.model_validate(b.model_dump(mode="json"))


def test_duplicate_signal_ids_rejected():
    b=ref().model_copy(deep=True); b.signals.append(b.signals[0].model_copy(deep=True))
    with pytest.raises(ValidationError): RelationshipDiscoveryHypothesisBundle.model_validate(b.model_dump(mode="json"))


def test_duplicate_reviewers_fail_supported_gate():
    b=ref().model_copy(deep=True); b.reviews[1].reviewer_ref=b.reviews[0].reviewer_ref
    with pytest.raises(ValidationError): RelationshipDiscoveryHypothesisBundle.model_validate(b.model_dump(mode="json"))


def test_one_evidence_group_fails_supported_gate():
    b=ref().model_copy(deep=True); b.evidence_positions[1].independence_group=b.evidence_positions[0].independence_group
    with pytest.raises(ValidationError): RelationshipDiscoveryHypothesisBundle.model_validate(b.model_dump(mode="json"))


def test_gate_must_cover_hypothesis_positions():
    b=ref().model_copy(deep=True); b.promotion_gates[0].required_evidence_position_refs=[b.evidence_positions[0].evidence_position_id]
    with pytest.raises(ValidationError): RelationshipDiscoveryHypothesisBundle.model_validate(b.model_dump(mode="json"))


def test_gate_must_cover_hypothesis_reviews():
    b=ref().model_copy(deep=True); b.promotion_gates[0].required_review_refs=[b.reviews[0].connection_hypothesis_review_id]
    with pytest.raises(ValidationError): RelationshipDiscoveryHypothesisBundle.model_validate(b.model_dump(mode="json"))


def test_source_observation_not_graph_fact(): assert ref().source_observed_relationships[0].source_observation_is_not_canonical_relationship_fact is True
def test_source_assertion_not_truth_verdict(): assert ref().source_observed_relationships[0].source_assertion_is_not_truth_verdict is True
def test_observation_no_edge(): assert ref().source_observed_relationships[0].observation_does_not_create_graph_edge is True
def test_signal_not_fact(): assert all(x.signal_is_not_relationship_fact for x in ref().signals)
def test_signal_not_evidence_by_itself(): assert all(x.signal_is_not_evidence_by_itself for x in ref().signals)
def test_signal_score_not_evidence_strength(): assert all(x.score_is_not_evidence_strength for x in ref().signals)
def test_candidate_not_fact(): assert ref().connection_candidates[0].candidate_is_not_relationship_fact is True
def test_candidate_not_evidence(): assert ref().connection_candidates[0].candidate_is_not_evidence is True
def test_candidate_no_edge(): assert ref().connection_candidates[0].candidate_does_not_create_graph_edge is True
def test_hypothesis_not_fact(): assert ref().connection_hypotheses[0].hypothesis_is_not_graph_fact is True
def test_hypothesis_not_evidence(): assert ref().connection_hypotheses[0].hypothesis_is_not_evidence is True
def test_hypothesis_no_edge(): assert ref().connection_hypotheses[0].hypothesis_does_not_create_graph_edge is True
def test_reviews_independent(): assert all(x.independent_review for x in ref().reviews)
def test_reviews_no_truth_promotion(): assert all(x.review_does_not_establish_relationship_truth for x in ref().reviews)
def test_reviews_no_edge(): assert all(x.review_does_not_create_graph_edge for x in ref().reviews)
def test_gate_requires_v376(): assert ref().promotion_gates[0].separate_v376_evidence_validation_required is True
def test_gate_no_cooccurrence(): assert ref().promotion_gates[0].cooccurrence_can_satisfy_gate is False
def test_gate_no_shared_attribute(): assert ref().promotion_gates[0].shared_attribute_can_satisfy_gate is False
def test_gate_no_graph_proximity(): assert ref().promotion_gates[0].graph_proximity_can_satisfy_gate is False
def test_gate_no_embedding_similarity(): assert ref().promotion_gates[0].embedding_similarity_can_satisfy_gate is False
def test_gate_no_model_score(): assert ref().promotion_gates[0].model_score_can_satisfy_gate is False
def test_gate_no_source_count(): assert ref().promotion_gates[0].source_count_can_satisfy_gate is False
def test_v382_cannot_create_evidence_edge(): assert ref().promotion_gates[0].v382_may_create_evidence_edge is False
def test_snapshot_immutable(): assert ref().snapshots[0].immutable_snapshot is True
def test_snapshot_no_truth_verdict(): assert ref().snapshots[0].snapshot_is_not_relationship_truth_verdict is True
def test_snapshot_no_mutation(): assert ref().snapshots[0].snapshot_does_not_mutate_graphs is True
def test_documentary_upstream_release(): assert ref().public_record_documentary_source_bundle.document_existence_is_not_claim_truth is True
def test_identity_boundary_preserved(): assert ref().public_record_documentary_source_bundle.identity_graph_mutation_performed is False
def test_evidence_boundary_preserved(): assert ref().public_record_documentary_source_bundle.evidence_graph_mutation_performed is False
