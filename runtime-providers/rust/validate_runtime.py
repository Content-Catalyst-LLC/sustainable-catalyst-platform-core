#!/usr/bin/env python3
from app.server import *

assert RUNTIME_ID == "sc-runtime-rust"
assert ADAPTER_ID == "adapter:sc-runtime-rust"
assert PROVIDER_VERSION == "1.0.0"
assert RUSTC_VERSION == "1.75.0"
assert CARGO_VERSION == "1.75.0"
assert OPERATIONS == ["prefix_sum","moving_average","connected_components","topological_sort","levenshtein_distance","fnv1a_64"]
for operation,payload in [
    ("prefix_sum",{"integers":[1,2,3]}),
    ("moving_average",{"values":[1,2,3],"window":2}),
    ("connected_components",{"adjacency_matrix":[[0,1],[1,0]]}),
    ("topological_sort",{"vertex_count":3,"edge_list":[[0,1],[1,2]]}),
    ("levenshtein_distance",{"text_a":"kitten","text_b":"sitting"}),
    ("fnv1a_64",{"text":"abc"}),
]:
    source=generated_source(operation,payload)
    assert source.startswith("#![forbid(unsafe_code)]")
    assert "SC_RESULT" in source
    assert "unsafe {" not in source

d=adapter_descriptor()
assert d["provider_id"]==RUNTIME_ID
assert d["boundaries"]["arbitrary_rust_source"] is False
assert d["boundaries"]["unsafe_rust_code"] is False
print("PASS - Sustainable Catalyst Rust Runtime v1.0.0 contract validation")
print(f"RUNTIME_ID={RUNTIME_ID}")
print(f"ADAPTER_ID={ADAPTER_ID}")
print(f"OPERATIONS={','.join(OPERATIONS)}")
print("UNSAFE_CODE=forbidden")
