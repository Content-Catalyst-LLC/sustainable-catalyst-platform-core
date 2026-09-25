from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.statistical_analysis_objects import (
    CONTRACT_VERSION,
    REFERENCE_R_ADAPTER_ID,
    REFERENCE_R_RUNTIME_ID,
    AnalysisStatus,
    AlternativeHypothesis,
    AssumptionStatus,
    ConfidenceInterval,
    EffectSizeResult,
    HypothesisTestResult,
    StatisticalAnalysisPackage,
    StatisticalAnalysisPlan,
    StatisticalAnalysisResult,
    StatisticalAnalysisType,
    StatisticalAssumptionCheck,
    StatisticalDataBinding,
    StatisticalDiagnostic,
    StatisticalExecutionBinding,
    StatisticalHypothesis,
    StatisticalMatrixResult,
    StatisticalMethodSpecification,
    StatisticalScale,
    StatisticalVariableBinding,
    StatisticalVariableRole,
    contract_document,
    normalize_r_runtime_result,
    reference_statistical_analysis_package,
)


def reference_plan():
    return reference_statistical_analysis_package().plan


def reference_execution(operation="linear_regression"):
    return StatisticalExecutionBinding(
        execution_binding_id=f"execution:{operation}:001",
        computational_job_ref=f"job:{operation}:001",
        runtime_adapter_ref=REFERENCE_R_ADAPTER_ID,
        runtime_ref=REFERENCE_R_RUNTIME_ID,
        runtime_version="1.0.0",
        environment_ref="environment:r-runtime:test",
        runtime_operation=operation,
    )


def test_contract_identity():
    doc = contract_document()
    assert doc["release"] == "3.37.0"
    assert doc["contract"] == CONTRACT_VERSION


def test_contract_links_r_runtime():
    doc = contract_document()
    assert "sc.core.r-runtime-migration.v1" in doc["depends_on"]
    assert "sc-runtime-r@1.0.0" in doc["runtime_normalizers"]


def test_reference_package_is_valid():
    package = reference_statistical_analysis_package()
    assert package.plan.method.runtime_operation == "linear_regression"
    assert package.results[0].status == AnalysisStatus.completed
    assert package.results[0].execution_binding.runtime_ref == "sc-runtime-r"


def test_variable_binding_fingerprint_is_stable():
    variable = reference_plan().data_binding.variables[0]
    assert variable.fingerprint() == deepcopy(variable).fingerprint()


def test_data_binding_requires_variables():
    with pytest.raises(ValidationError):
        StatisticalDataBinding(
            data_binding_id="data:test",
            dataset_version_ref="dataset-version:test",
            variables=[],
        )


def test_data_binding_rejects_duplicate_variable_ids():
    variable = StatisticalVariableBinding(
        variable_id="variable:x",
        source_field_ref="x",
        role=StatisticalVariableRole.predictor,
    )
    with pytest.raises(ValidationError):
        StatisticalDataBinding(
            data_binding_id="data:test",
            dataset_version_ref="dataset-version:test",
            variables=[variable, deepcopy(variable)],
        )


def test_data_binding_fingerprint_is_stable():
    binding = reference_plan().data_binding
    assert binding.fingerprint() == deepcopy(binding).fingerprint()


def test_method_fingerprint_is_stable():
    method = reference_plan().method
    assert method.fingerprint() == deepcopy(method).fingerprint()


def test_hypothesis_alpha_range():
    with pytest.raises(ValidationError):
        StatisticalHypothesis(
            hypothesis_id="hypothesis:test",
            null_hypothesis="no difference",
            alternative_hypothesis="difference",
            alpha=1.0,
        )


def test_plan_rejects_duplicate_hypothesis_ids():
    hypothesis = StatisticalHypothesis(
        hypothesis_id="hypothesis:test",
        null_hypothesis="no difference",
        alternative_hypothesis="difference",
    )
    plan = reference_plan().model_dump(mode="python")
    plan["hypotheses"] = [hypothesis.model_dump(), hypothesis.model_dump()]
    with pytest.raises(ValidationError):
        StatisticalAnalysisPlan.model_validate(plan)


def test_plan_alpha_must_match_hypothesis_alpha():
    hypothesis = StatisticalHypothesis(
        hypothesis_id="hypothesis:test",
        null_hypothesis="no difference",
        alternative_hypothesis="difference",
        alpha=0.01,
    )
    plan = reference_plan().model_dump(mode="python")
    plan["alpha"] = 0.05
    plan["hypotheses"] = [hypothesis.model_dump()]
    with pytest.raises(ValidationError):
        StatisticalAnalysisPlan.model_validate(plan)


def test_plan_fingerprint_ignores_created_at():
    plan = reference_plan()
    assert plan.fingerprint() == deepcopy(plan).fingerprint()


def test_confidence_interval_rejects_reversed_bounds():
    with pytest.raises(ValidationError):
        ConfidenceInterval(lower=1.0, upper=-1.0)


def test_estimate_rejects_negative_standard_error():
    from app.services.statistical_analysis_objects import StatisticalEstimate
    with pytest.raises(ValidationError):
        StatisticalEstimate(
            estimate_id="estimate:test",
            term="x",
            estimate=1.0,
            standard_error=-0.1,
        )


def test_hypothesis_result_p_value_range():
    with pytest.raises(ValidationError):
        HypothesisTestResult(
            test_result_id="test:test",
            test_name="test",
            statistic_name="t",
            statistic=1.0,
            p_value=1.1,
        )


def test_effect_size_fingerprint_is_stable():
    effect = EffectSizeResult(
        effect_size_id="effect:test",
        measure="cohen_d",
        value=0.5,
    )
    assert effect.fingerprint() == deepcopy(effect).fingerprint()


def test_diagnostic_fingerprint_is_stable():
    diagnostic = StatisticalDiagnostic(
        diagnostic_id="diagnostic:test",
        name="Normality",
        status=AssumptionStatus.warning,
        statistic=0.95,
        p_value=0.04,
    )
    assert diagnostic.fingerprint() == deepcopy(diagnostic).fingerprint()


def test_assumption_fingerprint_is_stable():
    check = StatisticalAssumptionCheck(
        assumption_check_id="assumption:test",
        assumption="Residual normality",
        status=AssumptionStatus.not_checked,
    )
    assert check.fingerprint() == deepcopy(check).fingerprint()


def test_matrix_requires_labels():
    with pytest.raises(ValidationError):
        StatisticalMatrixResult(
            matrix_result_id="matrix:test",
            name="Matrix",
            row_labels=[],
            column_labels=["x"],
            values=[],
        )


def test_matrix_row_count_matches_labels():
    with pytest.raises(ValidationError):
        StatisticalMatrixResult(
            matrix_result_id="matrix:test",
            name="Matrix",
            row_labels=["x", "y"],
            column_labels=["x"],
            values=[[1.0]],
        )


def test_matrix_column_count_matches_labels():
    with pytest.raises(ValidationError):
        StatisticalMatrixResult(
            matrix_result_id="matrix:test",
            name="Matrix",
            row_labels=["x"],
            column_labels=["x", "y"],
            values=[[1.0]],
        )


def test_execution_binding_fingerprint_is_stable():
    binding = reference_execution()
    assert binding.fingerprint() == deepcopy(binding).fingerprint()


def test_completed_result_requires_result_objects():
    with pytest.raises(ValidationError):
        StatisticalAnalysisResult(
            analysis_result_id="result:test",
            analysis_plan_ref="plan:test",
            status=AnalysisStatus.completed,
            execution_binding=reference_execution(),
        )


def test_result_rejects_reversed_timestamps():
    from datetime import datetime, timezone
    with pytest.raises(ValidationError):
        StatisticalAnalysisResult(
            analysis_result_id="result:test",
            analysis_plan_ref="plan:test",
            status=AnalysisStatus.completed,
            estimates=[
                {
                    "estimate_id": "estimate:test",
                    "term": "mean",
                    "estimate": 1.0,
                }
            ],
            execution_binding=reference_execution(),
            started_at=datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc),
            completed_at=datetime(2026, 9, 25, 11, 0, tzinfo=timezone.utc),
        )


def test_result_fingerprint_ignores_lifecycle_state():
    result = reference_statistical_analysis_package().results[0]
    other = deepcopy(result)
    other.status = AnalysisStatus.running
    other.started_at = None
    other.completed_at = None
    assert result.fingerprint() == other.fingerprint()


def test_package_requires_results():
    package = reference_statistical_analysis_package()
    with pytest.raises(ValidationError):
        StatisticalAnalysisPackage(
            package_id="package:test",
            plan=package.plan,
            results=[],
        )


def test_package_rejects_result_for_other_plan():
    package = reference_statistical_analysis_package()
    result = deepcopy(package.results[0])
    result.analysis_plan_ref = "plan:other"
    with pytest.raises(ValidationError):
        StatisticalAnalysisPackage(
            package_id="package:test",
            plan=package.plan,
            results=[result],
        )


def test_package_fingerprint_is_stable():
    package = reference_statistical_analysis_package()
    assert package.fingerprint() == deepcopy(package).fingerprint()
    assert len(package.fingerprint()) == 64


def test_normalize_descriptive_summary():
    plan = reference_plan()
    payload = {
        "operation": "descriptive_summary",
        "result": {
            "n": 5, "mean": 3, "sd": 1.58, "min": 1,
            "q1": 2, "median": 3, "q3": 4, "max": 5,
        },
    }
    result = normalize_r_runtime_result(
        analysis_plan=plan,
        runtime_payload=payload,
        execution_binding=reference_execution("descriptive_summary"),
        analysis_result_id="result:descriptive",
    )
    assert result.sample_size == 5
    assert len(result.estimates) == 7


def test_normalize_quantile_summary():
    result = normalize_r_runtime_result(
        analysis_plan=reference_plan(),
        runtime_payload={
            "operation": "quantile_summary",
            "result": {"q0": 1, "q25": 2, "q50": 3, "q75": 4, "q100": 5},
        },
        execution_binding=reference_execution("quantile_summary"),
        analysis_result_id="result:quantiles",
    )
    assert [x.term for x in result.estimates] == ["q0", "q25", "q50", "q75", "q100"]


def test_normalize_correlation_matrix():
    result = normalize_r_runtime_result(
        analysis_plan=reference_plan(),
        runtime_payload={
            "operation": "correlation_matrix",
            "result": {
                "columns": "x,y",
                "rows": [["x", "1,0.8"], ["y", "0.8,1"]],
            },
        },
        execution_binding=reference_execution("correlation_matrix"),
        analysis_result_id="result:correlation",
    )
    matrix = result.matrix_results[0]
    assert matrix.row_labels == ["x", "y"]
    assert matrix.values[0][1] == 0.8


def test_normalize_linear_regression():
    result = normalize_r_runtime_result(
        analysis_plan=reference_plan(),
        runtime_payload={
            "operation": "linear_regression",
            "result": {
                "r_squared": 0.91,
                "adjusted_r_squared": 0.88,
                "sigma": 1.2,
                "df_residual": 8,
                "rows": [
                    ["(Intercept)", "1,0.5,2,0.08"],
                    ["x", "2,0.4,5,0.001"],
                ],
            },
        },
        execution_binding=reference_execution("linear_regression"),
        analysis_result_id="result:regression",
    )
    assert len(result.estimates) == 2
    assert len(result.fit_statistics) == 4
    slope = [x for x in result.estimates if x.term == "x"][0]
    assert slope.estimate == 2
    assert slope.p_value == 0.001


def test_normalize_t_test():
    plan = reference_plan().model_copy(deep=True)
    plan.hypotheses = [
        StatisticalHypothesis(
            hypothesis_id="hypothesis:ttest",
            null_hypothesis="means are equal",
            alternative_hypothesis="means differ",
            alternative=AlternativeHypothesis.two_sided,
            alpha=0.05,
        )
    ]
    plan.alpha = 0.05
    result = normalize_r_runtime_result(
        analysis_plan=plan,
        runtime_payload={
            "operation": "t_test",
            "result": {
                "statistic": 2.4,
                "parameter": 18,
                "p_value": 0.027,
                "conf_low": 0.1,
                "conf_high": 2.2,
                "estimate_x": 5.2,
                "estimate_y": 4.0,
            },
        },
        execution_binding=reference_execution("t_test"),
        analysis_result_id="result:ttest",
    )
    test = result.hypothesis_tests[0]
    assert test.hypothesis_ref == "hypothesis:ttest"
    assert test.passed_threshold is True
    assert test.confidence_interval.lower == 0.1


def test_normalize_anova():
    result = normalize_r_runtime_result(
        analysis_plan=reference_plan(),
        runtime_payload={
            "operation": "one_way_anova",
            "result": {
                "df_between": 2,
                "df_within": 27,
                "f_value": 4.5,
                "p_value": 0.02,
            },
        },
        execution_binding=reference_execution("one_way_anova"),
        analysis_result_id="result:anova",
    )
    test = result.hypothesis_tests[0]
    assert test.statistic_name == "F"
    assert test.degrees_of_freedom == [2.0, 27.0]


def test_normalizer_rejects_unknown_operation():
    with pytest.raises(ValueError):
        normalize_r_runtime_result(
            analysis_plan=reference_plan(),
            runtime_payload={"operation": "unknown", "result": {}},
            execution_binding=reference_execution("unknown"),
            analysis_result_id="result:unknown",
        )


def test_normalizer_requires_result_object():
    with pytest.raises(ValueError):
        normalize_r_runtime_result(
            analysis_plan=reference_plan(),
            runtime_payload={"operation": "descriptive_summary", "result": []},
            execution_binding=reference_execution("descriptive_summary"),
            analysis_result_id="result:bad",
        )


def test_normalizer_rejects_bad_correlation_shape():
    with pytest.raises(ValueError):
        normalize_r_runtime_result(
            analysis_plan=reference_plan(),
            runtime_payload={
                "operation": "correlation_matrix",
                "result": {"columns": "x,y", "rows": [["x", "1"]]},
            },
            execution_binding=reference_execution("correlation_matrix"),
            analysis_result_id="result:bad-matrix",
        )


def test_reference_result_is_normalized_from_r():
    package = reference_statistical_analysis_package()
    result = package.results[0]
    assert result.execution_binding.runtime_ref == "sc-runtime-r"
    assert result.provenance["normalizer"] == CONTRACT_VERSION
    assert len(result.estimates) == 2
    assert len(result.fit_statistics) == 4


def test_reference_method_was_researcher_selected():
    package = reference_statistical_analysis_package()
    assert package.plan.provenance["core_selects_statistical_method"] is False
    assert package.plan.method.metadata["method_selected_by"] == "researcher"


def test_reference_preserves_limitations():
    result = reference_statistical_analysis_package().results[0]
    assert len(result.limitations) == 2


def test_core_does_not_execute_methods():
    doc = contract_document()
    assert doc["boundaries"]["core_executes_statistical_methods"] is False
    assert doc["integration"]["runtime_provider_executes_methods"] is True


def test_core_does_not_select_method():
    doc = contract_document()
    assert doc["boundaries"]["core_selects_statistical_method"] is False


def test_core_does_not_treat_significance_as_truth():
    doc = contract_document()
    assert doc["boundaries"]["core_interprets_significance_as_truth"] is False


def test_core_does_not_certify_assumptions_or_validity():
    doc = contract_document()
    assert doc["boundaries"]["core_certifies_assumptions"] is False
    assert doc["boundaries"]["core_certifies_statistical_validity"] is False


def test_contract_supports_future_statistical_domains():
    values = {x.value for x in StatisticalAnalysisType}
    assert "econometric" in values
    assert "psychometric" in values
    assert "bayesian" in values
    assert "time-series" in values


def test_variable_roles_cover_research_design():
    values = {x.value for x in StatisticalVariableRole}
    assert {"outcome", "predictor", "treatment", "control", "group", "weight"}.issubset(values)


def test_scales_cover_common_statistical_data():
    values = {x.value for x in StatisticalScale}
    assert {"nominal", "ordinal", "continuous", "count", "binary"}.issubset(values)
