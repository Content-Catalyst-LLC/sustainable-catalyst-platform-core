from app.services.federated_evidence_graph_exchange import contract_document, reference_federated_evidence_graph_exchange_bundle

c=contract_document(); b=reference_federated_evidence_graph_exchange_bundle()
assert c["ok"] is True and c["release"]=="3.89.0"
assert c["contract"]=="sc.core.federated-evidence-graph-exchange.v1"
assert len(b.nodes)==2 and len(b.object_descriptors)==5 and len(b.conflicts)==1
assert b.assessments[0].disposition.value=="accepted-for-local-validation"
assert c["principles"]["reference_first_exchange"] is True
assert c["boundaries"]["node_trust_establishes_content_truth"] is False
assert c["boundaries"]["signature_validity_establishes_content_truth"] is False
assert c["boundaries"]["remote_acceptance_creates_local_evidence"] is False
assert c["boundaries"]["evidence_graph_mutation_performed"] is False
print("PASS - Platform Core v3.89.0 Federated Evidence Graph Exchange Contract")
print(f"CONTRACT={c['contract']}")
print(f"NODES={len(b.nodes)}")
print(f"OBJECT_DESCRIPTORS={len(b.object_descriptors)}")
print(f"PACKAGE_REFERENCES={len(b.package_references)}")
print(f"CONFLICTS={len(b.conflicts)}")
print(f"ASSESSMENT={b.assessments[0].disposition.value}")
print("NODE_TRUST_IS_CONTENT_TRUTH=false")
print("SIGNATURE_VALIDITY_IS_CONTENT_TRUTH=false")
print("REMOTE_ACCEPTANCE_CREATES_LOCAL_EVIDENCE=false")
print("EVIDENCE_GRAPH_MUTATION_PERFORMED=false")
