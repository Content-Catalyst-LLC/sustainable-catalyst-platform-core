import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.server import (
    ADAPTER_ID,
    GRETL_PACKAGE_VERSION,
    GRETL_VERSION,
    OPERATIONS,
    PROVIDER_VERSION,
    RUNTIME_ID,
    PrepareRequest,
    adapter_descriptor,
    build_hansl_script,
    dataset_hash,
    parse_regression_coefficients,
    validate_columns,
    validate_identifier,
    validate_specification,
)


def test_identity():
    assert RUNTIME_ID == "sc-runtime-gretl"
    assert ADAPTER_ID == "adapter:sc-runtime-gretl"
    assert PROVIDER_VERSION == "1.0.0"
    assert GRETL_VERSION == "2023c"
    assert GRETL_PACKAGE_VERSION == "2023c-2.1build3"


def test_operations():
    assert OPERATIONS == [
        "ols", "robust_ols", "logit", "probit",
        "descriptive_summary", "correlation_matrix",
    ]


def test_identifier_valid():
    assert validate_identifier("income_2026") == "income_2026"


@pytest.mark.parametrize("name", ["bad name", "x; shell", "../x", "1x", "x-y"])
def test_identifier_rejects_unsafe(name):
    with pytest.raises(ValueError):
        validate_identifier(name)


def test_columns_valid():
    d = validate_columns({"y":[1,2,3], "x":[4,5,6]})
    assert d["y"] == [1.0,2.0,3.0]


def test_columns_equal_length():
    with pytest.raises(ValueError):
        validate_columns({"y":[1,2], "x":[3]})


def test_columns_finite():
    with pytest.raises(ValueError):
        validate_columns({"y":[1,float("inf")], "x":[2,3]})


def test_dataset_hash_stable():
    assert dataset_hash({"x":[1.0,2.0]}) == dataset_hash({"x":[1.0,2.0]})
    assert len(dataset_hash({"x":[1.0,2.0]})) == 64


def test_model_specification():
    cols = validate_columns({"y":[1,2,3], "x":[2,3,4]})
    validate_specification("ols", cols, "y", ["x"], [])


def test_model_missing_dependent():
    cols = validate_columns({"y":[1,2,3], "x":[2,3,4]})
    with pytest.raises(ValueError):
        validate_specification("ols", cols, None, ["x"], [])


def test_model_missing_predictor():
    cols = validate_columns({"y":[1,2,3], "x":[2,3,4]})
    with pytest.raises(ValueError):
        validate_specification("ols", cols, "y", ["missing"], [])


def test_summary_specification():
    cols = validate_columns({"y":[1,2,3], "x":[2,3,4]})
    validate_specification("descriptive_summary", cols, None, [], ["y","x"])


def test_summary_requires_variables():
    cols = validate_columns({"y":[1,2,3], "x":[2,3,4]})
    with pytest.raises(ValueError):
        validate_specification("descriptive_summary", cols, None, [], [])


@pytest.mark.parametrize("operation,expected", [
    ("ols", "ols y const x"),
    ("robust_ols", "ols y const x --robust"),
    ("logit", "logit y const x"),
    ("probit", "probit y const x"),
])
def test_fixed_model_scripts(operation, expected):
    script = build_hansl_script(
        operation=operation,
        csv_path=Path("/tmp/provider/data.csv"),
        dependent_variable="y",
        predictors=["x"],
        include_constant=True,
        variables=[],
    )
    assert expected in script
    assert "shell " not in script
    assert "\n!" not in script


def test_summary_script():
    script = build_hansl_script(
        operation="descriptive_summary",
        csv_path=Path("/tmp/provider/data.csv"),
        dependent_variable=None,
        predictors=[],
        include_constant=True,
        variables=["y","x"],
    )
    assert "summary y x" in script


def test_correlation_script():
    script = build_hansl_script(
        operation="correlation_matrix",
        csv_path=Path("/tmp/provider/data.csv"),
        dependent_variable=None,
        predictors=[],
        include_constant=True,
        variables=["y","x"],
    )
    assert "corr y x" in script


def test_parse_coefficients():
    transcript = """
                 coefficient   std. error
    const        1.100000      0.1
    x            0.975000      0.05
    """
    d = parse_regression_coefficients(
        transcript,
        include_constant=True,
        predictors=["x"],
    )
    assert d["const"] == 1.1
    assert d["x"] == 0.975


def test_prepare_valid_ols():
    req = PrepareRequest(
        operation="ols",
        columns={"y":[1,2,3], "x":[2,3,4]},
        dependent_variable="y",
        predictors=["x"],
    )
    assert req.operation == "ols"


def test_prepare_rejects_unknown_operation():
    with pytest.raises(ValidationError):
        PrepareRequest(
            operation="shell",
            columns={"y":[1,2,3], "x":[2,3,4]},
            dependent_variable="y",
            predictors=["x"],
        )


def test_prepare_rejects_unsafe_variable():
    with pytest.raises(ValidationError):
        PrepareRequest(
            operation="ols",
            columns={"y":[1,2,3], "bad name":[2,3,4]},
            dependent_variable="y",
            predictors=["bad name"],
        )


def test_adapter_descriptor_identity():
    d = adapter_descriptor()
    assert d["adapter_id"] == ADAPTER_ID
    assert d["provider_id"] == RUNTIME_ID
    assert d["language"] == "hansl"


def test_adapter_boundaries():
    b = adapter_descriptor()["boundaries"]
    assert b["arbitrary_hansl_source"] is False
    assert b["shell_execution"] is False
    assert b["runtime_package_install"] is False
    assert b["caller_filesystem_paths"] is False
