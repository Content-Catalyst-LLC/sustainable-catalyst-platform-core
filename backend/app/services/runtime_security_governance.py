from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.43.0"
CONTRACT_VERSION = "sc.core.runtime-security-governance.v1"

VERIFICATION_REPRODUCTION_CONTRACT = "sc.core.verification-reproduction-engine.v1"
ENVIRONMENT_PACKAGE_CONTRACT = "sc.core.reproducible-environment-package.v1"
CROSS_RUNTIME_WORKFLOW_CONTRACT = "sc.core.cross-runtime-research-workflow.v1"
RUNTIME_INTERCHANGE_CONTRACT = "sc.core.runtime-data-interchange.v1"
COMPUTATIONAL_JOB_CONTRACT = "sc.core.computational-job.v1"
RUNTIME_ADAPTER_CONTRACT = "sc.core.runtime-adapter.v1"
RUNTIME_OBJECT_CONTRACT = "sc.core.computational-runtime-object.v1"

REFERENCE_R_RUNTIME = "sc-runtime-r"
REFERENCE_R_ADAPTER = "adapter:sc-runtime-r"
REFERENCE_JULIA_RUNTIME = "catalyst-julia-runtime"
REFERENCE_JULIA_ADAPTER = "adapter:catalyst-julia-runtime"


class SecurityDecision(str, Enum):
    allow = "allow"
    deny = "deny"
    requires_approval = "requires-approval"


class SecurityPolicyState(str, Enum):
    draft = "draft"
    active = "active"
    superseded = "superseded"
    archived = "archived"


class NetworkAccessMode(str, Enum):
    none = "none"
    allowlist = "allowlist"
    unrestricted = "unrestricted"


class FilesystemAccessMode(str, Enum):
    read_only = "read-only"
    workspace_only = "workspace-only"
    allowlist = "allowlist"
    unrestricted = "unrestricted"


class PackageInstallMode(str, Enum):
    denied = "denied"
    lockfile_only = "lockfile-only"
    allowlist = "allowlist"
    unrestricted = "unrestricted"


class IsolationMechanism(str, Enum):
    process = "process"
    container = "container"
    sandbox = "sandbox"
    microvm = "microvm"
    wasm = "wasm"
    remote_worker = "remote-worker"
    other = "other"


class AttestationStatus(str, Enum):
    not_run = "not-run"
    passed = "passed"
    warning = "warning"
    failed = "failed"


class SecurityEventSeverity(str, Enum):
    info = "info"
    warning = "warning"
    high = "high"
    critical = "critical"


class ApprovalStatus(str, Enum):
    active = "active"
    revoked = "revoked"
    expired = "expired"


class SecurityCapability(str, Enum):
    network = "network"
    filesystem_write = "filesystem-write"
    package_install = "package-install"
    secret_access = "secret-access"
    shell = "shell"
    arbitrary_code = "arbitrary-code"
    artifact_egress = "artifact-egress"


class RuntimeIsolationProfile(BaseModel):
    isolation_profile_id: str = Field(min_length=2, max_length=500)
    mechanism: IsolationMechanism
    network_mode: NetworkAccessMode = NetworkAccessMode.none
    filesystem_mode: FilesystemAccessMode = FilesystemAccessMode.workspace_only
    package_install_mode: PackageInstallMode = PackageInstallMode.denied
    process_namespace_isolated: bool = True
    user_namespace_isolated: bool = True
    privilege_escalation_allowed: bool = False
    host_filesystem_mounted: bool = False
    shell_allowed: bool = False
    arbitrary_code_allowed: bool = False
    outbound_artifact_egress_allowed: bool = True
    resource_budget_ref: str | None = Field(default=None, max_length=500)
    syscall_policy_ref: str | None = Field(default=None, max_length=500)
    mandatory_access_control_ref: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_isolation(self):
        if self.host_filesystem_mounted and self.filesystem_mode != FilesystemAccessMode.unrestricted:
            raise ValueError("host filesystem mount requires unrestricted filesystem mode")
        if self.privilege_escalation_allowed and self.mechanism in {
            IsolationMechanism.sandbox,
            IsolationMechanism.microvm,
            IsolationMechanism.wasm,
        }:
            raise ValueError("high-isolation mechanisms cannot declare privilege escalation")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RuntimeSecurityPolicy(BaseModel):
    security_policy_id: str = Field(min_length=2, max_length=500)
    policy_version: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=500)
    state: SecurityPolicyState = SecurityPolicyState.active
    default_decision: SecurityDecision = SecurityDecision.deny
    isolation_profile: RuntimeIsolationProfile
    allowed_runtime_refs: list[str] = Field(default_factory=list)
    allowed_adapter_refs: list[str] = Field(default_factory=list)
    allowed_operations: dict[str, list[str]] = Field(default_factory=dict)
    allowed_network_destinations: list[str] = Field(default_factory=list)
    allowed_filesystem_prefixes: list[str] = Field(default_factory=list)
    allowed_package_refs: list[str] = Field(default_factory=list)
    allowed_secret_refs: list[str] = Field(default_factory=list)
    allowed_artifact_egress_classes: list[str] = Field(default_factory=list)
    approval_required_capabilities: list[SecurityCapability] = Field(default_factory=list)
    execution_policy_ref: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy(self):
        for label, values in [
            ("runtime refs", self.allowed_runtime_refs),
            ("adapter refs", self.allowed_adapter_refs),
            ("network destinations", self.allowed_network_destinations),
            ("filesystem prefixes", self.allowed_filesystem_prefixes),
            ("package refs", self.allowed_package_refs),
            ("secret refs", self.allowed_secret_refs),
            ("artifact egress classes", self.allowed_artifact_egress_classes),
        ]:
            if len(values) != len(set(values)):
                raise ValueError(f"allowed {label} must be unique")

        if len(self.approval_required_capabilities) != len(set(self.approval_required_capabilities)):
            raise ValueError("approval-required capabilities must be unique")

        for runtime_ref, operations in self.allowed_operations.items():
            if runtime_ref not in self.allowed_runtime_refs:
                raise ValueError("allowed operations reference runtime outside allowed_runtime_refs")
            if len(operations) != len(set(operations)):
                raise ValueError("allowed operations must be unique per runtime")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("state", None)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class RuntimeSecurityRequest(BaseModel):
    security_request_id: str = Field(min_length=2, max_length=500)
    runtime_ref: str = Field(min_length=2, max_length=500)
    runtime_adapter_ref: str = Field(min_length=2, max_length=500)
    operation: str = Field(min_length=1, max_length=500)
    computational_job_ref: str = Field(min_length=2, max_length=500)
    environment_ref: str = Field(min_length=2, max_length=1000)
    requested_network_destinations: list[str] = Field(default_factory=list)
    requested_read_paths: list[str] = Field(default_factory=list)
    requested_write_paths: list[str] = Field(default_factory=list)
    requested_package_refs: list[str] = Field(default_factory=list)
    requested_secret_refs: list[str] = Field(default_factory=list)
    shell_requested: bool = False
    arbitrary_code_requested: bool = False
    artifact_egress_classes: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def requested_capabilities(self) -> set[SecurityCapability]:
        capabilities: set[SecurityCapability] = set()
        if self.requested_network_destinations:
            capabilities.add(SecurityCapability.network)
        if self.requested_write_paths:
            capabilities.add(SecurityCapability.filesystem_write)
        if self.requested_package_refs:
            capabilities.add(SecurityCapability.package_install)
        if self.requested_secret_refs:
            capabilities.add(SecurityCapability.secret_access)
        if self.shell_requested:
            capabilities.add(SecurityCapability.shell)
        if self.arbitrary_code_requested:
            capabilities.add(SecurityCapability.arbitrary_code)
        if self.artifact_egress_classes:
            capabilities.add(SecurityCapability.artifact_egress)
        return capabilities

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GovernanceApproval(BaseModel):
    approval_id: str = Field(min_length=2, max_length=500)
    security_request_ref: str = Field(min_length=2, max_length=500)
    approved_capabilities: list[SecurityCapability] = Field(default_factory=list)
    approver_ref: str = Field(min_length=2, max_length=500)
    status: ApprovalStatus = ApprovalStatus.active
    approved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_approval(self):
        if not self.approved_capabilities:
            raise ValueError("governance approval requires capabilities")
        if len(self.approved_capabilities) != len(set(self.approved_capabilities)):
            raise ValueError("approved capabilities must be unique")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("approved_at", None)
        return canonical_sha256(payload)


class RuntimeSecurityViolation(BaseModel):
    violation_id: str = Field(min_length=2, max_length=500)
    code: str = Field(min_length=1, max_length=300)
    message: str = Field(min_length=1, max_length=5000)
    capability: SecurityCapability | None = None
    requested_value: Any | None = None
    policy_value: Any | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RuntimeSecurityDecision(BaseModel):
    security_decision_id: str = Field(min_length=2, max_length=500)
    security_policy_ref: str = Field(min_length=2, max_length=500)
    security_policy_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    security_request_ref: str = Field(min_length=2, max_length=500)
    security_request_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    decision: SecurityDecision
    violations: list[RuntimeSecurityViolation] = Field(default_factory=list)
    required_approval_capabilities: list[SecurityCapability] = Field(default_factory=list)
    approval_ref: str | None = Field(default=None, max_length=500)
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_decision(self):
        if self.decision == SecurityDecision.allow and self.violations:
            raise ValueError("allow decision cannot contain violations")
        if self.decision == SecurityDecision.deny and not self.violations:
            raise ValueError("deny decision requires violations")
        if self.decision == SecurityDecision.requires_approval and not self.required_approval_capabilities:
            raise ValueError("requires-approval decision requires capabilities")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("decided_at", None)
        return canonical_sha256(payload)


class IsolationAttestation(BaseModel):
    attestation_id: str = Field(min_length=2, max_length=500)
    security_policy_ref: str = Field(min_length=2, max_length=500)
    security_policy_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    security_request_ref: str = Field(min_length=2, max_length=500)
    security_request_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    security_decision_ref: str = Field(min_length=2, max_length=500)
    execution_host_ref: str = Field(min_length=2, max_length=500)
    computational_job_ref: str = Field(min_length=2, max_length=500)
    mechanism: IsolationMechanism
    enforcement_checks: dict[str, bool] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    status: AttestationStatus = AttestationStatus.not_run
    attested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_attestation(self):
        if self.status == AttestationStatus.passed:
            if not self.enforcement_checks:
                raise ValueError("passed isolation attestation requires enforcement checks")
            if not all(self.enforcement_checks.values()):
                raise ValueError("passed isolation attestation cannot contain failed checks")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("attested_at", None)
        return canonical_sha256(payload)


class RuntimeSecurityEvent(BaseModel):
    security_event_id: str = Field(min_length=2, max_length=500)
    severity: SecurityEventSeverity
    event_type: str = Field(min_length=1, max_length=300)
    security_policy_ref: str = Field(min_length=2, max_length=500)
    security_request_ref: str = Field(min_length=2, max_length=500)
    computational_job_ref: str | None = Field(default=None, max_length=500)
    runtime_ref: str | None = Field(default=None, max_length=500)
    details: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("occurred_at", None)
        return canonical_sha256(payload)


class RuntimeGovernanceRecord(BaseModel):
    governance_record_id: str = Field(min_length=2, max_length=500)
    policy: RuntimeSecurityPolicy
    request: RuntimeSecurityRequest
    decision: RuntimeSecurityDecision
    approval: GovernanceApproval | None = None
    attestation: IsolationAttestation | None = None
    events: list[RuntimeSecurityEvent] = Field(default_factory=list)
    reproduction_package_ref: str | None = Field(default=None, max_length=1000)
    workflow_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        if self.decision.security_policy_ref != self.policy.security_policy_id:
            raise ValueError("decision references wrong security policy")
        if self.decision.security_policy_fingerprint_sha256 != self.policy.fingerprint():
            raise ValueError("decision policy fingerprint mismatch")
        if self.decision.security_request_ref != self.request.security_request_id:
            raise ValueError("decision references wrong security request")
        if self.decision.security_request_fingerprint_sha256 != self.request.fingerprint():
            raise ValueError("decision request fingerprint mismatch")

        if self.approval is not None:
            if self.approval.security_request_ref != self.request.security_request_id:
                raise ValueError("approval references wrong security request")
            if self.decision.approval_ref != self.approval.approval_id:
                raise ValueError("decision approval_ref mismatch")

        if self.attestation is not None:
            if self.attestation.security_policy_ref != self.policy.security_policy_id:
                raise ValueError("attestation references wrong policy")
            if self.attestation.security_request_ref != self.request.security_request_id:
                raise ValueError("attestation references wrong request")
            if self.attestation.security_decision_ref != self.decision.security_decision_id:
                raise ValueError("attestation references wrong decision")
            if self.attestation.security_policy_fingerprint_sha256 != self.policy.fingerprint():
                raise ValueError("attestation policy fingerprint mismatch")
            if self.attestation.security_request_fingerprint_sha256 != self.request.fingerprint():
                raise ValueError("attestation request fingerprint mismatch")

        event_ids = [item.security_event_id for item in self.events]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("runtime security event ids must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "governance_record_id": self.governance_record_id,
            "policy_fingerprint_sha256": self.policy.fingerprint(),
            "request_fingerprint_sha256": self.request.fingerprint(),
            "decision_fingerprint_sha256": self.decision.fingerprint(),
            "approval_fingerprint_sha256": self.approval.fingerprint() if self.approval else None,
            "attestation_fingerprint_sha256": self.attestation.fingerprint() if self.attestation else None,
            "event_fingerprints": sorted(item.fingerprint() for item in self.events),
            "reproduction_package_ref": self.reproduction_package_ref,
            "workflow_ref": self.workflow_ref,
            "metadata": self.metadata,
        })


class RuntimeSecurityGovernanceBundle(BaseModel):
    bundle_id: str = Field(min_length=2, max_length=500)
    records: list[RuntimeGovernanceRecord] = Field(default_factory=list)
    source_object_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        if not self.records:
            raise ValueError("security governance bundle requires records")
        ids = [item.governance_record_id for item in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("governance record ids must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "bundle_id": self.bundle_id,
            "record_fingerprints": sorted(item.fingerprint() for item in self.records),
            "source_object_refs": sorted(self.source_object_refs),
            "metadata": self.metadata,
        })


def _prefix_allowed(path: str, allowed_prefixes: list[str]) -> bool:
    return any(path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in allowed_prefixes)


def evaluate_security_request(
    *,
    policy: RuntimeSecurityPolicy,
    request: RuntimeSecurityRequest,
    approval: GovernanceApproval | None = None,
    decision_id: str | None = None,
) -> RuntimeSecurityDecision:
    violations: list[RuntimeSecurityViolation] = []

    def violation(code: str, message: str, capability: SecurityCapability | None = None, requested: Any = None, policy_value: Any = None):
        violations.append(
            RuntimeSecurityViolation(
                violation_id=f"violation:{request.security_request_id}:{code}",
                code=code,
                message=message,
                capability=capability,
                requested_value=requested,
                policy_value=policy_value,
            )
        )

    if request.runtime_ref not in policy.allowed_runtime_refs:
        violation("runtime-not-allowed", "runtime is not allowed by policy", requested=request.runtime_ref)

    if request.runtime_adapter_ref not in policy.allowed_adapter_refs:
        violation("adapter-not-allowed", "runtime adapter is not allowed by policy", requested=request.runtime_adapter_ref)

    allowed_ops = policy.allowed_operations.get(request.runtime_ref, [])
    if request.operation not in allowed_ops:
        violation(
            "operation-not-allowed",
            "runtime operation is not allowed by policy",
            requested=request.operation,
            policy_value=allowed_ops,
        )

    profile = policy.isolation_profile

    if request.requested_network_destinations:
        if profile.network_mode == NetworkAccessMode.none:
            violation(
                "network-denied",
                "network access is disabled",
                SecurityCapability.network,
                request.requested_network_destinations,
                profile.network_mode.value,
            )
        elif profile.network_mode == NetworkAccessMode.allowlist:
            denied = sorted(
                set(request.requested_network_destinations)
                - set(policy.allowed_network_destinations)
            )
            if denied:
                violation(
                    "network-destination-not-allowed",
                    "one or more network destinations are outside the allowlist",
                    SecurityCapability.network,
                    denied,
                    policy.allowed_network_destinations,
                )

    if request.requested_write_paths:
        if profile.filesystem_mode == FilesystemAccessMode.read_only:
            violation(
                "filesystem-write-denied",
                "filesystem is read-only",
                SecurityCapability.filesystem_write,
                request.requested_write_paths,
                profile.filesystem_mode.value,
            )
        elif profile.filesystem_mode in {
            FilesystemAccessMode.workspace_only,
            FilesystemAccessMode.allowlist,
        }:
            denied = [
                path for path in request.requested_write_paths
                if not _prefix_allowed(path, policy.allowed_filesystem_prefixes)
            ]
            if denied:
                violation(
                    "filesystem-path-not-allowed",
                    "one or more write paths are outside allowed prefixes",
                    SecurityCapability.filesystem_write,
                    denied,
                    policy.allowed_filesystem_prefixes,
                )

    if request.requested_package_refs:
        if profile.package_install_mode == PackageInstallMode.denied:
            violation(
                "package-install-denied",
                "package installation is disabled",
                SecurityCapability.package_install,
                request.requested_package_refs,
                profile.package_install_mode.value,
            )
        elif profile.package_install_mode in {
            PackageInstallMode.lockfile_only,
            PackageInstallMode.allowlist,
        }:
            denied = sorted(set(request.requested_package_refs) - set(policy.allowed_package_refs))
            if denied:
                violation(
                    "package-not-allowed",
                    "one or more requested packages are not policy-approved",
                    SecurityCapability.package_install,
                    denied,
                    policy.allowed_package_refs,
                )

    denied_secrets = sorted(set(request.requested_secret_refs) - set(policy.allowed_secret_refs))
    if denied_secrets:
        violation(
            "secret-not-allowed",
            "one or more secret references are not allowed",
            SecurityCapability.secret_access,
            denied_secrets,
            policy.allowed_secret_refs,
        )

    if request.shell_requested and not profile.shell_allowed:
        violation(
            "shell-denied",
            "shell access is disabled",
            SecurityCapability.shell,
            True,
            False,
        )

    if request.arbitrary_code_requested and not profile.arbitrary_code_allowed:
        violation(
            "arbitrary-code-denied",
            "arbitrary code execution is disabled",
            SecurityCapability.arbitrary_code,
            True,
            False,
        )

    if request.artifact_egress_classes:
        if not profile.outbound_artifact_egress_allowed:
            violation(
                "artifact-egress-denied",
                "artifact egress is disabled",
                SecurityCapability.artifact_egress,
                request.artifact_egress_classes,
                False,
            )
        else:
            denied = sorted(
                set(request.artifact_egress_classes)
                - set(policy.allowed_artifact_egress_classes)
            )
            if denied:
                violation(
                    "artifact-egress-class-not-allowed",
                    "one or more artifact egress classes are not allowed",
                    SecurityCapability.artifact_egress,
                    denied,
                    policy.allowed_artifact_egress_classes,
                )

    if violations:
        decision = SecurityDecision.deny
        required_approvals: list[SecurityCapability] = []
        approval_ref = None
    else:
        requested_caps = request.requested_capabilities()
        approval_caps = sorted(
            requested_caps & set(policy.approval_required_capabilities),
            key=lambda item: item.value,
        )

        active_approval_caps: set[SecurityCapability] = set()
        approval_ref = None
        if approval is not None:
            if approval.security_request_ref != request.security_request_id:
                raise ValueError("governance approval references different request")
            if approval.status == ApprovalStatus.active:
                active_approval_caps = set(approval.approved_capabilities)
                approval_ref = approval.approval_id

        missing_approvals = [
            item for item in approval_caps
            if item not in active_approval_caps
        ]

        if missing_approvals:
            decision = SecurityDecision.requires_approval
            required_approvals = missing_approvals
            approval_ref = None
        else:
            decision = SecurityDecision.allow
            required_approvals = []
            if not approval_caps:
                approval_ref = None

    return RuntimeSecurityDecision(
        security_decision_id=decision_id or f"security-decision:{request.security_request_id}",
        security_policy_ref=policy.security_policy_id,
        security_policy_fingerprint_sha256=policy.fingerprint(),
        security_request_ref=request.security_request_id,
        security_request_fingerprint_sha256=request.fingerprint(),
        decision=decision,
        violations=violations,
        required_approval_capabilities=required_approvals,
        approval_ref=approval_ref,
        metadata={
            "policy_state": policy.state.value,
            "default_decision": policy.default_decision.value,
            "evaluation_contract": CONTRACT_VERSION,
        },
    )


def to_scientific_security_artifact(
    bundle: RuntimeSecurityGovernanceBundle,
) -> dict[str, Any]:
    return {
        "artifact_id": f"scientific-artifact:{bundle.bundle_id}",
        "artifact_kind": "package",
        "uri": f"core-ref://{bundle.bundle_id}",
        "content_sha256": bundle.fingerprint(),
        "media_type": "application/vnd.sustainable-catalyst.runtime-security-governance+json",
        "source_contract": CONTRACT_VERSION,
        "source_object_ref": bundle.bundle_id,
        "metadata": {
            "governance_record_count": len(bundle.records),
            "decision_counts": {
                value.value: sum(1 for record in bundle.records if record.decision.decision == value)
                for value in SecurityDecision
            },
        },
    }


def reference_runtime_security_governance_bundle() -> RuntimeSecurityGovernanceBundle:
    isolation = RuntimeIsolationProfile(
        isolation_profile_id="isolation-profile:research-runtime-standard:v1",
        mechanism=IsolationMechanism.container,
        network_mode=NetworkAccessMode.none,
        filesystem_mode=FilesystemAccessMode.workspace_only,
        package_install_mode=PackageInstallMode.denied,
        process_namespace_isolated=True,
        user_namespace_isolated=True,
        privilege_escalation_allowed=False,
        host_filesystem_mounted=False,
        shell_allowed=False,
        arbitrary_code_allowed=False,
        outbound_artifact_egress_allowed=True,
        resource_budget_ref="resource-budget:research-runtime-standard:v1",
        syscall_policy_ref="syscall-policy:research-runtime-standard:v1",
        mandatory_access_control_ref="mac-policy:research-runtime-standard:v1",
    )

    policy = RuntimeSecurityPolicy(
        security_policy_id="runtime-security-policy:research-standard:v1",
        policy_version="1.0.0",
        name="Research Runtime Standard Policy",
        isolation_profile=isolation,
        allowed_runtime_refs=[
            REFERENCE_R_RUNTIME,
            REFERENCE_JULIA_RUNTIME,
        ],
        allowed_adapter_refs=[
            REFERENCE_R_ADAPTER,
            REFERENCE_JULIA_ADAPTER,
        ],
        allowed_operations={
            REFERENCE_R_RUNTIME: [
                "descriptive_summary",
                "quantile_summary",
                "correlation_matrix",
                "linear_regression",
                "t_test",
                "one_way_anova",
            ],
            REFERENCE_JULIA_RUNTIME: [
                "identity",
                "sum",
                "mean",
                "matrix_multiply",
            ],
        },
        allowed_filesystem_prefixes=[
            "/workspace",
            "/tmp/sc-runtime",
        ],
        allowed_secret_refs=["secret-ref:sc-research-api-key"],
        allowed_artifact_egress_classes=["research-artifact"],
        approval_required_capabilities=[
            SecurityCapability.secret_access,
        ],
        execution_policy_ref="execution-policy:research-standard:v1",
        provenance={
            "source_release": CORE_RELEASE,
            "policy_owner": "platform-governance",
        },
    )

    safe_request = RuntimeSecurityRequest(
        security_request_id="security-request:r-regression:reference",
        runtime_ref=REFERENCE_R_RUNTIME,
        runtime_adapter_ref=REFERENCE_R_ADAPTER,
        operation="linear_regression",
        computational_job_ref="job:reference-r-regression",
        environment_ref="environment-package:reference-r-julia:v1",
        requested_read_paths=["/workspace/input/reference-regression.json"],
        requested_write_paths=["/workspace/output/reference-regression.json"],
        artifact_egress_classes=["research-artifact"],
    )
    safe_decision = evaluate_security_request(
        policy=policy,
        request=safe_request,
        decision_id="security-decision:r-regression:reference",
    )
    safe_attestation = IsolationAttestation(
        attestation_id="isolation-attestation:r-regression:reference",
        security_policy_ref=policy.security_policy_id,
        security_policy_fingerprint_sha256=policy.fingerprint(),
        security_request_ref=safe_request.security_request_id,
        security_request_fingerprint_sha256=safe_request.fingerprint(),
        security_decision_ref=safe_decision.security_decision_id,
        execution_host_ref="workspace-execution-host:reference",
        computational_job_ref=safe_request.computational_job_ref,
        mechanism=IsolationMechanism.container,
        enforcement_checks={
            "network-disabled": True,
            "filesystem-scoped": True,
            "package-install-disabled": True,
            "privilege-escalation-disabled": True,
            "shell-disabled": True,
            "arbitrary-code-disabled": True,
        },
        evidence_refs=[
            "security-evidence:runtime-container-policy:r-regression",
            "security-evidence:filesystem-scope:r-regression",
        ],
        status=AttestationStatus.passed,
    )
    safe_record = RuntimeGovernanceRecord(
        governance_record_id="governance-record:r-regression:reference",
        policy=policy,
        request=safe_request,
        decision=safe_decision,
        attestation=safe_attestation,
        events=[
            RuntimeSecurityEvent(
                security_event_id="security-event:r-regression:allowed",
                severity=SecurityEventSeverity.info,
                event_type="security-request-allowed",
                security_policy_ref=policy.security_policy_id,
                security_request_ref=safe_request.security_request_id,
                computational_job_ref=safe_request.computational_job_ref,
                runtime_ref=safe_request.runtime_ref,
                details={"decision": "allow"},
            )
        ],
        reproduction_package_ref="reproduction-package:reference-r-julia:v1",
        workflow_ref="cross-runtime-workflow:reference-r-julia:v1",
    )

    approval_request = RuntimeSecurityRequest(
        security_request_id="security-request:r-secret-access:reference",
        runtime_ref=REFERENCE_R_RUNTIME,
        runtime_adapter_ref=REFERENCE_R_ADAPTER,
        operation="linear_regression",
        computational_job_ref="job:reference-r-secret-regression",
        environment_ref="environment-package:reference-r-julia:v1",
        requested_read_paths=["/workspace/input/reference-regression.json"],
        requested_write_paths=["/workspace/output/reference-secret-regression.json"],
        requested_secret_refs=["secret-ref:sc-research-api-key"],
        artifact_egress_classes=["research-artifact"],
    )
    approval = GovernanceApproval(
        approval_id="governance-approval:r-secret-access:reference",
        security_request_ref=approval_request.security_request_id,
        approved_capabilities=[SecurityCapability.secret_access],
        approver_ref="governance-actor:reference-human-reviewer",
        status=ApprovalStatus.active,
        notes=["Reference proof of explicit human approval binding."],
    )
    approval_decision = evaluate_security_request(
        policy=policy,
        request=approval_request,
        approval=approval,
        decision_id="security-decision:r-secret-access:reference",
    )
    approval_record = RuntimeGovernanceRecord(
        governance_record_id="governance-record:r-secret-access:reference",
        policy=policy,
        request=approval_request,
        decision=approval_decision,
        approval=approval,
        events=[
            RuntimeSecurityEvent(
                security_event_id="security-event:r-secret-access:approved",
                severity=SecurityEventSeverity.info,
                event_type="governance-approval-applied",
                security_policy_ref=policy.security_policy_id,
                security_request_ref=approval_request.security_request_id,
                computational_job_ref=approval_request.computational_job_ref,
                runtime_ref=approval_request.runtime_ref,
                details={
                    "approval_ref": approval.approval_id,
                    "capability": "secret-access",
                },
            )
        ],
        reproduction_package_ref="reproduction-package:reference-r-julia:v1",
    )

    denied_request = RuntimeSecurityRequest(
        security_request_id="security-request:julia-arbitrary-code:reference",
        runtime_ref=REFERENCE_JULIA_RUNTIME,
        runtime_adapter_ref=REFERENCE_JULIA_ADAPTER,
        operation="matrix_multiply",
        computational_job_ref="job:reference-julia-arbitrary-code",
        environment_ref="environment-package:reference-r-julia:v1",
        arbitrary_code_requested=True,
    )
    denied_decision = evaluate_security_request(
        policy=policy,
        request=denied_request,
        decision_id="security-decision:julia-arbitrary-code:reference",
    )
    denied_record = RuntimeGovernanceRecord(
        governance_record_id="governance-record:julia-arbitrary-code:reference",
        policy=policy,
        request=denied_request,
        decision=denied_decision,
        events=[
            RuntimeSecurityEvent(
                security_event_id="security-event:julia-arbitrary-code:denied",
                severity=SecurityEventSeverity.high,
                event_type="security-request-denied",
                security_policy_ref=policy.security_policy_id,
                security_request_ref=denied_request.security_request_id,
                computational_job_ref=denied_request.computational_job_ref,
                runtime_ref=denied_request.runtime_ref,
                details={
                    "decision": "deny",
                    "violation_codes": [item.code for item in denied_decision.violations],
                },
            )
        ],
    )

    return RuntimeSecurityGovernanceBundle(
        bundle_id="runtime-security-governance-bundle:reference:v1",
        records=[safe_record, approval_record, denied_record],
        source_object_refs=[
            "reproduction-package:reference-r-julia:v1",
            "environment-package:reference-r-julia:v1",
            "cross-runtime-workflow-package:reference-r-julia:v1",
        ],
        metadata={
            "policy_enforcement_owner": "workspace-or-runtime-execution-host",
            "core_records_and_evaluates_policy": True,
        },
    )


def contract_document() -> dict[str, Any]:
    reference = reference_runtime_security_governance_bundle()
    decisions = [record.decision.decision.value for record in reference.records]

    pending_request = RuntimeSecurityRequest(
        security_request_id="security-request:secret-needs-approval:contract",
        runtime_ref=REFERENCE_R_RUNTIME,
        runtime_adapter_ref=REFERENCE_R_ADAPTER,
        operation="linear_regression",
        computational_job_ref="job:contract-secret-needs-approval",
        environment_ref="environment-package:reference-r-julia:v1",
        requested_secret_refs=["secret-ref:sc-research-api-key"],
    )
    pending = evaluate_security_request(
        policy=reference.records[0].policy,
        request=pending_request,
    )

    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            VERIFICATION_REPRODUCTION_CONTRACT,
            ENVIRONMENT_PACKAGE_CONTRACT,
            CROSS_RUNTIME_WORKFLOW_CONTRACT,
            RUNTIME_INTERCHANGE_CONTRACT,
            COMPUTATIONAL_JOB_CONTRACT,
            RUNTIME_ADAPTER_CONTRACT,
            RUNTIME_OBJECT_CONTRACT,
        ],
        "object_types": [
            "RuntimeIsolationProfile",
            "RuntimeSecurityPolicy",
            "RuntimeSecurityRequest",
            "GovernanceApproval",
            "RuntimeSecurityViolation",
            "RuntimeSecurityDecision",
            "IsolationAttestation",
            "RuntimeSecurityEvent",
            "RuntimeGovernanceRecord",
            "RuntimeSecurityGovernanceBundle",
        ],
        "capabilities": {
            "runtime_allowlists": True,
            "adapter_allowlists": True,
            "operation_allowlists": True,
            "network_governance": True,
            "filesystem_governance": True,
            "package_install_governance": True,
            "secret_reference_governance": True,
            "shell_and_arbitrary_code_governance": True,
            "artifact_egress_governance": True,
            "human_approval_bindings": True,
            "isolation_attestations": True,
            "security_event_provenance": True,
            "reproduction_security_binding": True,
            "scientific_registry_bridge": True,
        },
        "integration": {
            "verification_reproduction_engine": True,
            "reproducible_environment_packages": True,
            "cross_runtime_workflows": True,
            "computational_jobs": True,
            "runtime_adapters": True,
            "workspace_or_execution_host_enforces_isolation": True,
            "core_enforces_os_container_isolation": False,
        },
        "boundaries": {
            "core_launches_sandboxes": False,
            "core_applies_kernel_security_controls": False,
            "core_resolves_secret_values": False,
            "core_installs_packages": False,
            "core_grants_approval_without_approval_object": False,
            "core_certifies_isolation_without_attestation": False,
            "core_certifies_scientific_validity": False,
            "core_owns_policy_identity_evaluation_governance_and_attestation_contracts": True,
        },
        "reference": {
            "bundle_id": reference.bundle_id,
            "decisions": decisions,
            "pending_secret_request_decision": pending.decision.value,
            "pending_secret_required_capabilities": [
                item.value for item in pending.required_approval_capabilities
            ],
            "bundle_fingerprint_sha256": reference.fingerprint(),
        },
    }
