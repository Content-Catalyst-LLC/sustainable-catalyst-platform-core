from app.services.network_structure_community_motif import (
    CONTRACT_VERSION,
    contract_document,
    reference_network_structure_community_motif_bundle,
)

b = reference_network_structure_community_motif_bundle()
c = contract_document()
assert c["ok"] is True
assert c["release"] == "3.83.0"
assert c["contract"] == CONTRACT_VERSION
assert c["principles"]["centrality_is_not_importance"] is True
assert c["principles"]["community_membership_is_not_affiliation"] is True
assert c["principles"]["motif_participation_is_not_coordination"] is True
assert c["principles"]["bridge_score_is_not_influence"] is True
assert c["principles"]["structural_equivalence_is_not_identity"] is True
assert c["principles"]["network_analysis_is_not_wrongdoing"] is True
assert c["boundaries"]["v383_creates_evidence_edge"] is False
assert b.relationship_graph_mutation_performed is False
assert b.evidence_graph_mutation_performed is False
assert b.identity_graph_mutation_performed is False
print("PASS - Platform Core v3.83.0 Network Structure, Community & Motif Intelligence")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"EDGE_PROJECTIONS={len(b.edge_projections)}")
print(f"METRIC_RECORDS={len(b.metric_records)}")
print(f"COMMUNITY_ASSIGNMENTS={len(b.community_assignments)}")
print(f"COMMUNITIES={len(b.community_profiles)}")
print(f"MOTIF_INSTANCES={len(b.motif_instances)}")
print(f"BRIDGE_BROKER_RECORDS={len(b.bridge_broker_records)}")
print(f"STRUCTURAL_EQUIVALENCE_RECORDS={len(b.structural_equivalence_records)}")
print("CENTRALITY_IS_IMPORTANCE=false")
print("COMMUNITY_MEMBERSHIP_IS_AFFILIATION=false")
print("MOTIF_PARTICIPATION_IS_COORDINATION=false")
print("NETWORK_ANALYSIS_IS_WRONGDOING=false")
