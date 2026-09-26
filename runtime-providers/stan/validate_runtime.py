#!/usr/bin/env python3
from app.server import (
    ADAPTER_ID,
    OPERATIONS,
    PROVIDER_VERSION,
    RUNTIME_ID,
    adapter_descriptor,
    source_hash,
    validate_model_source,
)

model = """
data { int<lower=1> N; array[N] real y; }
parameters { real mu; }
model { mu ~ normal(0,1); y ~ normal(mu,1); }
"""

validate_model_source(model)
descriptor = adapter_descriptor()
assert descriptor["adapter_id"] == ADAPTER_ID
assert descriptor["provider_id"] == RUNTIME_ID
assert descriptor["provider_version"] == PROVIDER_VERSION
assert descriptor["capabilities"] == OPERATIONS
assert len(source_hash(model)) == 64
assert descriptor["boundaries"]["arbitrary_shell"] is False
assert descriptor["boundaries"]["stan_include_directives"] is False

print("PASS - Sustainable Catalyst Stan Runtime v1.0.0 contract validation")
print(f"RUNTIME_ID={RUNTIME_ID}")
print(f"ADAPTER_ID={ADAPTER_ID}")
print(f"OPERATIONS={','.join(OPERATIONS)}")
