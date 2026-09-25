import pytest
from pydantic import ValidationError
from app import server

def test_identity():
    assert server.RUNTIME_ID == "sc-runtime-r"
    assert server.PROVIDER_VERSION == "1.0.0"
    assert server.ADAPTER_ID == "adapter:sc-runtime-r"

def test_capabilities_are_allowlisted():
    assert server.CAPABILITIES == [
        "descriptive_summary","quantile_summary","correlation_matrix",
        "linear_regression","t_test","one_way_anova",
    ]

def test_legacy_aliases():
    assert server.canonical_operation("lm") == "linear_regression"
    assert server.canonical_operation("anova") == "one_way_anova"
    assert server.canonical_operation("summary") == "descriptive_summary"

def test_unknown_operation_rejected():
    with pytest.raises(ValueError):
        server.canonical_operation("system")

def test_numeric_vector_validation():
    assert server.validate_numeric_vector([1, 2.5, -3]) == [1.0, 2.5, -3.0]

def test_numeric_vector_rejects_bool():
    with pytest.raises(ValueError):
        server.validate_numeric_vector([True, 1])

def test_numeric_vector_rejects_nonfinite():
    with pytest.raises(ValueError):
        server.validate_numeric_vector([1, float("inf")])

def test_named_columns_require_equal_lengths():
    with pytest.raises(ValueError):
        server.validate_named_numeric_columns({"x": [1,2], "y": [1]})

def test_named_columns_reject_unsafe_names():
    with pytest.raises(ValueError):
        server.validate_named_numeric_columns({"x);system('id')": [1,2]})

def test_descriptive_script_contains_no_shell():
    script = server.build_r_script("descriptive_summary", {"values": [1,2,3]})
    assert "mean(x)" in script
    assert "system(" not in script

def test_quantile_script():
    assert "quantile(" in server.build_r_script("quantile_summary", {"values":[1,2,3,4]})

def test_correlation_method_validation():
    with pytest.raises(ValueError):
        server.build_r_script("correlation_matrix", {"data":{"x":[1,2],"y":[2,3]},"method":"evil"})

def test_linear_regression_requires_known_outcome():
    with pytest.raises(ValueError):
        server.build_r_script("linear_regression", {"data":{"x":[1,2],"y":[2,4]},"outcome":"z","predictors":["x"]})

def test_linear_regression_requires_predictors():
    with pytest.raises(ValueError):
        server.build_r_script("linear_regression", {"data":{"x":[1,2],"y":[2,4]},"outcome":"y","predictors":[]})

def test_linear_regression_uses_reformulate():
    script = server.build_r_script("linear_regression", {"data":{"x":[1,2,3],"y":[2,4,6]},"outcome":"y","predictors":["x"]})
    assert "reformulate" in script
    assert "eval(parse" not in script

def test_paired_ttest_requires_equal_lengths():
    with pytest.raises(ValueError):
        server.build_r_script("t_test", {"x":[1,2],"y":[1],"paired":True})

def test_ttest_alternative_is_allowlisted():
    with pytest.raises(ValueError):
        server.build_r_script("t_test", {"x":[1,2],"y":[2,3],"alternative":"execute"})

def test_anova_requires_two_groups():
    with pytest.raises(ValueError):
        server.build_r_script("one_way_anova", {"groups":[[1,2,3]]})

def test_anova_script_uses_aov():
    assert "aov(" in server.build_r_script("one_way_anova", {"groups":[[1,2,3],[2,3,4]]})

def test_prepare_request_validates_operation_and_inputs():
    body = server.PrepareRequest(operation="descriptive_summary", inputs={"values":[1,2,3]})
    assert body.operation == "descriptive_summary"

def test_prepare_request_rejects_bad_inputs():
    with pytest.raises(ValidationError):
        server.PrepareRequest(operation="descriptive_summary", inputs={"values":["x"]})

def test_adapter_descriptor():
    desc = server.adapter_descriptor()
    assert desc["provider_id"] == "sc-runtime-r"
    assert desc["provider_version"] == "1.0.0"
    assert desc["status"] == "registered"
    assert desc["boundaries"]["arbitrary_r_source"] is False

def test_tsv_parse_scalars():
    assert server.tsv_parse("n\t3\nmean\t2\nlabel\tok\n") == {"n":3,"mean":2,"label":"ok"}

def test_tsv_parse_rows():
    assert server.tsv_parse("__ROW__\tx\t1,2,3\n")["rows"] == [["x","1,2,3"]]

def test_run_r_requires_rscript(monkeypatch):
    monkeypatch.setattr(server, "rscript_path", lambda: None)
    with pytest.raises(RuntimeError):
        server.run_r("descriptive_summary", {"values":[1,2,3]})

def test_run_r_parses_fake_r_output(monkeypatch, tmp_path):
    fake = tmp_path / "Rscript"
    fake.write_text("#!/bin/sh\nprintf 'n\\t3\\nmean\\t2\\n'\n")
    fake.chmod(0o755)
    monkeypatch.setattr(server, "rscript_path", lambda: str(fake))
    result = server.run_r("descriptive_summary", {"values":[1,2,3]})
    assert result["result"]["n"] == 3
    assert result["result"]["mean"] == 2

def test_no_arbitrary_code_capability():
    desc = server.adapter_descriptor()
    assert "source" not in desc["capabilities"]
    assert "shell" not in desc["capabilities"]
