from app.services.relationship_discovery_hypotheses import (
    CONTRACT_VERSION,
    contract_document,
    reference_relationship_discovery_hypothesis_bundle,
)

b = reference_relationship_discovery_hypothesis_bundle()
c = contract_document()
assert c["contract"] == CONTRACT_VERSION
assert c["release"] == "3.82.0"
assert len(b.policies) == 1
assert len(b.signals) == 2
assert len(b.source_observed_relationships) == 1
assert len(b.connection_candidates) == 1
assert len(b.connection_hypotheses) == 1
assert len(b.evidence_positions) == 2
assert len(b.reviews) == 2
assert len(b.promotion_gates) == 1
assert b.connection_hypotheses[0].state.value == "supported-for-validation"
assert b.promotion_gates[0].gate_state == "eligible-for-evidence-validation"
assert b.cooccurrence_is_not_relationship is True
assert b.shared_attribute_is_not_relationship is True
assert b.graph_proximity_is_not_relationship is True
assert b.model_score_is_not_relationship_fact is True
assert b.source_observation_is_not_canonical_relationship_fact is True
assert b.hypothesis_is_not_graph_fact is True
assert b.relationship_graph_mutation_performed is False
assert b.evidence_graph_mutation_performed is False
assert b.identity_graph_mutation_performed is False
assert c["boundaries"]["core_creates_evidence_edge_in_v382"] is False
print("PASS - Platform Core v3.82.0 Relationship Discovery & Connection Hypothesis Objects")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"SIGNALS={len(b.signals)}")
print(f"SOURCE_OBSERVED_RELATIONSHIPS={len(b.source_observed_relationships)}")
print(f"CONNECTION_CANDIDATES={len(b.connection_candidates)}")
print(f"CONNECTION_HYPOTHESES={len(b.connection_hypotheses)}")
print(f"EVIDENCE_POSITIONS={len(b.evidence_positions)}")
print(f"INDEPENDENT_REVIEWERS={len({x.reviewer_ref for x in b.reviews})}")
print(f"HYPOTHESIS_STATE={b.connection_hypotheses[0].state.value}")
print(f"PROMOTION_GATE_STATE={b.promotion_gates[0].gate_state}")
print("COOCCURRENCE_IS_RELATIONSHIP=false")
print("SHARED_ATTRIBUTE_IS_RELATIONSHIP=false")
print("GRAPH_PROXIMITY_IS_RELATIONSHIP=false")
print("MODEL_SCORE_IS_RELATIONSHIP_FACT=false")
print("SOURCE_OBSERVATION_IS_CANONICAL_RELATIONSHIP_FACT=false")
print("HYPOTHESIS_IS_GRAPH_FACT=false")
print("EVIDENCE_EDGE_CREATED=false")
print("RELATIONSHIP_GRAPH_MUTATION_PERFORMED=false")
