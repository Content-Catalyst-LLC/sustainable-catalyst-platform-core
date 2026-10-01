from app.services.federation_governance_trust_policy_runtime import contract_document, reference_federation_governance_trust_policy_bundle

c=contract_document(); b=reference_federation_governance_trust_policy_bundle()
assert c["release"]=="3.96.0"
assert c["contract"]=="sc.core.federation-governance-trust-policy-runtime.v1"
assert c["reference"]["nodes"]==3 and c["reference"]["trust_scopes"]==6 and c["reference"]["permissions"]==6
assert c["reference"]["decisions"]==3 and c["reference"]["denied_decisions"]==1
assert all(c["principles"].values())
assert not any(c["boundaries"].values())
print("PASS - Platform Core v3.96.0 Federation Governance, Trust & Policy Runtime")
print(f"CONTRACT={c['contract']}")
for k in ["nodes","trust_scopes","permissions","actions","intake_rules","decisions","conflicts","audit_events","snapshots","reference_only_decisions","denied_decisions"]: print(f"{k.upper()}={c['reference'][k]}")
print("TRUST_ESTABLISHES_CONTENT_TRUTH=false")
print("POLICY_APPROVAL_CREATES_LOCAL_EVIDENCE=false")
print("REMOTE_CONTENT_BYPASSES_LOCAL_VALIDATION=false")
print("IDENTITY_GRAPH_MUTATION_PERFORMED=false")
print("RELATIONSHIP_GRAPH_MUTATION_PERFORMED=false")
print("EVIDENCE_GRAPH_MUTATION_PERFORMED=false")
