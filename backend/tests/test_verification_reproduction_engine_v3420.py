from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.verification_reproduction_engine import (
    CONTRACT_VERSION,
    CriterionVerificationResult,
    EvidenceKind,
    ReproductionAttempt,
    ReproductionComparisonStatus,
    ReproductionPackage,
    ReproductionPlan,
    ReproductionScope,
    ReproductionState,
    ReproductionTarget,
    ReproductionVerificationReport,
    VerificationCriterion,
    VerificationCriterionType,
    VerificationEvidence,
    VerificationOutcome,
    VerificationSeverity,
    assemble_verification_report,
    compare_reproduction,
    contract_document,
    reference_reproduction_package,
    to_scientific_reproduction_artifact,
    verify_criterion,
)


def ref_package():
    return reference_reproduction_package()


def ref_plan():
    return ref_package().plan


def ref_attempt():
    return ref_package().attempts[0]


def ref_report():
    return ref_package().reports[0]


def test_contract_identity():
    doc = contract_document()
    assert doc["release"] == "3.42.0"
    assert doc["contract"] == CONTRACT_VERSION


def test_contract_links_environment_packages():
    assert "sc.core.reproducible-environment-package.v1" in contract_document()["depends_on"]


def test_contract_links_cross_runtime_workflows():
    assert "sc.core.cross-runtime-research-workflow.v1" in contract_document()["depends_on"]


def test_contract_links_scientific_registry():
    assert "sc.core.scientific-result-artifact-registry.v1" in contract_document()["depends_on"]


def test_reference_package_is_valid():
    package = ref_package()
    assert package.plan.criteria
    assert package.attempts
    assert package.reports
    assert package.comparisons


def test_reference_scope_is_full_research_package():
    assert ref_plan().target.scope == ReproductionScope.full_research_package


def test_reference_verification_passes():
    report = ref_report()
    assert report.overall_outcome == VerificationOutcome.passed
    assert report.required_criteria_passed is True


def test_reference_comparison_equivalent():
    assert ref_package().comparisons[0].status == ReproductionComparisonStatus.equivalent


def test_exact_hash_criterion_requires_hash():
    with pytest.raises(ValidationError):
        VerificationCriterion(
            criterion_id="criterion:test",
            criterion_type=VerificationCriterionType.exact_hash,
            name="hash",
            expected_value="bad",
        )


def test_numeric_tolerance_requires_tolerance():
    with pytest.raises(ValidationError):
        VerificationCriterion(
            criterion_id="criterion:test",
            criterion_type=VerificationCriterionType.numeric_tolerance,
            name="numeric",
            expected_value=1.0,
        )


def test_criterion_fingerprint_stable():
    criterion = ref_plan().criteria[0]
    assert criterion.fingerprint() == deepcopy(criterion).fingerprint()


def test_target_requires_sha256():
    with pytest.raises(ValidationError):
        ReproductionTarget(
            target_id="target:test",
            scope=ReproductionScope.workflow,
            source_object_ref="workflow:test",
            source_contract="contract:test",
            source_fingerprint_sha256="abc",
        )


def test_target_fingerprint_stable():
    target = ref_plan().target
    assert target.fingerprint() == deepcopy(target).fingerprint()


def test_plan_requires_criteria():
    data = ref_plan().model_dump(mode="python")
    data["criteria"] = []
    with pytest.raises(ValidationError):
        ReproductionPlan.model_validate(data)


def test_plan_rejects_duplicate_criterion_ids():
    data = ref_plan().model_dump(mode="python")
    data["criteria"] = [data["criteria"][0], deepcopy(data["criteria"][0])]
    with pytest.raises(ValidationError):
        ReproductionPlan.model_validate(data)


def test_plan_fingerprint_stable():
    plan = ref_plan()
    assert plan.fingerprint() == deepcopy(plan).fingerprint()
    assert len(plan.fingerprint()) == 64


def test_evidence_requires_hash_when_hash_supplied():
    with pytest.raises(ValidationError):
        VerificationEvidence(
            evidence_id="evidence:test",
            criterion_ref="criterion:test",
            kind=EvidenceKind.content_hash,
            source_ref="artifact:test",
            content_sha256="bad",
        )


def test_evidence_fingerprint_ignores_collected_at():
    evidence = ref_report().evidence[0]
    assert evidence.fingerprint() == deepcopy(evidence).fingerprint()


def test_attempt_rejects_completed_at_when_not_completed():
    attempt = ref_attempt().model_dump(mode="python")
    attempt["state"] = "running"
    with pytest.raises(ValidationError):
        ReproductionAttempt.model_validate(attempt)


def test_failed_attempt_requires_failure_ref():
    attempt = ref_attempt().model_dump(mode="python")
    attempt["state"] = "failed"
    attempt["completed_at"] = None
    attempt["failure_ref"] = None
    with pytest.raises(ValidationError):
        ReproductionAttempt.model_validate(attempt)


def test_attempt_fingerprint_ignores_lifecycle():
    attempt = ref_attempt()
    other = deepcopy(attempt)
    other.state = ReproductionState.running
    other.started_at = None
    other.completed_at = None
    other.failure_ref = None
    assert attempt.fingerprint() == other.fingerprint()


def test_verify_exact_hash_pass():
    criterion = VerificationCriterion(
        criterion_id="criterion:hash",
        criterion_type=VerificationCriterionType.exact_hash,
        name="hash",
        expected_value="a" * 64,
    )
    evidence = VerificationEvidence(
        evidence_id="evidence:hash",
        criterion_ref=criterion.criterion_id,
        kind=EvidenceKind.content_hash,
        source_ref="artifact:test",
        content_sha256="a" * 64,
    )
    result = verify_criterion(criterion, evidence)
    assert result.outcome == VerificationOutcome.passed


def test_verify_exact_hash_fail():
    criterion = VerificationCriterion(
        criterion_id="criterion:hash",
        criterion_type=VerificationCriterionType.exact_hash,
        name="hash",
        expected_value="a" * 64,
    )
    evidence = VerificationEvidence(
        evidence_id="evidence:hash",
        criterion_ref=criterion.criterion_id,
        kind=EvidenceKind.content_hash,
        source_ref="artifact:test",
        content_sha256="b" * 64,
    )
    assert verify_criterion(criterion, evidence).outcome == VerificationOutcome.failed


def test_verify_runtime_version_pass():
    criterion = VerificationCriterion(
        criterion_id="criterion:runtime",
        criterion_type=VerificationCriterionType.runtime_version,
        name="runtime",
        expected_value="1.0.0",
    )
    evidence = VerificationEvidence(
        evidence_id="evidence:runtime",
        criterion_ref=criterion.criterion_id,
        kind=EvidenceKind.runtime_identity,
        source_ref="runtime:test",
        observed_value="1.0.0",
    )
    assert verify_criterion(criterion, evidence).outcome == VerificationOutcome.passed


def test_verify_runtime_version_fail():
    criterion = VerificationCriterion(
        criterion_id="criterion:runtime",
        criterion_type=VerificationCriterionType.runtime_version,
        name="runtime",
        expected_value="1.0.0",
    )
    evidence = VerificationEvidence(
        evidence_id="evidence:runtime",
        criterion_ref=criterion.criterion_id,
        kind=EvidenceKind.runtime_identity,
        source_ref="runtime:test",
        observed_value="2.0.0",
    )
    assert verify_criterion(criterion, evidence).outcome == VerificationOutcome.failed


def test_verify_row_count_pass():
    criterion = VerificationCriterion(
        criterion_id="criterion:rows",
        criterion_type=VerificationCriterionType.row_count,
        name="rows",
        expected_value=10,
    )
    evidence = VerificationEvidence(
        evidence_id="evidence:rows",
        criterion_ref=criterion.criterion_id,
        kind=EvidenceKind.scalar,
        source_ref="table:test",
        observed_value=10,
    )
    assert verify_criterion(criterion, evidence).outcome == VerificationOutcome.passed


def test_verify_numeric_tolerance_pass():
    criterion = VerificationCriterion(
        criterion_id="criterion:numeric",
        criterion_type=VerificationCriterionType.numeric_tolerance,
        name="numeric",
        expected_value=2.0,
        tolerance=0.01,
    )
    evidence = VerificationEvidence(
        evidence_id="evidence:numeric",
        criterion_ref=criterion.criterion_id,
        kind=EvidenceKind.metric,
        source_ref="result:test",
        observed_value=2.005,
    )
    result = verify_criterion(criterion, evidence)
    assert result.outcome == VerificationOutcome.passed
    assert result.absolute_difference == pytest.approx(0.005)


def test_verify_numeric_tolerance_fail():
    criterion = VerificationCriterion(
        criterion_id="criterion:numeric",
        criterion_type=VerificationCriterionType.numeric_tolerance,
        name="numeric",
        expected_value=2.0,
        tolerance=0.01,
    )
    evidence = VerificationEvidence(
        evidence_id="evidence:numeric",
        criterion_ref=criterion.criterion_id,
        kind=EvidenceKind.metric,
        source_ref="result:test",
        observed_value=2.1,
    )
    assert verify_criterion(criterion, evidence).outcome == VerificationOutcome.failed


def test_verify_numeric_unavailable_for_non_numeric():
    criterion = VerificationCriterion(
        criterion_id="criterion:numeric",
        criterion_type=VerificationCriterionType.numeric_tolerance,
        name="numeric",
        expected_value=2.0,
        tolerance=0.01,
    )
    evidence = VerificationEvidence(
        evidence_id="evidence:numeric",
        criterion_ref=criterion.criterion_id,
        kind=EvidenceKind.metric,
        source_ref="result:test",
        observed_value="not-a-number",
    )
    result = verify_criterion(criterion, evidence)
    assert result.outcome == VerificationOutcome.unavailable


def test_verify_custom_returns_warning():
    criterion = VerificationCriterion(
        criterion_id="criterion:custom",
        criterion_type=VerificationCriterionType.custom,
        name="custom",
    )
    evidence = VerificationEvidence(
        evidence_id="evidence:custom",
        criterion_ref=criterion.criterion_id,
        kind=EvidenceKind.other,
        source_ref="evidence:test",
    )
    assert verify_criterion(criterion, evidence).outcome == VerificationOutcome.warning


def test_verify_rejects_evidence_criterion_mismatch():
    criterion = ref_plan().criteria[0]
    evidence = deepcopy(ref_report().evidence[0])
    evidence.criterion_ref = "criterion:other"
    with pytest.raises(ValueError):
        verify_criterion(criterion, evidence)


def test_criterion_result_fingerprint_stable():
    result = ref_report().criterion_results[0]
    assert result.fingerprint() == deepcopy(result).fingerprint()


def test_report_rejects_duplicate_criterion_results():
    report = ref_report().model_dump(mode="python")
    report["criterion_results"] = [
        report["criterion_results"][0],
        deepcopy(report["criterion_results"][0]),
    ]
    with pytest.raises(ValidationError):
        ReproductionVerificationReport.model_validate(report)


def test_report_rejects_duplicate_evidence_ids():
    report = ref_report().model_dump(mode="python")
    report["evidence"] = [report["evidence"][0], deepcopy(report["evidence"][0])]
    with pytest.raises(ValidationError):
        ReproductionVerificationReport.model_validate(report)


def test_report_rejects_unknown_evidence_ref():
    report = ref_report().model_dump(mode="python")
    report["criterion_results"][0]["evidence_refs"] = ["evidence:missing"]
    with pytest.raises(ValidationError):
        ReproductionVerificationReport.model_validate(report)


def test_passed_report_requires_required_criteria_passed():
    report = ref_report().model_dump(mode="python")
    report["required_criteria_passed"] = False
    with pytest.raises(ValidationError):
        ReproductionVerificationReport.model_validate(report)


def test_report_fingerprint_stable():
    report = ref_report()
    assert report.fingerprint() == deepcopy(report).fingerprint()


def test_assemble_report_all_required_pass():
    package = ref_package()
    report = assemble_verification_report(
        report_id="report:test",
        plan=package.plan,
        attempt=package.attempts[0],
        evidence=package.reports[0].evidence,
    )
    assert report.overall_outcome == VerificationOutcome.passed
    assert report.required_criteria_passed is True


def test_assemble_report_missing_required_fails():
    package = ref_package()
    evidence = [
        item for item in package.reports[0].evidence
        if item.criterion_ref != "criterion:r-runtime-version"
    ]
    report = assemble_verification_report(
        report_id="report:test",
        plan=package.plan,
        attempt=package.attempts[0],
        evidence=evidence,
    )
    assert report.overall_outcome == VerificationOutcome.failed
    assert report.required_criteria_passed is False


def test_assemble_report_duplicate_evidence_per_criterion_rejected():
    package = ref_package()
    evidence = list(package.reports[0].evidence)
    evidence.append(deepcopy(evidence[0]).model_copy(update={"evidence_id": "evidence:duplicate"}))
    with pytest.raises(ValueError):
        assemble_verification_report(
            report_id="report:test",
            plan=package.plan,
            attempt=package.attempts[0],
            evidence=evidence,
        )


def test_advisory_failure_produces_warning():
    package = ref_package()
    plan = deepcopy(package.plan)
    advisory = VerificationCriterion(
        criterion_id="criterion:advisory",
        criterion_type=VerificationCriterionType.row_count,
        name="advisory row count",
        severity=VerificationSeverity.advisory,
        expected_value=5,
    )
    plan.criteria.append(advisory)
    evidence = list(package.reports[0].evidence)
    evidence.append(
        VerificationEvidence(
            evidence_id="evidence:advisory",
            criterion_ref=advisory.criterion_id,
            kind=EvidenceKind.scalar,
            source_ref="table:test",
            observed_value=4,
        )
    )
    attempt = deepcopy(package.attempts[0])
    attempt.reproduction_plan_fingerprint_sha256 = plan.fingerprint()
    report = assemble_verification_report(
        report_id="report:advisory",
        plan=plan,
        attempt=attempt,
        evidence=evidence,
    )
    assert report.overall_outcome == VerificationOutcome.warning
    assert report.required_criteria_passed is True
    assert report.advisory_warnings


def test_compare_equivalent_reference():
    package = ref_package()
    comparison = compare_reproduction(
        comparison_id="comparison:test",
        plan=package.plan,
        attempt=package.attempts[0],
        report=package.reports[0],
    )
    assert comparison.status == ReproductionComparisonStatus.equivalent


def test_compare_non_equivalent_when_artifact_missing():
    package = ref_package()
    attempt = deepcopy(package.attempts[0])
    attempt.produced_artifact_refs = []
    comparison = compare_reproduction(
        comparison_id="comparison:test",
        plan=package.plan,
        attempt=attempt,
        report=package.reports[0],
    )
    assert comparison.status == ReproductionComparisonStatus.non_equivalent
    assert comparison.mismatched_artifact_refs


def test_compare_non_equivalent_when_result_missing():
    package = ref_package()
    attempt = deepcopy(package.attempts[0])
    attempt.produced_result_refs = []
    comparison = compare_reproduction(
        comparison_id="comparison:test",
        plan=package.plan,
        attempt=attempt,
        report=package.reports[0],
    )
    assert comparison.status == ReproductionComparisonStatus.non_equivalent


def test_compare_rejects_report_attempt_mismatch():
    package = ref_package()
    report = deepcopy(package.reports[0])
    report.reproduction_attempt_ref = "attempt:other"
    with pytest.raises(ValueError):
        compare_reproduction(
            comparison_id="comparison:test",
            plan=package.plan,
            attempt=package.attempts[0],
            report=report,
        )


def test_compare_rejects_report_plan_mismatch():
    package = ref_package()
    report = deepcopy(package.reports[0])
    report.reproduction_plan_ref = "plan:other"
    with pytest.raises(ValueError):
        compare_reproduction(
            comparison_id="comparison:test",
            plan=package.plan,
            attempt=package.attempts[0],
            report=report,
        )


def test_comparison_fingerprint_stable():
    item = ref_package().comparisons[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_package_requires_attempt():
    package = ref_package()
    with pytest.raises(ValidationError):
        ReproductionPackage(
            package_id="package:test",
            plan=package.plan,
            attempts=[],
        )


def test_package_rejects_duplicate_attempt_ids():
    package = ref_package().model_dump(mode="python")
    package["attempts"] = [package["attempts"][0], deepcopy(package["attempts"][0])]
    with pytest.raises(ValidationError):
        ReproductionPackage.model_validate(package)


def test_package_rejects_duplicate_report_ids():
    package = ref_package().model_dump(mode="python")
    package["reports"] = [package["reports"][0], deepcopy(package["reports"][0])]
    with pytest.raises(ValidationError):
        ReproductionPackage.model_validate(package)


def test_package_rejects_duplicate_comparison_ids():
    package = ref_package().model_dump(mode="python")
    package["comparisons"] = [
        package["comparisons"][0],
        deepcopy(package["comparisons"][0]),
    ]
    with pytest.raises(ValidationError):
        ReproductionPackage.model_validate(package)


def test_package_rejects_attempt_wrong_plan():
    package = ref_package().model_dump(mode="python")
    package["attempts"][0]["reproduction_plan_ref"] = "plan:other"
    with pytest.raises(ValidationError):
        ReproductionPackage.model_validate(package)


def test_package_rejects_attempt_plan_fingerprint_mismatch():
    package = ref_package().model_dump(mode="python")
    package["attempts"][0]["reproduction_plan_fingerprint_sha256"] = "f" * 64
    with pytest.raises(ValidationError):
        ReproductionPackage.model_validate(package)


def test_package_rejects_report_unknown_attempt():
    package = ref_package().model_dump(mode="python")
    package["reports"][0]["reproduction_attempt_ref"] = "attempt:missing"
    with pytest.raises(ValidationError):
        ReproductionPackage.model_validate(package)


def test_package_rejects_report_wrong_plan():
    package = ref_package().model_dump(mode="python")
    package["reports"][0]["reproduction_plan_ref"] = "plan:other"
    with pytest.raises(ValidationError):
        ReproductionPackage.model_validate(package)


def test_package_rejects_comparison_unknown_attempt():
    package = ref_package().model_dump(mode="python")
    package["comparisons"][0]["reproduction_attempt_ref"] = "attempt:missing"
    with pytest.raises(ValidationError):
        ReproductionPackage.model_validate(package)


def test_package_rejects_comparison_unknown_report():
    package = ref_package().model_dump(mode="python")
    package["comparisons"][0]["verification_report_ref"] = "report:missing"
    with pytest.raises(ValidationError):
        ReproductionPackage.model_validate(package)


def test_package_fingerprint_stable():
    package = ref_package()
    assert package.fingerprint() == deepcopy(package).fingerprint()
    assert len(package.fingerprint()) == 64


def test_reference_plan_uses_v341_environment_package():
    assert ref_plan().reproduction_environment_package_ref == "environment-package:reference-r-julia:v1"


def test_reference_target_uses_v340_workflow():
    assert ref_plan().target.workflow_ref == "cross-runtime-workflow:reference-r-julia:v1"


def test_reference_attempt_execution_owner_not_core():
    attempt = ref_attempt()
    assert attempt.provenance["execution_owner"] == "workspace-or-execution-host"
    assert attempt.provenance["core_executed_reproduction"] is False


def test_reference_report_engine_contract():
    assert ref_report().metadata["engine_contract"] == CONTRACT_VERSION


def test_reference_comparison_is_descriptive():
    assert ref_package().comparisons[0].metadata["comparison_is_descriptive"] is True


def test_scientific_artifact_bridge():
    payload = to_scientific_reproduction_artifact(ref_package())
    assert payload["artifact_kind"] == "package"
    assert payload["source_contract"] == CONTRACT_VERSION
    assert payload["content_sha256"] == ref_package().fingerprint()


def test_scientific_artifact_bridge_validates_v338():
    from app.services.scientific_result_registry import ScientificArtifactRef
    payload = to_scientific_reproduction_artifact(ref_package())
    item = ScientificArtifactRef.model_validate(payload)
    assert item.source_object_ref == ref_package().package_id


def test_scientific_artifact_bridge_counts():
    payload = to_scientific_reproduction_artifact(ref_package())
    assert payload["metadata"]["attempt_count"] == 1
    assert payload["metadata"]["verification_report_count"] == 1
    assert payload["metadata"]["comparison_count"] == 1


def test_reproduction_scopes_cover_layers():
    values = {item.value for item in ReproductionScope}
    assert {
        "environment",
        "runtime-job",
        "workflow",
        "statistical-analysis",
        "scientific-artifact",
        "full-research-package",
    }.issubset(values)


def test_criterion_types_cover_reproduction_checks():
    values = {item.value for item in VerificationCriterionType}
    assert {
        "exact-hash",
        "schema-equivalence",
        "runtime-version",
        "dependency-version",
        "numeric-tolerance",
        "statistical-equivalence",
        "workflow-completion",
        "artifact-presence",
        "result-presence",
    }.issubset(values)


def test_evidence_kinds_cover_provenance_and_metrics():
    values = {item.value for item in EvidenceKind}
    assert {"content-hash", "runtime-identity", "metric", "artifact", "provenance"}.issubset(values)


def test_core_does_not_launch_reproduction_jobs():
    assert contract_document()["boundaries"]["core_launches_reproduction_jobs"] is False


def test_core_does_not_build_reproduction_environment():
    assert contract_document()["boundaries"]["core_builds_reproduction_environment"] is False


def test_core_does_not_reexecute_runtime_steps():
    assert contract_document()["boundaries"]["core_reexecutes_runtime_steps"] is False


def test_core_requires_evidence_for_equivalence():
    assert contract_document()["boundaries"]["core_declares_equivalence_without_evidence"] is False


def test_core_does_not_certify_scientific_validity():
    assert contract_document()["boundaries"]["core_certifies_scientific_validity"] is False


def test_execution_host_owns_reproduction():
    doc = contract_document()
    assert doc["integration"]["workspace_or_execution_host_executes_reproduction"] is True
    assert doc["integration"]["core_executes_reproduction"] is False


def test_reference_contract_outcome():
    doc = contract_document()
    assert doc["reference"]["verification_outcome"] == "passed"
    assert doc["reference"]["required_criteria_passed"] is True
    assert doc["reference"]["comparison_status"] == "equivalent"


def test_reference_package_hash_is_sha256():
    assert len(contract_document()["reference"]["package_fingerprint_sha256"]) == 64
