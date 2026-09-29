from app.services.evidence_graph_neural_validation import *
b=reference_evidence_graph_neural_validation_bundle(); c=contract_document(); a=b.promotion_authorizations[0]
assert c["release"]=="3.76.0"
assert c["principles"]["gnn_prediction_is_not_graph_fact"] is True
assert c["principles"]["neural_signal_is_not_evidence"] is True
assert c["principles"]["model_output_cannot_satisfy_evidence_gate"] is True
assert c["principles"]["promotion_requires_independent_evidence"] is True
assert a.decision.value=="authorized" and a.actual_evidence_graph_mutation_performed is False
assert a.model_outputs_counted_as_evidence is False and a.model_outputs_can_authorize_promotion is False
print("PASS - Platform Core v3.76.0 Evidence Graph Neural Analysis & Validation Workflow")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"NEURAL_SIGNALS={len(b.neural_signals)}")
print(f"EVIDENCE_ITEMS={len(b.evidence_items)}")
print(f"INDEPENDENT_REVIEWERS={len({x.reviewer_ref for x in b.assessments})}")
print(f"PROMOTION_DECISION={a.decision.value}")
print("GNN_PREDICTION_IS_GRAPH_FACT=false")
print("NEURAL_SIGNAL_IS_EVIDENCE=false")
print("MODEL_OUTPUT_CAN_SATISFY_EVIDENCE_GATE=false")
print("ACTUAL_GRAPH_MUTATION_PERFORMED=false")
