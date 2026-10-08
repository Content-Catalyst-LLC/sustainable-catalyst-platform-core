from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..models import LiveDataConnector
from ..services.connector_execution_profiles import (
    all_profiles,
    get_profile,
    profile_contract_document,
    profile_requested_by,
    reference_connector_profile_contract,
    resolve_profile_parameters,
    scheduled_profiles,
    validate_profile_against_connector,
)
from ..services.reliability import queue_connector_work

router = APIRouter(
    prefix="/v1/connector-profiles",
    tags=["Parameterized Connector Execution Profiles"],
)
public_router = APIRouter(
    prefix="/public/v1/connector-profiles",
    tags=["Parameterized Connector Execution Profiles — Public"],
)


class ProfileQueueRequest(BaseModel):
    overrides: dict[str, Any] = Field(default_factory=dict)


def _profile_payload(profile):
    payload = profile.model_dump(mode="json")
    payload["fingerprint_sha256"] = profile.fingerprint()
    return payload


@router.get("/contract", dependencies=[Depends(require_read)])
def contract():
    return profile_contract_document()


@public_router.get("/contract")
def public_contract():
    return profile_contract_document()


@router.get("/profiles", dependencies=[Depends(require_read)])
def profiles(connector_id: str | None = None, mode: str | None = None):
    items = all_profiles()
    if connector_id:
        items = [profile for profile in items if profile.connector_id == connector_id]
    if mode:
        items = [profile for profile in items if profile.mode.value == mode]
    return {"ok": True, "count": len(items), "items": [_profile_payload(item) for item in items]}


@public_router.get("/profiles")
def public_profiles(connector_id: str | None = None, mode: str | None = None):
    return profiles(connector_id=connector_id, mode=mode)


@router.get("/profiles/{profile_id:path}", dependencies=[Depends(require_read)])
def profile(profile_id: str):
    item = get_profile(profile_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Unknown connector execution profile.")
    return {"ok": True, "item": _profile_payload(item)}


@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request: Request, db: Session = Depends(get_session)):
    runtime = request.app.state.live_data_runtime
    settings = request.app.state.settings
    allowlist = set(settings.parameterized_profile_scheduler_ids)
    rows = []

    for item in all_profiles():
        connector = db.get(LiveDataConnector, item.connector_id)
        config_status = (
            runtime.connector_configuration_status(connector)
            if connector is not None
            else "connector_missing"
        )
        selected = item.scheduler_eligible and (not allowlist or item.profile_id in allowlist)
        rows.append(
            {
                "profile_id": item.profile_id,
                "connector_id": item.connector_id,
                "mode": item.mode.value,
                "scheduler_eligible": item.scheduler_eligible,
                "selected_by_allowlist": selected,
                "connector_configuration_status": config_status,
                "required_parameters": item.required_parameters,
                "required_one_of": item.required_one_of,
                "fingerprint_sha256": item.fingerprint(),
            }
        )

    return {
        "ok": True,
        "release": "4.21.0",
        "scheduler_enabled": settings.parameterized_profile_scheduler_enabled,
        "allowlist": list(settings.parameterized_profile_scheduler_ids),
        "max_per_pass": settings.parameterized_profile_max_per_pass,
        "profile_count": len(rows),
        "scheduler_eligible_count": len(scheduled_profiles()),
        "items": rows,
        "generated_at": datetime.now(timezone.utc),
    }


@router.post(
    "/profiles/{profile_id:path}/queue",
    dependencies=[Depends(require_write)],
)
def queue_profile(
    profile_id: str,
    payload: ProfileQueueRequest,
    request: Request,
    db: Session = Depends(get_session),
):
    item = get_profile(profile_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Unknown connector execution profile.")

    connector = db.get(LiveDataConnector, item.connector_id)
    if connector is None:
        raise HTTPException(status_code=409, detail="Profile connector is not registered.")

    runtime = request.app.state.live_data_runtime
    config_status = runtime.connector_configuration_status(connector)
    if config_status != "configured":
        raise HTTPException(
            status_code=409,
            detail=f"Connector configuration status is {config_status}.",
        )

    try:
        parameters = resolve_profile_parameters(
            item,
            now=datetime.now(timezone.utc),
            overrides=payload.overrides,
        )
        validate_profile_against_connector(
            item,
            connector,
            parameters=parameters,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    work = queue_connector_work(
        db,
        item.connector_id,
        parameters=parameters,
        requested_by=profile_requested_by(item.profile_id),
        priority=item.priority,
        max_attempts=item.max_attempts,
    )

    return {
        "ok": True,
        "profile_id": item.profile_id,
        "connector_id": item.connector_id,
        "work_item_id": work.id,
        "status": work.status,
        "requested_by": work.requested_by,
    }


@router.get("/reference", dependencies=[Depends(require_read)])
def reference():
    bundle = reference_connector_profile_contract()
    return {
        "ok": True,
        "bundle_fingerprint_sha256": bundle.fingerprint(),
        "bundle": bundle.model_dump(mode="json"),
    }
