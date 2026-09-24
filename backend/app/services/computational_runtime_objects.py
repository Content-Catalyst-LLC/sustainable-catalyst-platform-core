from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

CONTRACT_VERSION = "sc.core.computational-runtime-object.v1"
CORE_RELEASE = "3.22.0"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]{1,179}$")


class RuntimeKind(str, Enum):
    language = "language"
    domain = "domain"
    framework = "framework"
    compiled = "compiled"
    execution_target = "execution-target"


class ExecutionState(str, Enum):
    declared = "declared"
    queued = "queued"
    preparing = "preparing"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ArtifactKind(str, Enum):
    scalar = "scalar"
    table = "table"
    array = "array"
    matrix = "matrix"
    figure = "figure"
    file = "file"
    model = "model"
    notebook = "notebook"
    report = "report"
    log = "log"
    dataset = "dataset"
    environment = "environment"
    other = "other"


class DependencyKind(str, Enum):
    package = "package"
    library = "library"
    system = "system"
    compiler = "compiler"
    interpreter = "interpreter"
    runtime = "runtime"
    container = "container"
    service = "service"


def _sha256(value: str | None, field_name: str) -> str | None:
    if value is not None and not _SHA256_RE.fullmatch(value.lower()):
        raise ValueError(f"{field_name} must be a lowercase 64-character SHA-256 hex digest")
    return value.lower() if value is not None else None


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_sha256(value: Any) -> str:
    payload = value.model_dump(mode="json", exclude_none=True) if isinstance(value, BaseModel) else value
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


class RuntimeCapability(BaseModel):
    capability_key: str = Field(min_length=1, max_length=180)
    category: str = Field(default="compute", min_length=1, max_length=120)
    operations: list[str] = Field(default_factory=list)
    input_types: list[str] = Field(default_factory=list)
    output_types: list[str] = Field(default_factory=list)
    deterministic: bool | None = None
    arbitrary_code_execution: bool = False
    shell_execution: bool = False
    package_installation: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuntimeDependency(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    kind: DependencyKind = DependencyKind.package
    version: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, max_length=1000)
    content_sha256: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_hash(self):
        self.content_sha256 = _sha256(self.content_sha256, "content_sha256")
        return self


class RuntimeEnvironment(BaseModel):
    environment_id: str = Field(min_length=2, max_length=180)
    runtime_id: str = Field(min_length=2, max_length=180)
    schema_version: str = Field(default="sc.environment.v1", min_length=1, max_length=100)
    runtime_version: str = Field(min_length=1, max_length=100)
    platform: str | None = Field(default=None, max_length=255)
    architecture: str | None = Field(default=None, max_length=100)
    os_name: str | None = Field(default=None, max_length=100)
    os_version: str | None = Field(default=None, max_length=100)
    project_sha256: str | None = None
    manifest_sha256: str | None = None
    environment_sha256: str | None = None
    host_sha256: str | None = None
    dependencies: list[RuntimeDependency] = Field(default_factory=list)
    environment_variables: dict[str, str] = Field(default_factory=dict)
    runtime_flags: list[str] = Field(default_factory=list)
    hardware: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_environment(self):
        if not _ID_RE.fullmatch(self.environment_id):
            raise ValueError("environment_id must be a stable lowercase identifier")
        if not _ID_RE.fullmatch(self.runtime_id):
            raise ValueError("runtime_id must be a stable lowercase identifier")
        for name in ("project_sha256", "manifest_sha256", "environment_sha256", "host_sha256"):
            setattr(self, name, _sha256(getattr(self, name), name))
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("environment_sha256", None)
        payload.pop("host_sha256", None)
        return canonical_sha256(payload)


class ResourceBudget(BaseModel):
    timeout_seconds: int | None = Field(default=None, ge=1, le=86400)
    cpu_cores: float | None = Field(default=None, gt=0)
    memory_bytes: int | None = Field(default=None, ge=1)
    disk_bytes: int | None = Field(default=None, ge=1)
    gpu_count: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionPolicy(BaseModel):
    network_access: Literal["none", "restricted", "allowed"] = "none"
    filesystem_access: Literal["none", "read-only", "workspace", "declared"] = "workspace"
    arbitrary_code_execution: bool = False
    shell_execution: bool = False
    package_installation: bool = False
    allowed_operations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuntimeArtifact(BaseModel):
    artifact_id: str = Field(min_length=2, max_length=180)
    kind: ArtifactKind
    media_type: str | None = Field(default=None, max_length=255)
    uri: str | None = Field(default=None, max_length=2000)
    content_sha256: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    schema_ref: str | None = Field(default=None, max_length=1000)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_artifact(self):
        if not _ID_RE.fullmatch(self.artifact_id):
            raise ValueError("artifact_id must be a stable lowercase identifier")
        self.content_sha256 = _sha256(self.content_sha256, "content_sha256")
        return self


class ExecutionRequest(BaseModel):
    request_id: str = Field(min_length=2, max_length=180)
    runtime_id: str = Field(min_length=2, max_length=180)
    environment_id: str | None = Field(default=None, max_length=180)
    operation: str | None = Field(default=None, max_length=255)
    source_ref: str | None = Field(default=None, max_length=2000)
    entrypoint: str | None = Field(default=None, max_length=1000)
    arguments: list[Any] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    input_artifact_refs: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    resource_budget: ResourceBudget = Field(default_factory=ResourceBudget)
    execution_policy: ExecutionPolicy = Field(default_factory=ExecutionPolicy)
    expected_environment_fingerprint_sha256: str | None = None
    random_seed: int | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request(self):
        if not _ID_RE.fullmatch(self.request_id):
            raise ValueError("request_id must be a stable lowercase identifier")
        if not _ID_RE.fullmatch(self.runtime_id):
            raise ValueError("runtime_id must be a stable lowercase identifier")
        if not any((self.operation, self.source_ref, self.entrypoint)):
            raise ValueError("an execution request must declare operation, source_ref, or entrypoint")
        self.expected_environment_fingerprint_sha256 = _sha256(
            self.expected_environment_fingerprint_sha256,
            "expected_environment_fingerprint_sha256",
        )
        return self


class ExecutionRun(BaseModel):
    run_id: str = Field(min_length=2, max_length=180)
    request_id: str = Field(min_length=2, max_length=180)
    runtime_id: str = Field(min_length=2, max_length=180)
    environment_id: str | None = Field(default=None, max_length=180)
    state: ExecutionState = ExecutionState.declared
    external_execution_ref: str | None = Field(default=None, max_length=2000)
    queued_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    elapsed_ms: float | None = Field(default=None, ge=0)
    stdout_artifact_ref: str | None = Field(default=None, max_length=180)
    stderr_artifact_ref: str | None = Field(default=None, max_length=180)
    diagnostics: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    result_id: str = Field(min_length=2, max_length=180)
    run_id: str = Field(min_length=2, max_length=180)
    request_id: str = Field(min_length=2, max_length=180)
    runtime_id: str = Field(min_length=2, max_length=180)
    state: ExecutionState
    environment_fingerprint_sha256: str | None = None
    scalar_result: Any | None = None
    structured_result: dict[str, Any] | list[Any] | None = None
    artifact_refs: list[str] = Field(default_factory=list)
    diagnostics: list[dict[str, Any]] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_result(self):
        self.environment_fingerprint_sha256 = _sha256(
            self.environment_fingerprint_sha256,
            "environment_fingerprint_sha256",
        )
        if self.state == ExecutionState.completed and self.completed_at is None:
            self.completed_at = datetime.now(timezone.utc)
        return self


class RuntimeDescriptor(BaseModel):
    runtime_id: str = Field(min_length=2, max_length=180)
    runtime_kind: RuntimeKind = RuntimeKind.language
    language: str | None = Field(default=None, max_length=100)
    implementation: str = Field(min_length=1, max_length=180)
    runtime_version: str = Field(min_length=1, max_length=100)
    provider_version: str | None = Field(default=None, max_length=100)
    service_name: str | None = Field(default=None, max_length=255)
    contract_versions: list[str] = Field(default_factory=lambda: [CONTRACT_VERSION])
    capabilities: list[RuntimeCapability] = Field(default_factory=list)
    environment_ref: str | None = Field(default=None, max_length=180)
    health_ref: str | None = Field(default=None, max_length=2000)
    execution_host: str | None = Field(default=None, max_length=180)
    status: Literal["active", "degraded", "offline", "contract-only", "retired"] = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_runtime(self):
        if not _ID_RE.fullmatch(self.runtime_id):
            raise ValueError("runtime_id must be a stable lowercase identifier")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


OBJECT_TYPES = {
    "runtime": RuntimeDescriptor,
    "environment": RuntimeEnvironment,
    "capability": RuntimeCapability,
    "dependency": RuntimeDependency,
    "execution_request": ExecutionRequest,
    "execution_run": ExecutionRun,
    "execution_result": ExecutionResult,
    "artifact": RuntimeArtifact,
}


def contract_document() -> dict[str, Any]:
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "object_types": list(OBJECT_TYPES),
        "core_owns": [
            "runtime identity",
            "capability declarations",
            "environment identity",
            "execution request contracts",
            "execution lifecycle state",
            "result envelopes",
            "artifact identity",
            "provenance and reproducibility bindings",
        ],
        "runtime_provider_owns": [
            "runtime-specific process lifecycle",
            "interpreter/compiler invocation",
            "package-manager behavior",
            "runtime-specific serialization",
            "runtime-specific diagnostics",
        ],
        "boundaries": {
            "core_executes_arbitrary_source": False,
            "core_installs_runtime_packages": False,
            "core_selects_scientific_method_autonomously": False,
            "core_certifies_scientific_validity": False,
            "core_determines_truth": False,
        },
        "reference_runtime": {
            "runtime_id": "catalyst-julia-runtime",
            "provider_version": "0.2.0",
            "environment_contract": "sc.environment.v1",
            "execution_contract": "sc.execution.v1",
            "core_adapter_target": CONTRACT_VERSION,
        },
    }


def validate_object(object_type: str, payload: dict[str, Any]) -> BaseModel:
    model = OBJECT_TYPES.get(object_type)
    if model is None:
        raise ValueError(f"unknown object_type: {object_type}")
    return model.model_validate(payload)
