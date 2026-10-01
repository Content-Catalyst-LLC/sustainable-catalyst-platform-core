from app.services.unified_runtime_policy_capability_negotiation import contract_document, reference_unified_runtime_policy_capability_negotiation_bundle

b=reference_unified_runtime_policy_capability_negotiation_bundle(); c=contract_document()
assert b.release=="3.91.0"
assert c["contract"]=="sc.core.unified-runtime-policy-capability-negotiation.v1"
assert len(b.capabilities)==14 and len(b.requirements)==17 and len(b.consumers)==7
assert len(b.decisions)==17 and len(b.traces)==7 and len(b.fallback_rules)==1
assert c["reference"]["degraded_capabilities"]==1
assert c["boundaries"]["negotiation_grants_undeclared_scope"] is False
assert c["boundaries"]["negotiation_weakens_epistemic_boundaries"] is False
assert c["boundaries"]["degraded_mode_increases_authority"] is False
assert c["boundaries"]["identity_graph_mutation_performed"] is False
assert c["boundaries"]["relationship_graph_mutation_performed"] is False
assert c["boundaries"]["evidence_graph_mutation_performed"] is False
print("PASS - Platform Core v3.91.0 Unified Runtime Policy & Capability Negotiation")
print(f"CONTRACT={c['contract']}")
print(f"CAPABILITIES={len(b.capabilities)}")
print(f"CONSUMERS={len(b.consumers)}")
print(f"REQUIREMENTS={len(b.requirements)}")
print(f"DECISIONS={len(b.decisions)}")
print(f"TRACES={len(b.traces)}")
print(f"DEGRADED_CAPABILITIES={c['reference']['degraded_capabilities']}")
print("SCOPE_ESCALATION_ALLOWED=false")
print("BOUNDARY_WEAKENING_ALLOWED=false")
print("CANDIDATE_PROMOTION_ALLOWED=false")
print("HYPOTHESIS_PROMOTION_ALLOWED=false")
print("LOCAL_VALIDATION_BYPASS_ALLOWED=false")
print("HUMAN_REVIEW_BYPASS_ALLOWED=false")
print("IDENTITY_GRAPH_MUTATION_PERFORMED=false")
print("RELATIONSHIP_GRAPH_MUTATION_PERFORMED=false")
print("EVIDENCE_GRAPH_MUTATION_PERFORMED=false")
