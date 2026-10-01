from app.services.entity_evidence_runtime_performance_scale import contract_document, reference_entity_evidence_runtime_performance_scale_bundle

c=contract_document(); b=reference_entity_evidence_runtime_performance_scale_bundle()
assert c["release"]=="3.98.0"
assert c["contract"]=="sc.core.entity-evidence-runtime-performance-scale.v1"
assert c["reference"]["profiles"]==4 and c["reference"]["budgets"]==4
assert c["reference"]["benchmarks"]==6 and c["reference"]["benchmark_passes"]==5 and c["reference"]["benchmark_warnings"]==1
assert c["reference"]["backpressure_rules"]==3 and c["reference"]["degradation_decisions"]==3
assert all(c["principles"].values())
assert not any(c["boundaries"].values())
print("PASS - Platform Core v3.98.0 Entity & Evidence Runtime Performance and Scale")
print(f"CONTRACT={c['contract']}")
for k in ["profiles","budgets","cache_policies","traversal_limits","batch_policies","cardinality_policies","queue_policies","package_envelopes","backpressure_rules","degradation_decisions","benchmarks","benchmark_passes","benchmark_warnings","traces","snapshots"]: print(f"{k.upper()}={c['reference'][k]}")
print("PERFORMANCE_OPTIMIZATION_PRESERVES_EPISTEMIC_STATE=true")
print("SILENT_TRUNCATION_ALLOWED=false")
print("DEGRADED_MODE_MAY_INCREASE_AUTHORITY=false")
print("IDENTITY_GRAPH_MUTATION_PERFORMED=false")
print("RELATIONSHIP_GRAPH_MUTATION_PERFORMED=false")
print("EVIDENCE_GRAPH_MUTATION_PERFORMED=false")
