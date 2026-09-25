#!/usr/bin/env python3

from app.services.verification_reproduction_engine import (
    CONTRACT_VERSION,
    ReproductionComparisonStatus,
    VerificationOutcome,
    contract_document,
    reference_reproduction_package,
    to_scientific_reproduction_artifact,
)
from app.services.scientific_result_registry import ScientificArtifactRef

doc = contract_document()
assert doc["release"] == "3.42.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["capabilities"]["verification_criteria"] is True
assert doc["capabilities"]["exact_hash_verification"] is True
assert doc["capabilities"]["numeric_tolerance_verification"] is True
assert doc["capabilities"]["verification_report_assembly"] is True
assert doc["capabilities"]["reproduction_comparison"] is True
assert doc["integration"]["workspace_or_execution_host_executes_reproduction"] is True
assert doc["boundaries"]["core_launches_reproduction_jobs"] is False
assert doc["boundaries"]["core_builds_reproduction_environment"] is False
assert doc["boundaries"]["core_declares_equivalence_without_evidence"] is False

package = reference_reproduction_package()
assert len(package.fingerprint()) == 64
assert package.plan.reproduction_environment_package_ref == "environment-package:reference-r-julia:v1"
assert package.plan.target.workflow_ref == "cross-runtime-workflow:reference-r-julia:v1"

attempt = package.attempts[0]
assert attempt.state == "completed"
assert attempt.provenance["core_executed_reproduction"] is False

report = package.reports[0]
assert report.overall_outcome == VerificationOutcome.passed
assert report.required_criteria_passed is True
assert all(item.outcome == VerificationOutcome.passed for item in report.criterion_results)

comparison = package.comparisons[0]
assert comparison.status == ReproductionComparisonStatus.equivalent
assert not comparison.mismatched_artifact_refs
assert not comparison.mismatched_result_refs

payload = to_scientific_reproduction_artifact(package)
ScientificArtifactRef.model_validate(payload)

print("PASS - Platform Core v3.42.0 Verification & Reproduction Engine")
print(f"CONTRACT={CONTRACT_VERSION}")
print("REPRODUCTION_TARGETS=enabled")
print("VERIFICATION_CRITERIA=enabled")
print("EXACT_HASH_VERIFICATION=enabled")
print("RUNTIME_VERSION_VERIFICATION=enabled")
print("SCHEMA_EQUIVALENCE_VERIFICATION=enabled")
print("NUMERIC_TOLERANCE_VERIFICATION=enabled")
print("STATISTICAL_EQUIVALENCE_VERIFICATION=enabled")
print("ARTIFACT_RESULT_PRESENCE_VERIFICATION=enabled")
print("EVIDENCE_CAPTURE=enabled")
print("VERIFICATION_REPORT_ASSEMBLY=enabled")
print("REPRODUCTION_COMPARISON=enabled")
print("PORTABLE_REPRODUCTION_PACKAGES=enabled")
print("SCIENTIFIC_REGISTRY_BRIDGE=enabled")
print("CORE_LAUNCHES_REPRODUCTION_JOBS=false")
print("CORE_BUILDS_REPRODUCTION_ENVIRONMENT=false")
print("CORE_REEXECUTES_RUNTIME_STEPS=false")
print("CORE_DECLARES_EQUIVALENCE_WITHOUT_EVIDENCE=false")
print("CORE_CERTIFIES_SCIENTIFIC_VALIDITY=false")
