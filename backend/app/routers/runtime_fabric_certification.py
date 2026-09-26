from fastapi import APIRouter

from ..services.runtime_fabric_certification import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    ProductionCertificationEvidence,
    RuntimeFabricCertificationPlan,
    RuntimeProviderCertification,
    ProductRuntimeProfileCertification,
    RuntimeFabricProductionCertificate,
    assess_runtime_fabric,
    contract_document,
    reference_certification_evidence,
    reference_certification_plan,
    reference_product_profile_certifications,
    reference_provider_certifications,
    reference_runtime_fabric_certificate,
    issue_production_certificate,
    to_scientific_certification_artifact,
)

router = APIRouter(
    prefix="/api/v1/runtime-fabric-certification",
    tags=["runtime-fabric-certification"],
)
public_router = APIRouter(
    prefix="/public/v1/runtime-fabric-certification",
    tags=["public-runtime-fabric-certification"],
)


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/plan")
def get_plan():
    plan = reference_certification_plan()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "plan": plan.model_dump(mode="json", exclude_none=True),
        "plan_fingerprint_sha256": plan.fingerprint(),
    }


@router.get("/reference")
def get_reference():
    certificate = reference_runtime_fabric_certificate()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "certificate": certificate.model_dump(mode="json", exclude_none=True),
        "certificate_fingerprint_sha256": certificate.fingerprint(),
        "assessment_fingerprint_sha256": certificate.assessment.fingerprint(),
    }


@router.post("/assess")
def assess(body: dict):
    plan = RuntimeFabricCertificationPlan.model_validate(body["plan"])
    evidence = [
        ProductionCertificationEvidence.model_validate(item)
        for item in body.get("evidence", [])
    ]
    provider_certifications = [
        RuntimeProviderCertification.model_validate(item)
        for item in body.get("provider_certifications", [])
    ]
    product_profile_certifications = [
        ProductRuntimeProfileCertification.model_validate(item)
        for item in body.get("product_profile_certifications", [])
    ]
    assessment = assess_runtime_fabric(
        plan=plan,
        evidence=evidence,
        provider_certifications=provider_certifications,
        product_profile_certifications=product_profile_certifications,
        assessment_id=body.get(
            "assessment_id",
            "runtime-fabric-certification-assessment:api:v1",
        ),
    )
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "assessment": assessment.model_dump(mode="json", exclude_none=True),
        "assessment_fingerprint_sha256": assessment.fingerprint(),
    }


@router.post("/validate-certificate")
def validate_certificate(body: RuntimeFabricProductionCertificate):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "certificate_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/scientific-artifact")
def scientific_artifact(body: RuntimeFabricProductionCertificate):
    payload = to_scientific_certification_artifact(body)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "scientific_artifact": payload,
    }


@router.get("/reference-assessment-input")
def get_reference_assessment_input():
    plan = reference_certification_plan()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "plan": plan.model_dump(mode="json", exclude_none=True),
        "evidence": [
            item.model_dump(mode="json", exclude_none=True)
            for item in reference_certification_evidence()
        ],
        "provider_certifications": [
            item.model_dump(mode="json", exclude_none=True)
            for item in reference_provider_certifications()
        ],
        "product_profile_certifications": [
            item.model_dump(mode="json", exclude_none=True)
            for item in reference_product_profile_certifications()
        ],
    }


@router.post("/issue-certificate")
def issue_certificate(body: dict):
    from ..services.runtime_fabric_certification import RuntimeFabricCertificationAssessment
    assessment = RuntimeFabricCertificationAssessment.model_validate(body["assessment"])
    certificate = issue_production_certificate(
        assessment=assessment,
        production_target_ref=str(body["production_target_ref"]),
        issuer_ref=str(body.get("issuer_ref", "platform-core:production-deploy-verifier")),
        certificate_id=str(
            body.get(
                "certificate_id",
                "runtime-fabric-production-certificate:production:v1",
            )
        ),
        source_object_refs=list(body.get("source_object_refs", [])),
        metadata=dict(body.get("metadata", {})),
    )
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "certificate": certificate.model_dump(mode="json", exclude_none=True),
        "certificate_fingerprint_sha256": certificate.fingerprint(),
    }
