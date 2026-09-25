from __future__ import annotations

from fastapi import APIRouter

from ..services.ai_model_objects import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    AIModel,
    AIModelVersion,
    AIModelVersionBinding,
    compare_model_versions,
    contract_document,
    reference_ai_model,
)

router = APIRouter(prefix="/api/v1/ai-models", tags=["ai-models"])
public_router = APIRouter(prefix="/public/v1/ai-models", tags=["public-ai-models"])


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    binding = reference_ai_model()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "binding": binding.model_dump(mode="json", exclude_none=True),
        "model_fingerprint_sha256": binding.model.fingerprint(),
        "model_version_fingerprint_sha256": binding.model_version.fingerprint(),
        "binding_fingerprint_sha256": binding.fingerprint(),
    }


@router.post("/validate-model")
def validate_model(body: AIModel):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "model": body.model_dump(mode="json", exclude_none=True),
        "model_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-version")
def validate_version(body: AIModelVersion):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "model_version": body.model_dump(mode="json", exclude_none=True),
        "model_version_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-binding")
def validate_binding(body: AIModelVersionBinding):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "binding": body.model_dump(mode="json", exclude_none=True),
        "binding_fingerprint_sha256": body.fingerprint(),
    }


class CompareBody(AIModelVersionBinding):
    pass


@router.post("/compare-versions")
def compare_versions(body: dict):
    left = AIModelVersion.model_validate(body["left"])
    right = AIModelVersion.model_validate(body["right"])
    result = compare_model_versions(left, right)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "comparison": result.model_dump(mode="json", exclude_none=True),
    }
