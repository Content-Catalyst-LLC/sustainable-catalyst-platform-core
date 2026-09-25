from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.42.0"
CONTRACT_VERSION = "sc.core.verification-reproduction-engine.v1"

ENVIRONMENT_PACKAGE_CONTRACT = "sc.core.reproducible-environment-package.v1"
CROSS_RUNTIME_WORKFLOW_CONTRACT = "sc.core.cross-runtime-research-workflow.v1"
RUNTIME_INTERCHANGE_CONTRACT = "sc.core.runtime-data-interchange.v1"
SCIENTIFIC_REGISTRY_CONTRACT = "sc.core.scientific-result-artifact-registry.v1"
STATISTICAL_ANALYSIS_CONTRACT = "sc.core.statistical-analysis-object.v1"
COMPUTATIONAL_JOB_CONTRACT = "sc.core.computational-job.v1"
EXECUTION_ENVIRONMENT_CONTRACT = "sc.core.execution-environment-provenance.v1"


class ReproductionScope(str, Enum):
    environment = "environment"
    runtime_job = "runtime-job"
    workflow = "workflow"
    statistical_analysis = "statistical-analysis"
    scientific_artifact = "scientific-artifact"
    full_research_package = "full-research-package"


class ReproductionState(str, Enum):
    declared = "declared"
    ready = "ready"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class VerificationCriterionType(str, Enum):
    exact_hash = "exact-hash"
    schema_equivalence = "schema-equivalence"
    runtime_version = "runtime-version"
    dependency_version = "dependency-version"
    row_count = "row-count"
    column_count = "column-count"
    numeric_tolerance = "numeric-tolerance"
    categorical_equivalence = "categorical-equivalence"
    statistical_equivalence = "statistical-equivalence"
    workflow_completion = "workflow-completion"
    artifact_presence = "artifact-presence"
    result_presence = "result-presence"
    custom = "custom"


class VerificationSeverity(str, Enum):
    required = "required"
    advisory = "advisory"


class VerificationOutcome(str, Enum):
    not_run = "not-run"
    passed = "passed"
    warning = "warning"
    failed = "failed"
    unavailable = "unavailable"


class ReproductionComparisonStatus(str, Enum):
    equivalent = "equivalent"
    equivalent_with_warnings = "equivalent-with-warnings"
    non_equivalent = "non-equivalent"
    indeterminate = "indeterminate"


class EvidenceKind(str, Enum):
    content_hash = "content-hash"
    schema_fingerprint = "schema-fingerprint"
    runtime_identity = "runtime-identity"
    dependency_manifest = "dependency-manifest"
    scalar = "scalar"
    metric = "metric"
    table = "table"
    artifact = "artifact"
    log = "log"
    provenance = "provenance"
    other = "other"


class VerificationCriterion(BaseModel):
    criterion_id: str = Field(min_length=2, max_length=500)
    criterion_type: VerificationCriterionType
    name: str = Field(min_length=1, max_length=500)
    severity: VerificationSeverity = VerificationSeverity.required
    source_ref: str | None = Field(default=None, max_length=1000)
    expected_value: Any | None = None
    tolerance: float | None = Field(default=None, ge=0.0)
    unit: str | None = Field(default=None, max_length=200)
    comparator_ref: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_criterion(self):
        if self.criterion_type == VerificationCriterionType.numeric_tolerance:
            if self.tolerance is None:
                raise ValueError("numeric-tolerance criterion requires tolerance")
        if self.criterion_type == VerificationCriterionType.exact_hash:
            if not isinstance(self.expected_value, str):
                raise ValueError("exact-hash criterion requires expected hash")
            value = self.expected_value
            if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise ValueError("exact-hash expected value must be lowercase SHA-256")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReproductionTarget(BaseModel):
    target_id: str = Field(min_length=2, max_length=500)
    scope: ReproductionScope
    source_object_ref: str = Field(min_length=2, max_length=1000)
    source_contract: str = Field(min_length=2, max_length=300)
    source_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    environment_package_ref: str | None = Field(default=None, max_length=1000)
    workflow_ref: str | None = Field(default=None, max_length=1000)
    scientific_registry_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReproductionPlan(BaseModel):
    reproduction_plan_id: str = Field(min_length=2, max_length=500)
    name: str = Field(min_length=1, max_length=500)
    target: ReproductionTarget
    criteria: list[VerificationCriterion] = Field(default_factory=list)
    reproduction_environment_package_ref: str = Field(min_length=2, max_length=1000)
    execution_host_ref: str | None = Field(default=None, max_length=500)
    computational_job_refs: list[str] = Field(default_factory=list)
    workflow_run_ref: str | None = Field(default=None, max_length=1000)
    expected_artifact_refs: list[str] = Field(default_factory=list)
    expected_result_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_plan(self):
        ids = [item.criterion_id for item in self.criteria]
        if len(ids) != len(set(ids)):
            raise ValueError("verification criterion ids must be unique")
        if not self.criteria:
            raise ValueError("reproduction plan requires verification criteria")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class VerificationEvidence(BaseModel):
    evidence_id: str = Field(min_length=2, max_length=500)
    criterion_ref: str = Field(min_length=2, max_length=500)
    kind: EvidenceKind
    source_ref: str = Field(min_length=2, max_length=1000)
    observed_value: Any | None = None
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("collected_at", None)
        return canonical_sha256(payload)


class CriterionVerificationResult(BaseModel):
    criterion_ref: str = Field(min_length=2, max_length=500)
    outcome: VerificationOutcome
    evidence_refs: list[str] = Field(default_factory=list)
    expected_value: Any | None = None
    observed_value: Any | None = None
    absolute_difference: float | None = Field(default=None, ge=0.0)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReproductionAttempt(BaseModel):
    attempt_id: str = Field(min_length=2, max_length=500)
    reproduction_plan_ref: str = Field(min_length=2, max_length=500)
    reproduction_plan_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    state: ReproductionState = ReproductionState.declared
    reproduced_environment_ref: str | None = Field(default=None, max_length=1000)
    workflow_run_ref: str | None = Field(default=None, max_length=1000)
    computational_job_refs: list[str] = Field(default_factory=list)
    produced_artifact_refs: list[str] = Field(default_factory=list)
    produced_result_refs: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failure_ref: str | None = Field(default=None, max_length=1000)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_attempt(self):
        if self.completed_at is not None and self.state != ReproductionState.completed:
            raise ValueError("completed_at requires completed attempt")
        if self.state == ReproductionState.failed and not self.failure_ref:
            raise ValueError("failed attempt requires failure_ref")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        for key in ("state", "started_at", "completed_at", "failure_ref"):
            payload.pop(key, None)
        return canonical_sha256(payload)


class ReproductionVerificationReport(BaseModel):
    report_id: str = Field(min_length=2, max_length=500)
    reproduction_plan_ref: str = Field(min_length=2, max_length=500)
    reproduction_attempt_ref: str = Field(min_length=2, max_length=500)
    criterion_results: list[CriterionVerificationResult] = Field(default_factory=list)
    evidence: list[VerificationEvidence] = Field(default_factory=list)
    overall_outcome: VerificationOutcome = VerificationOutcome.not_run
    required_criteria_passed: bool = False
    advisory_warnings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_report(self):
        criterion_refs = [item.criterion_ref for item in self.criterion_results]
        if len(criterion_refs) != len(set(criterion_refs)):
            raise ValueError("criterion verification results must be unique by criterion_ref")

        evidence_ids = [item.evidence_id for item in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("verification evidence ids must be unique")

        known_evidence = set(evidence_ids)
        for result in self.criterion_results:
            if not set(result.evidence_refs).issubset(known_evidence):
                raise ValueError("criterion verification result references unknown evidence")

        if self.overall_outcome == VerificationOutcome.passed and not self.required_criteria_passed:
            raise ValueError("passed verification requires required criteria to pass")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "report_id": self.report_id,
            "reproduction_plan_ref": self.reproduction_plan_ref,
            "reproduction_attempt_ref": self.reproduction_attempt_ref,
            "criterion_result_fingerprints": sorted(
                item.fingerprint() for item in self.criterion_results
            ),
            "evidence_fingerprints": sorted(
                item.fingerprint() for item in self.evidence
            ),
            "overall_outcome": self.overall_outcome.value,
            "required_criteria_passed": self.required_criteria_passed,
            "advisory_warnings": sorted(self.advisory_warnings),
            "notes": self.notes,
            "metadata": self.metadata,
        })


class ReproductionComparison(BaseModel):
    comparison_id: str = Field(min_length=2, max_length=500)
    source_target_ref: str = Field(min_length=2, max_length=1000)
    reproduction_attempt_ref: str = Field(min_length=2, max_length=500)
    verification_report_ref: str = Field(min_length=2, max_length=500)
    status: ReproductionComparisonStatus
    matched_artifact_refs: list[str] = Field(default_factory=list)
    mismatched_artifact_refs: list[str] = Field(default_factory=list)
    matched_result_refs: list[str] = Field(default_factory=list)
    mismatched_result_refs: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReproductionPackage(BaseModel):
    package_id: str = Field(min_length=2, max_length=500)
    plan: ReproductionPlan
    attempts: list[ReproductionAttempt] = Field(default_factory=list)
    reports: list[ReproductionVerificationReport] = Field(default_factory=list)
    comparisons: list[ReproductionComparison] = Field(default_factory=list)
    source_object_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_package(self):
        if not self.attempts:
            raise ValueError("reproduction package requires at least one attempt")

        attempt_ids = [item.attempt_id for item in self.attempts]
        report_ids = [item.report_id for item in self.reports]
        comparison_ids = [item.comparison_id for item in self.comparisons]

        if len(attempt_ids) != len(set(attempt_ids)):
            raise ValueError("reproduction attempt ids must be unique")
        if len(report_ids) != len(set(report_ids)):
            raise ValueError("reproduction report ids must be unique")
        if len(comparison_ids) != len(set(comparison_ids)):
            raise ValueError("reproduction comparison ids must be unique")

        attempts = {item.attempt_id: item for item in self.attempts}
        reports = {item.report_id: item for item in self.reports}

        for attempt in self.attempts:
            if attempt.reproduction_plan_ref != self.plan.reproduction_plan_id:
                raise ValueError("attempt references wrong reproduction plan")
            if attempt.reproduction_plan_fingerprint_sha256 != self.plan.fingerprint():
                raise ValueError("attempt reproduction plan fingerprint mismatch")

        for report in self.reports:
            if report.reproduction_plan_ref != self.plan.reproduction_plan_id:
                raise ValueError("verification report references wrong plan")
            if report.reproduction_attempt_ref not in attempts:
                raise ValueError("verification report references unknown attempt")

        for comparison in self.comparisons:
            if comparison.reproduction_attempt_ref not in attempts:
                raise ValueError("comparison references unknown attempt")
            if comparison.verification_report_ref not in reports:
                raise ValueError("comparison references unknown verification report")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "package_id": self.package_id,
            "plan_fingerprint_sha256": self.plan.fingerprint(),
            "attempt_fingerprints": sorted(item.fingerprint() for item in self.attempts),
            "report_fingerprints": sorted(item.fingerprint() for item in self.reports),
            "comparison_fingerprints": sorted(item.fingerprint() for item in self.comparisons),
            "source_object_refs": sorted(self.source_object_refs),
            "metadata": self.metadata,
        })


def verify_criterion(
    criterion: VerificationCriterion,
    evidence: VerificationEvidence,
) -> CriterionVerificationResult:
    if evidence.criterion_ref != criterion.criterion_id:
        raise ValueError("verification evidence criterion_ref mismatch")

    expected = criterion.expected_value
    observed = evidence.observed_value
    outcome = VerificationOutcome.unavailable
    difference: float | None = None
    notes: list[str] = []

    if criterion.criterion_type == VerificationCriterionType.exact_hash:
        observed_hash = evidence.content_sha256 or str(observed or "")
        outcome = (
            VerificationOutcome.passed
            if observed_hash == expected
            else VerificationOutcome.failed
        )
    elif criterion.criterion_type in {
        VerificationCriterionType.runtime_version,
        VerificationCriterionType.dependency_version,
        VerificationCriterionType.row_count,
        VerificationCriterionType.column_count,
        VerificationCriterionType.categorical_equivalence,
        VerificationCriterionType.workflow_completion,
        VerificationCriterionType.artifact_presence,
        VerificationCriterionType.result_presence,
        VerificationCriterionType.schema_equivalence,
    }:
        outcome = (
            VerificationOutcome.passed
            if observed == expected
            else VerificationOutcome.failed
        )
    elif criterion.criterion_type in {
        VerificationCriterionType.numeric_tolerance,
        VerificationCriterionType.statistical_equivalence,
    }:
        try:
            exp = float(expected)
            obs = float(observed)
        except (TypeError, ValueError):
            outcome = VerificationOutcome.unavailable
            notes.append("numeric criterion requires numeric expected and observed values")
        else:
            difference = abs(obs - exp)
            tolerance = criterion.tolerance or 0.0
            outcome = (
                VerificationOutcome.passed
                if difference <= tolerance
                else VerificationOutcome.failed
            )
    else:
        outcome = VerificationOutcome.warning
        notes.append("custom criterion requires external comparator")

    return CriterionVerificationResult(
        criterion_ref=criterion.criterion_id,
        outcome=outcome,
        evidence_refs=[evidence.evidence_id],
        expected_value=expected,
        observed_value=observed,
        absolute_difference=difference,
        notes=notes,
    )


def assemble_verification_report(
    *,
    report_id: str,
    plan: ReproductionPlan,
    attempt: ReproductionAttempt,
    evidence: list[VerificationEvidence],
) -> ReproductionVerificationReport:
    evidence_by_criterion: dict[str, VerificationEvidence] = {}
    for item in evidence:
        if item.criterion_ref in evidence_by_criterion:
            raise ValueError("only one primary evidence item per criterion is supported in v1")
        evidence_by_criterion[item.criterion_ref] = item

    results: list[CriterionVerificationResult] = []
    advisory_warnings: list[str] = []
    required_passed = True

    for criterion in plan.criteria:
        item = evidence_by_criterion.get(criterion.criterion_id)
        if item is None:
            result = CriterionVerificationResult(
                criterion_ref=criterion.criterion_id,
                outcome=VerificationOutcome.unavailable,
                notes=["verification evidence unavailable"],
            )
        else:
            result = verify_criterion(criterion, item)
        results.append(result)

        if criterion.severity == VerificationSeverity.required:
            if result.outcome != VerificationOutcome.passed:
                required_passed = False
        elif result.outcome != VerificationOutcome.passed:
            advisory_warnings.append(
                f"{criterion.criterion_id}:{result.outcome.value}"
            )

    if required_passed and advisory_warnings:
        overall = VerificationOutcome.warning
    elif required_passed:
        overall = VerificationOutcome.passed
    else:
        overall = VerificationOutcome.failed

    return ReproductionVerificationReport(
        report_id=report_id,
        reproduction_plan_ref=plan.reproduction_plan_id,
        reproduction_attempt_ref=attempt.attempt_id,
        criterion_results=results,
        evidence=evidence,
        overall_outcome=overall,
        required_criteria_passed=required_passed,
        advisory_warnings=advisory_warnings,
        metadata={
            "engine_contract": CONTRACT_VERSION,
            "core_executed_reproduction": False,
        },
    )


def compare_reproduction(
    *,
    comparison_id: str,
    plan: ReproductionPlan,
    attempt: ReproductionAttempt,
    report: ReproductionVerificationReport,
) -> ReproductionComparison:
    if report.reproduction_attempt_ref != attempt.attempt_id:
        raise ValueError("comparison report/attempt mismatch")
    if report.reproduction_plan_ref != plan.reproduction_plan_id:
        raise ValueError("comparison report/plan mismatch")

    expected_artifacts = set(plan.expected_artifact_refs)
    produced_artifacts = set(attempt.produced_artifact_refs)
    expected_results = set(plan.expected_result_refs)
    produced_results = set(attempt.produced_result_refs)

    matched_artifacts = sorted(expected_artifacts & produced_artifacts)
    mismatched_artifacts = sorted(expected_artifacts - produced_artifacts)
    matched_results = sorted(expected_results & produced_results)
    mismatched_results = sorted(expected_results - produced_results)

    if report.overall_outcome == VerificationOutcome.passed and not (
        mismatched_artifacts or mismatched_results
    ):
        status = ReproductionComparisonStatus.equivalent
    elif report.overall_outcome == VerificationOutcome.warning and not (
        mismatched_artifacts or mismatched_results
    ):
        status = ReproductionComparisonStatus.equivalent_with_warnings
    elif report.overall_outcome == VerificationOutcome.failed or (
        mismatched_artifacts or mismatched_results
    ):
        status = ReproductionComparisonStatus.non_equivalent
    else:
        status = ReproductionComparisonStatus.indeterminate

    return ReproductionComparison(
        comparison_id=comparison_id,
        source_target_ref=plan.target.source_object_ref,
        reproduction_attempt_ref=attempt.attempt_id,
        verification_report_ref=report.report_id,
        status=status,
        matched_artifact_refs=matched_artifacts,
        mismatched_artifact_refs=mismatched_artifacts,
        matched_result_refs=matched_results,
        mismatched_result_refs=mismatched_results,
        metadata={
            "comparison_is_descriptive": True,
            "core_certifies_scientific_validity": False,
        },
    )


def to_scientific_reproduction_artifact(
    package: ReproductionPackage,
) -> dict[str, Any]:
    return {
        "artifact_id": f"scientific-artifact:{package.package_id}",
        "artifact_kind": "package",
        "uri": f"core-ref://{package.package_id}",
        "content_sha256": package.fingerprint(),
        "media_type": "application/vnd.sustainable-catalyst.reproduction-package+json",
        "source_contract": CONTRACT_VERSION,
        "source_object_ref": package.package_id,
        "metadata": {
            "reproduction_plan_ref": package.plan.reproduction_plan_id,
            "reproduction_scope": package.plan.target.scope.value,
            "attempt_count": len(package.attempts),
            "verification_report_count": len(package.reports),
            "comparison_count": len(package.comparisons),
        },
    }


def reference_reproduction_package() -> ReproductionPackage:
    target = ReproductionTarget(
        target_id="reproduction-target:reference-r-julia-workflow:v1",
        scope=ReproductionScope.full_research_package,
        source_object_ref="cross-runtime-workflow-package:reference-r-julia:v1",
        source_contract=CROSS_RUNTIME_WORKFLOW_CONTRACT,
        source_fingerprint_sha256="d" * 64,
        environment_package_ref="environment-package:reference-r-julia:v1",
        workflow_ref="cross-runtime-workflow:reference-r-julia:v1",
        scientific_registry_ref="scientific-registry:cross-runtime-reference:v1",
    )

    criteria = [
        VerificationCriterion(
            criterion_id="criterion:environment-package-hash",
            criterion_type=VerificationCriterionType.exact_hash,
            name="Environment package fingerprint matches",
            source_ref="environment-package:reference-r-julia:v1",
            expected_value="e" * 64,
        ),
        VerificationCriterion(
            criterion_id="criterion:r-runtime-version",
            criterion_type=VerificationCriterionType.runtime_version,
            name="R runtime version matches",
            source_ref="sc-runtime-r",
            expected_value="1.0.0",
        ),
        VerificationCriterion(
            criterion_id="criterion:julia-runtime-version",
            criterion_type=VerificationCriterionType.runtime_version,
            name="Julia runtime version matches",
            source_ref="catalyst-julia-runtime",
            expected_value="0.3.0",
        ),
        VerificationCriterion(
            criterion_id="criterion:workflow-completed",
            criterion_type=VerificationCriterionType.workflow_completion,
            name="Cross-runtime workflow completed",
            source_ref="cross-runtime-workflow-run:reference-r-julia:reproduction-001",
            expected_value="completed",
        ),
        VerificationCriterion(
            criterion_id="criterion:regression-slope",
            criterion_type=VerificationCriterionType.numeric_tolerance,
            name="Regression slope reproduced within tolerance",
            source_ref="stat-result:reference-regression:001:slope",
            expected_value=2.0,
            tolerance=1e-10,
        ),
        VerificationCriterion(
            criterion_id="criterion:final-artifact-present",
            criterion_type=VerificationCriterionType.artifact_presence,
            name="Final scientific artifact exists",
            source_ref="scientific-artifact:cross-runtime-reference-package",
            expected_value=True,
        ),
    ]

    plan = ReproductionPlan(
        reproduction_plan_id="reproduction-plan:reference-r-julia:v1",
        name="Reproduce Reference R-to-Julia Research Workflow",
        target=target,
        criteria=criteria,
        reproduction_environment_package_ref="environment-package:reference-r-julia:v1",
        execution_host_ref="workspace-execution-host:reference",
        computational_job_refs=[
            "job:reproduction-r-regression",
            "job:reproduction-julia-matrix",
            "job:reproduction-verification",
        ],
        workflow_run_ref="cross-runtime-workflow-run:reference-r-julia:reproduction-001",
        expected_artifact_refs=[
            "scientific-artifact:cross-runtime-reference-package",
        ],
        expected_result_refs=[
            "stat-result:reference-regression:001",
            "runtime-result:reference-julia-matrix",
        ],
        provenance={
            "plan_source_release": CORE_RELEASE,
            "core_executes_reproduction": False,
        },
    )

    attempt = ReproductionAttempt(
        attempt_id="reproduction-attempt:reference-r-julia:001",
        reproduction_plan_ref=plan.reproduction_plan_id,
        reproduction_plan_fingerprint_sha256=plan.fingerprint(),
        state=ReproductionState.completed,
        reproduced_environment_ref="environment:reproduced-reference-r-julia:001",
        workflow_run_ref="cross-runtime-workflow-run:reference-r-julia:reproduction-001",
        computational_job_refs=[
            "job:reproduction-r-regression",
            "job:reproduction-julia-matrix",
            "job:reproduction-verification",
        ],
        produced_artifact_refs=[
            "scientific-artifact:cross-runtime-reference-package",
        ],
        produced_result_refs=[
            "stat-result:reference-regression:001",
            "runtime-result:reference-julia-matrix",
        ],
        started_at=datetime(2026, 9, 25, 10, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 9, 25, 10, 5, tzinfo=timezone.utc),
        provenance={
            "execution_owner": "workspace-or-execution-host",
            "core_executed_reproduction": False,
        },
    )

    evidence = [
        VerificationEvidence(
            evidence_id="evidence:environment-package-hash",
            criterion_ref="criterion:environment-package-hash",
            kind=EvidenceKind.content_hash,
            source_ref="environment:reproduced-reference-r-julia:001",
            observed_value="e" * 64,
            content_sha256="e" * 64,
        ),
        VerificationEvidence(
            evidence_id="evidence:r-runtime-version",
            criterion_ref="criterion:r-runtime-version",
            kind=EvidenceKind.runtime_identity,
            source_ref="sc-runtime-r",
            observed_value="1.0.0",
        ),
        VerificationEvidence(
            evidence_id="evidence:julia-runtime-version",
            criterion_ref="criterion:julia-runtime-version",
            kind=EvidenceKind.runtime_identity,
            source_ref="catalyst-julia-runtime",
            observed_value="0.3.0",
        ),
        VerificationEvidence(
            evidence_id="evidence:workflow-completed",
            criterion_ref="criterion:workflow-completed",
            kind=EvidenceKind.provenance,
            source_ref="cross-runtime-workflow-run:reference-r-julia:reproduction-001",
            observed_value="completed",
        ),
        VerificationEvidence(
            evidence_id="evidence:regression-slope",
            criterion_ref="criterion:regression-slope",
            kind=EvidenceKind.metric,
            source_ref="stat-result:reference-regression:001:slope",
            observed_value=2.0,
        ),
        VerificationEvidence(
            evidence_id="evidence:final-artifact-present",
            criterion_ref="criterion:final-artifact-present",
            kind=EvidenceKind.artifact,
            source_ref="scientific-artifact:cross-runtime-reference-package",
            observed_value=True,
        ),
    ]

    report = assemble_verification_report(
        report_id="reproduction-verification-report:reference-r-julia:001",
        plan=plan,
        attempt=attempt,
        evidence=evidence,
    )

    comparison = compare_reproduction(
        comparison_id="reproduction-comparison:reference-r-julia:001",
        plan=plan,
        attempt=attempt,
        report=report,
    )

    return ReproductionPackage(
        package_id="reproduction-package:reference-r-julia:v1",
        plan=plan,
        attempts=[attempt],
        reports=[report],
        comparisons=[comparison],
        source_object_refs=[
            "environment-package-bundle:reference-r-julia:v1",
            "cross-runtime-workflow-package:reference-r-julia:v1",
            "scientific-registry-package:reference-regression:v1",
        ],
        metadata={
            "portable": True,
            "verification_engine": CONTRACT_VERSION,
            "reference_is_contract_proof": True,
        },
    )


def contract_document() -> dict[str, Any]:
    reference = reference_reproduction_package()
    report = reference.reports[0]
    comparison = reference.comparisons[0]

    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            ENVIRONMENT_PACKAGE_CONTRACT,
            CROSS_RUNTIME_WORKFLOW_CONTRACT,
            RUNTIME_INTERCHANGE_CONTRACT,
            SCIENTIFIC_REGISTRY_CONTRACT,
            STATISTICAL_ANALYSIS_CONTRACT,
            COMPUTATIONAL_JOB_CONTRACT,
            EXECUTION_ENVIRONMENT_CONTRACT,
        ],
        "object_types": [
            "VerificationCriterion",
            "ReproductionTarget",
            "ReproductionPlan",
            "VerificationEvidence",
            "CriterionVerificationResult",
            "ReproductionAttempt",
            "ReproductionVerificationReport",
            "ReproductionComparison",
            "ReproductionPackage",
        ],
        "capabilities": {
            "reproduction_targets": True,
            "verification_criteria": True,
            "exact_hash_verification": True,
            "runtime_version_verification": True,
            "dependency_version_verification": True,
            "schema_equivalence_verification": True,
            "numeric_tolerance_verification": True,
            "statistical_equivalence_verification": True,
            "artifact_and_result_presence_verification": True,
            "evidence_capture": True,
            "verification_report_assembly": True,
            "reproduction_comparison": True,
            "portable_reproduction_packages": True,
            "scientific_registry_bridge": True,
        },
        "integration": {
            "reproducible_environment_packages": True,
            "cross_runtime_workflows": True,
            "runtime_data_interchange": True,
            "scientific_result_registry": True,
            "statistical_analysis_objects": True,
            "workspace_or_execution_host_executes_reproduction": True,
            "core_executes_reproduction": False,
        },
        "boundaries": {
            "core_launches_reproduction_jobs": False,
            "core_builds_reproduction_environment": False,
            "core_reexecutes_runtime_steps": False,
            "core_declares_equivalence_without_evidence": False,
            "core_certifies_scientific_validity": False,
            "core_owns_reproduction_plans_criteria_evidence_reports_and_comparisons": True,
        },
        "reference": {
            "package_id": reference.package_id,
            "plan_id": reference.plan.reproduction_plan_id,
            "attempt_id": reference.attempts[0].attempt_id,
            "verification_outcome": report.overall_outcome.value,
            "required_criteria_passed": report.required_criteria_passed,
            "comparison_status": comparison.status.value,
            "package_fingerprint_sha256": reference.fingerprint(),
        },
    }
