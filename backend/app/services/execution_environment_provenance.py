from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import (
    DependencyKind,
    RuntimeDependency,
    RuntimeEnvironment,
    canonical_sha256,
)

CORE_RELEASE = "3.24.0"
CONTRACT_VERSION = "sc.core.execution-environment-provenance.v1"
ENVIRONMENT_CONTRACT_VERSION = "sc.environment.v1"
RUNTIME_OBJECT_CONTRACT_VERSION = "sc.core.computational-runtime-object.v1"
RUNTIME_ADAPTER_CONTRACT_VERSION = "sc.core.runtime-adapter.v1"


class DependencyRelation(str, Enum):
    requires = "requires"
    optional = "optional"
    build_requires = "build-requires"
    links = "links"
    contains = "contains"
    uses_service = "uses-service"
    provided_by = "provided-by"


class ReproducibilityStatus(str, Enum):
    locked = "locked"
    partially_locked = "partially-locked"
    observed = "observed"
    unresolved = "unresolved"


class DependencyNode(BaseModel):
    dependency_id: str = Field(min_length=2, max_length=240)
    dependency: RuntimeDependency
    direct: bool = False
    resolved: bool = True
    source_type: Literal[
        "package-manager",
        "system",
        "runtime",
        "container",
        "service",
        "declared",
        "observed",
    ] = "declared"
    license: str | None = Field(default=None, max_length=255)
    repository_ref: str | None = Field(default=None, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DependencyEdge(BaseModel):
    parent_dependency_id: str = Field(min_length=2, max_length=240)
    child_dependency_id: str = Field(min_length=2, max_length=240)
    relation: DependencyRelation = DependencyRelation.requires
    constraint: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def reject_self_edge(self):
        if self.parent_dependency_id == self.child_dependency_id:
            raise ValueError("dependency edge cannot reference the same dependency as parent and child")
        return self


class LockfileRecord(BaseModel):
    path: str = Field(min_length=1, max_length=2000)
    kind: Literal[
        "project",
        "manifest",
        "requirements",
        "lock",
        "container",
        "compiler",
        "system",
        "other",
    ] = "other"
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    package_manager: str | None = Field(default=None, max_length=120)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionEnvironmentProvenance(BaseModel):
    provenance_id: str = Field(min_length=2, max_length=240)
    environment: RuntimeEnvironment
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    capture_source: Literal[
        "runtime-provider",
        "workspace",
        "core",
        "container",
        "manual",
        "import",
    ] = "runtime-provider"
    reproducibility_status: ReproducibilityStatus = ReproducibilityStatus.observed
    lockfiles: list[LockfileRecord] = Field(default_factory=list)
    dependencies: list[DependencyNode] = Field(default_factory=list)
    dependency_edges: list[DependencyEdge] = Field(default_factory=list)
    interpreter_or_compiler: RuntimeDependency | None = None
    container_image_ref: str | None = Field(default=None, max_length=2000)
    container_image_digest: str | None = Field(
        default=None,
        pattern=r"^(?:sha256:)?[0-9a-f]{64}$",
    )
    os_release: dict[str, Any] = Field(default_factory=dict)
    hardware_profile: dict[str, Any] = Field(default_factory=dict)
    environment_variables_redacted: dict[str, str] = Field(default_factory=dict)
    runtime_flags: list[str] = Field(default_factory=list)
    parent_environment_ref: str | None = Field(default=None, max_length=240)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_dependency_graph(self):
        node_ids = [node.dependency_id for node in self.dependencies]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("dependency_id values must be unique")
        known = set(node_ids)
        for edge in self.dependency_edges:
            if edge.parent_dependency_id not in known:
                raise ValueError(f"unknown dependency edge parent: {edge.parent_dependency_id}")
            if edge.child_dependency_id not in known:
                raise ValueError(f"unknown dependency edge child: {edge.child_dependency_id}")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("captured_at", None)
        payload.pop("provenance_id", None)
        payload.get("metadata", {}).pop("observation_note", None)
        return canonical_sha256(payload)


class EnvironmentRequirement(BaseModel):
    runtime_id: str | None = Field(default=None, max_length=180)
    runtime_version: str | None = Field(default=None, max_length=100)
    expected_environment_fingerprint_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    required_dependencies: list[RuntimeDependency] = Field(default_factory=list)
    required_lockfile_hashes: list[str] = Field(default_factory=list)
    reproducibility_status: ReproducibilityStatus | None = None
    require_resolved_dependency_graph: bool = False


class RequirementMismatch(BaseModel):
    field: str
    expected: Any
    observed: Any
    reason: str


class RequirementVerification(BaseModel):
    ok: bool
    mismatches: list[RequirementMismatch] = Field(default_factory=list)
    environment_fingerprint_sha256: str


class EnvironmentDifference(BaseModel):
    category: Literal[
        "runtime",
        "dependency-added",
        "dependency-removed",
        "dependency-version",
        "dependency-hash",
        "lockfile",
        "platform",
        "hardware",
        "flags",
        "reproducibility",
    ]
    key: str
    left: Any = None
    right: Any = None


class EnvironmentComparison(BaseModel):
    exact_match: bool
    left_fingerprint_sha256: str
    right_fingerprint_sha256: str
    differences: list[EnvironmentDifference] = Field(default_factory=list)


def _dependency_map(record: ExecutionEnvironmentProvenance) -> dict[str, DependencyNode]:
    return {node.dependency_id: node for node in record.dependencies}


def compare_environments(
    left: ExecutionEnvironmentProvenance,
    right: ExecutionEnvironmentProvenance,
) -> EnvironmentComparison:
    differences: list[EnvironmentDifference] = []

    if left.environment.runtime_id != right.environment.runtime_id:
        differences.append(EnvironmentDifference(
            category="runtime",
            key="runtime_id",
            left=left.environment.runtime_id,
            right=right.environment.runtime_id,
        ))
    if left.environment.runtime_version != right.environment.runtime_version:
        differences.append(EnvironmentDifference(
            category="runtime",
            key="runtime_version",
            left=left.environment.runtime_version,
            right=right.environment.runtime_version,
        ))

    left_deps = _dependency_map(left)
    right_deps = _dependency_map(right)

    for dep_id in sorted(set(right_deps) - set(left_deps)):
        differences.append(EnvironmentDifference(
            category="dependency-added",
            key=dep_id,
            left=None,
            right=right_deps[dep_id].dependency.model_dump(mode="json", exclude_none=True),
        ))
    for dep_id in sorted(set(left_deps) - set(right_deps)):
        differences.append(EnvironmentDifference(
            category="dependency-removed",
            key=dep_id,
            left=left_deps[dep_id].dependency.model_dump(mode="json", exclude_none=True),
            right=None,
        ))
    for dep_id in sorted(set(left_deps).intersection(right_deps)):
        a = left_deps[dep_id].dependency
        b = right_deps[dep_id].dependency
        if a.version != b.version:
            differences.append(EnvironmentDifference(
                category="dependency-version",
                key=dep_id,
                left=a.version,
                right=b.version,
            ))
        if a.content_sha256 != b.content_sha256:
            differences.append(EnvironmentDifference(
                category="dependency-hash",
                key=dep_id,
                left=a.content_sha256,
                right=b.content_sha256,
            ))

    left_locks = {(item.path, item.kind): item.content_sha256 for item in left.lockfiles}
    right_locks = {(item.path, item.kind): item.content_sha256 for item in right.lockfiles}
    for key in sorted(set(left_locks).union(right_locks)):
        if left_locks.get(key) != right_locks.get(key):
            differences.append(EnvironmentDifference(
                category="lockfile",
                key=f"{key[1]}:{key[0]}",
                left=left_locks.get(key),
                right=right_locks.get(key),
            ))

    platform_fields = ("platform", "architecture", "os_name", "os_version")
    for field_name in platform_fields:
        a = getattr(left.environment, field_name)
        b = getattr(right.environment, field_name)
        if a != b:
            differences.append(EnvironmentDifference(
                category="platform",
                key=field_name,
                left=a,
                right=b,
            ))

    if left.hardware_profile != right.hardware_profile:
        differences.append(EnvironmentDifference(
            category="hardware",
            key="hardware_profile",
            left=left.hardware_profile,
            right=right.hardware_profile,
        ))

    if left.runtime_flags != right.runtime_flags:
        differences.append(EnvironmentDifference(
            category="flags",
            key="runtime_flags",
            left=left.runtime_flags,
            right=right.runtime_flags,
        ))

    if left.reproducibility_status != right.reproducibility_status:
        differences.append(EnvironmentDifference(
            category="reproducibility",
            key="reproducibility_status",
            left=left.reproducibility_status.value,
            right=right.reproducibility_status.value,
        ))

    return EnvironmentComparison(
        exact_match=not differences,
        left_fingerprint_sha256=left.fingerprint(),
        right_fingerprint_sha256=right.fingerprint(),
        differences=differences,
    )


def verify_requirement(
    record: ExecutionEnvironmentProvenance,
    requirement: EnvironmentRequirement,
) -> RequirementVerification:
    mismatches: list[RequirementMismatch] = []
    fingerprint = record.fingerprint()

    if requirement.runtime_id and record.environment.runtime_id != requirement.runtime_id:
        mismatches.append(RequirementMismatch(
            field="runtime_id",
            expected=requirement.runtime_id,
            observed=record.environment.runtime_id,
            reason="runtime identity mismatch",
        ))
    if requirement.runtime_version and record.environment.runtime_version != requirement.runtime_version:
        mismatches.append(RequirementMismatch(
            field="runtime_version",
            expected=requirement.runtime_version,
            observed=record.environment.runtime_version,
            reason="runtime version mismatch",
        ))
    if (
        requirement.expected_environment_fingerprint_sha256
        and fingerprint != requirement.expected_environment_fingerprint_sha256
    ):
        mismatches.append(RequirementMismatch(
            field="environment_fingerprint_sha256",
            expected=requirement.expected_environment_fingerprint_sha256,
            observed=fingerprint,
            reason="environment fingerprint mismatch",
        ))

    observed_deps = {
        (node.dependency.name, node.dependency.kind.value): node.dependency
        for node in record.dependencies
    }
    for required in requirement.required_dependencies:
        key = (required.name, required.kind.value)
        observed = observed_deps.get(key)
        if observed is None:
            mismatches.append(RequirementMismatch(
                field=f"dependency:{required.kind.value}:{required.name}",
                expected=required.model_dump(mode="json", exclude_none=True),
                observed=None,
                reason="required dependency is missing",
            ))
            continue
        if required.version and observed.version != required.version:
            mismatches.append(RequirementMismatch(
                field=f"dependency-version:{required.name}",
                expected=required.version,
                observed=observed.version,
                reason="dependency version mismatch",
            ))
        if required.content_sha256 and observed.content_sha256 != required.content_sha256:
            mismatches.append(RequirementMismatch(
                field=f"dependency-hash:{required.name}",
                expected=required.content_sha256,
                observed=observed.content_sha256,
                reason="dependency content hash mismatch",
            ))

    observed_lock_hashes = {item.content_sha256 for item in record.lockfiles}
    for expected_hash in requirement.required_lockfile_hashes:
        if expected_hash not in observed_lock_hashes:
            mismatches.append(RequirementMismatch(
                field="lockfile_hash",
                expected=expected_hash,
                observed=sorted(observed_lock_hashes),
                reason="required lockfile hash not present",
            ))

    if requirement.reproducibility_status and record.reproducibility_status != requirement.reproducibility_status:
        mismatches.append(RequirementMismatch(
            field="reproducibility_status",
            expected=requirement.reproducibility_status.value,
            observed=record.reproducibility_status.value,
            reason="reproducibility status mismatch",
        ))

    if requirement.require_resolved_dependency_graph:
        unresolved = [
            node.dependency_id for node in record.dependencies if not node.resolved
        ]
        if unresolved:
            mismatches.append(RequirementMismatch(
                field="dependency_graph",
                expected="all dependencies resolved",
                observed=unresolved,
                reason="unresolved dependencies remain",
            ))

    return RequirementVerification(
        ok=not mismatches,
        mismatches=mismatches,
        environment_fingerprint_sha256=fingerprint,
    )


def julia_v030_reference_provenance() -> ExecutionEnvironmentProvenance:
    env = RuntimeEnvironment(
        environment_id="catalyst-julia-runtime:production",
        runtime_id="catalyst-julia-runtime",
        schema_version=ENVIRONMENT_CONTRACT_VERSION,
        runtime_version="1.13.0",
        platform="linux",
        architecture="x86_64",
        os_name="ubuntu",
        os_version="24.04",
        metadata={
            "provider_version": "0.3.0",
            "adapter_contract": RUNTIME_ADAPTER_CONTRACT_VERSION,
            "adapter_status": "registered",
            "capture_note": "reference contract; live provider reports authoritative hashes",
        },
    )
    return ExecutionEnvironmentProvenance(
        provenance_id="envprov:catalyst-julia-runtime:v0.3.0",
        environment=env,
        capture_source="runtime-provider",
        reproducibility_status=ReproducibilityStatus.locked,
        interpreter_or_compiler=RuntimeDependency(
            name="julia",
            kind=DependencyKind.interpreter,
            version="1.13.0",
            source="catalyst-julia-runtime",
        ),
        provenance={
            "provider_version": "0.3.0",
            "adapter_id": "adapter:catalyst-julia-runtime",
            "environment_endpoint": "/v1/environment",
            "environment_fingerprint_endpoint": "/v1/environment/fingerprint",
        },
        metadata={
            "reference_runtime": True,
            "live_hashes_required_for_execution_reproduction": True,
        },
    )


def contract_document() -> dict[str, Any]:
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            RUNTIME_OBJECT_CONTRACT_VERSION,
            RUNTIME_ADAPTER_CONTRACT_VERSION,
            ENVIRONMENT_CONTRACT_VERSION,
        ],
        "object_types": [
            "ExecutionEnvironmentProvenance",
            "DependencyNode",
            "DependencyEdge",
            "LockfileRecord",
            "EnvironmentRequirement",
            "EnvironmentComparison",
            "RequirementVerification",
        ],
        "captures": [
            "runtime identity and exact version",
            "package and library dependencies",
            "dependency graph relationships",
            "project, manifest and lockfile hashes",
            "interpreter or compiler identity",
            "container image identity",
            "operating-system identity",
            "hardware profile",
            "runtime flags",
            "redacted environment-variable declarations",
            "reproducibility state",
            "parent environment lineage",
        ],
        "verification": {
            "stable_environment_fingerprint": True,
            "requirement_matching": True,
            "environment_comparison": True,
            "dependency_version_drift_detection": True,
            "dependency_hash_drift_detection": True,
            "lockfile_drift_detection": True,
        },
        "reference_runtime": {
            "runtime_id": "catalyst-julia-runtime",
            "provider_version": "0.3.0",
            "adapter_status": "registered",
            "adapter_contract": RUNTIME_ADAPTER_CONTRACT_VERSION,
            "environment_contract": ENVIRONMENT_CONTRACT_VERSION,
        },
        "boundaries": {
            "core_installs_dependencies": False,
            "core_mutates_runtime_environment": False,
            "core_executes_package_manager": False,
            "core_executes_runtime_directly": False,
            "core_certifies_scientific_validity": False,
        },
    }
