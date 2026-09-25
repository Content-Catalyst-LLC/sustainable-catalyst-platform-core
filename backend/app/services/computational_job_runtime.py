from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionState,
    RuntimeArtifact,
    canonical_sha256,
)
from .execution_environment_provenance import (
    EnvironmentRequirement,
    ExecutionEnvironmentProvenance,
    RequirementVerification,
    verify_requirement,
)

CORE_RELEASE = "3.25.0"
CONTRACT_VERSION = "sc.core.computational-job.v1"
RUNTIME_OBJECT_CONTRACT_VERSION = "sc.core.computational-runtime-object.v1"
RUNTIME_ADAPTER_CONTRACT_VERSION = "sc.core.runtime-adapter.v1"
ENVIRONMENT_PROVENANCE_CONTRACT_VERSION = "sc.core.execution-environment-provenance.v1"

TERMINAL_STATES = {
    ExecutionState.completed,
    ExecutionState.failed,
    ExecutionState.cancelled,
}

ALLOWED_TRANSITIONS: dict[ExecutionState, set[ExecutionState]] = {
    ExecutionState.declared: {ExecutionState.queued, ExecutionState.cancelled},
    ExecutionState.queued: {ExecutionState.preparing, ExecutionState.cancelled},
    ExecutionState.preparing: {
        ExecutionState.running,
        ExecutionState.failed,
        ExecutionState.cancelled,
    },
    ExecutionState.running: {
        ExecutionState.completed,
        ExecutionState.failed,
        ExecutionState.cancelled,
    },
    ExecutionState.completed: set(),
    ExecutionState.failed: set(),
    ExecutionState.cancelled: set(),
}


class JobPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class RetryPolicy(BaseModel):
    max_attempts: int = Field(default=1, ge=1, le=100)
    retry_on_states: list[ExecutionState] = Field(
        default_factory=lambda: [ExecutionState.failed]
    )
    backoff_seconds: float = Field(default=0.0, ge=0.0, le=86400.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class JobProviderBinding(BaseModel):
    adapter_id: str = Field(min_length=2, max_length=240)
    runtime_id: str = Field(min_length=2, max_length=180)
    provider_version: str | None = Field(default=None, max_length=100)
    capability_key: str | None = Field(default=None, max_length=180)
    operation: str | None = Field(default=None, max_length=180)
    execution_host: str | None = Field(default=None, max_length=240)
    transport: str | None = Field(default=None, max_length=120)
    selection_mode: Literal[
        "explicit",
        "user-selected",
        "workflow-selected",
        "policy-selected",
        "reproduction-pinned",
    ] = "explicit"
    selection_provenance: dict[str, Any] = Field(default_factory=dict)


class JobEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"event:{uuid4()}")
    event_type: Literal[
        "declared",
        "queued",
        "preparing",
        "started",
        "completed",
        "failed",
        "cancelled",
        "diagnostic",
        "artifact-bound",
        "result-bound",
    ]
    state: ExecutionState
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor_ref: str | None = Field(default=None, max_length=240)
    message: str | None = Field(default=None, max_length=4000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class JobAttempt(BaseModel):
    attempt_id: str = Field(default_factory=lambda: f"attempt:{uuid4()}")
    ordinal: int = Field(ge=1)
    state: ExecutionState = ExecutionState.declared
    adapter_id: str = Field(min_length=2, max_length=240)
    runtime_id: str = Field(min_length=2, max_length=180)
    environment_fingerprint_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    external_execution_ref: str | None = Field(default=None, max_length=500)
    queued_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    diagnostics: list[dict[str, Any]] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


class JobArtifactBinding(BaseModel):
    artifact: RuntimeArtifact
    role: Literal[
        "input",
        "output",
        "intermediate",
        "diagnostic",
        "log",
        "environment",
        "report",
    ] = "output"
    attempt_id: str | None = Field(default=None, max_length=240)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ComputationalJob(BaseModel):
    job_id: str = Field(min_length=2, max_length=240)
    state: ExecutionState = ExecutionState.declared
    priority: JobPriority = JobPriority.normal
    request: ExecutionRequest
    provider_binding: JobProviderBinding
    environment_requirement: EnvironmentRequirement | None = None
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    idempotency_key: str | None = Field(default=None, max_length=500)
    attempts: list[JobAttempt] = Field(default_factory=list)
    events: list[JobEvent] = Field(default_factory=list)
    result: ExecutionResult | None = None
    artifacts: list[JobArtifactBinding] = Field(default_factory=list)
    declared_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    submitted_by: str | None = Field(default=None, max_length=240)
    workflow_ref: str | None = Field(default=None, max_length=240)
    project_ref: str | None = Field(default=None, max_length=240)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_job_consistency(self):
        if self.request.runtime_id != self.provider_binding.runtime_id:
            raise ValueError(
                "request.runtime_id must match provider_binding.runtime_id"
            )
        ordinals = [attempt.ordinal for attempt in self.attempts]
        if len(ordinals) != len(set(ordinals)):
            raise ValueError("job attempt ordinals must be unique")
        if self.attempts and sorted(ordinals) != list(range(1, len(ordinals) + 1)):
            raise ValueError("job attempt ordinals must be contiguous starting at 1")
        if len(self.attempts) > self.retry_policy.max_attempts:
            raise ValueError("job attempts exceed retry_policy.max_attempts")
        if self.result is not None:
            if self.result.request_id != self.request.request_id:
                raise ValueError("result.request_id must match job request.request_id")
            if self.result.runtime_id != self.provider_binding.runtime_id:
                raise ValueError("result.runtime_id must match provider runtime_id")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        for key in (
            "state",
            "attempts",
            "events",
            "result",
            "artifacts",
            "declared_at",
            "updated_at",
        ):
            payload.pop(key, None)
        return canonical_sha256(payload)


class JobTransitionRequest(BaseModel):
    target_state: ExecutionState
    actor_ref: str | None = Field(default=None, max_length=240)
    message: str | None = Field(default=None, max_length=4000)
    external_execution_ref: str | None = Field(default=None, max_length=500)
    environment_fingerprint_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    diagnostics: list[dict[str, Any]] = Field(default_factory=list)


class JobDispatchEnvelope(BaseModel):
    job_id: str
    request_id: str
    adapter_id: str
    runtime_id: str
    provider_version: str | None = None
    execution_host: str | None = None
    transport: str | None = None
    operation: str | None = None
    source_ref: str | None = None
    entrypoint: str | None = None
    arguments: list[Any] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    parameters: dict[str, Any] = Field(default_factory=dict)
    expected_environment_fingerprint_sha256: str | None = None
    resource_budget: dict[str, Any] = Field(default_factory=dict)
    execution_policy: dict[str, Any] = Field(default_factory=dict)
    random_seed: int | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)


class JobValidationReport(BaseModel):
    ok: bool
    job_fingerprint_sha256: str
    environment_verification: RequirementVerification | None = None
    diagnostics: list[dict[str, Any]] = Field(default_factory=list)


def _event_type_for_state(state: ExecutionState) -> str:
    return {
        ExecutionState.declared: "declared",
        ExecutionState.queued: "queued",
        ExecutionState.preparing: "preparing",
        ExecutionState.running: "started",
        ExecutionState.completed: "completed",
        ExecutionState.failed: "failed",
        ExecutionState.cancelled: "cancelled",
    }[state]


def transition_job(
    job: ComputationalJob,
    request: JobTransitionRequest,
) -> ComputationalJob:
    current = job.state
    target = request.target_state

    if target not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(
            f"invalid job transition: {current.value} -> {target.value}"
        )

    data = job.model_dump(mode="python")
    now = datetime.now(timezone.utc)
    data["state"] = target
    data["updated_at"] = now

    attempts = list(data.get("attempts") or [])
    events = list(data.get("events") or [])

    if target == ExecutionState.preparing:
        next_ordinal = len(attempts) + 1
        if next_ordinal > job.retry_policy.max_attempts:
            raise ValueError("retry policy prevents another job attempt")
        attempts.append(
            JobAttempt(
                ordinal=next_ordinal,
                state=ExecutionState.preparing,
                adapter_id=job.provider_binding.adapter_id,
                runtime_id=job.provider_binding.runtime_id,
                environment_fingerprint_sha256=request.environment_fingerprint_sha256,
                external_execution_ref=request.external_execution_ref,
                queued_at=now,
                diagnostics=request.diagnostics,
                provenance={"job_id": job.job_id},
            ).model_dump(mode="python")
        )
    elif target == ExecutionState.running:
        if not attempts:
            raise ValueError("job must have a prepared attempt before running")
        attempts[-1]["state"] = ExecutionState.running
        attempts[-1]["started_at"] = now
        if request.external_execution_ref:
            attempts[-1]["external_execution_ref"] = request.external_execution_ref
        if request.environment_fingerprint_sha256:
            attempts[-1]["environment_fingerprint_sha256"] = (
                request.environment_fingerprint_sha256
            )
        attempts[-1]["diagnostics"] = request.diagnostics
    elif target in TERMINAL_STATES:
        if attempts:
            attempts[-1]["state"] = target
            attempts[-1]["completed_at"] = now
            attempts[-1]["diagnostics"] = request.diagnostics

    events.append(
        JobEvent(
            event_type=_event_type_for_state(target),
            state=target,
            occurred_at=now,
            actor_ref=request.actor_ref,
            message=request.message,
            metadata={
                "external_execution_ref": request.external_execution_ref,
                "environment_fingerprint_sha256":
                    request.environment_fingerprint_sha256,
            },
        ).model_dump(mode="python")
    )
    data["attempts"] = attempts
    data["events"] = events
    return ComputationalJob.model_validate(data)


def build_dispatch_envelope(job: ComputationalJob) -> JobDispatchEnvelope:
    request = job.request
    budget = request.resource_budget.model_dump(
        mode="json", exclude_none=True
    ) if request.resource_budget else {}
    policy = request.execution_policy.model_dump(
        mode="json", exclude_none=True
    ) if request.execution_policy else {}

    return JobDispatchEnvelope(
        job_id=job.job_id,
        request_id=request.request_id,
        adapter_id=job.provider_binding.adapter_id,
        runtime_id=job.provider_binding.runtime_id,
        provider_version=job.provider_binding.provider_version,
        execution_host=job.provider_binding.execution_host,
        transport=job.provider_binding.transport,
        operation=request.operation,
        source_ref=request.source_ref,
        entrypoint=request.entrypoint,
        arguments=request.arguments,
        inputs=request.inputs,
        parameters=request.parameters,
        expected_environment_fingerprint_sha256=(
            request.expected_environment_fingerprint_sha256
        ),
        resource_budget=budget,
        execution_policy=policy,
        random_seed=request.random_seed,
        provenance={
            **request.provenance,
            "job_id": job.job_id,
            "job_contract": CONTRACT_VERSION,
            "provider_selection_mode": job.provider_binding.selection_mode,
        },
    )


def validate_job(
    job: ComputationalJob,
    observed_environment: ExecutionEnvironmentProvenance | None = None,
) -> JobValidationReport:
    diagnostics: list[dict[str, Any]] = []
    verification = None

    if job.environment_requirement is not None:
        if observed_environment is None:
            diagnostics.append({
                "level": "warning",
                "code": "environment-not-observed",
                "message": (
                    "An environment requirement exists but no observed "
                    "environment was supplied for verification."
                ),
            })
        else:
            verification = verify_requirement(
                observed_environment,
                job.environment_requirement,
            )
            if not verification.ok:
                diagnostics.append({
                    "level": "error",
                    "code": "environment-requirement-mismatch",
                    "message": "Observed environment does not satisfy job requirement.",
                })

    return JobValidationReport(
        ok=not any(item.get("level") == "error" for item in diagnostics),
        job_fingerprint_sha256=job.fingerprint(),
        environment_verification=verification,
        diagnostics=diagnostics,
    )


def bind_result(
    job: ComputationalJob,
    result: ExecutionResult,
) -> ComputationalJob:
    data = job.model_dump(mode="python")
    data["result"] = result.model_dump(mode="python")
    data["updated_at"] = datetime.now(timezone.utc)
    return ComputationalJob.model_validate(data)


def reference_julia_job() -> ComputationalJob:
    request = ExecutionRequest(
        request_id="request:julia-v030-matrix-proof",
        runtime_id="catalyst-julia-runtime",
        operation="matrix_multiply",
        inputs={
            "a": [[1, 2], [3, 4]],
            "b": [[5, 6], [7, 8]],
        },
        parameters={},
        random_seed=325,
        provenance={
            "purpose": "Platform Core v3.25.0 unified computational job proof",
        },
    )
    binding = JobProviderBinding(
        adapter_id="adapter:catalyst-julia-runtime",
        runtime_id="catalyst-julia-runtime",
        provider_version="0.3.0",
        capability_key="governed-numeric-compute",
        operation="matrix_multiply",
        execution_host="contabo-vps",
        transport="http",
        selection_mode="reproduction-pinned",
        selection_provenance={
            "core_registry_release": "3.24.0",
            "adapter_status": "registered",
        },
    )
    return ComputationalJob(
        job_id="job:julia-v030-matrix-proof",
        request=request,
        provider_binding=binding,
        environment_requirement=EnvironmentRequirement(
            runtime_id="catalyst-julia-runtime",
            runtime_version="1.13.0",
            reproducibility_status="locked",
        ),
        retry_policy=RetryPolicy(max_attempts=1),
        submitted_by="platform-core-release-validation",
        provenance={
            "reference_job": True,
            "provider_release": "Catalyst Julia Runtime v0.3.0",
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
            ENVIRONMENT_PROVENANCE_CONTRACT_VERSION,
        ],
        "lifecycle": {
            state.value: sorted(item.value for item in targets)
            for state, targets in ALLOWED_TRANSITIONS.items()
        },
        "object_types": [
            "ComputationalJob",
            "JobProviderBinding",
            "JobAttempt",
            "JobEvent",
            "JobArtifactBinding",
            "RetryPolicy",
            "JobDispatchEnvelope",
            "JobValidationReport",
        ],
        "capabilities": {
            "stable_job_fingerprint": True,
            "explicit_provider_binding": True,
            "environment_requirement_binding": True,
            "attempt_lineage": True,
            "event_lineage": True,
            "result_binding": True,
            "artifact_binding": True,
            "dispatch_envelope": True,
            "idempotency_key": True,
            "retry_policy": True,
        },
        "reference_runtime": {
            "adapter_id": "adapter:catalyst-julia-runtime",
            "runtime_id": "catalyst-julia-runtime",
            "provider_version": "0.3.0",
            "adapter_status": "registered",
        },
        "boundaries": {
            "core_is_execution_host": False,
            "core_invokes_interpreter_directly": False,
            "core_selects_provider_autonomously": False,
            "core_installs_dependencies": False,
            "workspace_or_runtime_provider_executes_job": True,
            "core_owns_job_semantics_and_lineage": True,
        },
    }
