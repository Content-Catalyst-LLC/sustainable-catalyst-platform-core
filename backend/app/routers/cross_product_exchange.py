from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services.cross_product_exchange import create_package, create_receipt, list_packages, package_detail, readiness

router = APIRouter(prefix="/v1/exchange", tags=["Cross-Product Evidence Exchange"])
public_router = APIRouter(prefix="/api/v1/exchange", tags=["Unified Public API — Cross-Product Exchange Readiness"])


class ExchangeItemCreate(BaseModel):
    artifact_type: str = "evidence"
    subject_type: str
    subject_id: str
    snapshot_mode: str = "reference"
    evidence_role: str = "inherited"
    provenance: dict = Field(default_factory=dict)


class ExchangePackageCreate(BaseModel):
    origin_product: str
    target_product: str
    title: str = Field(min_length=1, max_length=400)
    purpose: str | None = None
    visibility: str = "internal"
    idempotency_key: str | None = Field(default=None, max_length=128)
    items: list[ExchangeItemCreate] = Field(min_length=1, max_length=100)
    provenance: dict = Field(default_factory=dict)


class ExchangeReceiptCreate(BaseModel):
    target_product: str
    state: str
    derived_object_id: str | None = None
    note: str | None = None
    metadata: dict = Field(default_factory=dict)


def _bad(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))


@router.get("/readiness", dependencies=[Depends(require_read)])
def exchange_readiness(request: Request):
    data = readiness()
    status = migration_status(request.app.state.database)
    data.update({
        "status": "ready" if request.app.state.settings.cross_product_exchange_enabled else "disabled",
        "release": request.app.state.settings.version,
        "migration_0017_applied": "0017" in status["applied"],
    })
    return data


@router.post("/packages", dependencies=[Depends(require_write)])
def create_exchange_package(payload: ExchangePackageCreate, db: Session = Depends(get_session)):
    try:
        row = create_package(db, **payload.model_dump())
        return package_detail(db, row.id)
    except ValueError as exc:
        raise _bad(exc)


@router.get("/packages", dependencies=[Depends(require_read)])
def exchange_packages(
    origin_product: str | None = None,
    target_product: str | None = None,
    state: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_session),
):
    return {"items": list_packages(db, origin_product=origin_product, target_product=target_product, state=state, limit=limit)}


@router.get("/packages/{package_id}", dependencies=[Depends(require_read)])
def exchange_package(package_id: str, db: Session = Depends(get_session)):
    try:
        return package_detail(db, package_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/packages/{package_id}/receipts", dependencies=[Depends(require_write)])
def receipt(package_id: str, payload: ExchangeReceiptCreate, db: Session = Depends(get_session)):
    try:
        row = create_receipt(db, package_id, **payload.model_dump())
        return jsonable_encoder({
            "id": row.id,
            "package_id": row.package_id,
            "target_product": row.target_product,
            "state": row.state,
            "derived_object_id": row.derived_object_id,
            "note": row.note,
            "metadata": row.metadata_json,
            "created_at": row.created_at,
        })
    except ValueError as exc:
        raise _bad(exc)


@public_router.get("/readiness")
def public_exchange_readiness(
    request: Request,
    _context: PublicApiContext = Depends(require_public_scope("data:read")),
):
    data = readiness()
    return PublicEnvelope(
        data=jsonable_encoder({
            "status": "ready" if request.app.state.settings.cross_product_exchange_enabled else "disabled",
            "release": request.app.state.settings.version,
            "products": data["products"],
            "artifact_types": data["artifact_types"],
            "reference_first": True,
            "non_destructive": True,
            "automatic_truth_promotion": False,
            "package_data_publicly_exposed": False,
        }),
        meta={"api_version": "v1", "request_id": request.state.request_id, "documentation": "/docs#tag/Unified-Public-API-Cross-Product-Exchange-Readiness"},
    )
