#!/usr/bin/env python3
from app.services.computational_job_runtime import (
    CONTRACT_VERSION,
    JobTransitionRequest,
    build_dispatch_envelope,
    contract_document,
    reference_julia_job,
    transition_job,
    validate_job,
)
from app.services.computational_runtime_objects import ExecutionState
from app.services.execution_environment_provenance import (
    julia_v030_reference_provenance,
)

doc = contract_document()
assert doc["release"] == "3.25.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["reference_runtime"]["provider_version"] == "0.3.0"
assert doc["reference_runtime"]["adapter_status"] == "registered"
assert doc["boundaries"]["core_is_execution_host"] is False

job = reference_julia_job()
assert len(job.fingerprint()) == 64

envelope = build_dispatch_envelope(job)
assert envelope.adapter_id == "adapter:catalyst-julia-runtime"
assert envelope.runtime_id == "catalyst-julia-runtime"
assert envelope.operation == "matrix_multiply"

env = julia_v030_reference_provenance()
report = validate_job(job, env)
assert report.ok is True
assert report.environment_verification is not None
assert report.environment_verification.ok is True

for target in (
    ExecutionState.queued,
    ExecutionState.preparing,
    ExecutionState.running,
    ExecutionState.completed,
):
    job = transition_job(job, JobTransitionRequest(target_state=target))

assert job.state == ExecutionState.completed
assert len(job.attempts) == 1
assert len(job.events) == 4

print("PASS - Platform Core v3.25.0 Unified Computational Job Runtime")
print(f"CONTRACT={CONTRACT_VERSION}")
print("REFERENCE_RUNTIME=catalyst-julia-runtime@0.3.0")
print("JOB_FINGERPRINTING=enabled")
print("ENVIRONMENT_REQUIREMENT_BINDING=enabled")
print("ATTEMPT_LINEAGE=enabled")
print("DISPATCH_ENVELOPE=enabled")
print("CORE_IS_EXECUTION_HOST=false")
