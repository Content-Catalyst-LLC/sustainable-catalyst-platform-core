from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.37.0"
CONTRACT_VERSION = "sc.core.statistical-analysis-object.v1"

R_RUNTIME_MIGRATION_CONTRACT = "sc.core.r-runtime-migration.v1"
RUNTIME_OBJECT_CONTRACT = "sc.core.computational-runtime-object.v1"
RUNTIME_ADAPTER_CONTRACT = "sc.core.runtime-adapter.v1"
COMPUTATIONAL_JOB_CONTRACT = "sc.core.computational-job.v1"
ENVIRONMENT_PROVENANCE_CONTRACT = "sc.core.execution-environment-provenance.v1"
AI_RESEARCH_OBJECT_CONTRACT = "sc.core.ai-research-object-system.v1"

REFERENCE_R_RUNTIME_ID = "sc-runtime-r"
REFERENCE_R_ADAPTER_ID = "adapter:sc-runtime-r"
REFERENCE_R_RUNTIME_VERSION = "1.0.0"


class StatisticalAnalysisType(str, Enum):
    descriptive = "descriptive"
    distribution = "distribution"
    correlation = "correlation"
    regression = "regression"
    hypothesis_test = "hypothesis-test"
    analysis_of_variance = "analysis-of-variance"
    time_series = "time-series"
    econometric = "econometric"
    psychometric = "psychometric"
    Bayesian = "bayesian"
    simulation = "simulation"
    custom = "custom"


class StatisticalVariableRole(str, Enum):
    outcome = "outcome"
    response = "response"
    predictor = "predictor"
    covariate = "covariate"
    exposure = "exposure"
    treatment = "treatment"
    control = "control"
    group = "group"
    weight = "weight"
    identifier = "identifier"
    time = "time"
    stratum = "stratum"
    cluster = "cluster"
    other = "other"


class StatisticalScale(str, Enum):
    nominal = "nominal"
    ordinal = "ordinal"
    interval = "interval"
    ratio = "ratio"
    binary = "binary"
    count = "count"
    continuous = "continuous"
    datetime = "datetime"
    other = "other"


class AnalysisStatus(str, Enum):
    declared = "declared"
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class AssumptionStatus(str, Enum):
    not_checked = "not-checked"
    passed = "passed"
    warning = "warning"
    failed = "failed"
    not_applicable = "not-applicable"


class AlternativeHypothesis(str, Enum):
    two_sided = "two-sided"
    less = "less"
    greater = "greater"


class StatisticalVariableBinding(BaseModel):
    variable_id: str = Field(min_length=2, max_length=300)
    source_field_ref: str = Field(min_length=1, max_length=1000)
    role: StatisticalVariableRole
    scale: StatisticalScale | None = None
    unit: str | None = Field(default=None, max_length=200)
    label: str | None = Field(default=None, max_length=500)
    transformation_ref: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class StatisticalDataBinding(BaseModel):
    data_binding_id: str = Field(min_length=2, max_length=300)
    dataset_version_ref: str = Field(min_length=2, max_length=500)
    feature_set_ref: str | None = Field(default=None, max_length=500)
    variables: list[StatisticalVariableBinding] = Field(default_factory=list)
    filter_ref: str | None = Field(default=None, max_length=500)
    sample_selection_ref: str | None = Field(default=None, max_length=500)
    row_count: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_binding(self):
        ids = [item.variable_id for item in self.variables]
        if len(ids) != len(set(ids)):
            raise ValueError("statistical variable ids must be unique")
        if not self.variables:
            raise ValueError("statistical data binding requires variables")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class StatisticalMethodSpecification(BaseModel):
    method_id: str = Field(min_length=2, max_length=300)
    name: str = Field(min_length=1, max_length=500)
    analysis_type: StatisticalAnalysisType
    runtime_operation: str | None = Field(default=None, max_length=300)
    formula: str | None = Field(default=None, max_length=2000)
    parameters: dict[str, Any] = Field(default_factory=dict)
    method_reference_refs: list[str] = Field(default_factory=list)
    preferred_runtime_refs: list[str] = Field(default_factory=list)
    deterministic: bool | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class StatisticalHypothesis(BaseModel):
    hypothesis_id: str = Field(min_length=2, max_length=300)
    null_hypothesis: str = Field(min_length=1, max_length=10000)
    alternative_hypothesis: str = Field(min_length=1, max_length=10000)
    alternative: AlternativeHypothesis = AlternativeHypothesis.two_sided
    alpha: float = Field(default=0.05, gt=0.0, lt=1.0)
    preregistered: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class StatisticalAnalysisPlan(BaseModel):
    analysis_plan_id: str = Field(min_length=2, max_length=300)
    name: str = Field(min_length=1, max_length=500)
    objective: str = Field(min_length=1, max_length=20000)
    research_question_refs: list[str] = Field(default_factory=list)
    hypothesis_refs: list[str] = Field(default_factory=list)
    data_binding: StatisticalDataBinding
    method: StatisticalMethodSpecification
    hypotheses: list[StatisticalHypothesis] = Field(default_factory=list)
    alpha: float | None = Field(default=None, gt=0.0, lt=1.0)
    random_seed: int | None = None
    preregistration_ref: str | None = Field(default=None, max_length=1000)
    source_commit: str | None = Field(default=None, max_length=300)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_plan(self):
        ids = [item.hypothesis_id for item in self.hypotheses]
        if len(ids) != len(set(ids)):
            raise ValueError("statistical hypothesis ids must be unique")
        if self.alpha is not None:
            for hypothesis in self.hypotheses:
                if abs(hypothesis.alpha - self.alpha) > 1e-12:
                    raise ValueError(
                        "plan alpha and hypothesis alpha must agree when plan alpha is set"
                    )
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class ConfidenceInterval(BaseModel):
    confidence_level: float = Field(default=0.95, gt=0.0, lt=1.0)
    lower: float
    upper: float

    @model_validator(mode="after")
    def validate_bounds(self):
        if self.lower > self.upper:
            raise ValueError("confidence interval lower bound exceeds upper bound")
        return self


class StatisticalEstimate(BaseModel):
    estimate_id: str = Field(min_length=2, max_length=500)
    term: str = Field(min_length=1, max_length=500)
    estimate: float | int
    standard_error: float | None = Field(default=None, ge=0.0)
    statistic: float | None = None
    p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    degrees_of_freedom: float | None = Field(default=None, ge=0.0)
    confidence_interval: ConfidenceInterval | None = None
    unit: str | None = Field(default=None, max_length=200)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class HypothesisTestResult(BaseModel):
    test_result_id: str = Field(min_length=2, max_length=500)
    hypothesis_ref: str | None = Field(default=None, max_length=500)
    test_name: str = Field(min_length=1, max_length=500)
    statistic_name: str = Field(min_length=1, max_length=100)
    statistic: float
    p_value: float = Field(ge=0.0, le=1.0)
    degrees_of_freedom: float | list[float] | None = None
    alpha: float = Field(default=0.05, gt=0.0, lt=1.0)
    passed_threshold: bool | None = None
    confidence_interval: ConfidenceInterval | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EffectSizeResult(BaseModel):
    effect_size_id: str = Field(min_length=2, max_length=500)
    measure: str = Field(min_length=1, max_length=200)
    value: float
    confidence_interval: ConfidenceInterval | None = None
    interpretation: str | None = Field(default=None, max_length=5000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ModelFitStatistic(BaseModel):
    fit_statistic_id: str = Field(min_length=2, max_length=500)
    name: str = Field(min_length=1, max_length=200)
    value: float | int
    metadata: dict[str, Any] = Field(default_factory=dict)


class StatisticalDiagnostic(BaseModel):
    diagnostic_id: str = Field(min_length=2, max_length=500)
    name: str = Field(min_length=1, max_length=500)
    status: AssumptionStatus = AssumptionStatus.not_checked
    statistic: float | None = None
    p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    threshold: float | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class StatisticalAssumptionCheck(BaseModel):
    assumption_check_id: str = Field(min_length=2, max_length=500)
    assumption: str = Field(min_length=1, max_length=1000)
    status: AssumptionStatus
    diagnostic_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class StatisticalMatrixResult(BaseModel):
    matrix_result_id: str = Field(min_length=2, max_length=500)
    name: str = Field(min_length=1, max_length=500)
    row_labels: list[str] = Field(default_factory=list)
    column_labels: list[str] = Field(default_factory=list)
    values: list[list[float]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_matrix(self):
        if not self.row_labels or not self.column_labels:
            raise ValueError("matrix result requires row and column labels")
        if len(self.values) != len(self.row_labels):
            raise ValueError("matrix row count must match row labels")
        for row in self.values:
            if len(row) != len(self.column_labels):
                raise ValueError("matrix column count must match column labels")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class StatisticalExecutionBinding(BaseModel):
    execution_binding_id: str = Field(min_length=2, max_length=500)
    computational_job_ref: str = Field(min_length=2, max_length=500)
    runtime_adapter_ref: str = Field(min_length=2, max_length=500)
    runtime_ref: str = Field(min_length=2, max_length=500)
    runtime_version: str | None = Field(default=None, max_length=200)
    environment_ref: str = Field(min_length=2, max_length=500)
    runtime_operation: str = Field(min_length=1, max_length=300)
    raw_result_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class StatisticalAnalysisResult(BaseModel):
    analysis_result_id: str = Field(min_length=2, max_length=500)
    analysis_plan_ref: str = Field(min_length=2, max_length=500)
    status: AnalysisStatus
    sample_size: int | None = Field(default=None, ge=0)
    estimates: list[StatisticalEstimate] = Field(default_factory=list)
    hypothesis_tests: list[HypothesisTestResult] = Field(default_factory=list)
    effect_sizes: list[EffectSizeResult] = Field(default_factory=list)
    fit_statistics: list[ModelFitStatistic] = Field(default_factory=list)
    diagnostics: list[StatisticalDiagnostic] = Field(default_factory=list)
    assumption_checks: list[StatisticalAssumptionCheck] = Field(default_factory=list)
    matrix_results: list[StatisticalMatrixResult] = Field(default_factory=list)
    execution_binding: StatisticalExecutionBinding
    artifact_refs: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_result(self):
        if (
            self.status == AnalysisStatus.completed
            and not any(
                [
                    self.estimates,
                    self.hypothesis_tests,
                    self.effect_sizes,
                    self.fit_statistics,
                    self.matrix_results,
                ]
            )
        ):
            raise ValueError("completed statistical analysis requires result objects")

        if (
            self.started_at is not None
            and self.completed_at is not None
            and self.completed_at < self.started_at
        ):
            raise ValueError("completed_at cannot precede started_at")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        for key in ("status", "started_at", "completed_at"):
            payload.pop(key, None)
        return canonical_sha256(payload)


class StatisticalAnalysisPackage(BaseModel):
    package_id: str = Field(min_length=2, max_length=500)
    plan: StatisticalAnalysisPlan
    results: list[StatisticalAnalysisResult] = Field(default_factory=list)
    source_object_refs: list[str] = Field(default_factory=list)
    result_artifact_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_package(self):
        if not self.results:
            raise ValueError("statistical analysis package requires results")
        for result in self.results:
            if result.analysis_plan_ref != self.plan.analysis_plan_id:
                raise ValueError("statistical result must reference package plan")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "package_id": self.package_id,
            "plan_fingerprint_sha256": self.plan.fingerprint(),
            "result_fingerprints": sorted(item.fingerprint() for item in self.results),
            "source_object_refs": sorted(self.source_object_refs),
            "result_artifact_refs": sorted(self.result_artifact_refs),
            "provenance": self.provenance,
            "metadata": self.metadata,
        })


def _float(value: Any, *, name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be numeric")


def _row_numbers(row: list[str], *, expected: int) -> tuple[str, list[float]]:
    if len(row) != 2:
        raise ValueError("R table row must contain row label and comma-separated values")
    label = row[0]
    parts = row[1].split(",")
    if len(parts) != expected:
        raise ValueError("R table row has unexpected column count")
    return label, [_float(item, name=f"row:{label}") for item in parts]


def normalize_r_runtime_result(
    *,
    analysis_plan: StatisticalAnalysisPlan,
    runtime_payload: dict[str, Any],
    execution_binding: StatisticalExecutionBinding,
    analysis_result_id: str,
) -> StatisticalAnalysisResult:
    operation = runtime_payload.get("operation")
    raw = runtime_payload.get("result")
    if not isinstance(raw, dict):
        raise ValueError("R runtime payload must contain a result object")

    estimates: list[StatisticalEstimate] = []
    tests: list[HypothesisTestResult] = []
    fit: list[ModelFitStatistic] = []
    matrices: list[StatisticalMatrixResult] = []
    sample_size: int | None = None

    if operation == "descriptive_summary":
        sample_size = int(raw["n"])
        for term in ("mean", "sd", "min", "q1", "median", "q3", "max"):
            estimates.append(
                StatisticalEstimate(
                    estimate_id=f"{analysis_result_id}:estimate:{term}",
                    term=term,
                    estimate=_float(raw[term], name=term),
                )
            )

    elif operation == "quantile_summary":
        for term in ("q0", "q25", "q50", "q75", "q100"):
            estimates.append(
                StatisticalEstimate(
                    estimate_id=f"{analysis_result_id}:estimate:{term}",
                    term=term,
                    estimate=_float(raw[term], name=term),
                )
            )

    elif operation == "correlation_matrix":
        columns = str(raw["columns"]).split(",")
        rows = raw.get("rows", [])
        labels: list[str] = []
        values: list[list[float]] = []
        for row in rows:
            label, nums = _row_numbers(row, expected=len(columns))
            labels.append(label)
            values.append(nums)
        matrices.append(
            StatisticalMatrixResult(
                matrix_result_id=f"{analysis_result_id}:matrix:correlation",
                name="Correlation Matrix",
                row_labels=labels,
                column_labels=columns,
                values=values,
                metadata={"runtime_operation": operation},
            )
        )

    elif operation == "linear_regression":
        fit.extend(
            [
                ModelFitStatistic(
                    fit_statistic_id=f"{analysis_result_id}:fit:r-squared",
                    name="r_squared",
                    value=_float(raw["r_squared"], name="r_squared"),
                ),
                ModelFitStatistic(
                    fit_statistic_id=f"{analysis_result_id}:fit:adjusted-r-squared",
                    name="adjusted_r_squared",
                    value=_float(raw["adjusted_r_squared"], name="adjusted_r_squared"),
                ),
                ModelFitStatistic(
                    fit_statistic_id=f"{analysis_result_id}:fit:sigma",
                    name="sigma",
                    value=_float(raw["sigma"], name="sigma"),
                ),
                ModelFitStatistic(
                    fit_statistic_id=f"{analysis_result_id}:fit:df-residual",
                    name="df_residual",
                    value=_float(raw["df_residual"], name="df_residual"),
                ),
            ]
        )
        for row in raw.get("rows", []):
            label, nums = _row_numbers(row, expected=4)
            estimates.append(
                StatisticalEstimate(
                    estimate_id=f"{analysis_result_id}:coefficient:{label}",
                    term=label,
                    estimate=nums[0],
                    standard_error=max(0.0, nums[1]),
                    statistic=nums[2],
                    p_value=nums[3],
                    degrees_of_freedom=_float(raw["df_residual"], name="df_residual"),
                )
            )

    elif operation == "t_test":
        hypothesis_ref = (
            analysis_plan.hypotheses[0].hypothesis_id
            if analysis_plan.hypotheses
            else None
        )
        alpha = (
            analysis_plan.hypotheses[0].alpha
            if analysis_plan.hypotheses
            else (analysis_plan.alpha or 0.05)
        )
        p_value = _float(raw["p_value"], name="p_value")
        tests.append(
            HypothesisTestResult(
                test_result_id=f"{analysis_result_id}:test:t",
                hypothesis_ref=hypothesis_ref,
                test_name="t-test",
                statistic_name="t",
                statistic=_float(raw["statistic"], name="statistic"),
                p_value=p_value,
                degrees_of_freedom=_float(raw["parameter"], name="parameter"),
                alpha=alpha,
                passed_threshold=p_value < alpha,
                confidence_interval=ConfidenceInterval(
                    confidence_level=1.0 - alpha,
                    lower=_float(raw["conf_low"], name="conf_low"),
                    upper=_float(raw["conf_high"], name="conf_high"),
                ),
            )
        )
        if "estimate_x" in raw:
            estimates.append(
                StatisticalEstimate(
                    estimate_id=f"{analysis_result_id}:estimate:x",
                    term="estimate_x",
                    estimate=_float(raw["estimate_x"], name="estimate_x"),
                )
            )
        if "estimate_y" in raw:
            estimates.append(
                StatisticalEstimate(
                    estimate_id=f"{analysis_result_id}:estimate:y",
                    term="estimate_y",
                    estimate=_float(raw["estimate_y"], name="estimate_y"),
                )
            )

    elif operation == "one_way_anova":
        alpha = analysis_plan.alpha or 0.05
        p_value = _float(raw["p_value"], name="p_value")
        tests.append(
            HypothesisTestResult(
                test_result_id=f"{analysis_result_id}:test:anova-f",
                hypothesis_ref=(
                    analysis_plan.hypotheses[0].hypothesis_id
                    if analysis_plan.hypotheses
                    else None
                ),
                test_name="one-way ANOVA",
                statistic_name="F",
                statistic=_float(raw["f_value"], name="f_value"),
                p_value=p_value,
                degrees_of_freedom=[
                    _float(raw["df_between"], name="df_between"),
                    _float(raw["df_within"], name="df_within"),
                ],
                alpha=alpha,
                passed_threshold=p_value < alpha,
            )
        )

    else:
        raise ValueError(f"unsupported normalized R runtime operation: {operation}")

    return StatisticalAnalysisResult(
        analysis_result_id=analysis_result_id,
        analysis_plan_ref=analysis_plan.analysis_plan_id,
        status=AnalysisStatus.completed,
        sample_size=sample_size,
        estimates=estimates,
        hypothesis_tests=tests,
        fit_statistics=fit,
        matrix_results=matrices,
        execution_binding=execution_binding,
        provenance={
            "normalizer": CONTRACT_VERSION,
            "runtime_payload_operation": operation,
            "raw_runtime_payload_preserved_externally": True,
            "core_certifies_statistical_validity": False,
        },
    )


def reference_statistical_analysis_package() -> StatisticalAnalysisPackage:
    data_binding = StatisticalDataBinding(
        data_binding_id="stat-data:reference-regression",
        dataset_version_ref="dataset-version:reference-regression:v1",
        variables=[
            StatisticalVariableBinding(
                variable_id="variable:x",
                source_field_ref="x",
                role=StatisticalVariableRole.predictor,
                scale=StatisticalScale.continuous,
            ),
            StatisticalVariableBinding(
                variable_id="variable:y",
                source_field_ref="y",
                role=StatisticalVariableRole.outcome,
                scale=StatisticalScale.continuous,
            ),
        ],
        row_count=5,
    )

    method = StatisticalMethodSpecification(
        method_id="stat-method:ols-linear-regression",
        name="Ordinary Least Squares Linear Regression",
        analysis_type=StatisticalAnalysisType.regression,
        runtime_operation="linear_regression",
        formula="y ~ x",
        preferred_runtime_refs=[REFERENCE_R_RUNTIME_ID],
        deterministic=True,
        metadata={
            "core_selected_method": False,
            "method_selected_by": "researcher",
        },
    )

    plan = StatisticalAnalysisPlan(
        analysis_plan_id="stat-plan:reference-regression:v1",
        name="Reference Regression Analysis",
        objective="Estimate the linear relationship between x and y.",
        research_question_refs=["research-question:reference-regression"],
        data_binding=data_binding,
        method=method,
        source_commit="reference-statistical-analysis-commit",
        provenance={
            "method_selection": "researcher-declared",
            "core_selects_statistical_method": False,
        },
    )

    execution = StatisticalExecutionBinding(
        execution_binding_id="stat-execution:reference-regression:001",
        computational_job_ref="job:reference-r-linear-regression-001",
        runtime_adapter_ref=REFERENCE_R_ADAPTER_ID,
        runtime_ref=REFERENCE_R_RUNTIME_ID,
        runtime_version=REFERENCE_R_RUNTIME_VERSION,
        environment_ref="environment:reference-r-runtime-1.0",
        runtime_operation="linear_regression",
        raw_result_ref="runtime-result:reference-r-linear-regression-001",
    )

    runtime_payload = {
        "operation": "linear_regression",
        "elapsed_ms": 12,
        "result": {
            "r_squared": 1.0,
            "adjusted_r_squared": 1.0,
            "sigma": 0.0,
            "df_residual": 3,
            "rows": [
                ["(Intercept)", "0,0,0,1"],
                ["x", "2,0,999999,0"],
            ],
        },
    }

    result = normalize_r_runtime_result(
        analysis_plan=plan,
        runtime_payload=runtime_payload,
        execution_binding=execution,
        analysis_result_id="stat-result:reference-regression:001",
    )
    result.limitations = [
        "Reference payload is a deterministic contract proof, not substantive research evidence.",
        "Core records results and provenance but does not certify model assumptions or validity.",
    ]

    return StatisticalAnalysisPackage(
        package_id="stat-package:reference-regression:v1",
        plan=plan,
        results=[result],
        source_object_refs=[
            "dataset-version:reference-regression:v1",
            "runtime-registration:sc-runtime-r:1.0.0",
        ],
        result_artifact_refs=["runtime-result:reference-r-linear-regression-001"],
        provenance={
            "core_release": CORE_RELEASE,
            "statistical_runtime": REFERENCE_R_RUNTIME_ID,
        },
    )


def contract_document() -> dict[str, Any]:
    reference = reference_statistical_analysis_package()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            R_RUNTIME_MIGRATION_CONTRACT,
            RUNTIME_OBJECT_CONTRACT,
            RUNTIME_ADAPTER_CONTRACT,
            COMPUTATIONAL_JOB_CONTRACT,
            ENVIRONMENT_PROVENANCE_CONTRACT,
            AI_RESEARCH_OBJECT_CONTRACT,
        ],
        "object_types": [
            "StatisticalVariableBinding",
            "StatisticalDataBinding",
            "StatisticalMethodSpecification",
            "StatisticalHypothesis",
            "StatisticalAnalysisPlan",
            "ConfidenceInterval",
            "StatisticalEstimate",
            "HypothesisTestResult",
            "EffectSizeResult",
            "ModelFitStatistic",
            "StatisticalDiagnostic",
            "StatisticalAssumptionCheck",
            "StatisticalMatrixResult",
            "StatisticalExecutionBinding",
            "StatisticalAnalysisResult",
            "StatisticalAnalysisPackage",
        ],
        "capabilities": {
            "analysis_plans": True,
            "data_and_variable_bindings": True,
            "method_specifications": True,
            "hypothesis_objects": True,
            "confidence_intervals": True,
            "parameter_estimates": True,
            "hypothesis_test_results": True,
            "effect_sizes": True,
            "model_fit_statistics": True,
            "diagnostics_and_assumptions": True,
            "matrix_results": True,
            "runtime_execution_binding": True,
            "r_runtime_normalization": True,
            "reproducible_statistical_packages": True,
        },
        "runtime_normalizers": {
            "sc-runtime-r@1.0.0": [
                "descriptive_summary",
                "quantile_summary",
                "correlation_matrix",
                "linear_regression",
                "t_test",
                "one_way_anova",
            ]
        },
        "integration": {
            "research_lab_primary_statistical_workflow": True,
            "workbench_interactive_statistical_workflow": True,
            "workspace_orchestrates_statistical_jobs": True,
            "core_owns_statistical_objects_and_provenance": True,
            "runtime_provider_executes_methods": True,
        },
        "boundaries": {
            "core_executes_statistical_methods": False,
            "core_selects_statistical_method": False,
            "core_interprets_significance_as_truth": False,
            "core_certifies_assumptions": False,
            "core_certifies_statistical_validity": False,
            "core_owns_identity_lineage_and_result_contracts": True,
        },
        "reference": {
            "analysis_plan_id": reference.plan.analysis_plan_id,
            "analysis_result_id": reference.results[0].analysis_result_id,
            "package_id": reference.package_id,
            "package_fingerprint_sha256": reference.fingerprint(),
        },
    }
