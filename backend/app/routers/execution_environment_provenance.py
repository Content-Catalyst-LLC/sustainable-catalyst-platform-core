from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.execution_environment_provenance import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    EnvironmentRequirement,
    ExecutionEnvironmentProvenance,
    compare_environments,
    contract_document,
    julia_v030_reference_provenance,
    verify_requirement,
)

router = APIRouter(
    prefix="/api/v1/execution-environments",
    tags=["execution-environments"],
)
public_router = APIRouter(
    prefix="/public/v1/execution-environments",
    tags=["public-execution-environments"],
)


class CompareRequest(BaseModel):
    left: ExecutionEnvironmentProvenance
    right: ExecutionEnvironmentProvenance


class RequirementRequest(BaseModel):
    environment: ExecutionEnvironmentProvenance
    requirement: EnvironmentRequirement


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference/julia-v0.3.0")
def get_julia_reference():
    record = julia_v030_reference_provenance()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "environment_provenance": record.model_dump(mode="json", exclude_none=True),
        "fingerprint_sha256": record.fingerprint(),
    }


@router.post("/validate")
def validate_environment(body: ExecutionEnvironmentProvenance):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "environment_provenance": body.model_dump(mode="json", exclude_none=True),
        "fingerprint_sha256": body.fingerprint(),
    }


@router.post("/fingerprint")
def fingerprint_environment(body: ExecutionEnvironmentProvenance):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "fingerprint_sha256": body.fingerprint(),
    }


@router.post("/compare")
def compare(body: CompareRequest):
    comparison = compare_environments(body.left, body.right)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "comparison": comparison.model_dump(mode="json", exclude_none=True),
    }


@router.post("/verify-requirement")
def verify(body: RequirementRequest):
    result = verify_requirement(body.environment, body.requirement)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "verification": result.model_dump(mode="json", exclude_none=True),
    }
