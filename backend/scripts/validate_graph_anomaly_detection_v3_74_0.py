from app.services.graph_anomaly_detection import *
b=reference_graph_anomaly_detection_bundle(); c=contract_document()
assert CORE_RELEASE=="3.74.0"
assert CONTRACT_VERSION=="sc.core.graph-anomaly-detection.v1"
assert c["principles"]["anomaly_is_not_graph_fact"] is True
assert c["principles"]["anomaly_is_not_evidence"] is True
assert c["principles"]["anomaly_is_not_wrongdoing"] is True
assert c["principles"]["gnn_prediction_is_not_graph_fact"] is True
assert c["boundaries"]["core_promotes_anomaly_to_evidence"] is False
assert c["boundaries"]["runtime_may_mutate_evidence_graph"] is False
assert all(x.is_graph_fact is False and x.is_evidence is False and x.is_wrongdoing_finding is False for x in b.scores)
print("PASS - Platform Core v3.74.0 Graph Anomaly Detection")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"TASKS={len(b.tasks)}")
print(f"TARGETS={len(b.targets)}")
print(f"SCORES={len(b.scores)}")
print(f"EXPLANATIONS={len(b.explanations)}")
print(f"REVIEWS={len(b.reviews)}")
print("ANOMALY_IS_GRAPH_FACT=false")
print("ANOMALY_IS_EVIDENCE=false")
print("ANOMALY_IS_WRONGDOING=false")
print("GNN_PREDICTION_IS_GRAPH_FACT=false")
