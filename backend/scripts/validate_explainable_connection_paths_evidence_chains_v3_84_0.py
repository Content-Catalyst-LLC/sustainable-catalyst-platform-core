from app.services.explainable_connection_paths_evidence_chains import (
    CONTRACT_VERSION,
    contract_document,
    reference_explainable_connection_paths_evidence_chains_bundle,
)

b = reference_explainable_connection_paths_evidence_chains_bundle()
c = contract_document()
assert c["ok"] is True
assert c["release"] == "3.84.0"
assert c["contract"] == CONTRACT_VERSION
assert c["principles"]["path_existence_is_not_relationship_truth"] is True
assert c["principles"]["shortest_path_is_not_strongest_evidence"] is True
assert c["principles"]["path_length_is_not_causal_distance"] is True
assert c["principles"]["multiple_paths_are_not_independent_corroboration"] is True
assert c["principles"]["evidence_chain_is_not_truth_verdict"] is True
assert c["principles"]["missing_path_is_not_no_relationship"] is True
assert c["principles"]["contradictions_remain_visible"] is True
assert c["boundaries"]["v384_creates_evidence_edge"] is False
assert c["boundaries"]["v384_creates_canonical_relationship_fact"] is False
assert b.relationship_graph_mutation_performed is False
assert b.evidence_graph_mutation_performed is False
assert b.identity_graph_mutation_performed is False
print("PASS - Platform Core v3.84.0 Explainable Connection Paths & Evidence Chains")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"PATH_STEPS={len(b.path_steps)}")
print(f"CONNECTION_PATHS={len(b.connection_paths)}")
print(f"EVIDENCE_CHAIN_ITEMS={len(b.evidence_chain_items)}")
print(f"EVIDENCE_CHAINS={len(b.evidence_chains)}")
print(f"CONTRADICTION_MARKERS={len(b.contradiction_markers)}")
print(f"ALTERNATIVE_PATH_COMPARISONS={len(b.alternative_path_comparisons)}")
print(f"BOTTLENECK_RECORDS={len(b.bottleneck_records)}")
print("PATH_EXISTENCE_IS_RELATIONSHIP_TRUTH=false")
print("SHORTEST_PATH_IS_STRONGEST_EVIDENCE=false")
print("PATH_LENGTH_IS_CAUSAL_DISTANCE=false")
print("EVIDENCE_CHAIN_IS_TRUTH_VERDICT=false")
