import json

import pytest
from pydantic import ValidationError

from app.server import (
    ADAPTER_ID,
    GHC_PACKAGE_VERSION,
    GHC_VERSION,
    OPERATIONS,
    PROVIDER_VERSION,
    RUNTIME_ID,
    PrepareRequest,
    adapter_descriptor,
    haskell_source,
    validate_payload,
)


def test_identity():
    assert RUNTIME_ID == "sc-runtime-haskell"
    assert ADAPTER_ID == "adapter:sc-runtime-haskell"
    assert PROVIDER_VERSION == "1.0.0"
    assert GHC_VERSION == "9.4.7"
    assert GHC_PACKAGE_VERSION == "9.4.7-3"


def test_operations():
    assert OPERATIONS == [
        "gcd", "lcm", "rational_reduce", "factorial", "fibonacci",
        "binomial_coefficient", "integer_power", "graph_reachable",
    ]

@pytest.mark.parametrize("operation,payload", [
    ("gcd", {"a":84,"b":30}),
    ("lcm", {"a":21,"b":6}),
    ("rational_reduce", {"numerator":42,"denominator":56}),
    ("factorial", {"n":10}),
    ("fibonacci", {"n":20}),
    ("binomial_coefficient", {"n":10,"k":3}),
    ("integer_power", {"base":2,"exponent":64}),
    ("graph_reachable", {"source":1,"target":4,"edges":[[1,2],[2,3],[3,4]]}),
])
def test_validate_supported(operation, payload):
    assert validate_payload(operation, payload)


def test_reject_unknown_operation():
    with pytest.raises(ValueError):
        validate_payload("shell", {})


def test_reject_bool_as_integer():
    with pytest.raises(ValueError):
        validate_payload("gcd", {"a":True,"b":2})


def test_reject_zero_denominator():
    with pytest.raises(ValueError):
        validate_payload("rational_reduce", {"numerator":1,"denominator":0})


def test_reject_negative_factorial():
    with pytest.raises(ValueError):
        validate_payload("factorial", {"n":-1})


def test_reject_bad_binomial():
    with pytest.raises(ValueError):
        validate_payload("binomial_coefficient", {"n":4,"k":7})


def test_reject_negative_exponent():
    with pytest.raises(ValueError):
        validate_payload("integer_power", {"base":2,"exponent":-1})


def test_reject_bad_edge():
    with pytest.raises(ValueError):
        validate_payload("graph_reachable", {"source":1,"target":2,"edges":[[1]]})

@pytest.mark.parametrize("operation,payload,needle", [
    ("gcd", {"a":84,"b":30}, "gcd (84 :: Integer) (30 :: Integer)"),
    ("lcm", {"a":21,"b":6}, "lcm (21 :: Integer) (6 :: Integer)"),
    ("rational_reduce", {"numerator":42,"denominator":56}, "42 :: Integer) % (56 :: Integer"),
    ("factorial", {"n":10}, "factorial (10 :: Integer)"),
    ("fibonacci", {"n":20}, "fib (20 :: Integer)"),
    ("binomial_coefficient", {"n":10,"k":3}, "choose (10 :: Integer) (3 :: Integer)"),
    ("integer_power", {"base":2,"exponent":8}, "(2 :: Integer) ^ (8 :: Integer)"),
    ("graph_reachable", {"source":1,"target":3,"edges":[[1,2],[2,3]]}, "edges = [(1,2),(2,3)]"),
])
def test_generated_source(operation, payload, needle):
    src = haskell_source(operation, payload)
    assert needle in src
    assert "System.Process" not in src
    assert "System.IO" not in src


def test_generated_source_no_caller_code():
    src = haskell_source("gcd", {"a":84,"b":30})
    assert "readFile" not in src
    assert "writeFile" not in src
    assert "getArgs" not in src


def test_prepare_valid():
    req = PrepareRequest(operation="rational_reduce", payload={"numerator":42,"denominator":56})
    assert req.operation == "rational_reduce"


def test_prepare_rejects_invalid():
    with pytest.raises(ValidationError):
        PrepareRequest(operation="rational_reduce", payload={"numerator":42,"denominator":0})


def test_adapter_descriptor():
    d = adapter_descriptor()
    assert d["adapter_id"] == ADAPTER_ID
    assert d["provider_id"] == RUNTIME_ID
    assert d["language"] == "haskell"
    assert d["runtime_kind"] == "language"


def test_adapter_boundaries():
    b = adapter_descriptor()["boundaries"]
    assert b["arbitrary_haskell_source"] is False
    assert b["shell_execution"] is False
    assert b["runtime_package_install"] is False
    assert b["caller_filesystem_paths"] is False
