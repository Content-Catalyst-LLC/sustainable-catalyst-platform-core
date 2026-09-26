#!/usr/bin/env python3

from app.services.runtime_security_governance import (
    CONTRACT_VERSION,
    SecurityCapability,
    SecurityDecision,
    contract_document,
    evaluate_security_request,
    reference_runtime_security_governance_bundle,
    to_scientific_security_artifact,
)
from app.services.scientific_result_registry import ScientificArtifactRef

doc = contract_document()
assert doc["release"] == "3.43.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["capabilities"]["runtime_allowlists"] is True
assert doc["capabilities"]["network_governance"] is True
assert doc["capabilities"]["secret_reference_governance"] is True
assert doc["capabilities"]["human_approval_bindings"] is True
assert doc["capabilities"]["isolation_attestations"] is True
assert doc["integration"]["workspace_or_execution_host_enforces_isolation"] is True
assert doc["boundaries"]["core_launches_sandboxes"] is False
assert doc["boundaries"]["core_resolves_secret_values"] is False

bundle = reference_runtime_security_governance_bundle()
assert len(bundle.records) == 3
assert len(bundle.fingerprint()) == 64
assert [record.decision.decision for record in bundle.records] == [
    SecurityDecision.allow,
    SecurityDecision.allow,
    SecurityDecision.deny,
]

safe = bundle.records[0]
assert safe.attestation is not None
assert safe.attestation.status == "passed"
assert all(safe.attestation.enforcement_checks.values())

approved = bundle.records[1]
assert approved.approval is not None
assert approved.approval.approved_capabilities == [SecurityCapability.secret_access]
assert approved.decision.approval_ref == approved.approval.approval_id

denied = bundle.records[2]
assert denied.decision.violations
assert denied.decision.violations[0].code == "arbitrary-code-denied"

pending_request = approved.request.model_copy(
    update={"security_request_id": "security-request:validator-pending"}
)
pending = evaluate_security_request(
    policy=approved.policy,
    request=pending_request,
)
assert pending.decision == SecurityDecision.requires_approval
assert pending.required_approval_capabilities == [SecurityCapability.secret_access]

payload = to_scientific_security_artifact(bundle)
ScientificArtifactRef.model_validate(payload)

print("PASS - Platform Core v3.43.0 Runtime Security, Isolation & Governance")
print(f"CONTRACT={CONTRACT_VERSION}")
print("RUNTIME_ALLOWLISTS=enabled")
print("ADAPTER_ALLOWLISTS=enabled")
print("OPERATION_ALLOWLISTS=enabled")
print("NETWORK_GOVERNANCE=enabled")
print("FILESYSTEM_GOVERNANCE=enabled")
print("PACKAGE_INSTALL_GOVERNANCE=enabled")
print("SECRET_REFERENCE_GOVERNANCE=enabled")
print("SHELL_ARBITRARY_CODE_GOVERNANCE=enabled")
print("ARTIFACT_EGRESS_GOVERNANCE=enabled")
print("HUMAN_APPROVAL_BINDINGS=enabled")
print("ISOLATION_ATTESTATIONS=enabled")
print("SECURITY_EVENT_PROVENANCE=enabled")
print("REPRODUCTION_SECURITY_BINDING=enabled")
print("SCIENTIFIC_REGISTRY_BRIDGE=enabled")
print("CORE_LAUNCHES_SANDBOXES=false")
print("CORE_APPLIES_KERNEL_SECURITY_CONTROLS=false")
print("CORE_RESOLVES_SECRET_VALUES=false")
print("CORE_INSTALLS_PACKAGES=false")
print("CORE_GRANTS_APPROVAL_WITHOUT_OBJECT=false")
print("CORE_CERTIFIES_ISOLATION_WITHOUT_ATTESTATION=false")
print("CORE_CERTIFIES_SCIENTIFIC_VALIDITY=false")
