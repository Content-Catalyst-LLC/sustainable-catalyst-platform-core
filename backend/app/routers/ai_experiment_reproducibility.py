from fastapi import APIRouter
from ..services.ai_experiment_reproducibility import (
    CORE_RELEASE,
    CONTRACT_VERSION,
    AIExperimentDefinition,
    ExperimentRunBinding,
    AIExperimentReproducibilityPackage,
    ReproductionAttempt,
    ReproducibilityAssessment,
    AIExperimentPackageBundle,
    contract_document,
    reference_experiment_bundle,
)

router = APIRouter(
    prefix="/api/v1/ai-experiments",
    tags=["ai-experiments"],
)
public_router = APIRouter(
    prefix="/public/v1/ai-experiments",
    tags=["public-ai-experiments"],
)

@router.get("/contract")
def get_contract():
    return contract_document()

@public_router.get("/contract")
def get_public_contract():
    return contract_document()

@router.get("/reference")
def get_reference():
    bundle = reference_experiment_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
        "experiment_fingerprint_sha256": bundle.experiment.fingerprint(),
        "reproducibility_package_fingerprint_sha256": (
            bundle.reproducibility_package.fingerprint()
        ),
        "reproduction_attempt_fingerprints": {
            item.reproduction_attempt_id: item.fingerprint()
            for item in bundle.reproduction_attempts
        },
        "assessment_fingerprints": {
            item.reproducibility_assessment_id: item.fingerprint()
            for item in bundle.assessments
        },
    }

@router.post("/validate-experiment")
def validate_experiment(body: AIExperimentDefinition):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "experiment_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-run-binding")
def validate_run_binding(body: ExperimentRunBinding):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "run_binding_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-reproducibility-package")
def validate_reproducibility_package(body: AIExperimentReproducibilityPackage):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "reproducibility_package_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-reproduction-attempt")
def validate_reproduction_attempt(body: ReproductionAttempt):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "reproduction_attempt_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-assessment")
def validate_assessment(body: ReproducibilityAssessment):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "reproducibility_assessment_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-bundle")
def validate_bundle(body: AIExperimentPackageBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
    }
