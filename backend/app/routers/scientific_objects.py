from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import scientific_objects


router = APIRouter(prefix="/v1/scientific-objects", tags=["Scientific Object Storage & Processing Adapters"])
public_router = APIRouter(prefix="/api/v1/scientific-objects", tags=["Unified Public API — Scientific Objects"])


class ExternalReferenceCreate(BaseModel):
    uri: str = Field(min_length=1, max_length=3000)
    title: str = Field(min_length=1, max_length=1000)
    format: str = Field(min_length=1, max_length=100)
    media_type: str | None = Field(default=None, max_length=300)
    size_bytes: int | None = Field(default=None, ge=0)
    content_hash: str | None = Field(default=None, max_length=128)
    checksum_algorithm: str | None = Field(default=None, max_length=40)
    scientific_asset_id: str | None = None
    parent_object_id: str | None = None
    public: bool = False
    retention_class: str = Field(default="provider-managed", min_length=1, max_length=80)
    license_name: str | None = Field(default=None, max_length=300)
    attribution: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str = Field(default="operator", min_length=1, max_length=255)
    derived: bool = False


class ProcessingCreate(BaseModel):
    input_object_id: str
    adapter_key: str = Field(min_length=1, max_length=160)
    operation: str = Field(min_length=1, max_length=120)
    idempotency_key: str = Field(min_length=1, max_length=255)
    parameters: dict[str, Any] = Field(default_factory=dict)
    requested_by: str = Field(default="operator", min_length=1, max_length=255)


def bad(exc: Exception) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))


def require_public_metadata_enabled(request: Request) -> None:
    if not request.app.state.settings.scientific_object_public_metadata_enabled:
        raise HTTPException(status_code=404, detail="Scientific object public metadata API is disabled.")


@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request: Request, db: Session = Depends(get_session)):
    data = scientific_objects.readiness(db, request.app.state.settings)
    migrations = migration_status(request.app.state.database)
    data.update({
        "release": request.app.state.settings.version,
        "migration_0030_applied": "0030" in migrations["applied"],
        "scientific_asset_registry_integrated": True,
        "derived_object_lineage": True,
        "credential_free_external_references": True,
    })
    return data


@router.get("", dependencies=[Depends(require_read)])
def objects(
    backend_key: str | None = None,
    format: str | None = None,
    scientific_asset_id: str | None = None,
    parent_object_id: str | None = None,
    derived: bool | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
):
    rows, total = scientific_objects.list_objects(
        db,
        backend_key=backend_key,
        format_name=format,
        scientific_asset_id=scientific_asset_id,
        parent_object_id=parent_object_id,
        derived=derived,
        limit=limit,
        offset=offset,
    )
    return {"items": [scientific_objects.object_read(row) for row in rows], "total": total, "limit": limit, "offset": offset}


@router.get("/adapters", dependencies=[Depends(require_read)])
def adapters(db: Session = Depends(get_session)):
    return {"items": [scientific_objects.adapter_read(row) for row in scientific_objects.list_adapters(db)]}


@router.get("/processing-runs/{run_id}", dependencies=[Depends(require_read)])
def processing_run(run_id: str, db: Session = Depends(get_session)):
    return scientific_objects.run_read(scientific_objects.processing_run_or_404(db, run_id))


@router.get("/{object_id}", dependencies=[Depends(require_read)])
def object_detail(object_id: str, db: Session = Depends(get_session)):
    return scientific_objects.object_read(scientific_objects.object_or_404(db, object_id))


@router.get("/{object_id}/content", dependencies=[Depends(require_read)])
def object_content(object_id: str, request: Request, db: Session = Depends(get_session)):
    row = scientific_objects.object_or_404(db, object_id)
    try:
        path = scientific_objects.content_path(db, request.app.state.settings, object_id)
    except ValueError as exc:
        raise bad(exc)
    return FileResponse(path=path, media_type=row.media_type or "application/octet-stream", filename=path.name)


@router.put("/upload/{format_name}", dependencies=[Depends(require_write)])
async def upload_object(
    format_name: str,
    request: Request,
    title: str = Query(min_length=1, max_length=1000),
    scientific_asset_id: str | None = None,
    parent_object_id: str | None = None,
    public: bool = False,
    retention_class: str = "standard",
    license_name: str | None = None,
    attribution: str | None = None,
    created_by: str = "operator",
    db: Session = Depends(get_session),
):
    payload = await request.body()
    if not payload:
        raise HTTPException(status_code=422, detail="Scientific object upload body is empty.")
    try:
        row = scientific_objects.store_bytes(
            db,
            request.app.state.settings,
            payload,
            title=title,
            format_name=format_name,
            media_type=request.headers.get("content-type"),
            scientific_asset_id=scientific_asset_id,
            parent_object_id=parent_object_id,
            public=public,
            retention_class=retention_class,
            license_name=license_name,
            attribution=attribution,
            provenance={"ingest_method": "direct-upload", "core_release": request.app.state.settings.version},
            created_by=created_by,
        )
    except ValueError as exc:
        raise bad(exc)
    return scientific_objects.object_read(row)


@router.post("/register-reference", dependencies=[Depends(require_write)])
def register_reference(payload: ExternalReferenceCreate, request: Request, db: Session = Depends(get_session)):
    try:
        row = scientific_objects.register_external_reference(
            db,
            request.app.state.settings,
            format_name=payload.format,
            **payload.model_dump(exclude={"format"}),
        )
    except ValueError as exc:
        raise bad(exc)
    return scientific_objects.object_read(row)


@router.post("/process", dependencies=[Depends(require_write)])
def process(payload: ProcessingCreate, request: Request, db: Session = Depends(get_session)):
    try:
        row = scientific_objects.process_object(db, request.app.state.settings, **payload.model_dump())
    except ValueError as exc:
        raise bad(exc)
    return scientific_objects.run_read(row)


@public_router.get("/readiness", response_model=PublicEnvelope)
def public_readiness(request: Request, db: Session = Depends(get_session), _context: PublicApiContext = Depends(require_public_scope("data:read"))):
    require_public_metadata_enabled(request)
    data = scientific_objects.readiness(db, request.app.state.settings)
    safe = {
        "enabled": data["enabled"],
        "processing_enabled": data["processing_enabled"],
        "stored_objects": data["stored_objects"],
        "external_references": data["external_references"],
        "processing_adapters": data["processing_adapters"],
        "executable_adapters": data["executable_adapters"],
        "arbitrary_code_execution": False,
        "credential_values_persisted": False,
        "external_fetch_by_core": False,
        "release": request.app.state.settings.version,
    }
    return PublicEnvelope(data=safe, meta={"api_version": "v1", "request_id": request.state.request_id})


@public_router.get("", response_model=PublicEnvelope)
def public_objects(
    request: Request,
    backend_key: str | None = None,
    format: str | None = None,
    scientific_asset_id: str | None = None,
    parent_object_id: str | None = None,
    derived: bool | None = None,
    limit: int = Query(default=100, ge=1),
    offset: int = Query(default=0, ge=0),
    context: PublicApiContext = Depends(require_public_scope("data:read")),
    db: Session = Depends(get_session),
):
    require_public_metadata_enabled(request)
    limit = min(limit, context.plan.max_page_size, request.app.state.settings.page_size_max)
    rows, total = scientific_objects.list_objects(
        db,
        backend_key=backend_key,
        format_name=format,
        scientific_asset_id=scientific_asset_id,
        parent_object_id=parent_object_id,
        derived=derived,
        public_only=True,
        limit=limit,
        offset=offset,
    )
    return PublicEnvelope(data=[scientific_objects.object_read(row) for row in rows], meta={"api_version": "v1", "request_id": request.state.request_id, "pagination": {"total": total, "limit": limit, "offset": offset}})


@public_router.get("/adapters", response_model=PublicEnvelope)
def public_adapters(request: Request, db: Session = Depends(get_session), _context: PublicApiContext = Depends(require_public_scope("data:read"))):
    require_public_metadata_enabled(request)
    rows = scientific_objects.list_adapters(db, public_only=True)
    return PublicEnvelope(data=[scientific_objects.adapter_read(row) for row in rows], meta={"api_version": "v1", "request_id": request.state.request_id})


@public_router.get("/{object_id}", response_model=PublicEnvelope)
def public_object(object_id: str, request: Request, db: Session = Depends(get_session), _context: PublicApiContext = Depends(require_public_scope("data:read"))):
    require_public_metadata_enabled(request)
    row = scientific_objects.object_or_404(db, object_id, public_only=True)
    return PublicEnvelope(data=scientific_objects.object_read(row), meta={"api_version": "v1", "request_id": request.state.request_id})
