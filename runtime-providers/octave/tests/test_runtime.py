from pathlib import Path

import pytest
from pydantic import ValidationError

from app.server import (
    ADAPTER_ID, OCTAVE_VERSION, OPERATIONS, PROVIDER_VERSION, RUNTIME_ID,
    PrepareRequest, adapter_descriptor, operation_script, payload_hash,
    validate_operation_payload, validate_payload,
)


def test_identity():
    assert RUNTIME_ID == "sc-runtime-octave"
    assert ADAPTER_ID == "adapter:sc-runtime-octave"
    assert PROVIDER_VERSION == "1.0.0"
    assert OCTAVE_VERSION == "8.4.0"


def test_operations():
    assert OPERATIONS == [
        "matrix_multiply", "linear_solve", "eigenvalues",
        "svd", "fft", "polynomial_roots",
    ]


def test_validate_payload():
    assert validate_payload({"A": [[1.0, 2.0], [3.0, 4.0]]})["A"][0][0] == 1.0


def test_validate_payload_rejects_string():
    with pytest.raises(ValueError):
        validate_payload({"A": [["bad"]]})


def test_validate_payload_rejects_bool():
    with pytest.raises(ValueError):
        validate_payload({"x": [True]})


def test_payload_hash_stable():
    assert payload_hash({"x": [1,2,3]}) == payload_hash({"x": [1,2,3]})
    assert len(payload_hash({"x": [1,2,3]})) == 64


@pytest.mark.parametrize("operation,payload", [
    ("matrix_multiply", {"A": [[1]], "B": [[2]]}),
    ("linear_solve", {"A": [[2]], "b": [4]}),
    ("eigenvalues", {"A": [[2]]}),
    ("svd", {"A": [[2]]}),
    ("fft", {"x": [1,2,3]}),
    ("polynomial_roots", {"coefficients": [1,0,-1]}),
])
def test_operation_payloads(operation, payload):
    validate_operation_payload(operation, payload)


def test_missing_operation_field():
    with pytest.raises(ValueError):
        validate_operation_payload("linear_solve", {"A": [[1]]})


def test_prepare_valid():
    req = PrepareRequest(
        operation="linear_solve",
        values={"A": [[3,1],[1,2]], "b": [9,8]},
    )
    assert req.operation == "linear_solve"


def test_prepare_rejects_unknown_operation():
    with pytest.raises(ValidationError):
        PrepareRequest(operation="eval", values={"x":[1]})


def test_prepare_rejects_bad_values():
    with pytest.raises(ValidationError):
        PrepareRequest(operation="fft", values={"x":["bad"]})


@pytest.mark.parametrize("operation", OPERATIONS)
def test_operation_script_is_fixed(operation):
    script = operation_script(operation)
    assert "jsondecode" in script
    assert "jsonencode" in script
    assert "system(" not in script
    assert "eval(" not in script


def test_adapter_descriptor_identity():
    d = adapter_descriptor()
    assert d["adapter_id"] == ADAPTER_ID
    assert d["provider_id"] == RUNTIME_ID
    assert d["provider_version"] == PROVIDER_VERSION


def test_adapter_boundaries():
    b = adapter_descriptor()["boundaries"]
    assert b["arbitrary_octave_source"] is False
    assert b["shell_execution"] is False
    assert b["runtime_package_install"] is False
    assert b["caller_filesystem_paths"] is False
