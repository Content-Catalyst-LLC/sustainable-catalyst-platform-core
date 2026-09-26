from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.runtime_fabric_certification import (
    CONTRACT_VERSION,
    REFERENCE_JULIA_RUNTIME,
    REFERENCE_JULIA_VERSION,
    REFERENCE_R_RUNTIME,
    REFERENCE_R_VERSION,
    CertificationDomain,
    CertificationStatus,
    CriterionOutcome,
    CriterionSeverity,
    EvidenceStatus,
    ProductProfileCertificationStatus,
    ProductionCertificationCriterion,
    ProductionCertificationEvidence,
    RuntimeFabricCertificationAssessment,
    RuntimeFabricCertificationPlan,
    RuntimeFabricProductionCertificate,
    RuntimeProviderCertification,
    ProductRuntimeProfileCertification,
    ProviderCertificationStatus,
    assess_runtime_fabric,
    contract_document,
    evaluate_criterion,
    reference_certification_evidence,
    reference_certification_plan,
    reference_product_profile_certifications,
    reference_provider_certifications,
    reference_runtime_fabric_certificate,
    issue_production_certificate,
    to_scientific_certification_artifact,
)


def ref_plan():
    return reference_certification_plan()


def ref_evidence():
    return reference_certification_evidence()


def ref_providers():
    return reference_provider_certifications()


def ref_products():
    return reference_product_profile_certifications()


def ref_certificate():
    return reference_runtime_fabric_certificate()


def test_contract_identity():
    doc = contract_document()
    assert doc["release"] == "3.45.0"
    assert doc["contract"] == CONTRACT_VERSION


def test_contract_depends_on_v344():
    assert "sc.core.unified-runtime-api.v1" in contract_document()["depends_on"]


def test_contract_depends_on_v343():
    assert "sc.core.runtime-security-governance.v1" in contract_document()["depends_on"]


def test_contract_depends_on_v342():
    assert "sc.core.verification-reproduction-engine.v1" in contract_document()["depends_on"]


def test_contract_depends_on_v341():
    assert "sc.core.reproducible-environment-package.v1" in contract_document()["depends_on"]


def test_contract_depends_on_v340():
    assert "sc.core.cross-runtime-research-workflow.v1" in contract_document()["depends_on"]


def test_plan_targets_release():
    plan = ref_plan()
    assert plan.target_release == "3.45.0"
    assert plan.target_tag == "v3.45.0"


def test_plan_has_blockers():
    assert any(x.severity == CriterionSeverity.blocker for x in ref_plan().criteria)


def test_plan_has_required():
    assert any(x.severity == CriterionSeverity.required for x in ref_plan().criteria)


def test_plan_domains_cover_runtime_fabric():
    domains = {x.domain for x in ref_plan().criteria}
    assert CertificationDomain.release_identity in domains
    assert CertificationDomain.runtime_registration in domains
    assert CertificationDomain.security_governance in domains
    assert CertificationDomain.environment_reproducibility in domains
    assert CertificationDomain.runtime_interchange in domains
    assert CertificationDomain.cross_runtime_workflow in domains
    assert CertificationDomain.reproduction_verification in domains
    assert CertificationDomain.product_runtime_profiles in domains


def test_plan_requires_criteria():
    data = ref_plan().model_dump(mode="python")
    data["criteria"] = []
    with pytest.raises(ValidationError):
        RuntimeFabricCertificationPlan.model_validate(data)


def test_plan_rejects_duplicate_criterion_ids():
    data = ref_plan().model_dump(mode="python")
    data["criteria"].append(deepcopy(data["criteria"][0]))
    with pytest.raises(ValidationError):
        RuntimeFabricCertificationPlan.model_validate(data)


def test_plan_rejects_duplicate_runtime_refs():
    data = ref_plan().model_dump(mode="python")
    data["required_runtime_refs"].append(data["required_runtime_refs"][0])
    with pytest.raises(ValidationError):
        RuntimeFabricCertificationPlan.model_validate(data)


def test_plan_rejects_duplicate_product_profile_refs():
    data = ref_plan().model_dump(mode="python")
    data["required_product_profile_refs"].append(data["required_product_profile_refs"][0])
    with pytest.raises(ValidationError):
        RuntimeFabricCertificationPlan.model_validate(data)


def test_plan_fingerprint_stable():
    plan = ref_plan()
    assert plan.fingerprint() == deepcopy(plan).fingerprint()
    assert len(plan.fingerprint()) == 64


def test_criterion_fingerprint_stable():
    item = ref_plan().criteria[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_evidence_sha256_validation():
    with pytest.raises(ValidationError):
        ProductionCertificationEvidence(
            evidence_id="evidence:test",
            criterion_ref="criterion:test",
            source_ref="source:test",
            observed_value=True,
            content_sha256="bad",
        )


def test_evidence_fingerprint_ignores_time():
    item = ref_evidence()[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_evaluate_pass():
    criterion = ProductionCertificationCriterion(
        criterion_id="criterion:test",
        domain=CertificationDomain.core_health,
        name="test",
        severity=CriterionSeverity.required,
        expected_value=True,
        evidence_source_ref="source:test",
    )
    evidence = ProductionCertificationEvidence(
        evidence_id="evidence:test",
        criterion_ref=criterion.criterion_id,
        source_ref="source:test",
        observed_value=True,
    )
    result = evaluate_criterion(criterion, evidence)
    assert result.outcome == CriterionOutcome.passed


def test_evaluate_required_mismatch_fails():
    criterion = ProductionCertificationCriterion(
        criterion_id="criterion:test",
        domain=CertificationDomain.core_health,
        name="test",
        severity=CriterionSeverity.required,
        expected_value=True,
        evidence_source_ref="source:test",
    )
    evidence = ProductionCertificationEvidence(
        evidence_id="evidence:test",
        criterion_ref=criterion.criterion_id,
        source_ref="source:test",
        observed_value=False,
    )
    assert evaluate_criterion(criterion, evidence).outcome == CriterionOutcome.failed


def test_evaluate_advisory_mismatch_warns():
    criterion = ProductionCertificationCriterion(
        criterion_id="criterion:test",
        domain=CertificationDomain.core_health,
        name="test",
        severity=CriterionSeverity.advisory,
        expected_value=True,
        evidence_source_ref="source:test",
    )
    evidence = ProductionCertificationEvidence(
        evidence_id="evidence:test",
        criterion_ref=criterion.criterion_id,
        source_ref="source:test",
        observed_value=False,
    )
    assert evaluate_criterion(criterion, evidence).outcome == CriterionOutcome.warning


def test_evaluate_missing_evidence_not_run():
    criterion = ref_plan().criteria[0]
    assert evaluate_criterion(criterion, None).outcome == CriterionOutcome.not_run


def test_evaluate_invalid_required_fails():
    criterion = ref_plan().criteria[0]
    evidence = ProductionCertificationEvidence(
        evidence_id="evidence:test",
        criterion_ref=criterion.criterion_id,
        source_ref="source:test",
        status=EvidenceStatus.invalid,
        observed_value=criterion.expected_value,
    )
    assert evaluate_criterion(criterion, evidence).outcome == CriterionOutcome.failed


def test_evaluate_rejects_wrong_criterion_ref():
    criterion = ref_plan().criteria[0]
    evidence = ProductionCertificationEvidence(
        evidence_id="evidence:test",
        criterion_ref="criterion:other",
        source_ref="source:test",
        observed_value=criterion.expected_value,
    )
    with pytest.raises(ValueError):
        evaluate_criterion(criterion, evidence)


def test_provider_certification_rejects_duplicate_operations():
    with pytest.raises(ValidationError):
        RuntimeProviderCertification(
            provider_certification_id="provider:test",
            runtime_ref="runtime:test",
            runtime_version="1.0",
            runtime_adapter_ref="adapter:test",
            adapter_contract="contract:test",
            provider_status=ProviderCertificationStatus.certified,
            required_operation_refs=["x", "x"],
        )


def test_provider_certification_rejects_duplicate_evidence_refs():
    with pytest.raises(ValidationError):
        RuntimeProviderCertification(
            provider_certification_id="provider:test",
            runtime_ref="runtime:test",
            runtime_version="1.0",
            runtime_adapter_ref="adapter:test",
            adapter_contract="contract:test",
            provider_status=ProviderCertificationStatus.certified,
            evidence_refs=["e:test", "e:test"],
        )


def test_provider_fingerprint_stable():
    item = ref_providers()[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_reference_r_provider_certified():
    item = [x for x in ref_providers() if x.runtime_ref == REFERENCE_R_RUNTIME][0]
    assert item.runtime_version == REFERENCE_R_VERSION
    assert item.provider_status == ProviderCertificationStatus.certified


def test_reference_julia_provider_certified():
    item = [x for x in ref_providers() if x.runtime_ref == REFERENCE_JULIA_RUNTIME][0]
    assert item.runtime_version == REFERENCE_JULIA_VERSION
    assert item.provider_status == ProviderCertificationStatus.certified


def test_product_profile_rejects_duplicate_runtime_refs():
    with pytest.raises(ValidationError):
        ProductRuntimeProfileCertification(
            product_certification_id="product:test",
            product_id="workspace",
            product_profile_ref="profile:test",
            status=ProductProfileCertificationStatus.contract_ready,
            allowed_runtime_refs=["r", "r"],
        )


def test_product_profile_rejects_duplicate_evidence_refs():
    with pytest.raises(ValidationError):
        ProductRuntimeProfileCertification(
            product_certification_id="product:test",
            product_id="workspace",
            product_profile_ref="profile:test",
            status=ProductProfileCertificationStatus.contract_ready,
            evidence_refs=["e", "e"],
        )


def test_product_fingerprint_stable():
    item = ref_products()[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_reference_product_profiles_contract_ready():
    assert [x.status for x in ref_products()] == [
        ProductProfileCertificationStatus.contract_ready,
        ProductProfileCertificationStatus.contract_ready,
        ProductProfileCertificationStatus.contract_ready,
    ]


def test_reference_product_profiles_do_not_claim_repo_integration():
    assert all(x.product_repository_integration_certified is False for x in ref_products())


def test_assessment_reference_certified():
    cert = ref_certificate()
    assert cert.assessment.status == CertificationStatus.certified
    assert not cert.assessment.blocker_failures
    assert not cert.assessment.required_failures
    assert not cert.assessment.advisory_warnings


def test_assessment_blocker_failure_not_certified():
    plan = ref_plan()
    evidence = ref_evidence()
    evidence[0] = evidence[0].model_copy(update={"observed_value": "wrong"})
    assessment = assess_runtime_fabric(
        plan=plan,
        evidence=evidence,
        provider_certifications=ref_providers(),
        product_profile_certifications=ref_products(),
    )
    assert assessment.status == CertificationStatus.not_certified
    assert "criterion:release-version" in assessment.blocker_failures


def test_assessment_required_failure_not_certified():
    plan = ref_plan()
    evidence = ref_evidence()
    idx = next(i for i, x in enumerate(evidence) if x.criterion_ref == "criterion:runtime-catalog")
    evidence[idx] = evidence[idx].model_copy(update={"observed_value": []})
    assessment = assess_runtime_fabric(
        plan=plan,
        evidence=evidence,
        provider_certifications=ref_providers(),
        product_profile_certifications=ref_products(),
    )
    assert assessment.status == CertificationStatus.not_certified
    assert "criterion:runtime-catalog" in assessment.required_failures


def test_assessment_advisory_warning_certified_with_warnings():
    plan = ref_plan()
    extra = ProductionCertificationCriterion(
        criterion_id="criterion:advisory-test",
        domain=CertificationDomain.core_health,
        name="advisory",
        severity=CriterionSeverity.advisory,
        expected_value=True,
        evidence_source_ref="source:advisory",
    )
    plan.criteria.append(extra)
    evidence = ref_evidence() + [
        ProductionCertificationEvidence(
            evidence_id="evidence:advisory-test",
            criterion_ref=extra.criterion_id,
            source_ref="source:advisory",
            observed_value=False,
        )
    ]
    assessment = assess_runtime_fabric(
        plan=plan,
        evidence=evidence,
        provider_certifications=ref_providers(),
        product_profile_certifications=ref_products(),
    )
    assert assessment.status == CertificationStatus.certified_with_warnings
    assert "criterion:advisory-test" in assessment.advisory_warnings


def test_missing_required_provider_is_blocker():
    providers = [x for x in ref_providers() if x.runtime_ref != REFERENCE_JULIA_RUNTIME]
    assessment = assess_runtime_fabric(
        plan=ref_plan(),
        evidence=ref_evidence(),
        provider_certifications=providers,
        product_profile_certifications=ref_products(),
    )
    assert assessment.status == CertificationStatus.not_certified
    assert f"provider:{REFERENCE_JULIA_RUNTIME}" in assessment.blocker_failures


def test_uncertified_required_provider_is_blocker():
    providers = ref_providers()
    providers[0] = providers[0].model_copy(update={
        "provider_status": ProviderCertificationStatus.not_certified
    })
    assessment = assess_runtime_fabric(
        plan=ref_plan(),
        evidence=ref_evidence(),
        provider_certifications=providers,
        product_profile_certifications=ref_products(),
    )
    assert assessment.status == CertificationStatus.not_certified


def test_missing_required_product_profile_fails():
    products = ref_products()[:-1]
    assessment = assess_runtime_fabric(
        plan=ref_plan(),
        evidence=ref_evidence(),
        provider_certifications=ref_providers(),
        product_profile_certifications=products,
    )
    assert assessment.status == CertificationStatus.not_certified
    assert any(x.startswith("product-profile:") for x in assessment.required_failures)


def test_not_ready_required_product_profile_fails():
    products = ref_products()
    products[0] = products[0].model_copy(update={
        "status": ProductProfileCertificationStatus.not_ready
    })
    assessment = assess_runtime_fabric(
        plan=ref_plan(),
        evidence=ref_evidence(),
        provider_certifications=ref_providers(),
        product_profile_certifications=products,
    )
    assert assessment.status == CertificationStatus.not_certified


def test_duplicate_primary_evidence_rejected():
    evidence = ref_evidence()
    evidence.append(
        deepcopy(evidence[0]).model_copy(update={"evidence_id": "evidence:duplicate"})
    )
    with pytest.raises(ValueError):
        assess_runtime_fabric(
            plan=ref_plan(),
            evidence=evidence,
            provider_certifications=ref_providers(),
            product_profile_certifications=ref_products(),
        )


def test_assessment_rejects_duplicate_result_refs():
    cert = ref_certificate()
    data = cert.assessment.model_dump(mode="python")
    data["results"].append(deepcopy(data["results"][0]))
    with pytest.raises(ValidationError):
        RuntimeFabricCertificationAssessment.model_validate(data)


def test_assessment_rejects_duplicate_evidence_ids():
    cert = ref_certificate()
    data = cert.assessment.model_dump(mode="python")
    data["evidence"].append(deepcopy(data["evidence"][0]))
    with pytest.raises(ValidationError):
        RuntimeFabricCertificationAssessment.model_validate(data)


def test_assessment_rejects_unknown_evidence_ref():
    cert = ref_certificate()
    data = cert.assessment.model_dump(mode="python")
    data["results"][0]["evidence_ref"] = "evidence:missing"
    with pytest.raises(ValidationError):
        RuntimeFabricCertificationAssessment.model_validate(data)


def test_certified_assessment_rejects_warning():
    cert = ref_certificate()
    data = cert.assessment.model_dump(mode="python")
    data["advisory_warnings"] = ["criterion:test"]
    with pytest.raises(ValidationError):
        RuntimeFabricCertificationAssessment.model_validate(data)


def test_certified_with_warnings_rejects_blocker():
    cert = ref_certificate()
    data = cert.assessment.model_dump(mode="python")
    data["status"] = "certified-with-warnings"
    data["blocker_failures"] = ["criterion:test"]
    with pytest.raises(ValidationError):
        RuntimeFabricCertificationAssessment.model_validate(data)


def test_not_certified_requires_failure():
    cert = ref_certificate()
    data = cert.assessment.model_dump(mode="python")
    data["status"] = "not-certified"
    with pytest.raises(ValidationError):
        RuntimeFabricCertificationAssessment.model_validate(data)


def test_assessment_fingerprint_stable():
    assessment = ref_certificate().assessment
    assert assessment.fingerprint() == deepcopy(assessment).fingerprint()
    assert len(assessment.fingerprint()) == 64


def test_certificate_requires_certifiable_assessment():
    cert = ref_certificate()
    data = cert.model_dump(mode="python")
    data["assessment"]["status"] = "not-certified"
    data["assessment"]["blocker_failures"] = ["criterion:test"]
    with pytest.raises(ValidationError):
        RuntimeFabricProductionCertificate.model_validate(data)


def test_certificate_fingerprint_stable():
    cert = ref_certificate()
    assert cert.fingerprint() == deepcopy(cert).fingerprint()
    assert len(cert.fingerprint()) == 64


def test_reference_certificate_release():
    cert = ref_certificate()
    assert cert.certified_release == "3.45.0"
    assert cert.certified_tag == "v3.45.0"


def test_reference_certificate_is_contract_proof():
    cert = ref_certificate()
    assert cert.metadata["certificate_kind"] == "reference-contract-proof"
    assert cert.metadata["live_production_certification_occurs_in_deploy_verifier"] is True


def test_reference_evidence_count_matches_plan():
    assert len(ref_evidence()) == len(ref_plan().criteria)


def test_reference_evidence_all_observed():
    assert all(x.status == EvidenceStatus.observed for x in ref_evidence())


def test_reference_results_all_pass():
    assert all(
        x.outcome == CriterionOutcome.passed
        for x in ref_certificate().assessment.results
    )


def test_scientific_artifact_bridge():
    payload = to_scientific_certification_artifact(ref_certificate())
    assert payload["artifact_kind"] == "package"
    assert payload["source_contract"] == CONTRACT_VERSION
    assert payload["content_sha256"] == ref_certificate().fingerprint()


def test_scientific_artifact_bridge_validates_v338():
    from app.services.scientific_result_registry import ScientificArtifactRef
    payload = to_scientific_certification_artifact(ref_certificate())
    item = ScientificArtifactRef.model_validate(payload)
    assert item.source_object_ref == ref_certificate().certificate_id


def test_scientific_artifact_metadata():
    payload = to_scientific_certification_artifact(ref_certificate())
    meta = payload["metadata"]
    assert meta["certified_release"] == "3.45.0"
    assert meta["certification_status"] == "certified"
    assert meta["provider_count"] == 2
    assert meta["product_profile_count"] == 3


def test_contract_reference_status():
    doc = contract_document()
    assert doc["reference"]["assessment_status"] == "certified"
    assert doc["reference"]["blocker_failures"] == []
    assert doc["reference"]["required_failures"] == []


def test_contract_reference_provider_refs():
    assert contract_document()["reference"]["provider_runtime_refs"] == [
        REFERENCE_R_RUNTIME,
        REFERENCE_JULIA_RUNTIME,
    ]


def test_contract_reference_product_profiles():
    assert contract_document()["reference"]["product_profile_refs"] == [
        "product-runtime-profile:workspace:v1",
        "product-runtime-profile:research-lab:v1",
        "product-runtime-profile:workbench:v1",
    ]


def test_contract_reference_fingerprint_sha256():
    assert len(contract_document()["reference"]["certificate_fingerprint_sha256"]) == 64


def test_boundary_reference_not_live_evidence():
    assert contract_document()["boundaries"]["reference_certificate_is_live_production_evidence"] is False


def test_boundary_deploy_verifier_supplies_live_evidence():
    assert contract_document()["boundaries"]["deploy_verifier_supplies_live_production_evidence"] is True


def test_boundary_external_products_not_certified():
    assert contract_document()["boundaries"]["external_product_repository_integration_certified"] is False


def test_boundary_no_scientific_validity():
    assert contract_document()["boundaries"]["core_certifies_scientific_validity"] is False


def test_boundary_core_does_not_select_or_execute_runtime():
    assert contract_document()["boundaries"]["core_autonomously_selects_or_executes_runtime"] is False


def test_capabilities_production_certificate():
    caps = contract_document()["capabilities"]
    assert caps["runtime_provider_certification"] is True
    assert caps["unified_runtime_api_certification"] is True
    assert caps["security_governance_certification"] is True
    assert caps["portable_production_certificates"] is True


def test_issue_production_certificate_from_certified_assessment():
    assessment = ref_certificate().assessment
    cert = issue_production_certificate(
        assessment=assessment,
        production_target_ref="production-target:contabo-core",
        issuer_ref="platform-core:deploy-verifier",
        source_object_refs=["live-evidence:reference"],
    )
    assert cert.metadata["certificate_kind"] == "live-production"
    assert cert.production_target_ref == "production-target:contabo-core"
    assert len(cert.fingerprint()) == 64


def test_issue_production_certificate_rejects_failed_assessment():
    assessment = ref_certificate().assessment.model_copy(
        update={
            "status": CertificationStatus.not_certified,
            "blocker_failures": ["criterion:test"],
        }
    )
    with pytest.raises(ValidationError):
        issue_production_certificate(
            assessment=assessment,
            production_target_ref="production-target:test",
            issuer_ref="issuer:test",
        )
