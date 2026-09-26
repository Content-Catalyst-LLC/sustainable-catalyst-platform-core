#!/usr/bin/env python3
from pathlib import Path
from app.server import (
    ADAPTER_ID, OPERATIONS, PROVIDER_VERSION, RUNTIME_ID,
    adapter_descriptor, build_hansl_script, dataset_hash, validate_columns,
)

columns = validate_columns({"y":[1,2,3], "x":[2,3,4]})
script = build_hansl_script(
    operation="ols",
    csv_path=Path("/tmp/sc-gretl/data.csv"),
    dependent_variable="y",
    predictors=["x"],
    include_constant=True,
    variables=[],
)
d = adapter_descriptor()
assert d["adapter_id"] == ADAPTER_ID
assert d["provider_id"] == RUNTIME_ID
assert d["provider_version"] == PROVIDER_VERSION
assert d["capabilities"] == OPERATIONS
assert len(dataset_hash(columns)) == 64
assert "ols y const x" in script
assert d["boundaries"]["arbitrary_hansl_source"] is False
assert d["boundaries"]["shell_execution"] is False

print("PASS - Sustainable Catalyst gretl/hansl Runtime v1.0.0 contract validation")
print(f"RUNTIME_ID={RUNTIME_ID}")
print(f"ADAPTER_ID={ADAPTER_ID}")
print(f"OPERATIONS={','.join(OPERATIONS)}")
