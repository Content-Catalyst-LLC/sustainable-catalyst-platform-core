from fastapi import APIRouter

from ..services.statistical_analysis_objects import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    StatisticalAnalysisPackage,
    StatisticalAnalysisPlan,
    StatisticalAnalysisResult,
    StatisticalExecutionBinding,
    contract_document,
    normalize_r_runtime_result,
    reference_statistical_analysis_package,
)

router = APIRouter(
    prefix="/api/v1/statistical-analysis",
    tags=["statistical-analysis"],
)
public_router = APIRouter(
    prefix="/public/v1/statistical-analysis",
    tags=["public-statistical-analysis"],
)


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    package = reference_statistical_analysis_package()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "package": package.model_dump(mode="json", exclude_none=True),
        "plan_fingerprint_sha256": package.plan.fingerprint(),
        "result_fingerprints": {
            result.analysis_result_id: result.fingerprint()
            for result in package.results
        },
        "package_fingerprint_sha256": package.fingerprint(),
    }


@router.post("/validate-plan")
def validate_plan(body: StatisticalAnalysisPlan):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "analysis_plan_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-result")
def validate_result(body: StatisticalAnalysisResult):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "analysis_result_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-package")
def validate_package(body: StatisticalAnalysisPackage):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "package_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/normalize-r-runtime-result")
def normalize_r_result(body: dict):
    plan = StatisticalAnalysisPlan.model_validate(body["analysis_plan"])
    execution = StatisticalExecutionBinding.model_validate(body["execution_binding"])
    result = normalize_r_runtime_result(
        analysis_plan=plan,
        runtime_payload=body["runtime_payload"],
        execution_binding=execution,
        analysis_result_id=str(body["analysis_result_id"]),
    )
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "result": result.model_dump(mode="json", exclude_none=True),
        "analysis_result_fingerprint_sha256": result.fingerprint(),
    }
