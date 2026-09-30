from app.services.multi_hop_research_investigation_graph_reasoning import (
    CONTRACT_VERSION,
    contract_document,
    reference_multi_hop_research_investigation_graph_reasoning_bundle,
)

b = reference_multi_hop_research_investigation_graph_reasoning_bundle()
c = contract_document()
assert c["ok"] is True
assert c["release"] == "3.85.0"
assert c["contract"] == CONTRACT_VERSION
assert c["principles"]["multi_hop_reachability_is_not_relationship_truth"] is True
assert c["principles"]["reasoning_chain_is_not_proof"] is True
assert c["principles"]["analytical_confidence_is_not_probability_of_truth"] is True
assert c["principles"]["repeated_paths_are_not_independent_corroboration"] is True
assert c["principles"]["contradiction_propagation_is_non_dispositive"] is True
assert c["principles"]["target_reached_is_not_relationship_fact"] is True
assert c["boundaries"]["runtime_may_promote_candidate_or_hypothesis"] is False
assert c["boundaries"]["v385_creates_evidence_edge"] is False
assert b.relationship_graph_mutation_performed is False
assert b.evidence_graph_mutation_performed is False
assert b.identity_graph_mutation_performed is False
print("PASS - Platform Core v3.85.0 Multi-Hop Research & Investigation Graph Reasoning")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"QUERIES={len(b.queries)}")
print(f"HOPS={len(b.hops)}")
print(f"BRANCHES={len(b.branches)}")
print(f"INFERENCE_STEPS={len(b.inference_steps)}")
print(f"CONTRADICTION_PROPAGATIONS={len(b.contradiction_propagations)}")
print(f"SOURCE_INDEPENDENCE_ASSESSMENTS={len(b.source_independence_assessments)}")
print(f"STOPPING_DECISIONS={len(b.stopping_decisions)}")
print("MULTI_HOP_REACHABILITY_IS_RELATIONSHIP_TRUTH=false")
print("REASONING_CHAIN_IS_PROOF=false")
print("ANALYTICAL_CONFIDENCE_IS_TRUTH_PROBABILITY=false")
print("TARGET_REACHED_IS_RELATIONSHIP_FACT=false")
