#!/usr/bin/env python3

from app.services.runtime_fabric_certification import (
    CONTRACT_VERSION,
    CertificationStatus,
    CriterionOutcome,
    reference_certification_evidence,
    reference_certification_plan,
    reference_product_profile_certifications,
    reference_provider_certifications,
    reference_runtime_fabric_certificate,
    contract_document,
    to_scientific_certification_artifact,
)
from app.services.scientific_result_registry import ScientificArtifactRef

doc = contract_document()
assert doc["release"] == "3.45.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["capabilities"]["runtime_provider_certification"] is True
assert doc["capabilities"]["security_governance_certification"] is True
assert doc["capabilities"]["runtime_interchange_certification"] is True
assert doc["capabilities"]["cross_runtime_workflow_certification"] is True
assert doc["capabilities"]["portable_production_certificates"] is True
assert doc["boundaries"]["reference_certificate_is_live_production_evidence"] is False
assert doc["boundaries"]["deploy_verifier_supplies_live_production_evidence"] is True
assert doc["boundaries"]["external_product_repository_integration_certified"] is False
assert doc["boundaries"]["core_certifies_scientific_validity"] is False

plan = reference_certification_plan()
assert plan.target_release == "3.45.0"
assert plan.target_tag == "v3.45.0"
assert len(plan.criteria) == 14
assert len(reference_certification_evidence()) == 14

providers = reference_provider_certifications()
assert [x.runtime_ref for x in providers] == ["sc-runtime-r", "catalyst-julia-runtime"]
assert all(x.provider_status == "certified" for x in providers)

products = reference_product_profile_certifications()
assert [x.product_id for x in products] == ["workspace", "research-lab", "workbench"]
assert all(x.status == "contract-ready" for x in products)
assert all(x.product_repository_integration_certified is False for x in products)

certificate = reference_runtime_fabric_certificate()
assessment = certificate.assessment
assert assessment.status == CertificationStatus.certified
assert not assessment.blocker_failures
assert not assessment.required_failures
assert not assessment.advisory_warnings
assert all(x.outcome == CriterionOutcome.passed for x in assessment.results)
assert len(certificate.fingerprint()) == 64

payload = to_scientific_certification_artifact(certificate)
ScientificArtifactRef.model_validate(payload)

print("PASS - Platform Core v3.45.0 Runtime Fabric Production Certification")
print(f"CONTRACT={CONTRACT_VERSION}")
print("RELEASE_IDENTITY_CERTIFICATION=enabled")
print("RUNTIME_PROVIDER_CERTIFICATION=enabled")
print("UNIFIED_RUNTIME_API_CERTIFICATION=enabled")
print("SECURITY_GOVERNANCE_CERTIFICATION=enabled")
print("ENVIRONMENT_REPRODUCIBILITY_CERTIFICATION=enabled")
print("RUNTIME_INTERCHANGE_CERTIFICATION=enabled")
print("CROSS_RUNTIME_WORKFLOW_CERTIFICATION=enabled")
print("REPRODUCTION_VERIFICATION_CERTIFICATION=enabled")
print("PRODUCT_PROFILE_CONTRACT_CERTIFICATION=enabled")
print("SCIENTIFIC_REGISTRY_PACKAGING=enabled")
print("BLOCKER_REQUIRED_ADVISORY_GATES=enabled")
print("PORTABLE_PRODUCTION_CERTIFICATES=enabled")
print("REFERENCE_CERTIFICATE_IS_LIVE_PRODUCTION_EVIDENCE=false")
print("DEPLOY_VERIFIER_SUPPLIES_LIVE_PRODUCTION_EVIDENCE=true")
print("EXTERNAL_PRODUCT_REPOSITORY_INTEGRATION_CERTIFIED=false")
print("CORE_CERTIFIES_SCIENTIFIC_VALIDITY=false")
