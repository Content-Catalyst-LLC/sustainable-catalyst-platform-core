from app.services.unified_runtime_observability_audit_drift_intelligence import contract_document, reference_unified_runtime_observability_audit_drift_bundle

c=contract_document(); b=reference_unified_runtime_observability_audit_drift_bundle()
assert c["release"]=="3.97.0"
assert c["contract"]=="sc.core.unified-runtime-observability-audit-drift-intelligence.v1"
assert c["reference"]["health_observations"]==6 and c["reference"]["contract_health"]==3
assert c["reference"]["drift_baselines"]==3 and c["reference"]["drift_observations"]==5
assert c["reference"]["alerts"]==4 and c["reference"]["slo_breaches"]==1
assert all(c["principles"].values())
assert not any(c["boundaries"].values())
print("PASS - Platform Core v3.97.0 Unified Runtime Observability, Audit & Drift Intelligence")
print(f"CONTRACT={c['contract']}")
for k in ["health_observations","contract_health","audit_events","provenance_gaps","drift_baselines","drift_observations","stale_evidence_signals","federation_policy_drift","slo_indicators","alerts","traces","snapshots","out_of_tolerance_drifts","slo_breaches"]: print(f"{k.upper()}={c['reference'][k]}")
print("DRIFT_ESTABLISHES_CLAIM_FALSE=false")
print("FAILED_HEALTH_CHECK_INVALIDATES_EVIDENCE=false")
print("ALERT_PROMOTES_OR_DEMOTES_EPISTEMIC_STATE=false")
print("IDENTITY_GRAPH_MUTATION_PERFORMED=false")
print("RELATIONSHIP_GRAPH_MUTATION_PERFORMED=false")
print("EVIDENCE_GRAPH_MUTATION_PERFORMED=false")
