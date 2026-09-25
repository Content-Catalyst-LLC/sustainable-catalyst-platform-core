from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.computational_job_runtime import (
    CONTRACT_VERSION,
    ComputationalJob,
    JobProviderBinding,
    JobTransitionRequest,
    RetryPolicy,
    build_dispatch_envelope,
    contract_document,
    reference_julia_job,
    transition_job,
    validate_job,
)
from app.services.computational_runtime_objects import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionState,
)
from app.services.execution_environment_provenance import (
    julia_v030_reference_provenance,
)


def test_contract_declares_unified_job_runtime_and_core_boundaries():
    doc = contract_document()
    assert doc["release"] == "3.25.0"
    assert doc["contract"] == CONTRACT_VERSION
    assert doc["capabilities"]["explicit_provider_binding"] is True
    assert doc["boundaries"]["core_is_execution_host"] is False
    assert doc["boundaries"]["core_selects_provider_autonomously"] is False


def test_reference_julia_job_uses_registered_v030_adapter():
    job = reference_julia_job()
    assert job.provider_binding.adapter_id == "adapter:catalyst-julia-runtime"
    assert job.provider_binding.provider_version == "0.3.0"
    assert job.provider_binding.selection_mode == "reproduction-pinned"
    assert job.request.operation == "matrix_multiply"


def test_job_fingerprint_is_stable_across_mutable_lifecycle_fields():
    a = reference_julia_job()
    b = deepcopy(a)
    b.state = ExecutionState.queued
    b.events = []
    assert a.fingerprint() == b.fingerprint()
    assert len(a.fingerprint()) == 64


def test_dispatch_envelope_preserves_runtime_operation_and_provenance():
    job = reference_julia_job()
    envelope = build_dispatch_envelope(job)
    assert envelope.runtime_id == "catalyst-julia-runtime"
    assert envelope.adapter_id == "adapter:catalyst-julia-runtime"
    assert envelope.operation == "matrix_multiply"
    assert envelope.provenance["job_contract"] == CONTRACT_VERSION


def test_valid_lifecycle_declared_to_running():
    job = reference_julia_job()
    job = transition_job(job, JobTransitionRequest(target_state="queued"))
    assert job.state == ExecutionState.queued

    job = transition_job(
        job,
        JobTransitionRequest(
            target_state="preparing",
            environment_fingerprint_sha256="a" * 64,
        ),
    )
    assert job.state == ExecutionState.preparing
    assert len(job.attempts) == 1

    job = transition_job(
        job,
        JobTransitionRequest(
            target_state="running",
            external_execution_ref="julia-exec-1",
        ),
    )
    assert job.state == ExecutionState.running
    assert job.attempts[0].external_execution_ref == "julia-exec-1"
    assert len(job.events) == 3


def test_completed_job_is_terminal():
    job = reference_julia_job()
    for target in ["queued", "preparing", "running", "completed"]:
        job = transition_job(job, JobTransitionRequest(target_state=target))
    with pytest.raises(ValueError):
        transition_job(job, JobTransitionRequest(target_state="running"))


def test_invalid_declared_to_running_transition_rejected():
    with pytest.raises(ValueError):
        transition_job(
            reference_julia_job(),
            JobTransitionRequest(target_state="running"),
        )


def test_retry_policy_limits_new_attempts():
    job = reference_julia_job()
    job.retry_policy = RetryPolicy(max_attempts=1)
    job = transition_job(job, JobTransitionRequest(target_state="queued"))
    job = transition_job(job, JobTransitionRequest(target_state="preparing"))
    job = transition_job(job, JobTransitionRequest(target_state="running"))
    job = transition_job(job, JobTransitionRequest(target_state="failed"))
    assert job.state == ExecutionState.failed
    assert len(job.attempts) == 1


def test_environment_requirement_verifies_julia_reference_environment():
    job = reference_julia_job()
    env = julia_v030_reference_provenance()
    report = validate_job(job, env)
    assert report.ok is True
    assert report.environment_verification is not None
    assert report.environment_verification.ok is True


def test_missing_observed_environment_is_warning_not_error():
    report = validate_job(reference_julia_job())
    assert report.ok is True
    assert report.environment_verification is None
    assert report.diagnostics[0]["code"] == "environment-not-observed"


def test_job_rejects_runtime_binding_mismatch():
    request = ExecutionRequest(
        request_id="request:test",
        runtime_id="runtime-a",
        operation="sum",
    )
    with pytest.raises(ValidationError):
        ComputationalJob(
            job_id="job:test",
            request=request,
            provider_binding=JobProviderBinding(
                adapter_id="adapter:runtime-b",
                runtime_id="runtime-b",
            ),
        )


def test_job_result_binding_identity_contract():
    job = reference_julia_job()
    result = ExecutionResult(
        result_id="result:test",
        run_id="run:test",
        request_id=job.request.request_id,
        runtime_id=job.provider_binding.runtime_id,
        state="completed",
        scalar_result=10.0,
    )
    data = job.model_dump(mode="python")
    data["result"] = result.model_dump(mode="python")
    rebound = ComputationalJob.model_validate(data)
    assert rebound.result.scalar_result == 10.0


def test_job_result_rejects_wrong_request_identity():
    job = reference_julia_job()
    result = ExecutionResult(
        result_id="result:test",
        run_id="run:test",
        request_id="request:wrong",
        runtime_id=job.provider_binding.runtime_id,
        state="completed",
        scalar_result=10.0,
    )
    data = job.model_dump(mode="python")
    data["result"] = result.model_dump(mode="python")
    with pytest.raises(ValidationError):
        ComputationalJob.model_validate(data)
