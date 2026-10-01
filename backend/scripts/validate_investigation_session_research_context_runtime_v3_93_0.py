from app.services.investigation_session_research_context_runtime import contract_document, reference_investigation_session_research_context_bundle

d=contract_document(); b=reference_investigation_session_research_context_bundle()
assert d["ok"] is True and d["release"]=="3.93.0"
assert d["contract"]=="sc.core.investigation-session-research-context-runtime.v1"
assert d["reference"]["bindings"]==15 and d["reference"]["remote_references"]==1
assert d["boundaries"]["session_context_is_evidence"] is False
assert d["boundaries"]["persisted_hypothesis_is_graph_fact"] is False
assert d["boundaries"]["identity_graph_mutation_performed"] is False
assert d["boundaries"]["relationship_graph_mutation_performed"] is False
assert d["boundaries"]["evidence_graph_mutation_performed"] is False
print("PASS - Platform Core v3.93.0 Investigation Session & Research Context Runtime")
print(f"CONTRACT={d['contract']}")
print(f"SESSIONS={d['reference']['sessions']}")
print(f"BINDINGS={d['reference']['bindings']}")
print(f"FILTERS={d['reference']['filters']}")
print(f"HYPOTHESES={d['reference']['hypotheses']}")
print(f"CONTRIBUTIONS={d['reference']['contributions']}")
print(f"CHECKPOINTS={d['reference']['checkpoints']}")
print(f"REMOTE_REFERENCES={d['reference']['remote_references']}")
print(f"SESSION_STATUS={d['reference']['session_status']}")
print(f"HYPOTHESIS_STATE={d['reference']['hypothesis_state']}")
print("SESSION_CONTEXT_IS_EVIDENCE=false")
print("PERSISTED_HYPOTHESIS_IS_GRAPH_FACT=false")
print("IDENTITY_GRAPH_MUTATION_PERFORMED=false")
print("RELATIONSHIP_GRAPH_MUTATION_PERFORMED=false")
print("EVIDENCE_GRAPH_MUTATION_PERFORMED=false")
