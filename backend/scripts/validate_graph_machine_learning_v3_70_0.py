from app.services.graph_machine_learning import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    GraphRunKind,
    contract_document,
    reference_graph_ml_foundation_bundle,
)

bundle = reference_graph_ml_foundation_bundle()
contract = contract_document()

assert CORE_RELEASE == "3.70.0"
assert CONTRACT_VERSION == "sc.core.graph-machine-learning-foundation.v1"
assert contract["principles"]["gnn_prediction_is_not_graph_fact"] is True
assert contract["principles"]["predicted_relationship_is_not_evidence_edge"] is True
assert contract["principles"]["predicted_relationship_requires_separate_validation_before_evidence_edge"] is True
assert contract["boundaries"]["core_promotes_prediction_to_evidence_edge"] is False
assert contract["roadmap_integration"]["prepares_v3710_graph_embedding_objects_runtime_contracts"] is True
assert contract["roadmap_integration"]["prepares_v3760_evidence_graph_neural_analysis_validation_workflow"] is True
assert any(x.run_kind == GraphRunKind.infer for x in bundle.run_provenance)
assert all(x.is_graph_fact is False and x.is_evidence_edge is False for x in bundle.predicted_relationships)
assert all(x.prediction_id not in {e.evidence_edge_ref for s in bundle.snapshots for e in s.evidence_edges} for x in bundle.predicted_relationships)

print("PASS - Platform Core v3.70.0 Graph Machine Learning Foundation")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"SNAPSHOTS={len(bundle.snapshots)}")
print(f"EVIDENCE_EDGES={sum(len(x.evidence_edges) for x in bundle.snapshots)}")
print(f"GRAPH_TASKS={len(bundle.tasks)}")
print(f"RUNTIME_CONTRACTS={len(bundle.runtime_contracts)}")
print(f"RUNS={len(bundle.run_provenance)}")
print(f"PREDICTED_RELATIONSHIPS={len(bundle.predicted_relationships)}")
print("GNN_PREDICTION_IS_GRAPH_FACT=false")
print("PREDICTED_RELATIONSHIP_IS_EVIDENCE_EDGE=false")
print("SEPARATE_VALIDATION_REQUIRED=true")
