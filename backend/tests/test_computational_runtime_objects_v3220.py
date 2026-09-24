import pytest
from pydantic import ValidationError

from app.services.computational_runtime_objects import (
    CONTRACT_VERSION,
    ExecutionRequest,
    ExecutionResult,
    ExecutionState,
    RuntimeCapability,
    RuntimeDependency,
    RuntimeDescriptor,
    RuntimeEnvironment,
    canonical_sha256,
    contract_document,
    validate_object,
)


def test_contract_boundary_and_reference_runtime():
    doc = contract_document()
    assert doc["release"] == "3.22.0"
    assert doc["contract"] == CONTRACT_VERSION
    assert doc["reference_runtime"]["provider_version"] == "0.2.0"
    assert doc["boundaries"]["core_executes_arbitrary_source"] is False
    assert "execution_result" in doc["object_types"]


def test_runtime_descriptor_is_deterministically_fingerprinted():
    runtime = RuntimeDescriptor(
        runtime_id="catalyst-julia-runtime",
        runtime_kind="language",
        language="julia",
        implementation="Julia",
        runtime_version="1.13.0",
        provider_version="0.2.0",
        service_name="catalyst-julia-runtime",
        execution_host="contabo-vps",
        capabilities=[
            RuntimeCapability(
                capability_key="allowlisted-operations",
                operations=["identity", "sum", "mean", "matrix_multiply"],
                input_types=["json"],
                output_types=["json"],
                deterministic=True,
            )
        ],
        metadata={"environment_contract": "sc.environment.v1"},
    )
    assert runtime.fingerprint() == runtime.fingerprint()
    assert len(runtime.fingerprint()) == 64


def test_environment_preserves_julia_v020_fingerprint_contract():
    digest = "a" * 64
    env = RuntimeEnvironment(
        environment_id="julia-prod-1",
        runtime_id="catalyst-julia-runtime",
        runtime_version="1.13.0",
        project_sha256=digest,
        manifest_sha256=digest,
        environment_sha256=digest,
        dependencies=[
            RuntimeDependency(name="HTTP", version="1.11.0"),
            RuntimeDependency(name="JSON3", version="1.14.3"),
        ],
    )
    assert env.environment_sha256 == digest
    assert len(env.fingerprint()) == 64


def test_execution_request_requires_invocation_intent():
    with pytest.raises(ValidationError):
        ExecutionRequest(
            request_id="request-1",
            runtime_id="catalyst-julia-runtime",
        )


def test_execution_request_accepts_environment_lock():
    digest = "b" * 64
    req = ExecutionRequest(
        request_id="request-2",
        runtime_id="catalyst-julia-runtime",
        operation="sum",
        inputs={"values": [1, 2, 3]},
        expected_environment_fingerprint_sha256=digest,
        execution_policy={
            "network_access": "none",
            "filesystem_access": "workspace",
            "arbitrary_code_execution": False,
            "shell_execution": False,
            "package_installation": False,
            "allowed_operations": ["sum"],
        },
    )
    assert req.expected_environment_fingerprint_sha256 == digest


def test_completed_result_gets_completion_time():
    result = ExecutionResult(
        result_id="result-1",
        run_id="run-1",
        request_id="request-2",
        runtime_id="catalyst-julia-runtime",
        state=ExecutionState.completed,
        scalar_result=6,
    )
    assert result.completed_at is not None


def test_unknown_object_type_is_rejected():
    with pytest.raises(ValueError):
        validate_object("mystery", {"id": "x"})


def test_canonical_hash_is_order_invariant():
    assert canonical_sha256({"b": 2, "a": 1}) == canonical_sha256({"a": 1, "b": 2})
