from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.ai_inference_provenance import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    AIArtifactProvenance,
    AIInferenceInput,
    AIInferenceParameterSet,
    AIInferenceRun,
    AIInferenceRunBundle,
    compare_inference_runs,
    contract_document,
    reference_inference_run,
)

router = APIRouter(
    prefix="/api/v1/ai-inference-provenance",
    tags=["ai-inference-provenance"],
)
public_router = APIRouter(
    prefix="/public/v1/ai-inference-provenance",
    tags=["public-ai-inference-provenance"],
)


class CompareRequest(BaseModel):
    left: AIInferenceRun
    right: AIInferenceRun


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    bundle = reference_inference_run()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "inference_run_fingerprint_sha256": bundle.inference_run.fingerprint(),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
        "artifact_fingerprints": {
            item.ai_artifact_id: item.fingerprint()
            for item in bundle.inference_run.artifacts
        },
        "input_fingerprints": {
            item.input_id: item.fingerprint()
            for item in bundle.inference_run.inputs
        },
    }


@router.post("/validate-input")
def validate_input(body: AIInferenceInput):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "input": body.model_dump(mode="json", exclude_none=True),
        "input_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-parameter-set")
def validate_parameter_set(body: AIInferenceParameterSet):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "parameter_set": body.model_dump(mode="json", exclude_none=True),
        "parameter_set_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-artifact")
def validate_artifact(body: AIArtifactProvenance):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "artifact": body.model_dump(mode="json", exclude_none=True),
        "artifact_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-run")
def validate_run(body: AIInferenceRun):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "inference_run": body.model_dump(mode="json", exclude_none=True),
        "inference_run_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-bundle")
def validate_bundle(body: AIInferenceRunBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": body.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/compare-runs")
def compare_runs(body: CompareRequest):
    comparison = compare_inference_runs(body.left, body.right)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "comparison": comparison.model_dump(mode="json", exclude_none=True),
    }
