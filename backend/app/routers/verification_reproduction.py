from fastapi import APIRouter

from ..services.verification_reproduction_engine import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    ReproductionAttempt,
    ReproductionPackage,
    ReproductionPlan,
    VerificationCriterion,
    VerificationEvidence,
    assemble_verification_report,
    compare_reproduction,
    contract_document,
    reference_reproduction_package,
    to_scientific_reproduction_artifact,
    verify_criterion,
)

router = APIRouter(
    prefix="/api/v1/verification-reproduction",
    tags=["verification-reproduction"],
)
public_router = APIRouter(
    prefix="/public/v1/verification-reproduction",
    tags=["public-verification-reproduction"],
)


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    package = reference_reproduction_package()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "package": package.model_dump(mode="json", exclude_none=True),
        "plan_fingerprint_sha256": package.plan.fingerprint(),
        "attempt_fingerprints": {
            item.attempt_id: item.fingerprint()
            for item in package.attempts
        },
        "report_fingerprints": {
            item.report_id: item.fingerprint()
            for item in package.reports
        },
        "comparison_fingerprints": {
            item.comparison_id: item.fingerprint()
            for item in package.comparisons
        },
        "package_fingerprint_sha256": package.fingerprint(),
    }


@router.post("/verify-criterion")
def verify_single_criterion(body: dict):
    criterion = VerificationCriterion.model_validate(body["criterion"])
    evidence = VerificationEvidence.model_validate(body["evidence"])
    result = verify_criterion(criterion, evidence)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "result": result.model_dump(mode="json", exclude_none=True),
        "result_fingerprint_sha256": result.fingerprint(),
    }


@router.post("/assemble-report")
def assemble_report(body: dict):
    plan = ReproductionPlan.model_validate(body["plan"])
    attempt = ReproductionAttempt.model_validate(body["attempt"])
    evidence = [
        VerificationEvidence.model_validate(item)
        for item in body.get("evidence", [])
    ]
    report = assemble_verification_report(
        report_id=str(body["report_id"]),
        plan=plan,
        attempt=attempt,
        evidence=evidence,
    )
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "report": report.model_dump(mode="json", exclude_none=True),
        "report_fingerprint_sha256": report.fingerprint(),
    }


@router.post("/compare")
def compare(body: dict):
    plan = ReproductionPlan.model_validate(body["plan"])
    attempt = ReproductionAttempt.model_validate(body["attempt"])
    from ..services.verification_reproduction_engine import ReproductionVerificationReport
    report = ReproductionVerificationReport.model_validate(body["report"])
    comparison = compare_reproduction(
        comparison_id=str(body["comparison_id"]),
        plan=plan,
        attempt=attempt,
        report=report,
    )
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "comparison": comparison.model_dump(mode="json", exclude_none=True),
        "comparison_fingerprint_sha256": comparison.fingerprint(),
    }


@router.post("/validate-package")
def validate_package(body: ReproductionPackage):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "package_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/scientific-artifact")
def scientific_artifact(body: ReproductionPackage):
    payload = to_scientific_reproduction_artifact(body)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "scientific_artifact": payload,
    }
