#!/usr/bin/env python3
from app.server import (
    ADAPTER_ID, OPERATIONS, PROVIDER_VERSION, RUNTIME_ID,
    adapter_descriptor, operation_script, payload_hash, validate_payload,
)

validate_payload({"A": [[3.0,1.0],[1.0,2.0]], "b": [9.0,8.0]})
d = adapter_descriptor()
assert d["adapter_id"] == ADAPTER_ID
assert d["provider_id"] == RUNTIME_ID
assert d["provider_version"] == PROVIDER_VERSION
assert d["capabilities"] == OPERATIONS
assert len(payload_hash({"x":[1,2,3]})) == 64
assert "system(" not in operation_script("linear_solve")
assert d["boundaries"]["arbitrary_octave_source"] is False
assert d["boundaries"]["shell_execution"] is False

print("PASS - Sustainable Catalyst Octave Runtime v1.0.0 contract validation")
print(f"RUNTIME_ID={RUNTIME_ID}")
print(f"ADAPTER_ID={ADAPTER_ID}")
print(f"OPERATIONS={','.join(OPERATIONS)}")
