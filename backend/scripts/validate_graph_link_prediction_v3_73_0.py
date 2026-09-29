from app.services.graph_link_prediction import CONTRACT_VERSION, CORE_RELEASE, contract_document, reference_graph_link_prediction_bundle

b = reference_graph_link_prediction_bundle()
c = contract_document()
assert CORE_RELEASE == "3.73.0"
assert CONTRACT_VERSION == "sc.core.graph-link-prediction-candidate-relationship.v1"
assert c["principles"]["gnn_prediction_is_not_graph_fact"] is True
assert c["principles"]["candidate_relationship_is_not_evidence_edge"] is True
assert c["boundaries"]["core_promotes_candidate_to_evidence_edge"] is False
assert c["promotion_requirements"]["independent_validation_required"] is True
assert all(x.is_graph_fact is False and x.is_evidence_edge is False for x in b.candidate_relationships)
print("PASS - Platform Core v3.73.0 Link Prediction & Candidate Relationship Objects")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"CANDIDATE_PAIRS={len(b.candidate_pairs)}")
print(f"PREDICTIONS={len(b.predictions)}")
print(f"CANDIDATE_RELATIONSHIPS={len(b.candidate_relationships)}")
print(f"REVIEWS={len(b.review_records)}")
print("GNN_PREDICTION_IS_GRAPH_FACT=false")
print("CANDIDATE_RELATIONSHIP_IS_EVIDENCE_EDGE=false")
print("SEPARATE_EVIDENCE_VALIDATION_REQUIRED=true")
