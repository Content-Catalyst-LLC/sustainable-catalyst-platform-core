from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ValidationError

from ..services.computational_runtime_objects import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    canonical_sha256,
    contract_document,
    validate_object,
)

router = APIRouter(prefix="/api/v1/computational-runtime-objects", tags=["computational-runtime-objects"])
public_router = APIRouter(prefix="/public/v1/computational-runtime-objects", tags=["public-computational-runtime-objects"])


class ValidateEnvelope(BaseModel):
    object_type: str = Field(min_length=1, max_length=80)
    object: dict[str, Any]


class FingerprintEnvelope(BaseModel):
    object_type: str = Field(min_length=1, max_length=80)
    object: dict[str, Any]


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.post("/validate")
def validate_runtime_object(body: ValidateEnvelope):
    try:
        obj = validate_object(body.object_type, body.object)
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "object_type": body.object_type,
        "normalized": obj.model_dump(mode="json", exclude_none=True),
        "fingerprint_sha256": canonical_sha256(obj),
    }


@router.post("/fingerprint")
def fingerprint_runtime_object(body: FingerprintEnvelope):
    try:
        obj = validate_object(body.object_type, body.object)
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "object_type": body.object_type,
        "fingerprint_sha256": canonical_sha256(obj),
    }
