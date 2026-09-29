from app.services.graph_classification import CORE_RELEASE,CONTRACT_VERSION,contract_document,reference_graph_classification_bundle
b=reference_graph_classification_bundle(); c=contract_document()
assert CORE_RELEASE=="3.72.0" and CONTRACT_VERSION=="sc.core.graph-node-edge-classification.v1"
assert len(b.label_spaces)==2 and len(b.tasks)==2 and len(b.predictions)==2
assert all(x.is_graph_fact is False and x.is_evidence is False and x.is_evidence_edge is False for x in b.predictions)
assert c["principles"]["node_classification_is_not_graph_fact"] is True
assert c["principles"]["edge_classification_is_not_graph_fact"] is True
assert c["principles"]["gnn_prediction_is_not_graph_fact"] is True
assert c["boundaries"]["v372_performs_link_prediction"] is False
print("PASS - Platform Core v3.72.0 Node & Edge Classification Objects")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"LABEL_SPACES={len(b.label_spaces)}")
print(f"TASKS={len(b.tasks)}")
print(f"PREDICTIONS={len(b.predictions)}")
print("NODE_CLASSIFICATION_IS_GRAPH_FACT=false")
print("EDGE_CLASSIFICATION_IS_GRAPH_FACT=false")
print("CLASSIFICATION_IS_EVIDENCE=false")
print("V372_PERFORMS_LINK_PREDICTION=false")
