#!/usr/bin/env python3
from app.server import (
    ADAPTER_ID, GHC_PACKAGE_VERSION, GHC_VERSION, OPERATIONS,
    PROVIDER_VERSION, RUNTIME_ID, adapter_descriptor, haskell_source,
    validate_payload,
)

payload = validate_payload("rational_reduce", {"numerator":42,"denominator":56})
source = haskell_source("rational_reduce", payload)
d = adapter_descriptor()
assert d["adapter_id"] == ADAPTER_ID
assert d["provider_id"] == RUNTIME_ID
assert d["provider_version"] == PROVIDER_VERSION
assert d["native_runtime_version"] == GHC_VERSION
assert d["native_package_version"] == GHC_PACKAGE_VERSION
assert d["capabilities"] == OPERATIONS
assert "42 :: Integer) % (56 :: Integer" in source
assert d["boundaries"]["arbitrary_haskell_source"] is False
assert d["boundaries"]["shell_execution"] is False
print("PASS - Sustainable Catalyst Haskell Runtime v1.0.0 contract validation")
print(f"RUNTIME_ID={RUNTIME_ID}")
print(f"ADAPTER_ID={ADAPTER_ID}")
print(f"GHC_VERSION={GHC_VERSION}")
print(f"OPERATIONS={','.join(OPERATIONS)}")
