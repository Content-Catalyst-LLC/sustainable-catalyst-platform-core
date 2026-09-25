from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.ai_research_object_system import (
    CONTRACT_VERSION,
    AIResearchContractBinding,
    AIResearchLifecycleState,
    AIResearchLineageQuery,
    AIResearchObjectEnvelope,
    AIResearchObjectKind,
    AIResearchObjectRef,
    AIResearchObjectRegistry,
    AIResearchPackageManifest,
    AIResearchRelationship,
    AIResearchRelationshipGraph,
    AIResearchRelationshipType,
    AIResearchSnapshot,
    AIResearchSystemManifest,
    LineageDirection,
    UnifiedAIResearchObjectBundle,
    contract_document,
    reference_unified_ai_research_bundle,
    trace_lineage,
)


def test_contract_declares_unified_ai_research_system():
    doc = contract_document()
    assert doc["release"] == "3.35.0"
    assert doc["contract"] == CONTRACT_VERSION
    assert doc["capabilities"]["canonical_cross_contract_identity"] is True
    assert doc["integration"]["core_duplicates_source_payloads"] is False


def test_reference_bundle_is_valid():
    bundle = reference_unified_ai_research_bundle()
    assert len(bundle.registry.objects) == 13
    assert len(bundle.graph.relationships) == 17
    assert bundle.packages


def test_manifest_unifies_eight_ai_contracts():
    doc = contract_document()
    assert len(doc["unifies"]) == 8
    assert "sc.core.ai-model.v1" in doc["unifies"]
    assert "sc.core.ai-calibration-drift-risk.v1" in doc["unifies"]


def test_manifest_rejects_duplicate_binding_ids():
    b = AIResearchContractBinding(
        binding_id="binding:test",
        contract="contract:test:1",
        introduced_release="1.0.0",
        object_kinds=[AIResearchObjectKind.other],
    )
    with pytest.raises(ValidationError):
        AIResearchSystemManifest(
            manifest_id="manifest:test",
            contract_bindings=[b, deepcopy(b)],
        )


def test_manifest_rejects_duplicate_contracts():
    b1 = AIResearchContractBinding(
        binding_id="binding:test:1",
        contract="contract:test",
        introduced_release="1.0.0",
        object_kinds=[AIResearchObjectKind.other],
    )
    b2 = AIResearchContractBinding(
        binding_id="binding:test:2",
        contract="contract:test",
        introduced_release="1.1.0",
        object_kinds=[AIResearchObjectKind.evidence],
    )
    with pytest.raises(ValidationError):
        AIResearchSystemManifest(
            manifest_id="manifest:test",
            contract_bindings=[b1, b2],
        )


def test_manifest_requires_current_system_contract():
    bundle = reference_unified_ai_research_bundle()
    data = bundle.manifest.model_dump(mode="python")
    data["system_contract"] = "sc.core.other.v1"
    with pytest.raises(ValidationError):
        AIResearchSystemManifest.model_validate(data)


def test_manifest_fingerprint_ignores_created_at():
    manifest = reference_unified_ai_research_bundle().manifest
    assert manifest.fingerprint() == deepcopy(manifest).fingerprint()


def test_object_ref_sha256_is_validated():
    with pytest.raises(ValidationError):
        AIResearchObjectRef(
            object_id="object:test",
            object_kind=AIResearchObjectKind.other,
            contract="contract:test",
            fingerprint_sha256="abc",
        )


def test_object_ref_fingerprint_is_stable():
    ref = reference_unified_ai_research_bundle().registry.objects[0].object_ref
    assert ref.fingerprint() == deepcopy(ref).fingerprint()


def test_object_envelope_fingerprint_ignores_registration_and_lifecycle():
    envelope = reference_unified_ai_research_bundle().registry.objects[0]
    other = deepcopy(envelope)
    other.lifecycle_state = AIResearchLifecycleState.archived
    assert envelope.fingerprint() == other.fingerprint()


def test_registry_rejects_duplicate_object_ids():
    envelope = reference_unified_ai_research_bundle().registry.objects[0]
    with pytest.raises(ValidationError):
        AIResearchObjectRegistry(
            registry_id="registry:test",
            objects=[envelope, deepcopy(envelope)],
        )


def test_registry_object_index():
    registry = reference_unified_ai_research_bundle().registry
    index = registry.object_index()
    assert "ai-model-version:reference-classifier:1.0.0" in index


def test_registry_fingerprint_is_stable():
    registry = reference_unified_ai_research_bundle().registry
    assert registry.fingerprint() == deepcopy(registry).fingerprint()


def test_relationship_rejects_self_reference():
    with pytest.raises(ValidationError):
        AIResearchRelationship(
            relationship_id="rel:test",
            source_object_ref="object:test",
            target_object_ref="object:test",
            relationship_type=AIResearchRelationshipType.references,
        )


def test_relationship_confidence_range():
    with pytest.raises(ValidationError):
        AIResearchRelationship(
            relationship_id="rel:test",
            source_object_ref="object:a",
            target_object_ref="object:b",
            relationship_type=AIResearchRelationshipType.references,
            confidence=1.2,
        )


def test_relationship_fingerprint_is_stable():
    relationship = reference_unified_ai_research_bundle().graph.relationships[0]
    assert relationship.fingerprint() == deepcopy(relationship).fingerprint()


def test_graph_rejects_duplicate_object_ids():
    bundle = reference_unified_ai_research_bundle()
    data = bundle.graph.model_dump(mode="python")
    data["object_ids"] = [data["object_ids"][0], data["object_ids"][0]]
    with pytest.raises(ValidationError):
        AIResearchRelationshipGraph.model_validate(data)


def test_graph_rejects_duplicate_relationship_ids():
    bundle = reference_unified_ai_research_bundle()
    data = bundle.graph.model_dump(mode="python")
    data["relationships"] = [
        data["relationships"][0],
        deepcopy(data["relationships"][0]),
    ]
    with pytest.raises(ValidationError):
        AIResearchRelationshipGraph.model_validate(data)


def test_graph_rejects_unknown_source():
    bundle = reference_unified_ai_research_bundle()
    data = bundle.graph.model_dump(mode="python")
    data["relationships"][0]["source_object_ref"] = "object:missing"
    with pytest.raises(ValidationError):
        AIResearchRelationshipGraph.model_validate(data)


def test_graph_rejects_unknown_target():
    bundle = reference_unified_ai_research_bundle()
    data = bundle.graph.model_dump(mode="python")
    data["relationships"][0]["target_object_ref"] = "object:missing"
    with pytest.raises(ValidationError):
        AIResearchRelationshipGraph.model_validate(data)


def test_graph_fingerprint_is_stable():
    graph = reference_unified_ai_research_bundle().graph
    assert graph.fingerprint() == deepcopy(graph).fingerprint()


def test_upstream_lineage_from_snapshot_reaches_model():
    bundle = reference_unified_ai_research_bundle()
    path = trace_lineage(
        bundle.graph,
        AIResearchLineageQuery(
            start_object_ref="monitoring-snapshot:reference:current",
            direction=LineageDirection.upstream,
            max_depth=2,
        ),
    )
    assert "ai-model-version:reference-classifier:1.0.0" in path.object_refs


def test_upstream_lineage_from_snapshot_reaches_robustness_through_risk():
    bundle = reference_unified_ai_research_bundle()
    path = trace_lineage(
        bundle.graph,
        AIResearchLineageQuery(
            start_object_ref="monitoring-snapshot:reference:current",
            direction=LineageDirection.upstream,
            max_depth=3,
        ),
    )
    assert "robustness-run:reference-classifier-noise:001" in path.object_refs


def test_upstream_lineage_from_model_reaches_dataset():
    bundle = reference_unified_ai_research_bundle()
    path = trace_lineage(
        bundle.graph,
        AIResearchLineageQuery(
            start_object_ref="ai-model-version:reference-classifier:1.0.0",
            direction=LineageDirection.upstream,
            max_depth=1,
        ),
    )
    assert "dataset-version:reference-classification:v1" in path.object_refs


def test_downstream_lineage_from_model_reaches_inference():
    bundle = reference_unified_ai_research_bundle()
    path = trace_lineage(
        bundle.graph,
        AIResearchLineageQuery(
            start_object_ref="ai-model-version:reference-classifier:1.0.0",
            direction=LineageDirection.downstream,
            max_depth=1,
        ),
    )
    assert "inference-run:reference-classifier:001" in path.object_refs


def test_downstream_lineage_from_model_reaches_evaluation():
    bundle = reference_unified_ai_research_bundle()
    path = trace_lineage(
        bundle.graph,
        AIResearchLineageQuery(
            start_object_ref="ai-model-version:reference-classifier:1.0.0",
            direction=LineageDirection.downstream,
            max_depth=1,
        ),
    )
    assert "evaluation-run:reference-classifier:001" in path.object_refs


def test_relationship_filtered_lineage():
    bundle = reference_unified_ai_research_bundle()
    path = trace_lineage(
        bundle.graph,
        AIResearchLineageQuery(
            start_object_ref="inference-run:reference-classifier:001",
            direction=LineageDirection.upstream,
            relationship_types=[AIResearchRelationshipType.uses_prompt],
            max_depth=2,
        ),
    )
    assert path.object_refs == [
        "inference-run:reference-classifier:001",
        "prompt-version:research-evidence-synthesis:1.0.0",
    ]


def test_lineage_excludes_start_when_requested():
    bundle = reference_unified_ai_research_bundle()
    path = trace_lineage(
        bundle.graph,
        AIResearchLineageQuery(
            start_object_ref="ai-model-version:reference-classifier:1.0.0",
            direction=LineageDirection.upstream,
            include_start=False,
            max_depth=1,
        ),
    )
    assert "ai-model-version:reference-classifier:1.0.0" not in path.object_refs


def test_lineage_max_depth_zero_marks_truncated():
    bundle = reference_unified_ai_research_bundle()
    path = trace_lineage(
        bundle.graph,
        AIResearchLineageQuery(
            start_object_ref="monitoring-snapshot:reference:current",
            direction=LineageDirection.upstream,
            max_depth=0,
        ),
    )
    assert path.truncated is True


def test_lineage_missing_start_raises():
    bundle = reference_unified_ai_research_bundle()
    with pytest.raises(ValueError):
        trace_lineage(
            bundle.graph,
            AIResearchLineageQuery(
                start_object_ref="object:missing",
                direction=LineageDirection.upstream,
            ),
        )


def test_lineage_path_fingerprint_is_stable():
    bundle = reference_unified_ai_research_bundle()
    path = trace_lineage(
        bundle.graph,
        AIResearchLineageQuery(
            start_object_ref="monitoring-snapshot:reference:current",
            direction=LineageDirection.upstream,
            max_depth=3,
        ),
    )
    assert path.fingerprint() == deepcopy(path).fingerprint()


def test_snapshot_fingerprint_is_stable():
    snapshot = reference_unified_ai_research_bundle().snapshot
    assert snapshot.fingerprint() == deepcopy(snapshot).fingerprint()


def test_package_requires_objects():
    with pytest.raises(ValidationError):
        AIResearchPackageManifest(
            package_id="package:test",
            snapshot_ref="snapshot:test",
            selected_object_refs=[],
        )


def test_package_roots_must_be_selected():
    with pytest.raises(ValidationError):
        AIResearchPackageManifest(
            package_id="package:test",
            snapshot_ref="snapshot:test",
            selected_object_refs=["object:a"],
            root_object_refs=["object:b"],
        )


def test_package_fingerprint_is_stable():
    package = reference_unified_ai_research_bundle().packages[0]
    assert package.fingerprint() == deepcopy(package).fingerprint()


def test_bundle_rejects_registry_manifest_mismatch():
    bundle = reference_unified_ai_research_bundle()
    registry = deepcopy(bundle.registry)
    registry.contract_manifest_ref = "manifest:other"
    with pytest.raises(ValidationError):
        UnifiedAIResearchObjectBundle(
            manifest=bundle.manifest,
            registry=registry,
            graph=bundle.graph,
            snapshot=bundle.snapshot,
            packages=bundle.packages,
        )


def test_bundle_rejects_graph_registry_mismatch():
    bundle = reference_unified_ai_research_bundle()
    graph = deepcopy(bundle.graph)
    graph.registry_ref = "registry:other"
    with pytest.raises(ValidationError):
        UnifiedAIResearchObjectBundle(
            manifest=bundle.manifest,
            registry=bundle.registry,
            graph=graph,
            snapshot=bundle.snapshot,
            packages=bundle.packages,
        )


def test_bundle_requires_graph_and_registry_object_sets_to_match():
    bundle = reference_unified_ai_research_bundle()
    graph = deepcopy(bundle.graph)
    graph.object_ids = graph.object_ids[:-1]
    graph.relationships = [
        edge
        for edge in graph.relationships
        if edge.source_object_ref in graph.object_ids
        and edge.target_object_ref in graph.object_ids
    ]
    with pytest.raises(ValidationError):
        UnifiedAIResearchObjectBundle(
            manifest=bundle.manifest,
            registry=bundle.registry,
            graph=graph,
            snapshot=bundle.snapshot,
            packages=[],
        )


def test_bundle_rejects_wrong_source_contract_for_kind():
    bundle = reference_unified_ai_research_bundle()
    registry = deepcopy(bundle.registry)
    registry.objects[0].object_ref.contract = "sc.core.ai-evaluation-benchmark.v1"
    snapshot = deepcopy(bundle.snapshot)
    snapshot.registry_fingerprint_sha256 = registry.fingerprint()
    with pytest.raises(ValidationError):
        UnifiedAIResearchObjectBundle(
            manifest=bundle.manifest,
            registry=registry,
            graph=bundle.graph,
            snapshot=snapshot,
            packages=[],
        )


def test_bundle_rejects_snapshot_manifest_fingerprint_mismatch():
    bundle = reference_unified_ai_research_bundle()
    snapshot = deepcopy(bundle.snapshot)
    snapshot.manifest_fingerprint_sha256 = "f" * 64
    with pytest.raises(ValidationError):
        UnifiedAIResearchObjectBundle(
            manifest=bundle.manifest,
            registry=bundle.registry,
            graph=bundle.graph,
            snapshot=snapshot,
            packages=[],
        )


def test_bundle_rejects_snapshot_registry_fingerprint_mismatch():
    bundle = reference_unified_ai_research_bundle()
    snapshot = deepcopy(bundle.snapshot)
    snapshot.registry_fingerprint_sha256 = "f" * 64
    with pytest.raises(ValidationError):
        UnifiedAIResearchObjectBundle(
            manifest=bundle.manifest,
            registry=bundle.registry,
            graph=bundle.graph,
            snapshot=snapshot,
            packages=[],
        )


def test_bundle_rejects_snapshot_graph_fingerprint_mismatch():
    bundle = reference_unified_ai_research_bundle()
    snapshot = deepcopy(bundle.snapshot)
    snapshot.graph_fingerprint_sha256 = "f" * 64
    with pytest.raises(ValidationError):
        UnifiedAIResearchObjectBundle(
            manifest=bundle.manifest,
            registry=bundle.registry,
            graph=bundle.graph,
            snapshot=snapshot,
            packages=[],
        )


def test_bundle_rejects_non_unified_relationship_contract():
    bundle = reference_unified_ai_research_bundle()
    graph = deepcopy(bundle.graph)
    graph.relationships[0].contract = "contract:other"
    snapshot = deepcopy(bundle.snapshot)
    snapshot.graph_fingerprint_sha256 = graph.fingerprint()
    with pytest.raises(ValidationError):
        UnifiedAIResearchObjectBundle(
            manifest=bundle.manifest,
            registry=bundle.registry,
            graph=graph,
            snapshot=snapshot,
            packages=[],
        )


def test_bundle_rejects_package_snapshot_mismatch():
    bundle = reference_unified_ai_research_bundle()
    package = deepcopy(bundle.packages[0])
    package.snapshot_ref = "snapshot:other"
    with pytest.raises(ValidationError):
        UnifiedAIResearchObjectBundle(
            manifest=bundle.manifest,
            registry=bundle.registry,
            graph=bundle.graph,
            snapshot=bundle.snapshot,
            packages=[package],
        )


def test_bundle_rejects_package_object_outside_registry():
    bundle = reference_unified_ai_research_bundle()
    package = deepcopy(bundle.packages[0])
    package.selected_object_refs.append("object:missing")
    with pytest.raises(ValidationError):
        UnifiedAIResearchObjectBundle(
            manifest=bundle.manifest,
            registry=bundle.registry,
            graph=bundle.graph,
            snapshot=bundle.snapshot,
            packages=[package],
        )


def test_bundle_rejects_package_relationship_outside_graph():
    bundle = reference_unified_ai_research_bundle()
    package = deepcopy(bundle.packages[0])
    package.selected_relationship_refs.append("rel:missing")
    with pytest.raises(ValidationError):
        UnifiedAIResearchObjectBundle(
            manifest=bundle.manifest,
            registry=bundle.registry,
            graph=bundle.graph,
            snapshot=bundle.snapshot,
            packages=[package],
        )


def test_bundle_fingerprint_is_stable():
    bundle = reference_unified_ai_research_bundle()
    assert bundle.fingerprint() == deepcopy(bundle).fingerprint()
    assert len(bundle.fingerprint()) == 64


def test_reference_registry_is_reference_only():
    bundle = reference_unified_ai_research_bundle()
    assert bundle.registry.metadata["payload_mode"] == "reference-only"
    assert all(item.object_ref.payload_ref for item in bundle.registry.objects)


def test_reference_manifest_does_not_duplicate_payloads():
    bundle = reference_unified_ai_research_bundle()
    assert bundle.manifest.metadata["object_payloads_duplicated"] is False


def test_reference_snapshot_covers_ai_releases_327_through_334():
    snapshot = reference_unified_ai_research_bundle().snapshot
    assert snapshot.source_release_refs == [
        "v3.27.0",
        "v3.28.0",
        "v3.29.0",
        "v3.30.0",
        "v3.31.0",
        "v3.32.0",
        "v3.33.0",
        "v3.34.0",
    ]


def test_reference_contains_product_ownership():
    bundle = reference_unified_ai_research_bundle()
    owners = {item.object_ref.product_owner for item in bundle.registry.objects}
    assert "knowledge-library" in owners
    assert "research-librarian" in owners
    assert "research-lab" in owners
    assert "platform-core" in owners


def test_reference_package_roots_model_and_monitoring_snapshot():
    package = reference_unified_ai_research_bundle().packages[0]
    assert "ai-model-version:reference-classifier:1.0.0" in package.root_object_refs
    assert "monitoring-snapshot:reference:current" in package.root_object_refs


def test_contract_preserves_source_product_boundaries():
    doc = contract_document()
    assert doc["integration"]["knowledge_library_objects_remain_owned_by_library"] is True
    assert doc["integration"]["research_librarian_objects_remain_owned_by_librarian"] is True
    assert doc["integration"]["research_lab_objects_remain_owned_by_lab"] is True


def test_core_does_not_execute_or_select_or_certify():
    doc = contract_document()
    assert doc["boundaries"]["core_executes_ai_jobs"] is False
    assert doc["boundaries"]["core_selects_best_model"] is False
    assert doc["boundaries"]["core_certifies_scientific_validity"] is False


def test_core_does_not_materialize_payloads_or_mutate_objects():
    doc = contract_document()
    assert doc["boundaries"]["core_materializes_source_payloads"] is False
    assert doc["boundaries"]["core_autonomously_changes_research_objects"] is False
