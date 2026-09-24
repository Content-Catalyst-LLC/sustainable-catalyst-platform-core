from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from ..services.runtime_adapter_registry import (
    ADAPTER_CONTRACT_VERSION,
    CORE_RELEASE,
    REGISTRY,
    CapabilityRequirement,
    RuntimeAdapterDescriptor,
    contract_document,
)

router = APIRouter(prefix="/api/v1/runtime-adapters", tags=["runtime-adapters"])
public_router = APIRouter(prefix="/public/v1/runtime-adapters", tags=["public-runtime-adapters"])


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("")
def list_adapters():
    adapters = REGISTRY.list()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": ADAPTER_CONTRACT_VERSION,
        "count": len(adapters),
        "adapters": [
            adapter.model_dump(mode="json", exclude_none=True)
            for adapter in adapters
        ],
    }


@router.get("/capabilities")
def list_capability_index():
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": ADAPTER_CONTRACT_VERSION,
        "index": REGISTRY.capability_index(),
    }


@router.get("/{adapter_id:path}")
def get_adapter(adapter_id: str):
    adapter = REGISTRY.get(adapter_id)
    if adapter is None:
        raise HTTPException(status_code=404, detail="runtime adapter not found")
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": ADAPTER_CONTRACT_VERSION,
        "adapter": adapter.model_dump(mode="json", exclude_none=True),
        "fingerprint_sha256": adapter.fingerprint(),
    }


@router.post("/validate")
def validate_adapter(body: RuntimeAdapterDescriptor):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": ADAPTER_CONTRACT_VERSION,
        "adapter": body.model_dump(mode="json", exclude_none=True),
        "fingerprint_sha256": body.fingerprint(),
    }


@router.post("/resolve")
def resolve_capability(body: CapabilityRequirement):
    candidates = REGISTRY.resolve(body)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": ADAPTER_CONTRACT_VERSION,
        "selection_mode": "candidate-discovery-only",
        "selected_adapter": None,
        "candidate_count": len(candidates),
        "candidates": [
            candidate.model_dump(mode="json", exclude_none=True)
            for candidate in candidates
        ],
    }
