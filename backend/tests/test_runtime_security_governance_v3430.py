from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.runtime_security_governance import (
    CONTRACT_VERSION,
    REFERENCE_JULIA_ADAPTER,
    REFERENCE_JULIA_RUNTIME,
    REFERENCE_R_ADAPTER,
    REFERENCE_R_RUNTIME,
    ApprovalStatus,
    AttestationStatus,
    FilesystemAccessMode,
    GovernanceApproval,
    IsolationAttestation,
    IsolationMechanism,
    NetworkAccessMode,
    PackageInstallMode,
    RuntimeGovernanceRecord,
    RuntimeIsolationProfile,
    RuntimeSecurityDecision,
    RuntimeSecurityEvent,
    RuntimeSecurityGovernanceBundle,
    RuntimeSecurityPolicy,
    RuntimeSecurityRequest,
    RuntimeSecurityViolation,
    SecurityCapability,
    SecurityDecision,
    SecurityEventSeverity,
    SecurityPolicyState,
    contract_document,
    evaluate_security_request,
    reference_runtime_security_governance_bundle,
    to_scientific_security_artifact,
)


def ref_bundle():
    return reference_runtime_security_governance_bundle()


def ref_policy():
    return ref_bundle().records[0].policy


def safe_request():
    return ref_bundle().records[0].request


def test_contract_identity():
    doc = contract_document()
    assert doc["release"] == "3.43.0"
    assert doc["contract"] == CONTRACT_VERSION


def test_contract_links_v342_reproduction_engine():
    assert "sc.core.verification-reproduction-engine.v1" in contract_document()["depends_on"]


def test_contract_links_v341_environment_packages():
    assert "sc.core.reproducible-environment-package.v1" in contract_document()["depends_on"]


def test_contract_links_v340_workflow():
    assert "sc.core.cross-runtime-research-workflow.v1" in contract_document()["depends_on"]


def test_reference_bundle_has_three_governance_records():
    assert len(ref_bundle().records) == 3


def test_reference_decisions_cover_allow_and_deny():
    decisions = {record.decision.decision for record in ref_bundle().records}
    assert SecurityDecision.allow in decisions
    assert SecurityDecision.deny in decisions


def test_reference_secret_approval_record_has_approval():
    record = [
        item for item in ref_bundle().records
        if item.request.security_request_id == "security-request:r-secret-access:reference"
    ][0]
    assert record.approval is not None
    assert record.decision.decision == SecurityDecision.allow


def test_reference_denied_record_has_violation():
    record = [
        item for item in ref_bundle().records
        if item.decision.decision == SecurityDecision.deny
    ][0]
    assert record.decision.violations
    assert record.decision.violations[0].code == "arbitrary-code-denied"


def test_isolation_profile_rejects_host_mount_without_unrestricted_fs():
    with pytest.raises(ValidationError):
        RuntimeIsolationProfile(
            isolation_profile_id="isolation:test",
            mechanism=IsolationMechanism.container,
            filesystem_mode=FilesystemAccessMode.workspace_only,
            host_filesystem_mounted=True,
        )


def test_high_isolation_rejects_privilege_escalation():
    with pytest.raises(ValidationError):
        RuntimeIsolationProfile(
            isolation_profile_id="isolation:test",
            mechanism=IsolationMechanism.sandbox,
            privilege_escalation_allowed=True,
        )


def test_container_profile_can_be_unrestricted_if_explicit():
    profile = RuntimeIsolationProfile(
        isolation_profile_id="isolation:test",
        mechanism=IsolationMechanism.container,
        filesystem_mode=FilesystemAccessMode.unrestricted,
        host_filesystem_mounted=True,
    )
    assert profile.host_filesystem_mounted is True


def test_isolation_fingerprint_stable():
    profile = ref_policy().isolation_profile
    assert profile.fingerprint() == deepcopy(profile).fingerprint()


def test_policy_rejects_duplicate_runtime_refs():
    data = ref_policy().model_dump(mode="python")
    data["allowed_runtime_refs"].append(data["allowed_runtime_refs"][0])
    with pytest.raises(ValidationError):
        RuntimeSecurityPolicy.model_validate(data)


def test_policy_rejects_duplicate_adapter_refs():
    data = ref_policy().model_dump(mode="python")
    data["allowed_adapter_refs"].append(data["allowed_adapter_refs"][0])
    with pytest.raises(ValidationError):
        RuntimeSecurityPolicy.model_validate(data)


def test_policy_rejects_duplicate_secret_refs():
    data = ref_policy().model_dump(mode="python")
    data["allowed_secret_refs"].append(data["allowed_secret_refs"][0])
    with pytest.raises(ValidationError):
        RuntimeSecurityPolicy.model_validate(data)


def test_policy_rejects_duplicate_approval_capabilities():
    data = ref_policy().model_dump(mode="python")
    data["approval_required_capabilities"] = [
        SecurityCapability.secret_access,
        SecurityCapability.secret_access,
    ]
    with pytest.raises(ValidationError):
        RuntimeSecurityPolicy.model_validate(data)


def test_policy_rejects_operations_for_unknown_runtime():
    data = ref_policy().model_dump(mode="python")
    data["allowed_operations"]["runtime:missing"] = ["op"]
    with pytest.raises(ValidationError):
        RuntimeSecurityPolicy.model_validate(data)


def test_policy_rejects_duplicate_operations():
    data = ref_policy().model_dump(mode="python")
    data["allowed_operations"][REFERENCE_R_RUNTIME] = ["mean", "mean"]
    with pytest.raises(ValidationError):
        RuntimeSecurityPolicy.model_validate(data)


def test_policy_fingerprint_ignores_state():
    policy = ref_policy()
    other = deepcopy(policy)
    other.state = SecurityPolicyState.archived
    assert policy.fingerprint() == other.fingerprint()


def test_policy_fingerprint_ignores_created_at():
    policy = ref_policy()
    assert policy.fingerprint() == deepcopy(policy).fingerprint()
    assert len(policy.fingerprint()) == 64


def test_request_capabilities_network():
    req = safe_request().model_copy(update={
        "requested_network_destinations": ["https://example.test"]
    })
    assert SecurityCapability.network in req.requested_capabilities()


def test_request_capabilities_write():
    req = safe_request()
    assert SecurityCapability.filesystem_write in req.requested_capabilities()


def test_request_capabilities_package_install():
    req = safe_request().model_copy(update={"requested_package_refs": ["pkg:test"]})
    assert SecurityCapability.package_install in req.requested_capabilities()


def test_request_capabilities_secret():
    req = safe_request().model_copy(update={"requested_secret_refs": ["secret-ref:test"]})
    assert SecurityCapability.secret_access in req.requested_capabilities()


def test_request_capabilities_shell():
    req = safe_request().model_copy(update={"shell_requested": True})
    assert SecurityCapability.shell in req.requested_capabilities()


def test_request_capabilities_arbitrary_code():
    req = safe_request().model_copy(update={"arbitrary_code_requested": True})
    assert SecurityCapability.arbitrary_code in req.requested_capabilities()


def test_request_capabilities_egress():
    req = safe_request()
    assert SecurityCapability.artifact_egress in req.requested_capabilities()


def test_request_fingerprint_stable():
    req = safe_request()
    assert req.fingerprint() == deepcopy(req).fingerprint()


def test_approval_requires_capabilities():
    with pytest.raises(ValidationError):
        GovernanceApproval(
            approval_id="approval:test",
            security_request_ref="request:test",
            approved_capabilities=[],
            approver_ref="actor:test",
        )


def test_approval_rejects_duplicate_capabilities():
    with pytest.raises(ValidationError):
        GovernanceApproval(
            approval_id="approval:test",
            security_request_ref="request:test",
            approved_capabilities=[
                SecurityCapability.secret_access,
                SecurityCapability.secret_access,
            ],
            approver_ref="actor:test",
        )


def test_approval_fingerprint_ignores_time():
    approval = ref_bundle().records[1].approval
    assert approval is not None
    assert approval.fingerprint() == deepcopy(approval).fingerprint()


def test_violation_fingerprint_stable():
    violation = RuntimeSecurityViolation(
        violation_id="violation:test",
        code="test",
        message="test violation",
    )
    assert violation.fingerprint() == deepcopy(violation).fingerprint()


def test_allow_decision_rejects_violations():
    policy = ref_policy()
    req = safe_request()
    with pytest.raises(ValidationError):
        RuntimeSecurityDecision(
            security_decision_id="decision:test",
            security_policy_ref=policy.security_policy_id,
            security_policy_fingerprint_sha256=policy.fingerprint(),
            security_request_ref=req.security_request_id,
            security_request_fingerprint_sha256=req.fingerprint(),
            decision=SecurityDecision.allow,
            violations=[
                RuntimeSecurityViolation(
                    violation_id="violation:test",
                    code="bad",
                    message="bad",
                )
            ],
        )


def test_deny_decision_requires_violation():
    policy = ref_policy()
    req = safe_request()
    with pytest.raises(ValidationError):
        RuntimeSecurityDecision(
            security_decision_id="decision:test",
            security_policy_ref=policy.security_policy_id,
            security_policy_fingerprint_sha256=policy.fingerprint(),
            security_request_ref=req.security_request_id,
            security_request_fingerprint_sha256=req.fingerprint(),
            decision=SecurityDecision.deny,
        )


def test_requires_approval_decision_requires_capability():
    policy = ref_policy()
    req = safe_request()
    with pytest.raises(ValidationError):
        RuntimeSecurityDecision(
            security_decision_id="decision:test",
            security_policy_ref=policy.security_policy_id,
            security_policy_fingerprint_sha256=policy.fingerprint(),
            security_request_ref=req.security_request_id,
            security_request_fingerprint_sha256=req.fingerprint(),
            decision=SecurityDecision.requires_approval,
        )


def test_decision_fingerprint_stable():
    decision = ref_bundle().records[0].decision
    assert decision.fingerprint() == deepcopy(decision).fingerprint()


def test_passed_attestation_requires_checks():
    policy = ref_policy()
    req = safe_request()
    decision = evaluate_security_request(policy=policy, request=req)
    with pytest.raises(ValidationError):
        IsolationAttestation(
            attestation_id="attestation:test",
            security_policy_ref=policy.security_policy_id,
            security_policy_fingerprint_sha256=policy.fingerprint(),
            security_request_ref=req.security_request_id,
            security_request_fingerprint_sha256=req.fingerprint(),
            security_decision_ref=decision.security_decision_id,
            execution_host_ref="host:test",
            computational_job_ref=req.computational_job_ref,
            mechanism=IsolationMechanism.container,
            status=AttestationStatus.passed,
        )


def test_passed_attestation_rejects_failed_check():
    policy = ref_policy()
    req = safe_request()
    decision = evaluate_security_request(policy=policy, request=req)
    with pytest.raises(ValidationError):
        IsolationAttestation(
            attestation_id="attestation:test",
            security_policy_ref=policy.security_policy_id,
            security_policy_fingerprint_sha256=policy.fingerprint(),
            security_request_ref=req.security_request_id,
            security_request_fingerprint_sha256=req.fingerprint(),
            security_decision_ref=decision.security_decision_id,
            execution_host_ref="host:test",
            computational_job_ref=req.computational_job_ref,
            mechanism=IsolationMechanism.container,
            enforcement_checks={"network-disabled": False},
            status=AttestationStatus.passed,
        )


def test_reference_attestation_passed():
    attestation = ref_bundle().records[0].attestation
    assert attestation is not None
    assert attestation.status == AttestationStatus.passed
    assert all(attestation.enforcement_checks.values())


def test_attestation_fingerprint_stable():
    attestation = ref_bundle().records[0].attestation
    assert attestation is not None
    assert attestation.fingerprint() == deepcopy(attestation).fingerprint()


def test_security_event_fingerprint_ignores_time():
    event = ref_bundle().records[0].events[0]
    assert event.fingerprint() == deepcopy(event).fingerprint()


def test_governance_record_rejects_wrong_policy_ref():
    record = ref_bundle().records[0].model_dump(mode="python")
    record["decision"]["security_policy_ref"] = "policy:wrong"
    with pytest.raises(ValidationError):
        RuntimeGovernanceRecord.model_validate(record)


def test_governance_record_rejects_wrong_policy_fingerprint():
    record = ref_bundle().records[0].model_dump(mode="python")
    record["decision"]["security_policy_fingerprint_sha256"] = "f" * 64
    with pytest.raises(ValidationError):
        RuntimeGovernanceRecord.model_validate(record)


def test_governance_record_rejects_wrong_request_ref():
    record = ref_bundle().records[0].model_dump(mode="python")
    record["decision"]["security_request_ref"] = "request:wrong"
    with pytest.raises(ValidationError):
        RuntimeGovernanceRecord.model_validate(record)


def test_governance_record_rejects_wrong_request_fingerprint():
    record = ref_bundle().records[0].model_dump(mode="python")
    record["decision"]["security_request_fingerprint_sha256"] = "f" * 64
    with pytest.raises(ValidationError):
        RuntimeGovernanceRecord.model_validate(record)


def test_governance_record_rejects_wrong_approval_request():
    record = ref_bundle().records[1].model_dump(mode="python")
    record["approval"]["security_request_ref"] = "request:wrong"
    with pytest.raises(ValidationError):
        RuntimeGovernanceRecord.model_validate(record)


def test_governance_record_rejects_wrong_approval_ref():
    record = ref_bundle().records[1].model_dump(mode="python")
    record["decision"]["approval_ref"] = "approval:wrong"
    with pytest.raises(ValidationError):
        RuntimeGovernanceRecord.model_validate(record)


def test_governance_record_rejects_wrong_attestation_decision():
    record = ref_bundle().records[0].model_dump(mode="python")
    record["attestation"]["security_decision_ref"] = "decision:wrong"
    with pytest.raises(ValidationError):
        RuntimeGovernanceRecord.model_validate(record)


def test_governance_record_rejects_duplicate_event_ids():
    record = ref_bundle().records[0].model_dump(mode="python")
    record["events"] = [record["events"][0], deepcopy(record["events"][0])]
    with pytest.raises(ValidationError):
        RuntimeGovernanceRecord.model_validate(record)


def test_governance_record_fingerprint_stable():
    record = ref_bundle().records[0]
    assert record.fingerprint() == deepcopy(record).fingerprint()


def test_bundle_requires_records():
    with pytest.raises(ValidationError):
        RuntimeSecurityGovernanceBundle(
            bundle_id="bundle:test",
            records=[],
        )


def test_bundle_rejects_duplicate_record_ids():
    record = ref_bundle().records[0]
    with pytest.raises(ValidationError):
        RuntimeSecurityGovernanceBundle(
            bundle_id="bundle:test",
            records=[record, deepcopy(record)],
        )


def test_bundle_fingerprint_stable():
    bundle = ref_bundle()
    assert bundle.fingerprint() == deepcopy(bundle).fingerprint()
    assert len(bundle.fingerprint()) == 64


def test_safe_request_allowed():
    policy = ref_policy()
    req = safe_request()
    decision = evaluate_security_request(policy=policy, request=req)
    assert decision.decision == SecurityDecision.allow
    assert not decision.violations


def test_unknown_runtime_denied():
    req = safe_request().model_copy(update={"runtime_ref": "runtime:missing"})
    decision = evaluate_security_request(policy=ref_policy(), request=req)
    assert decision.decision == SecurityDecision.deny
    assert any(v.code == "runtime-not-allowed" for v in decision.violations)


def test_unknown_adapter_denied():
    req = safe_request().model_copy(update={"runtime_adapter_ref": "adapter:missing"})
    decision = evaluate_security_request(policy=ref_policy(), request=req)
    assert decision.decision == SecurityDecision.deny
    assert any(v.code == "adapter-not-allowed" for v in decision.violations)


def test_unknown_operation_denied():
    req = safe_request().model_copy(update={"operation": "dangerous-op"})
    decision = evaluate_security_request(policy=ref_policy(), request=req)
    assert decision.decision == SecurityDecision.deny
    assert any(v.code == "operation-not-allowed" for v in decision.violations)


def test_network_request_denied_when_network_none():
    req = safe_request().model_copy(update={
        "requested_network_destinations": ["https://example.test"]
    })
    decision = evaluate_security_request(policy=ref_policy(), request=req)
    assert decision.decision == SecurityDecision.deny
    assert any(v.code == "network-denied" for v in decision.violations)


def test_network_allowlist_permits_allowed_destination():
    policy = deepcopy(ref_policy())
    policy.isolation_profile.network_mode = NetworkAccessMode.allowlist
    policy.allowed_network_destinations = ["https://api.example.test"]
    req = safe_request().model_copy(update={
        "requested_network_destinations": ["https://api.example.test"]
    })
    decision = evaluate_security_request(policy=policy, request=req)
    assert decision.decision == SecurityDecision.allow


def test_network_allowlist_denies_unknown_destination():
    policy = deepcopy(ref_policy())
    policy.isolation_profile.network_mode = NetworkAccessMode.allowlist
    policy.allowed_network_destinations = ["https://api.example.test"]
    req = safe_request().model_copy(update={
        "requested_network_destinations": ["https://other.example.test"]
    })
    decision = evaluate_security_request(policy=policy, request=req)
    assert decision.decision == SecurityDecision.deny
    assert any(v.code == "network-destination-not-allowed" for v in decision.violations)


def test_workspace_write_path_allowed():
    decision = evaluate_security_request(policy=ref_policy(), request=safe_request())
    assert decision.decision == SecurityDecision.allow


def test_write_path_outside_workspace_denied():
    req = safe_request().model_copy(update={"requested_write_paths": ["/etc/passwd"]})
    decision = evaluate_security_request(policy=ref_policy(), request=req)
    assert decision.decision == SecurityDecision.deny
    assert any(v.code == "filesystem-path-not-allowed" for v in decision.violations)


def test_read_only_mode_denies_write():
    policy = deepcopy(ref_policy())
    policy.isolation_profile.filesystem_mode = FilesystemAccessMode.read_only
    decision = evaluate_security_request(policy=policy, request=safe_request())
    assert decision.decision == SecurityDecision.deny
    assert any(v.code == "filesystem-write-denied" for v in decision.violations)


def test_package_install_denied():
    req = safe_request().model_copy(update={"requested_package_refs": ["pkg:numpy"]})
    decision = evaluate_security_request(policy=ref_policy(), request=req)
    assert decision.decision == SecurityDecision.deny
    assert any(v.code == "package-install-denied" for v in decision.violations)


def test_package_allowlist_permits_allowed_package():
    policy = deepcopy(ref_policy())
    policy.isolation_profile.package_install_mode = PackageInstallMode.allowlist
    policy.allowed_package_refs = ["pkg:numpy@2"]
    req = safe_request().model_copy(update={"requested_package_refs": ["pkg:numpy@2"]})
    decision = evaluate_security_request(policy=policy, request=req)
    assert decision.decision == SecurityDecision.allow


def test_package_allowlist_denies_unknown_package():
    policy = deepcopy(ref_policy())
    policy.isolation_profile.package_install_mode = PackageInstallMode.allowlist
    policy.allowed_package_refs = ["pkg:numpy@2"]
    req = safe_request().model_copy(update={"requested_package_refs": ["pkg:other@1"]})
    decision = evaluate_security_request(policy=policy, request=req)
    assert decision.decision == SecurityDecision.deny
    assert any(v.code == "package-not-allowed" for v in decision.violations)


def test_unknown_secret_denied():
    req = safe_request().model_copy(update={"requested_secret_refs": ["secret-ref:other"]})
    decision = evaluate_security_request(policy=ref_policy(), request=req)
    assert decision.decision == SecurityDecision.deny
    assert any(v.code == "secret-not-allowed" for v in decision.violations)


def test_allowed_secret_requires_approval():
    req = safe_request().model_copy(
        update={
            "security_request_id": "request:secret",
            "requested_secret_refs": ["secret-ref:sc-research-api-key"],
        }
    )
    decision = evaluate_security_request(policy=ref_policy(), request=req)
    assert decision.decision == SecurityDecision.requires_approval
    assert decision.required_approval_capabilities == [SecurityCapability.secret_access]


def test_allowed_secret_with_approval_allowed():
    req = safe_request().model_copy(
        update={
            "security_request_id": "request:secret",
            "requested_secret_refs": ["secret-ref:sc-research-api-key"],
        }
    )
    approval = GovernanceApproval(
        approval_id="approval:secret",
        security_request_ref=req.security_request_id,
        approved_capabilities=[SecurityCapability.secret_access],
        approver_ref="actor:reviewer",
    )
    decision = evaluate_security_request(policy=ref_policy(), request=req, approval=approval)
    assert decision.decision == SecurityDecision.allow
    assert decision.approval_ref == approval.approval_id


def test_revoked_approval_does_not_authorize():
    req = safe_request().model_copy(
        update={
            "security_request_id": "request:secret",
            "requested_secret_refs": ["secret-ref:sc-research-api-key"],
        }
    )
    approval = GovernanceApproval(
        approval_id="approval:secret",
        security_request_ref=req.security_request_id,
        approved_capabilities=[SecurityCapability.secret_access],
        approver_ref="actor:reviewer",
        status=ApprovalStatus.revoked,
    )
    decision = evaluate_security_request(policy=ref_policy(), request=req, approval=approval)
    assert decision.decision == SecurityDecision.requires_approval


def test_approval_for_other_request_rejected():
    req = safe_request().model_copy(
        update={
            "security_request_id": "request:secret",
            "requested_secret_refs": ["secret-ref:sc-research-api-key"],
        }
    )
    approval = GovernanceApproval(
        approval_id="approval:secret",
        security_request_ref="request:other",
        approved_capabilities=[SecurityCapability.secret_access],
        approver_ref="actor:reviewer",
    )
    with pytest.raises(ValueError):
        evaluate_security_request(policy=ref_policy(), request=req, approval=approval)


def test_shell_request_denied():
    req = safe_request().model_copy(update={"shell_requested": True})
    decision = evaluate_security_request(policy=ref_policy(), request=req)
    assert decision.decision == SecurityDecision.deny
    assert any(v.code == "shell-denied" for v in decision.violations)


def test_arbitrary_code_request_denied():
    req = safe_request().model_copy(update={"arbitrary_code_requested": True})
    decision = evaluate_security_request(policy=ref_policy(), request=req)
    assert decision.decision == SecurityDecision.deny
    assert any(v.code == "arbitrary-code-denied" for v in decision.violations)


def test_disallowed_egress_class_denied():
    req = safe_request().model_copy(update={"artifact_egress_classes": ["credential-dump"]})
    decision = evaluate_security_request(policy=ref_policy(), request=req)
    assert decision.decision == SecurityDecision.deny
    assert any(v.code == "artifact-egress-class-not-allowed" for v in decision.violations)


def test_egress_disabled_denies_all_egress():
    policy = deepcopy(ref_policy())
    policy.isolation_profile.outbound_artifact_egress_allowed = False
    decision = evaluate_security_request(policy=policy, request=safe_request())
    assert decision.decision == SecurityDecision.deny
    assert any(v.code == "artifact-egress-denied" for v in decision.violations)


def test_decision_fingerprint_contains_policy_and_request():
    decision = evaluate_security_request(policy=ref_policy(), request=safe_request())
    assert decision.security_policy_fingerprint_sha256 == ref_policy().fingerprint()
    assert decision.security_request_fingerprint_sha256 == safe_request().fingerprint()


def test_scientific_artifact_bridge():
    payload = to_scientific_security_artifact(ref_bundle())
    assert payload["artifact_kind"] == "package"
    assert payload["source_contract"] == CONTRACT_VERSION
    assert payload["content_sha256"] == ref_bundle().fingerprint()


def test_scientific_artifact_bridge_validates_v338():
    from app.services.scientific_result_registry import ScientificArtifactRef
    payload = to_scientific_security_artifact(ref_bundle())
    item = ScientificArtifactRef.model_validate(payload)
    assert item.source_object_ref == ref_bundle().bundle_id


def test_scientific_artifact_decision_counts():
    payload = to_scientific_security_artifact(ref_bundle())
    counts = payload["metadata"]["decision_counts"]
    assert counts["allow"] == 2
    assert counts["deny"] == 1
    assert counts["requires-approval"] == 0


def test_security_capabilities_cover_governance_surface():
    values = {item.value for item in SecurityCapability}
    assert {
        "network",
        "filesystem-write",
        "package-install",
        "secret-access",
        "shell",
        "arbitrary-code",
        "artifact-egress",
    }.issubset(values)


def test_isolation_mechanisms_cover_execution_models():
    values = {item.value for item in IsolationMechanism}
    assert {"container", "sandbox", "microvm", "wasm", "remote-worker"}.issubset(values)


def test_core_does_not_launch_sandboxes():
    assert contract_document()["boundaries"]["core_launches_sandboxes"] is False


def test_core_does_not_apply_kernel_controls():
    assert contract_document()["boundaries"]["core_applies_kernel_security_controls"] is False


def test_core_does_not_resolve_secrets():
    assert contract_document()["boundaries"]["core_resolves_secret_values"] is False


def test_core_does_not_install_packages():
    assert contract_document()["boundaries"]["core_installs_packages"] is False


def test_core_does_not_grant_approval_without_object():
    assert contract_document()["boundaries"]["core_grants_approval_without_approval_object"] is False


def test_core_does_not_certify_isolation_without_attestation():
    assert contract_document()["boundaries"]["core_certifies_isolation_without_attestation"] is False


def test_core_does_not_certify_scientific_validity():
    assert contract_document()["boundaries"]["core_certifies_scientific_validity"] is False


def test_execution_host_enforces_isolation():
    doc = contract_document()
    assert doc["integration"]["workspace_or_execution_host_enforces_isolation"] is True
    assert doc["integration"]["core_enforces_os_container_isolation"] is False


def test_contract_reference_pending_secret_requires_approval():
    doc = contract_document()
    assert doc["reference"]["pending_secret_request_decision"] == "requires-approval"
    assert doc["reference"]["pending_secret_required_capabilities"] == ["secret-access"]


def test_contract_reference_decisions():
    assert contract_document()["reference"]["decisions"] == ["allow", "allow", "deny"]


def test_contract_bundle_fingerprint_is_sha256():
    assert len(contract_document()["reference"]["bundle_fingerprint_sha256"]) == 64
