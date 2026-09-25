from fastapi import APIRouter
from ..services.ai_error_robustness import (
    CORE_RELEASE,
    CONTRACT_VERSION,
    FailureTaxonomy,
    ErrorObservation,
    EvaluationSliceDefinition,
    RobustnessTestDefinition,
    RobustnessRun,
    ErrorAnalysisReport,
    AIRobustnessFailureBundle,
    contract_document,
    reference_robustness_failure_bundle,
)

router = APIRouter(
    prefix="/api/v1/ai-error-robustness",
    tags=["ai-error-robustness"],
)
public_router = APIRouter(
    prefix="/public/v1/ai-error-robustness",
    tags=["public-ai-error-robustness"],
)

@router.get("/contract")
def get_contract():
    return contract_document()

@public_router.get("/contract")
def get_public_contract():
    return contract_document()

@router.get("/reference")
def get_reference():
    bundle = reference_robustness_failure_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
        "failure_taxonomy_fingerprint_sha256": bundle.failure_taxonomy.fingerprint(),
        "error_analysis_report_fingerprint_sha256": (
            bundle.error_analysis_report.fingerprint()
        ),
        "robustness_run_fingerprints": {
            item.robustness_run_id: item.fingerprint()
            for item in bundle.robustness_runs
        },
        "error_observation_fingerprints": {
            item.error_observation_id: item.fingerprint()
            for item in bundle.error_observations
        },
    }

@router.post("/validate-taxonomy")
def validate_taxonomy(body: FailureTaxonomy):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "failure_taxonomy_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-error-observation")
def validate_error_observation(body: ErrorObservation):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "error_observation_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-slice")
def validate_slice(body: EvaluationSliceDefinition):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "slice_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-robustness-test")
def validate_robustness_test(body: RobustnessTestDefinition):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "robustness_test_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-robustness-run")
def validate_robustness_run(body: RobustnessRun):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "robustness_run_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-report")
def validate_report(body: ErrorAnalysisReport):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "error_analysis_report_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-bundle")
def validate_bundle(body: AIRobustnessFailureBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
    }
