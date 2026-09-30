import pytest
from pydantic import ValidationError

from app.services.network_structure_community_motif import (
    CONTRACT_VERSION,
    BridgeBrokerRecord,
    CommunityAssignment,
    CommunityDetectionRun,
    CommunityProfile,
    MotifDefinition,
    MotifInstance,
    NetworkAnalysisPolicy,
    NetworkAnalysisRun,
    NetworkEdgeProjection,
    NetworkIntelligenceSnapshot,
    NetworkMetricRecord,
    NetworkStructureCommunityMotifBundle,
    NetworkStructureSnapshot,
    StructuralEquivalenceRecord,
    contract_document,
    reference_network_structure_community_motif_bundle,
)


def ref():
    return reference_network_structure_community_motif_bundle()


def invalid(mutator):
    b = ref().model_copy(deep=True)
    mutator(b)
    with pytest.raises(ValidationError):
        NetworkStructureCommunityMotifBundle.model_validate(b.model_dump(mode="json"))


def test_contract_identity():
    c = contract_document()
    assert c["ok"] is True
    assert c["release"] == "3.83.0"
    assert c["contract"] == CONTRACT_VERSION
    assert c["database_migration"] == "none"


def test_reference_bundle_roundtrip():
    b = ref()
    rebuilt = NetworkStructureCommunityMotifBundle.model_validate(b.model_dump(mode="json"))
    assert rebuilt.fingerprint() == b.fingerprint()


@pytest.mark.parametrize("name", [
    "centrality_is_not_importance",
    "community_membership_is_not_affiliation",
    "motif_participation_is_not_coordination",
    "bridge_score_is_not_influence",
    "structural_equivalence_is_not_identity",
    "network_structure_is_not_causality",
    "network_analysis_is_not_wrongdoing",
    "analytical_edge_projection_is_not_graph_fact",
])
def test_contract_principles(name):
    assert contract_document()["principles"][name] is True


@pytest.mark.parametrize("name", [
    "core_executes_large_scale_network_analysis",
    "runtime_may_mutate_evidence_graph",
    "runtime_may_promote_relationships",
    "community_assignment_may_create_affiliation_edge",
    "motif_instance_may_create_coordination_edge",
    "centrality_may_be_used_as_evidence_strength",
    "v383_creates_evidence_edge",
])
def test_contract_boundaries_false(name):
    assert contract_document()["boundaries"][name] is False


@pytest.mark.parametrize("name", [
    "extends_v3820_relationship_discovery",
    "prepares_v3840_explainable_connection_paths_evidence_chains",
    "prepares_v3850_multihop_research_investigation_graph_reasoning",
    "preserves_v3760_evidence_validation_boundary",
])
def test_roadmap_flags(name):
    assert contract_document()["roadmap_integration"][name] is True


@pytest.mark.parametrize("field", [
    "centrality_is_not_importance",
    "community_membership_is_not_affiliation",
    "motif_participation_is_not_coordination",
    "bridge_score_is_not_influence",
    "structural_equivalence_is_not_identity",
    "network_structure_is_not_causality",
    "network_analysis_is_not_wrongdoing",
])
def test_bundle_invariants(field):
    assert getattr(ref(), field) is True


@pytest.mark.parametrize("field", [
    "relationship_graph_mutation_performed",
    "evidence_graph_mutation_performed",
    "identity_graph_mutation_performed",
])
def test_bundle_mutations_false(field):
    assert getattr(ref(), field) is False


def test_policy_defaults_are_non_actuating():
    p = NetworkAnalysisPolicy(network_analysis_policy_id="policy:test")
    assert p.centrality_can_establish_importance is False
    assert p.community_membership_can_establish_affiliation is False
    assert p.motif_participation_can_establish_coordination is False
    assert p.network_analysis_can_establish_wrongdoing is False


def test_edge_self_reference_rejected():
    d = ref().edge_projections[0].model_dump(); d["object_entity_ref"] = d["subject_entity_ref"]
    with pytest.raises(ValidationError): NetworkEdgeProjection.model_validate(d)


def test_edge_requires_exactly_one_upstream_binding():
    d = ref().edge_projections[0].model_dump(); d["connection_candidate_ref"] = ref().relationship_discovery_hypothesis_bundle.connection_candidates[0].connection_candidate_id
    with pytest.raises(ValidationError): NetworkEdgeProjection.model_validate(d)


def test_edge_state_must_match_bound_object():
    d = ref().edge_projections[0].model_dump(); d["epistemic_state"] = "candidate"
    with pytest.raises(ValidationError): NetworkEdgeProjection.model_validate(d)


def test_weight_requires_semantics():
    d = ref().edge_projections[0].model_dump(); d["weight_semantics"] = None
    with pytest.raises(ValidationError): NetworkEdgeProjection.model_validate(d)


def test_structure_requires_unique_entities():
    d = ref().structure_snapshots[0].model_dump(); d["entity_refs"].append(d["entity_refs"][0])
    with pytest.raises(ValidationError): NetworkStructureSnapshot.model_validate(d)


def test_structure_requires_unique_edges():
    d = ref().structure_snapshots[0].model_dump(); d["edge_projection_refs"].append(d["edge_projection_refs"][0])
    with pytest.raises(ValidationError): NetworkStructureSnapshot.model_validate(d)


def test_run_time_order_enforced():
    d = ref().analysis_runs[0].model_dump(); d["started_at"] = "2026-10-01T00:00:00Z"; d["completed_at"] = "2026-09-30T00:00:00Z"
    with pytest.raises(ValidationError): NetworkAnalysisRun.model_validate(d)


def test_assignment_score_requires_semantics():
    d = ref().community_assignments[0].model_dump(); d["membership_score_semantics"] = None
    with pytest.raises(ValidationError): CommunityAssignment.model_validate(d)


def test_profile_label_requires_generation_basis():
    d = ref().community_profiles[0].model_dump(); d["label_generated_from"] = None
    with pytest.raises(ValidationError): CommunityProfile.model_validate(d)


def test_motif_score_requires_semantics():
    d = ref().motif_instances[0].model_dump(); d["motif_score_semantics"] = None
    with pytest.raises(ValidationError): MotifInstance.model_validate(d)


def test_structural_equivalence_self_pair_rejected():
    d = ref().structural_equivalence_records[0].model_dump(); d["entity_b_ref"] = d["entity_a_ref"]
    with pytest.raises(ValidationError): StructuralEquivalenceRecord.model_validate(d)


@pytest.mark.parametrize("mutator", [
    lambda b: setattr(b.edge_projections[0], "subject_entity_ref", "entity:missing"),
    lambda b: setattr(b.edge_projections[0], "object_entity_ref", "entity:missing"),
    lambda b: setattr(b.edge_projections[0], "source_observed_relationship_ref", "observed:missing"),
    lambda b: setattr(b.edge_projections[1], "connection_hypothesis_ref", "hypothesis:missing"),
    lambda b: setattr(b.edge_projections[1], "promotion_gate_ref", "gate:missing"),
    lambda b: setattr(b.structure_snapshots[0], "entity_refs", ["entity:missing", b.structure_snapshots[0].entity_refs[1]]),
    lambda b: setattr(b.structure_snapshots[0], "edge_projection_refs", ["edge:missing"]),
    lambda b: setattr(b.structure_snapshots[0], "relationship_discovery_snapshot_ref", "snapshot:missing"),
    lambda b: setattr(b.analysis_runs[0], "network_structure_snapshot_ref", "snapshot:missing"),
    lambda b: setattr(b.analysis_runs[0], "network_analysis_policy_ref", "policy:missing"),
    lambda b: setattr(b.metric_records[0], "network_analysis_run_ref", "run:missing"),
    lambda b: setattr(b.metric_records[0], "network_structure_snapshot_ref", "snapshot:missing"),
    lambda b: setattr(b.metric_records[0], "target_entity_ref", "entity:missing"),
    lambda b: setattr(b.community_runs[0], "network_structure_snapshot_ref", "snapshot:missing"),
    lambda b: setattr(b.community_runs[0], "network_analysis_policy_ref", "policy:missing"),
    lambda b: setattr(b.community_assignments[0], "community_detection_run_ref", "community-run:missing"),
    lambda b: setattr(b.community_assignments[0], "network_structure_snapshot_ref", "snapshot:missing"),
    lambda b: setattr(b.community_assignments[0], "entity_ref", "entity:missing"),
    lambda b: setattr(b.community_profiles[0], "community_detection_run_ref", "community-run:missing"),
    lambda b: setattr(b.community_profiles[0], "member_entity_refs", ["entity:missing"]),
    lambda b: setattr(b.motif_instances[0], "motif_definition_ref", "motif-def:missing"),
    lambda b: setattr(b.motif_instances[0], "network_structure_snapshot_ref", "snapshot:missing"),
    lambda b: setattr(b.motif_instances[0], "detected_by_run_ref", "run:missing"),
    lambda b: setattr(b.motif_instances[0], "participating_entity_refs", ["entity:missing", b.motif_instances[0].participating_entity_refs[1]]),
    lambda b: setattr(b.motif_instances[0], "participating_edge_projection_refs", ["edge:missing"]),
    lambda b: setattr(b.bridge_broker_records[0], "network_analysis_run_ref", "run:missing"),
    lambda b: setattr(b.bridge_broker_records[0], "network_structure_snapshot_ref", "snapshot:missing"),
    lambda b: setattr(b.bridge_broker_records[0], "entity_ref", "entity:missing"),
    lambda b: setattr(b.bridge_broker_records[0], "community_ids", ["community:missing"]),
    lambda b: setattr(b.structural_equivalence_records[0], "network_analysis_run_ref", "run:missing"),
    lambda b: setattr(b.structural_equivalence_records[0], "network_structure_snapshot_ref", "snapshot:missing"),
    lambda b: setattr(b.structural_equivalence_records[0], "entity_a_ref", "entity:missing"),
    lambda b: setattr(b.intelligence_snapshots[0], "network_structure_snapshot_ref", "snapshot:missing"),
    lambda b: setattr(b.intelligence_snapshots[0], "network_analysis_policy_refs", ["policy:missing"]),
    lambda b: setattr(b.intelligence_snapshots[0], "network_analysis_run_refs", ["run:missing"]),
    lambda b: setattr(b.intelligence_snapshots[0], "network_metric_record_refs", ["metric:missing"]),
    lambda b: setattr(b.intelligence_snapshots[0], "community_detection_run_refs", ["community-run:missing"]),
    lambda b: setattr(b.intelligence_snapshots[0], "community_assignment_refs", ["assignment:missing"]),
    lambda b: setattr(b.intelligence_snapshots[0], "community_profile_refs", ["profile:missing"]),
    lambda b: setattr(b.intelligence_snapshots[0], "motif_definition_refs", ["motif-def:missing"]),
    lambda b: setattr(b.intelligence_snapshots[0], "motif_instance_refs", ["motif:missing"]),
    lambda b: setattr(b.intelligence_snapshots[0], "bridge_broker_record_refs", ["bridge:missing"]),
    lambda b: setattr(b.intelligence_snapshots[0], "structural_equivalence_record_refs", ["structural:missing"]),
])
def test_bundle_rejects_unresolved_references(mutator):
    invalid(mutator)


def test_structure_must_contain_edge_endpoints():
    b = ref().model_copy(deep=True)
    b.structure_snapshots[0].entity_refs = [b.structure_snapshots[0].entity_refs[0], "entity:missing"]
    with pytest.raises(ValidationError): NetworkStructureCommunityMotifBundle.model_validate(b.model_dump(mode="json"))


def test_community_profile_must_match_assignments():
    invalid(lambda b: setattr(b.community_profiles[0], "member_entity_refs", [b.community_profiles[0].member_entity_refs[0]]))


def test_motif_node_count_must_match_definition():
    b = ref().model_copy(deep=True); b.motif_definitions[0].required_node_count = 3
    with pytest.raises(ValidationError): NetworkStructureCommunityMotifBundle.model_validate(b.model_dump(mode="json"))


def test_motif_edge_count_must_match_definition():
    b = ref().model_copy(deep=True); b.motif_definitions[0].required_edge_count = 3
    with pytest.raises(ValidationError): NetworkStructureCommunityMotifBundle.model_validate(b.model_dump(mode="json"))


@pytest.mark.parametrize("collection,attr", [
    ("policies", "network_analysis_policy_id"),
    ("edge_projections", "network_edge_projection_id"),
    ("structure_snapshots", "network_structure_snapshot_id"),
    ("analysis_runs", "network_analysis_run_id"),
    ("metric_records", "network_metric_record_id"),
    ("community_runs", "community_detection_run_id"),
    ("community_assignments", "community_assignment_id"),
    ("community_profiles", "community_profile_id"),
    ("motif_definitions", "motif_definition_id"),
    ("motif_instances", "motif_instance_id"),
    ("bridge_broker_records", "bridge_broker_record_id"),
    ("structural_equivalence_records", "structural_equivalence_record_id"),
    ("intelligence_snapshots", "network_intelligence_snapshot_id"),
])
def test_duplicate_ids_rejected(collection, attr):
    b = ref().model_copy(deep=True)
    items = getattr(b, collection)
    items.append(items[0].model_copy(deep=True))
    with pytest.raises(ValidationError): NetworkStructureCommunityMotifBundle.model_validate(b.model_dump(mode="json"))


def test_schema_generation():
    schema = NetworkStructureCommunityMotifBundle.model_json_schema()
    assert schema["title"] == "NetworkStructureCommunityMotifBundle"
    assert "$defs" in schema


@pytest.mark.parametrize("obj", [
    lambda b: b.policies[0], lambda b: b.edge_projections[0], lambda b: b.structure_snapshots[0],
    lambda b: b.analysis_runs[0], lambda b: b.metric_records[0], lambda b: b.community_runs[0],
    lambda b: b.community_assignments[0], lambda b: b.community_profiles[0], lambda b: b.motif_definitions[0],
    lambda b: b.motif_instances[0], lambda b: b.bridge_broker_records[0], lambda b: b.structural_equivalence_records[0],
    lambda b: b.intelligence_snapshots[0],
])
def test_object_fingerprints_are_sha256(obj):
    fp = obj(ref()).fingerprint()
    assert len(fp) == 64
    int(fp, 16)


def test_contract_reference_counts():
    c = contract_document()["reference"]
    assert c["edge_projections"] == 2
    assert c["metric_records"] == 2
    assert c["community_assignments"] == 2
    assert c["communities"] == 1
    assert c["motif_instances"] == 1
    assert c["bridge_broker_records"] == 1
    assert c["structural_equivalence_records"] == 1


def test_reference_preserves_edge_epistemic_states():
    states = {x.epistemic_state.value for x in ref().edge_projections}
    assert states == {"source-observed", "hypothesis"}


def test_reference_does_not_include_candidate_as_fact():
    assert all(x.edge_projection_is_not_graph_fact for x in ref().edge_projections)


def test_network_runtime_is_non_mutating():
    run = ref().analysis_runs[0]
    assert run.runtime_may_mutate_evidence_graph is False
    assert run.runtime_may_promote_relationships is False


def test_community_assignments_are_not_affiliations():
    assert all(x.community_membership_is_not_affiliation for x in ref().community_assignments)


def test_motif_instance_is_not_coordination():
    assert ref().motif_instances[0].motif_participation_is_not_coordination is True


def test_bridge_record_is_not_influence():
    assert ref().bridge_broker_records[0].bridge_score_is_not_influence is True


def test_structural_equivalence_is_not_identity():
    assert ref().structural_equivalence_records[0].structural_equivalence_is_not_identity is True
