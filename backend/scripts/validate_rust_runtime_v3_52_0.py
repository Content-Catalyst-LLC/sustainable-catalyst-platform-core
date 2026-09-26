#!/usr/bin/env python3
from app.services.rust_runtime import *
from app.services.scientific_result_registry import ScientificArtifactRef

doc=contract_document()
assert doc["release"]=="3.52.0"
assert doc["contract"]==CONTRACT_VERSION
assert doc["runtime_id"]==RUNTIME_ID
assert doc["adapter_id"]==ADAPTER_ID
assert doc["provider_version"]==PROVIDER_VERSION
assert doc["rustc_version"]==RUSTC_VERSION
assert doc["cargo_version"]==CARGO_VERSION
assert doc["edition"]=="2021"
assert doc["operations"]==RUST_OPERATIONS
assert doc["capabilities"]["safe_native_systems"] is True
assert doc["capabilities"]["unsafe_code_forbidden"] is True
assert doc["boundaries"]["core_executes_rust"] is False
assert doc["boundaries"]["arbitrary_rust_source"] is False
assert doc["boundaries"]["unsafe_rust_code"] is False
bundle=reference_runtime_bundle()
assert bundle.registration.runtime_id==RUNTIME_ID
assert bundle.registration.runtime_kind=="language"
assert bundle.registration.language=="rust"
assert bundle.registration.edition=="2021"
assert bundle.reference_request.operation=="prefix_sum"
assert len(bundle.fingerprint())==64
ScientificArtifactRef.model_validate(to_scientific_rust_artifact(bundle))
print("PASS - Platform Core v3.52.0 Rust Runtime")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"RUNTIME_ID={RUNTIME_ID}")
print(f"PROVIDER_VERSION={PROVIDER_VERSION}")
print(f"RUSTC_VERSION={RUSTC_VERSION}")
print(f"CARGO_VERSION={CARGO_VERSION}")
print("SAFE_NATIVE_SYSTEMS=enabled")
print("GRAPH_PROCESSING=enabled")
print("TEXT_ALGORITHMS=enabled")
print("DETERMINISTIC_HASHING=enabled")
print("UNSAFE_CODE=forbidden")
print("ARBITRARY_RUST_SOURCE=false")
print("CORE_EXECUTES_RUST=false")
