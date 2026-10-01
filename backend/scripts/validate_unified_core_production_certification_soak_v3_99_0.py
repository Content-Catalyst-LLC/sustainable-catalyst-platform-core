from app.services.unified_core_production_certification_soak import contract_document, reference_unified_core_production_certification_soak_bundle

c=contract_document(); b=reference_unified_core_production_certification_soak_bundle()
assert c["release"]=="3.99.0"
assert c["contract"]=="sc.core.unified-core-production-certification-soak.v1"
assert c["reference"]["contracts"]==42
assert c["reference"]["gates"]==12 and c["reference"]["gate_passes"]==11 and c["reference"]["gate_warnings"]==1
assert c["reference"]["route_surfaces"]==4 and c["reference"]["recovery_records"]==4
assert c["reference"]["soak_observations"]==3 and c["reference"]["soak_pending"]==2
assert c["reference"]["decision"]=="approved-for-controlled-soak" and c["reference"]["minimum_soak_hours"]==24
assert all(c["principles"].values())
assert not any(c["boundaries"].values())
print("PASS - Platform Core v3.99.0 Unified Core Production Certification & Soak")
print(f"CONTRACT={c['contract']}")
for k in ["contracts","gates","gate_passes","gate_warnings","route_surfaces","recovery_records","soak_observations","soak_pending","qualifications","minimum_soak_hours","snapshots"]: print(f"{k.upper()}={c['reference'][k]}")
print(f"DECISION={c['reference']['decision']}")
print("FULL_PRODUCTION_CERTIFICATION_REQUIRES_ELAPSED_SOAK=true")
print("PRODUCTION_CERTIFICATION_CLAIMED_BEFORE_ELAPSED_SOAK=false")
print("IDENTITY_GRAPH_MUTATION_PERFORMED=false")
print("RELATIONSHIP_GRAPH_MUTATION_PERFORMED=false")
print("EVIDENCE_GRAPH_MUTATION_PERFORMED=false")
