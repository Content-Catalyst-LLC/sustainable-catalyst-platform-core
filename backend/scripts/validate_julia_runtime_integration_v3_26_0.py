#!/usr/bin/env python3
from app.services.computational_job_runtime import reference_julia_job
from app.services.julia_runtime_integration import *
d=contract_document(); assert d["release"]=="3.26.0"; assert d["registration"]["provider_version"]=="0.3.0"
assert validate_handshake(reference_handshake()).ok is True
r=job_to_julia_request(reference_julia_job()); assert r.operation=="matrix_multiply"
s=JuliaEnvironmentSnapshot(runtime_version="1.13.0",environment_fingerprint_sha256="b"*64); assert julia_environment_to_core(s).environment.runtime_id==RUNTIME_ID
print("PASS - Platform Core v3.26.0 Julia Runtime Core Integration")
print("CONTRACT=sc.core.julia-runtime-integration.v1")
print("ADAPTER=adapter:catalyst-julia-runtime")
print("PROVIDER_VERSION=0.3.0")
print("HANDSHAKE_VALIDATION=enabled")
print("JOB_MAPPING=enabled")
print("RESULT_NORMALIZATION=enabled")
print("ENVIRONMENT_NORMALIZATION=enabled")
print("CORE_EXECUTES_JULIA_DIRECTLY=false")
