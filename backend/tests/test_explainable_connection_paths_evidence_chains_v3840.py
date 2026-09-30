import pytest
from pydantic import ValidationError

from app.services.explainable_connection_paths_evidence_chains import (
    CONTRACT_VERSION,
    AlternativeConnectionPathComparison,
    ConnectionPathEvidenceSnapshot,
    ConnectionPathPolicy,
    ConnectionPathStep,
    EvidenceChain,
    EvidenceChainItem,
    ExplainableConnectionPath,
    ExplainableConnectionPathsEvidenceChainsBundle,
    PathBottleneckRecord,
    PathContradictionMarker,
    contract_document,
    reference_explainable_connection_paths_evidence_chains_bundle,
)


def ref():
    return reference_explainable_connection_paths_evidence_chains_bundle()


def revalidate(b):
    return ExplainableConnectionPathsEvidenceChainsBundle.model_validate(b.model_dump(mode="json"))


def invalid(mutator):
    b = ref().model_copy(deep=True)
    mutator(b)
    with pytest.raises((ValidationError, ValueError)):
        revalidate(b)


def test_contract_identity():
    c = contract_document()
    assert c["ok"] is True
    assert c["release"] == "3.84.0"
    assert c["contract"] == CONTRACT_VERSION
    assert c["database_migration"] == "none"


@pytest.mark.parametrize("key", [
    "path_existence_is_not_relationship_truth",
    "shortest_path_is_not_strongest_evidence",
    "path_length_is_not_causal_distance",
    "multiple_paths_are_not_independent_corroboration",
    "evidence_chain_is_not_truth_verdict",
    "missing_path_is_not_no_relationship",
    "algorithmic_path_selection_is_not_investigator_conclusion",
    "contradictions_remain_visible",
    "epistemic_edge_state_is_preserved",
])
def test_contract_principles_true(key):
    assert contract_document()["principles"][key] is True


@pytest.mark.parametrize("key", [
    "runtime_may_mutate_evidence_graph",
    "runtime_may_mutate_identity_graph",
    "runtime_may_promote_relationships",
    "v384_creates_evidence_edge",
    "v384_creates_canonical_relationship_fact",
])
def test_contract_boundaries_false(key):
    assert contract_document()["boundaries"][key] is False


def test_reference_bundle_validates():
    assert revalidate(ref()).fingerprint() == ref().fingerprint()


def test_reference_counts():
    b = ref()
    assert len(b.policies) == 1
    assert len(b.path_steps) == 2
    assert len(b.connection_paths) == 2
    assert len(b.evidence_chain_items) == 2
    assert len(b.contradiction_markers) == 1
    assert len(b.evidence_chains) == 1
    assert len(b.alternative_path_comparisons) == 1
    assert len(b.bottleneck_records) == 1
    assert len(b.snapshots) == 1


@pytest.mark.parametrize("obj_getter", [
    lambda b: b.policies[0],
    lambda b: b.path_steps[0],
    lambda b: b.connection_paths[0],
    lambda b: b.evidence_chain_items[0],
    lambda b: b.contradiction_markers[0],
    lambda b: b.evidence_chains[0],
    lambda b: b.alternative_path_comparisons[0],
    lambda b: b.bottleneck_records[0],
    lambda b: b.snapshots[0],
])
def test_object_fingerprint_is_sha256(obj_getter):
    fp = obj_getter(ref()).fingerprint()
    assert len(fp) == 64
    int(fp, 16)


@pytest.mark.parametrize("field", [
    "path_existence_is_not_relationship_truth",
    "shortest_path_is_not_strongest_evidence",
    "path_length_is_not_causal_distance",
    "multiple_paths_are_not_independent_corroboration",
    "evidence_chain_is_not_truth_verdict",
    "missing_path_is_not_no_relationship",
    "algorithmic_path_selection_is_not_investigator_conclusion",
])
def test_top_level_invariants_true(field):
    assert getattr(ref(), field) is True


@pytest.mark.parametrize("field", [
    "relationship_graph_mutation_performed",
    "evidence_graph_mutation_performed",
    "identity_graph_mutation_performed",
])
def test_top_level_mutation_flags_false(field):
    assert getattr(ref(), field) is False


@pytest.mark.parametrize("field", [
    "shortest_path_can_establish_strongest_evidence",
    "path_length_can_establish_causal_distance",
    "multiple_paths_can_establish_independent_corroboration",
    "path_existence_can_establish_relationship_truth",
    "missing_path_can_establish_no_relationship",
])
def test_policy_forbids_epistemic_overreach(field):
    assert getattr(ref().policies[0], field) is False


@pytest.mark.parametrize("field", [
    "require_immutable_network_snapshot",
    "require_step_epistemic_state",
    "require_step_provenance",
    "require_documentary_anchor_when_available",
    "require_evidence_position_provenance",
    "preserve_source_independence_groups",
    "preserve_contradictions",
    "preserve_alternative_paths",
])
def test_policy_requires_provenance_and_context(field):
    assert getattr(ref().policies[0], field) is True


def test_primary_and_alternative_preserve_distinct_epistemic_states():
    b = ref()
    states = [x.epistemic_state.value for x in b.path_steps]
    assert states == ["source-observed", "hypothesis"]


@pytest.mark.parametrize("index,field", [
    (0, "step_is_not_relationship_fact"),
    (0, "step_is_not_causal_claim"),
    (0, "analytical_path_inclusion_does_not_promote_edge"),
    (1, "step_is_not_relationship_fact"),
    (1, "step_is_not_causal_claim"),
    (1, "analytical_path_inclusion_does_not_promote_edge"),
])
def test_path_step_boundaries(index, field):
    assert getattr(ref().path_steps[index], field) is True


@pytest.mark.parametrize("index,field", [
    (0, "path_is_explanation_not_truth_verdict"),
    (0, "shortest_path_is_not_strongest_evidence"),
    (0, "path_length_is_not_causal_distance"),
    (0, "path_does_not_mutate_graphs"),
    (1, "path_is_explanation_not_truth_verdict"),
    (1, "shortest_path_is_not_strongest_evidence"),
    (1, "path_length_is_not_causal_distance"),
    (1, "path_does_not_mutate_graphs"),
])
def test_connection_path_boundaries(index, field):
    assert getattr(ref().connection_paths[index], field) is True


@pytest.mark.parametrize("index,field", [
    (0, "item_is_not_truth_verdict"),
    (0, "source_count_is_not_evidence_strength"),
    (0, "source_repetition_is_not_independent_corroboration"),
    (1, "item_is_not_truth_verdict"),
    (1, "source_count_is_not_evidence_strength"),
    (1, "source_repetition_is_not_independent_corroboration"),
])
def test_evidence_chain_item_boundaries(index, field):
    assert getattr(ref().evidence_chain_items[index], field) is True


@pytest.mark.parametrize("field", [
    "evidence_chain_is_not_truth_verdict",
    "evidence_chain_length_is_not_strength",
    "repeated_sources_do_not_create_independence",
    "chain_does_not_promote_relationships",
])
def test_evidence_chain_boundaries(field):
    assert getattr(ref().evidence_chains[0], field) is True


def test_contradiction_remains_visible_and_non_dispositive():
    m = ref().contradiction_markers[0]
    assert m.contradiction_does_not_auto_invalidate_path is True
    assert m.contradiction_must_remain_visible is True


def test_alternative_path_is_not_independent_evidence():
    c = ref().alternative_path_comparisons[0]
    assert c.alternative_path_is_not_independent_evidence is True
    assert c.multiple_paths_do_not_establish_truth is True
    assert c.shared_source_ancestry is True


def test_bottleneck_is_not_truth_or_strength_verdict():
    b = ref().bottleneck_records[0]
    assert b.bottleneck_is_not_proof_path_is_false is True
    assert b.bottleneck_is_not_evidence_strength_score is True


def test_snapshot_is_immutable_explanatory_view():
    s = ref().snapshots[0]
    assert s.immutable_snapshot is True
    assert s.snapshot_is_explanatory_not_evidentiary_promotion is True
    assert s.snapshot_does_not_mutate_graphs is True


def test_primary_path_uses_source_observed_edge():
    b = ref()
    assert b.path_steps[0].epistemic_state.value == "source-observed"


def test_alternative_path_uses_hypothesis_edge():
    b = ref()
    assert b.path_steps[1].epistemic_state.value == "hypothesis"


def test_evidence_chain_preserves_two_independence_groups():
    assert len(ref().evidence_chains[0].independence_groups) == 2


def test_evidence_chain_preserves_qualification():
    assert {x.position.value for x in ref().evidence_chain_items} == {"supports", "qualifies"}


def test_contradiction_links_upstream_reconciliation_conflict():
    assert len(ref().contradiction_markers[0].reconciliation_conflict_refs) == 1


def test_schema_generation():
    schema = ExplainableConnectionPathsEvidenceChainsBundle.model_json_schema()
    assert schema["title"] == "ExplainableConnectionPathsEvidenceChainsBundle"
    assert "$defs" in schema


@pytest.mark.parametrize("collection,attr", [
    ("policies", "connection_path_policy_id"),
    ("path_steps", "connection_path_step_id"),
    ("connection_paths", "connection_path_id"),
    ("evidence_chain_items", "evidence_chain_item_id"),
    ("contradiction_markers", "path_contradiction_marker_id"),
    ("evidence_chains", "evidence_chain_id"),
    ("alternative_path_comparisons", "alternative_path_comparison_id"),
    ("bottleneck_records", "path_bottleneck_record_id"),
    ("snapshots", "connection_path_evidence_snapshot_id"),
])
def test_duplicate_ids_rejected(collection, attr):
    b = ref().model_copy(deep=True)
    items = getattr(b, collection)
    items.append(items[0].model_copy(deep=True))
    with pytest.raises((ValidationError, ValueError)):
        revalidate(b)


@pytest.mark.parametrize("mutator", [
    lambda b: setattr(b.path_steps[0], "from_entity_ref", "entity:missing"),
    lambda b: setattr(b.path_steps[0], "to_entity_ref", "entity:missing"),
    lambda b: setattr(b.path_steps[0], "network_edge_projection_ref", "edge:missing"),
    lambda b: setattr(b.path_steps[0], "documentary_segment_refs", ["segment:missing"]),
    lambda b: setattr(b.path_steps[0], "documentary_interpretation_refs", ["interp:missing"]),
    lambda b: setattr(b.path_steps[0], "relationship_evidence_position_refs", ["position:missing"]),
    lambda b: setattr(b.connection_paths[0], "network_structure_snapshot_ref", "snapshot:missing"),
    lambda b: setattr(b.connection_paths[0], "connection_path_policy_ref", "policy:missing"),
    lambda b: setattr(b.connection_paths[0], "start_entity_ref", "entity:missing"),
    lambda b: setattr(b.connection_paths[0], "end_entity_ref", "entity:missing"),
    lambda b: setattr(b.connection_paths[0], "step_refs", ["step:missing"]),
    lambda b: setattr(b.evidence_chain_items[0], "connection_path_ref", "path:missing"),
    lambda b: setattr(b.evidence_chain_items[0], "path_step_ref", "step:missing"),
    lambda b: setattr(b.evidence_chain_items[0], "documentary_segment_refs", ["segment:missing"]),
    lambda b: setattr(b.evidence_chain_items[0], "documentary_interpretation_refs", ["interp:missing"]),
    lambda b: setattr(b.evidence_chain_items[0], "relationship_evidence_position_refs", ["position:missing"]),
    lambda b: setattr(b.evidence_chain_items[0], "source_refs", ["source:missing"]),
    lambda b: setattr(b.contradiction_markers[0], "connection_path_ref", "path:missing"),
    lambda b: setattr(b.contradiction_markers[0], "affected_step_refs", ["step:missing"]),
    lambda b: setattr(b.contradiction_markers[0], "affected_chain_item_refs", ["item:missing"]),
    lambda b: setattr(b.contradiction_markers[0], "reconciliation_conflict_refs", ["conflict:missing"]),
    lambda b: setattr(b.evidence_chains[0], "connection_path_ref", "path:missing"),
    lambda b: setattr(b.evidence_chains[0], "item_refs", ["item:missing"]),
    lambda b: setattr(b.evidence_chains[0], "contradiction_marker_refs", ["marker:missing"]),
    lambda b: setattr(b.alternative_path_comparisons[0], "primary_path_ref", "path:missing"),
    lambda b: setattr(b.alternative_path_comparisons[0], "alternative_path_ref", "path:missing"),
    lambda b: setattr(b.alternative_path_comparisons[0], "divergence_step_refs", ["step:missing"]),
    lambda b: setattr(b.bottleneck_records[0], "connection_path_ref", "path:missing"),
    lambda b: setattr(b.bottleneck_records[0], "path_step_ref", "step:missing"),
    lambda b: setattr(b.snapshots[0], "network_intelligence_snapshot_ref", "network-intelligence:missing"),
    lambda b: setattr(b.snapshots[0], "policy_refs", ["policy:missing"]),
    lambda b: setattr(b.snapshots[0], "path_refs", ["path:missing"]),
    lambda b: setattr(b.snapshots[0], "evidence_chain_refs", ["chain:missing"]),
    lambda b: setattr(b.snapshots[0], "contradiction_marker_refs", ["marker:missing"]),
    lambda b: setattr(b.snapshots[0], "alternative_path_comparison_refs", ["comparison:missing"]),
    lambda b: setattr(b.snapshots[0], "bottleneck_record_refs", ["bottleneck:missing"]),
])
def test_bundle_rejects_unresolved_references(mutator):
    invalid(mutator)


def test_step_rejects_epistemic_state_mismatch():
    invalid(lambda b: setattr(b.path_steps[0], "epistemic_state", b.path_steps[1].epistemic_state))


def test_step_rejects_endpoint_mismatch_with_edge():
    invalid(lambda b: setattr(b.path_steps[0], "to_entity_ref", b.path_steps[0].from_entity_ref))


def test_path_rejects_noncontiguous_sequence_index():
    b = ref().model_copy(deep=True)
    p = b.connection_paths[0]
    alt = b.path_steps[1].model_copy(deep=True)
    alt.connection_path_step_id = "connection-path-step:synthetic:second:v1"
    alt.sequence_index = 3
    alt.from_entity_ref = p.end_entity_ref
    alt.to_entity_ref = p.start_entity_ref
    b.path_steps.append(alt)
    p.step_refs.append(alt.connection_path_step_id)
    with pytest.raises((ValidationError, ValueError)):
        revalidate(b)


def test_evidence_chain_rejects_unlisted_independence_group():
    invalid(lambda b: setattr(b.evidence_chains[0], "independence_groups", [b.evidence_chain_items[0].independence_group]))


def test_evidence_item_step_must_belong_to_path():
    invalid(lambda b: setattr(b.evidence_chain_items[0], "path_step_ref", b.path_steps[1].connection_path_step_id))


def test_contradiction_step_must_belong_to_path():
    invalid(lambda b: setattr(b.contradiction_markers[0], "affected_step_refs", [b.path_steps[1].connection_path_step_id]))


def test_bottleneck_step_must_belong_to_path():
    invalid(lambda b: setattr(b.bottleneck_records[0], "path_step_ref", b.path_steps[0].connection_path_step_id))


def test_alternative_paths_must_share_endpoints():
    b = ref().model_copy(deep=True)
    b.connection_paths[1].end_entity_ref = b.connection_paths[1].start_entity_ref
    with pytest.raises((ValidationError, ValueError)):
        revalidate(b)


@pytest.mark.parametrize("factory,kwargs", [
    (ConnectionPathStep, dict(
        connection_path_step_id="step:x", sequence_index=0, from_entity_ref="entity:a", to_entity_ref="entity:a",
        network_edge_projection_ref="edge:x", epistemic_state="candidate", provenance_refs=["p:x"], explanation="x")),
    (ExplainableConnectionPath, dict(
        connection_path_id="path:x", network_structure_snapshot_ref="snap:x", connection_path_policy_ref="policy:x",
        start_entity_ref="entity:a", end_entity_ref="entity:a", step_refs=["step:x"], algorithm_name="x",
        explanation="x", created_at="2026-09-30T00:00:00Z")),
    (AlternativeConnectionPathComparison, dict(
        alternative_path_comparison_id="cmp:x", primary_path_ref="path:x", alternative_path_ref="path:x",
        divergence_step_refs=["step:x"], comparison_summary="x", provenance_refs=["p:x"])),
])
def test_local_objects_reject_same_identity_endpoints(factory, kwargs):
    with pytest.raises(ValidationError):
        factory(**kwargs)


@pytest.mark.parametrize("factory,kwargs,field", [
    (ConnectionPathStep, dict(connection_path_step_id="step:x", sequence_index=0, from_entity_ref="a:a", to_entity_ref="b:b", network_edge_projection_ref="edge:x", epistemic_state="candidate", provenance_refs=["p:x", "p:x"], explanation="x"), "provenance_refs"),
    (EvidenceChainItem, dict(evidence_chain_item_id="item:x", connection_path_ref="path:x", path_step_ref="step:x", sequence_index=0, position="supports", documentary_segment_refs=["seg:x", "seg:x"], independence_group="g:x", explanation="x", provenance_refs=["p:x"]), "documentary_segment_refs"),
    (EvidenceChain, dict(evidence_chain_id="chain:x", connection_path_ref="path:x", item_refs=["item:x", "item:x"], independence_groups=["g:x"], chain_summary="x", created_at="2026-09-30T00:00:00Z"), "item_refs"),
    (PathContradictionMarker, dict(path_contradiction_marker_id="m:x", connection_path_ref="path:x", affected_step_refs=["step:x", "step:x"], reconciliation_conflict_refs=["c:x"], contradiction_summary="x", provenance_refs=["p:x"]), "affected_step_refs"),
    (ConnectionPathEvidenceSnapshot, dict(connection_path_evidence_snapshot_id="snap:x", network_intelligence_snapshot_ref="ni:x", policy_refs=["p:x", "p:x"], path_refs=["path:x"], evidence_chain_refs=["chain:x"], created_at="2026-09-30T00:00:00Z"), "policy_refs"),
])
def test_local_objects_reject_duplicate_refs(factory, kwargs, field):
    with pytest.raises(ValidationError):
        factory(**kwargs)


def test_scored_path_requires_score_semantics():
    with pytest.raises(ValidationError):
        ExplainableConnectionPath(
            connection_path_id="path:x", network_structure_snapshot_ref="snap:x", connection_path_policy_ref="policy:x",
            start_entity_ref="entity:a", end_entity_ref="entity:b", step_refs=["step:x"], algorithm_name="x",
            path_score=1.0, explanation="x", created_at="2026-09-30T00:00:00Z"
        )


def test_evidence_item_requires_evidence_material():
    with pytest.raises(ValidationError):
        EvidenceChainItem(
            evidence_chain_item_id="item:x", connection_path_ref="path:x", path_step_ref="step:x",
            sequence_index=0, position="supports", independence_group="g:x", explanation="x", provenance_refs=["p:x"]
        )


def test_contradiction_requires_context():
    with pytest.raises(ValidationError):
        PathContradictionMarker(
            path_contradiction_marker_id="m:x", connection_path_ref="path:x", affected_step_refs=["step:x"],
            contradiction_summary="x", provenance_refs=["p:x"]
        )


@pytest.mark.parametrize("object_type", [
    ConnectionPathPolicy,
    ConnectionPathStep,
    ExplainableConnectionPath,
    EvidenceChainItem,
    PathContradictionMarker,
    EvidenceChain,
    AlternativeConnectionPathComparison,
    PathBottleneckRecord,
    ConnectionPathEvidenceSnapshot,
    ExplainableConnectionPathsEvidenceChainsBundle,
])
def test_contract_lists_object_type(object_type):
    assert object_type.__name__ in contract_document()["object_types"]


@pytest.mark.parametrize("contract", [
    "sc.core.network-structure-community-motif-intelligence.v1",
    "sc.core.relationship-discovery-connection-hypothesis.v1",
    "sc.core.public-record-documentary-source-object-model.v1",
    "sc.core.cross-source-entity-reconciliation-identity-provenance.v1",
    "sc.core.evidence-graph-neural-analysis-validation.v1",
])
def test_contract_declares_upstream_contract(contract):
    assert contract in contract_document()["extends_contracts"]


def test_contract_reference_mutation_flags_false():
    r = contract_document()["reference"]
    assert r["relationship_graph_mutation_performed"] is False
    assert r["evidence_graph_mutation_performed"] is False
    assert r["identity_graph_mutation_performed"] is False


def test_contract_reference_states():
    r = contract_document()["reference"]
    assert r["primary_path_epistemic_state"] == "source-observed"
    assert r["alternative_path_epistemic_state"] == "hypothesis"


def test_contract_reference_counts_match_bundle():
    r = contract_document()["reference"]
    b = ref()
    assert r["path_steps"] == len(b.path_steps)
    assert r["connection_paths"] == len(b.connection_paths)
    assert r["evidence_chain_items"] == len(b.evidence_chain_items)
    assert r["evidence_chains"] == len(b.evidence_chains)
    assert r["contradiction_markers"] == len(b.contradiction_markers)
    assert r["alternative_path_comparisons"] == len(b.alternative_path_comparisons)
    assert r["bottleneck_records"] == len(b.bottleneck_records)
