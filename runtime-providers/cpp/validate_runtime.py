#!/usr/bin/env python3
from app.server import *

assert RUNTIME_ID == "sc-runtime-cpp"
assert ADAPTER_ID == "adapter:sc-runtime-cpp"
assert PROVIDER_VERSION == "1.0.0"
assert set(OPERATIONS) == {
    "dot_product", "matrix_multiply", "linear_interpolation",
    "polynomial_evaluate", "fir_filter", "dijkstra_shortest_path",
}
d = adapter_descriptor()
assert d["language_profiles"] == ["c11", "cpp17"]
assert d["boundaries"]["arbitrary_c_cpp_source"] is False
assert d["boundaries"]["provider_managed_compilation"] is True
print("PASS - Sustainable Catalyst C/C++ Runtime v1.0.0 contract validation")
print("RUNTIME_ID=" + RUNTIME_ID)
print("ADAPTER_ID=" + ADAPTER_ID)
print("LANGUAGE_PROFILES=c11,cpp17")
