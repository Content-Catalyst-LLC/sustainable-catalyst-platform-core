from app.services.unified_entity_evidence_query_api import contract_document, reference_unified_entity_evidence_query_bundle

b=reference_unified_entity_evidence_query_bundle(); c=contract_document()
assert b.release=="3.92.0"
assert c["contract"]=="sc.core.unified-entity-evidence-query-api.v1"
assert len(b.plan_steps)==15 and len(b.results)==15 and len(b.provenance_refs)==15
assert c["reference"]["final_disposition"]=="complete-with-qualifications"
for k in ["single_governed_query_surface","capability_negotiation_required","source_contract_identity_preserved","epistemic_state_preserved","provenance_preserved","validation_state_preserved","contradictions_preserved","remote_references_remain_remote","consumer_scope_enforced","retrieval_scores_are_relevance_only","query_plans_are_reproducible","result_sets_are_explicitly_qualified"]:
    assert c["principles"][k] is True
for k in ["query_flattens_epistemic_states","query_promotes_candidate_to_fact","query_promotes_hypothesis_to_evidence","query_promotes_remote_reference_to_local_evidence","retrieval_score_is_evidence_strength","retrieval_score_is_probability_of_truth","absence_from_results_proves_nonexistence","query_completeness_is_evidence_completeness","query_result_is_truth_verdict","query_bypasses_local_validation","identity_graph_mutation_performed","relationship_graph_mutation_performed","evidence_graph_mutation_performed"]:
    assert c["boundaries"][k] is False
print("PASS - Platform Core v3.92.0 Unified Entity & Evidence Query API")
print(f"CONTRACT={c['contract']}")
print(f"PLAN_STEPS={len(b.plan_steps)}")
print(f"RESULTS={len(b.results)}")
print(f"PROVENANCE_REFS={len(b.provenance_refs)}")
print(f"RESULT_SETS={len(b.result_sets)}")
print(f"TRACES={len(b.traces)}")
print(f"FINAL_DISPOSITION={c['reference']['final_disposition']}")
print("CROSS_STATE_FLATTENING_ALLOWED=false")
print("CANDIDATE_PROMOTION_ALLOWED=false")
print("HYPOTHESIS_PROMOTION_ALLOWED=false")
print("REMOTE_REFERENCE_PROMOTION_ALLOWED=false")
print("RETRIEVAL_SCORE_IS_EVIDENCE_STRENGTH=false")
print("LOCAL_VALIDATION_BYPASS_ALLOWED=false")
print("IDENTITY_GRAPH_MUTATION_PERFORMED=false")
print("RELATIONSHIP_GRAPH_MUTATION_PERFORMED=false")
print("EVIDENCE_GRAPH_MUTATION_PERFORMED=false")
