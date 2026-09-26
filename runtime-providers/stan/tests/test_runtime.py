from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.server import (
    ADAPTER_ID,
    CMDSTAN_VERSION,
    OPERATIONS,
    PROVIDER_VERSION,
    RUNTIME_ID,
    PrepareRequest,
    adapter_descriptor,
    build_command,
    source_hash,
    validate_data,
    validate_model_source,
    validate_options,
)


MODEL = """
data { int<lower=1> N; array[N] real y; }
parameters { real mu; }
model { mu ~ normal(0, 1); y ~ normal(mu, 1); }
"""


def test_identity():
    assert RUNTIME_ID == "sc-runtime-stan"
    assert ADAPTER_ID == "adapter:sc-runtime-stan"
    assert PROVIDER_VERSION == "1.0.0"
    assert CMDSTAN_VERSION


def test_operations():
    assert OPERATIONS == [
        "compile_model",
        "sample",
        "optimize",
        "variational",
        "diagnose",
    ]


def test_source_valid():
    assert validate_model_source(MODEL) == MODEL


def test_source_rejects_include():
    with pytest.raises(ValueError):
        validate_model_source('#include "evil.stan"\n' + MODEL)


def test_source_hash_stable():
    assert source_hash(MODEL) == source_hash(MODEL)
    assert len(source_hash(MODEL)) == 64


def test_data_requires_object():
    with pytest.raises(ValueError):
        validate_data([1, 2, 3])


def test_data_valid():
    assert validate_data({"N": 1, "y": [1.0]})["N"] == 1


def test_options_reject_unknown():
    with pytest.raises(ValueError):
        validate_options({"shell": True})


def test_options_adapt_delta():
    assert validate_options({"adapt_delta": 0.9})["adapt_delta"] == 0.9


def test_options_reject_bad_adapt_delta():
    with pytest.raises(ValueError):
        validate_options({"adapt_delta": 1.5})


def test_prepare_sample_valid():
    req = PrepareRequest(
        operation="sample",
        model_id="model:test",
        model_source=MODEL,
        data={"N": 1, "y": [1.0]},
        num_warmup=10,
        num_samples=20,
    )
    assert req.operation == "sample"


def test_prepare_compile_without_data_valid():
    req = PrepareRequest(
        operation="compile_model",
        model_id="model:test",
        model_source=MODEL,
    )
    assert req.data == {}


def test_prepare_non_compile_requires_data():
    with pytest.raises(ValidationError):
        PrepareRequest(
            operation="sample",
            model_id="model:test",
            model_source=MODEL,
        )


def test_prepare_rejects_unknown_operation():
    with pytest.raises(ValidationError):
        PrepareRequest(
            operation="shell",
            model_id="model:test",
            model_source=MODEL,
            data={"N": 1},
        )


def test_prepare_chains_limited_to_one():
    with pytest.raises(ValidationError):
        PrepareRequest(
            operation="sample",
            model_id="model:test",
            model_source=MODEL,
            data={"N": 1},
            chains=2,
        )


def test_build_sample_command():
    cmd = build_command(
        Path("/tmp/model"),
        "sample",
        Path("/tmp/data.json"),
        Path("/tmp/output.csv"),
        seed=123,
        num_warmup=10,
        num_samples=20,
        thin=1,
        refresh=0,
        options={"adapt_delta": 0.9},
    )
    joined = " ".join(cmd)
    assert "sample" in cmd
    assert "num_warmup=10" in cmd
    assert "num_samples=20" in cmd
    assert "seed=123" in joined
    assert "file=/tmp/data.json" in joined
    assert "file=/tmp/output.csv" in joined


def test_build_optimize_command():
    cmd = build_command(
        Path("/tmp/model"),
        "optimize",
        Path("/tmp/data.json"),
        Path("/tmp/output.csv"),
        seed=123,
        num_warmup=0,
        num_samples=1,
        thin=1,
        refresh=0,
        options={"algorithm": "lbfgs"},
    )
    assert "algorithm=lbfgs" in cmd


def test_build_variational_command():
    cmd = build_command(
        Path("/tmp/model"),
        "variational",
        Path("/tmp/data.json"),
        Path("/tmp/output.csv"),
        seed=123,
        num_warmup=0,
        num_samples=1,
        thin=1,
        refresh=0,
        options={"algorithm": "meanfield", "iter": 1000, "output_samples": 100},
    )
    assert "algorithm=meanfield" in cmd
    assert "iter=1000" in cmd
    assert "output_samples=100" in cmd


def test_adapter_descriptor_identity():
    d = adapter_descriptor()
    assert d["adapter_id"] == ADAPTER_ID
    assert d["provider_id"] == RUNTIME_ID
    assert d["provider_version"] == PROVIDER_VERSION


def test_adapter_descriptor_boundaries():
    b = adapter_descriptor()["boundaries"]
    assert b["arbitrary_shell"] is False
    assert b["runtime_package_install"] is False
    assert b["stan_include_directives"] is False
    assert b["multi_chain_parallel_v1"] is False
