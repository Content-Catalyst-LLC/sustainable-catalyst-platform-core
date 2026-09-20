from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_arguments as svc

router = APIRouter(prefix="/v1/research/arguments", tags=["Research Argument & Evidentiary Synthesis Engine"])
public_router = APIRouter(prefix="/api/v1/research/arguments", tags=["Unified Public API — Research Argument Intelligence"])


class Payload(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)


def enabled(request: Request):
    if not request.app.state.settings.research_argument_evidentiary_synthesis_enabled:
        raise HTTPException(503, "Research Argument & Evidentiary Synthesis Engine is disabled.")


def call(fn, *args):
    try:
        return fn(*args)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/readiness", dependencies=[Depends(require_read)])
def ready(request: Request, db: Session = Depends(get_session)):
    enabled(request)
    out = svc.readiness(db)
    out["migration_0083_applied"] = "0083" in migration_status(request.app.state.database)["applied"]
    return out


@router.post("/projects/{project_id}", dependencies=[Depends(require_write)])
def create_argument(project_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.create_argument, db, project_id, payload.data)


@router.post("/{argument_id}/revisions", dependencies=[Depends(require_write)])
def revise_argument(argument_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.revise_argument, db, argument_id, payload.data)


@router.post("/{argument_id}/nodes", dependencies=[Depends(require_write)])
def add_node(argument_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.add_node, db, argument_id, payload.data)


@router.post("/{argument_id}/edges", dependencies=[Depends(require_write)])
def add_edge(argument_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.add_edge, db, argument_id, payload.data)


@router.post("/{argument_id}/syntheses", dependencies=[Depends(require_write)])
def create_synthesis(argument_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.create_synthesis, db, argument_id, payload.data)


@router.post("/syntheses/{synthesis_id}/components", dependencies=[Depends(require_write)])
def add_synthesis_component(synthesis_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.add_synthesis_component, db, synthesis_id, payload.data)


@router.post("/{argument_id}/counterarguments", dependencies=[Depends(require_write)])
def add_counterargument(argument_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.add_counterargument, db, argument_id, payload.data)


@router.post("/{argument_id}/tensions", dependencies=[Depends(require_write)])
def add_tension(argument_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.add_tension, db, argument_id, payload.data)


@router.get("/{argument_id}/map", dependencies=[Depends(require_read)])
def argument_map(argument_id: str, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.argument_map, db, argument_id)


@router.get("/{argument_id}/bundle", dependencies=[Depends(require_read)])
def argument_bundle(argument_id: str, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.bundle, db, argument_id)


@router.post("/{argument_id}/snapshots", dependencies=[Depends(require_write)])
def argument_snapshot(argument_id: str, payload: Payload, request: Request, db: Session = Depends(get_session)):
    enabled(request)
    return call(svc.snapshot, db, argument_id, payload.data)


@public_router.get("/{argument_id}/map", response_model=PublicEnvelope)
def public_map(
    argument_id: str,
    request: Request,
    db: Session = Depends(get_session),
    ctx: PublicApiContext = Depends(require_public_scope("data:read")),
):
    enabled(request)
    return PublicEnvelope(
        data=call(svc.argument_map, db, argument_id, True),
        meta={"release": "2.79.0", "contract": svc.CONTRACT},
    )


@public_router.get("/{argument_id}/bundle", response_model=PublicEnvelope)
def public_bundle(
    argument_id: str,
    request: Request,
    db: Session = Depends(get_session),
    ctx: PublicApiContext = Depends(require_public_scope("data:read")),
):
    enabled(request)
    return PublicEnvelope(
        data=call(svc.bundle, db, argument_id, True),
        meta={"release": "2.79.0", "contract": svc.CONTRACT},
    )
