from app.services.knowledge_graph_representation_learning import contract_document, reference_knowledge_graph_representation_learning_bundle

b=reference_knowledge_graph_representation_learning_bundle(); c=contract_document()
assert c["release"]=="3.75.0"
assert c["contract"]=="sc.core.knowledge-graph-representation-learning.v1"
assert c["principles"]["triple_score_is_not_graph_fact"] is True
assert c["principles"]["triple_score_is_not_evidence"] is True
assert c["principles"]["negative_sample_is_not_false_fact"] is True
assert c["principles"]["gnn_prediction_is_not_graph_fact"] is True
assert c["boundaries"]["core_promotes_scored_triple_to_evidence_edge"] is False
assert c["boundaries"]["runtime_may_mutate_evidence_graph"] is False
assert len(b.vectors)==5 and len(b.triple_scores)==2
print("PASS - Platform Core v3.75.0 Knowledge Graph Representation Learning")
print(f"CONTRACT={c['contract']}")
print(f"TASKS={len(b.tasks)}")
print(f"REPRESENTATION_SPACES={len(b.representation_spaces)}")
print(f"VECTORS={len(b.vectors)}")
print(f"TRIPLE_SCORES={len(b.triple_scores)}")
print("TRIPLE_SCORE_IS_GRAPH_FACT=false")
print("TRIPLE_SCORE_IS_EVIDENCE=false")
print("NEGATIVE_SAMPLE_IS_FALSE_FACT=false")
print("GNN_PREDICTION_IS_GRAPH_FACT=false")
