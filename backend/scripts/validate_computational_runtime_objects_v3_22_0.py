#!/usr/bin/env python3
from app.services.computational_runtime_objects import (
    CONTRACT_VERSION,
    ExecutionRequest,
    RuntimeDescriptor,
    RuntimeEnvironment,
    contract_document,
)

doc = contract_document()
assert doc["release"] == "3.22.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["reference_runtime"]["provider_version"] == "0.2.0"
assert doc["boundaries"]["core_executes_arbitrary_source"] is False

runtime = RuntimeDescriptor(
    runtime_id="catalyst-julia-runtime",
    language="julia",
    implementation="Julia",
    runtime_version="1.13.0",
    provider_version="0.2.0",
)
assert len(runtime.fingerprint()) == 64

env = RuntimeEnvironment(
    environment_id="julia-production",
    runtime_id="catalyst-julia-runtime",
    runtime_version="1.13.0",
    environment_sha256="a" * 64,
)
assert len(env.fingerprint()) == 64

request = ExecutionRequest(
    request_id="v322-validation-request",
    runtime_id="catalyst-julia-runtime",
    operation="sum",
    inputs={"values": [1, 2, 3]},
    expected_environment_fingerprint_sha256="a" * 64,
)
assert request.operation == "sum"

print("PASS - Platform Core v3.22.0 Computational Runtime Object Model")
print(f"CONTRACT={CONTRACT_VERSION}")
print("REFERENCE_RUNTIME=catalyst-julia-runtime@0.2.0")
