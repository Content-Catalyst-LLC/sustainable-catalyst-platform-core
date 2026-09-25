from fastapi import APIRouter

from ..services.cross_runtime_research_workflow import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    CrossRuntimeWorkflowDefinition,
    CrossRuntimeWorkflowPackage,
    CrossRuntimeWorkflowRun,
    WorkflowReadinessReport,
    contract_document,
    reference_cross_runtime_workflow_package,
    topological_step_order,
    to_scientific_workflow_artifact,
    workflow_readiness,
)

router = APIRouter(
    prefix="/api/v1/cross-runtime-workflows",
    tags=["cross-runtime-workflows"],
)
public_router = APIRouter(
    prefix="/public/v1/cross-runtime-workflows",
    tags=["public-cross-runtime-workflows"],
)


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    package = reference_cross_runtime_workflow_package()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "package": package.model_dump(mode="json", exclude_none=True),
        "definition_fingerprint_sha256": package.definition.fingerprint(),
        "run_fingerprint_sha256": package.run.fingerprint(),
        "package_fingerprint_sha256": package.fingerprint(),
        "topological_order": topological_step_order(package.definition),
    }


@router.post("/validate-definition")
def validate_definition(body: CrossRuntimeWorkflowDefinition):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "workflow_fingerprint_sha256": body.fingerprint(),
        "topological_order": topological_step_order(body),
    }


@router.post("/readiness")
def readiness(body: dict):
    workflow = CrossRuntimeWorkflowDefinition.model_validate(body["workflow"])
    result = workflow_readiness(
        workflow,
        completed_step_refs=list(body.get("completed_step_refs", [])),
        verified_handoff_refs=list(body.get("verified_handoff_refs", [])),
    )
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "readiness": result.model_dump(mode="json", exclude_none=True),
        "readiness_fingerprint_sha256": result.fingerprint(),
    }


@router.post("/validate-run")
def validate_run(body: CrossRuntimeWorkflowRun):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "run_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-package")
def validate_package(body: CrossRuntimeWorkflowPackage):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "package_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/scientific-artifact")
def scientific_artifact(body: CrossRuntimeWorkflowPackage):
    payload = to_scientific_workflow_artifact(body)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "scientific_artifact": payload,
    }
