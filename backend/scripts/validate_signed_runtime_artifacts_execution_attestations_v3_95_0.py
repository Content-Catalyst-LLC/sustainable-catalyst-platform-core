from app.services.signed_runtime_artifacts_execution_attestations import contract_document, reference_signed_runtime_artifacts_execution_attestations_bundle, VerificationDisposition

d=contract_document(); b=reference_signed_runtime_artifacts_execution_attestations_bundle()
assert d["release"]=="3.95.0"
assert d["contract"]=="sc.core.signed-runtime-artifacts-execution-attestations.v1"
assert d["reference"]["artifacts"]==8
assert d["reference"]["execution_manifests"]==2
assert d["reference"]["attestations"]==5
assert d["reference"]["verifications"]==5
assert d["reference"]["chains"]==2
assert d["reference"]["revoked_verifications"]==1
assert d["boundaries"]["valid_signature_establishes_content_truth"] is False
assert d["boundaries"]["attestation_promotes_epistemic_state"] is False
assert d["boundaries"]["signed_remote_reference_becomes_local_evidence"] is False
assert any(x.disposition==VerificationDisposition.revoked for x in b.verifications)
assert b.identity_graph_mutation_performed is False
assert b.relationship_graph_mutation_performed is False
assert b.evidence_graph_mutation_performed is False
print("PASS - Platform Core v3.95.0 Signed Runtime Artifacts & Execution Attestations")
print(f"CONTRACT={d['contract']}")
for k in ['signers','keys','revocations','artifacts','execution_manifests','attestations','verifications','chains','remote_reference_artifacts','revoked_verifications']:
    print(f"{k.upper()}={d['reference'][k]}")
print("VALID_SIGNATURE_ESTABLISHES_CONTENT_TRUTH=false")
print("ATTESTATION_PROMOTES_EPISTEMIC_STATE=false")
print("SIGNED_REMOTE_REFERENCE_BECOMES_LOCAL_EVIDENCE=false")
print("IDENTITY_GRAPH_MUTATION_PERFORMED=false")
print("RELATIONSHIP_GRAPH_MUTATION_PERFORMED=false")
print("EVIDENCE_GRAPH_MUTATION_PERFORMED=false")
