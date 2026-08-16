from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import credentials

router = APIRouter(prefix="/v1/credentials", tags=["Identity, Credential & Cryptographic Key Lifecycle"])
public_router = APIRouter(prefix="/api/v1/credentials", tags=["Unified Public API — Credential Lifecycle"])

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class CredentialWrite(StrictModel):
    credential_key: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=300)
    credential_type: str = Field(min_length=1, max_length=80)
    purpose: str = Field(min_length=1, max_length=300)
    owner_scope: str = Field(default="platform-core", min_length=1, max_length=120)
    provider: str = Field(default="environment", min_length=1, max_length=120)
    secret_reference: str = Field(min_length=1, max_length=1000)
    allowed_consumers: list[str] = Field(default_factory=list)
    allowed_operations: list[str] = Field(default_factory=list)
    rotation_interval_days: int | None = Field(default=None, ge=1, le=3650)
    overlap_minutes: int | None = Field(default=None, ge=0, le=10080)
    status: str = "active"
    enabled: bool = True
    public_summary: bool = False
    metadata: dict = Field(default_factory=dict)

class KeyVersionWrite(StrictModel):
    key_id: str | None = Field(default=None, max_length=255)
    algorithm: str = Field(default="opaque", min_length=1, max_length=80)
    fingerprint_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)

class RotationWrite(StrictModel):
    to_key_version_id: str
    requested_by: str = Field(default="operator", max_length=255)
    reason: str = Field(default="scheduled-rotation", max_length=500)
    overlap_minutes: int | None = Field(default=None, ge=0, le=10080)
    metadata: dict = Field(default_factory=dict)

class CompleteRotationWrite(StrictModel):
    actor: str = Field(default="operator", max_length=255)

class RevokeWrite(StrictModel):
    reason: str = Field(min_length=1, max_length=500)
    actor: str = Field(default="operator", max_length=255)
    compromised: bool = False

class UseWrite(StrictModel):
    service_id: str = Field(min_length=1, max_length=255)
    operation: str = Field(min_length=1, max_length=120)
    key_version_id: str | None = None
    success: bool = True
    context: dict = Field(default_factory=dict)
    occurred_at: datetime | None = None

def bad(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))

@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request: Request, db: Session = Depends(get_session)):
    body = credentials.readiness(db, request.app.state.settings)
    migrations = migration_status(request.app.state.database)
    body.update({"release": request.app.state.settings.version, "migration_0028_applied": "0028" in migrations["applied"], "pending_migrations": migrations["pending"]})
    return body

@router.post("/registry", dependencies=[Depends(require_write)])
def write_registry(payload: CredentialWrite, request: Request, db: Session = Depends(get_session)):
    try:
        return jsonable_encoder(credentials.credential_dict(credentials.upsert_credential(db, request.app.state.settings, **payload.model_dump())))
    except ValueError as exc: raise bad(exc)

@router.get("/registry", dependencies=[Depends(require_read)])
def registry(enabled_only: bool = Query(False), db: Session = Depends(get_session)):
    return {"items": jsonable_encoder([credentials.credential_dict(row) for row in credentials.list_credentials(db, enabled_only=enabled_only)])}

@router.post("/bootstrap/core", dependencies=[Depends(require_write)])
def bootstrap(request: Request, db: Session = Depends(get_session)):
    rows = credentials.bootstrap_core_credentials(db, request.app.state.settings)
    return {"items": jsonable_encoder([credentials.credential_dict(row) for row in rows]), "secret_values_persisted": False}

@router.post("/registry/{credential_id}/versions", dependencies=[Depends(require_write)])
def register_version(credential_id: str, payload: KeyVersionWrite, request: Request, db: Session = Depends(get_session)):
    try:
        return jsonable_encoder(credentials.key_version_dict(credentials.register_key_version(db, request.app.state.settings, credential_id, **payload.model_dump())))
    except ValueError as exc: raise bad(exc)

@router.get("/registry/{credential_id}/versions", dependencies=[Depends(require_read)])
def versions(credential_id: str, db: Session = Depends(get_session)):
    try: return {"items": jsonable_encoder([credentials.key_version_dict(row) for row in credentials.list_key_versions(db, credential_id)])}
    except ValueError as exc: raise bad(exc)

@router.post("/registry/{credential_id}/rotate", dependencies=[Depends(require_write)])
def rotate(credential_id: str, payload: RotationWrite, db: Session = Depends(get_session)):
    try: return jsonable_encoder(credentials.rotation_dict(credentials.rotate(db, credential_id, **payload.model_dump())))
    except ValueError as exc: raise bad(exc)

@router.get("/rotations", dependencies=[Depends(require_read)])
def rotations(credential_id: str | None = Query(None), limit: int = Query(200, ge=1, le=5000), db: Session = Depends(get_session)):
    return {"items": jsonable_encoder([credentials.rotation_dict(row) for row in credentials.list_rotations(db, credential_id, limit=limit)])}

@router.post("/rotations/{rotation_id}/complete", dependencies=[Depends(require_write)])
def complete(rotation_id: str, payload: CompleteRotationWrite, db: Session = Depends(get_session)):
    try: return jsonable_encoder(credentials.rotation_dict(credentials.complete_rotation(db, rotation_id, actor=payload.actor)))
    except ValueError as exc: raise bad(exc)

@router.post("/versions/{key_version_id}/revoke", dependencies=[Depends(require_write)])
def revoke(key_version_id: str, payload: RevokeWrite, db: Session = Depends(get_session)):
    try: return jsonable_encoder(credentials.key_version_dict(credentials.revoke_key(db, key_version_id, **payload.model_dump())))
    except ValueError as exc: raise bad(exc)

@router.post("/registry/{credential_id}/use-events", dependencies=[Depends(require_write)])
def record_use(credential_id: str, payload: UseWrite, db: Session = Depends(get_session)):
    try: return jsonable_encoder(credentials.use_event_dict(credentials.record_use(db, credential_id, **payload.model_dump())))
    except ValueError as exc: raise bad(exc)

@router.get("/use-events", dependencies=[Depends(require_read)])
def use_events(credential_id: str | None = Query(None), limit: int = Query(200, ge=1, le=5000), db: Session = Depends(get_session)):
    return {"items": jsonable_encoder([credentials.use_event_dict(row) for row in credentials.list_use_events(db, credential_id, limit=limit)])}

@router.get("/events", dependencies=[Depends(require_read)])
def events(credential_id: str | None = Query(None), limit: int = Query(200, ge=1, le=5000), db: Session = Depends(get_session)):
    return {"items": jsonable_encoder([credentials.lifecycle_event_dict(row) for row in credentials.list_lifecycle_events(db, credential_id, limit=limit)])}

@public_router.get("/status")
def public_status(request: Request, db: Session = Depends(get_session), _context: PublicApiContext = Depends(require_public_scope("data:read"))):
    safe = credentials.public_status(db, request.app.state.settings); safe["release"] = request.app.state.settings.version
    return PublicEnvelope(data=safe, meta={"api_version": "v1", "request_id": request.state.request_id})
