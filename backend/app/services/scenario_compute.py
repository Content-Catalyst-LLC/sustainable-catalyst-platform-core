from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    Entity, ResearchModelRecord, ResearchModelVersionRecord, ResearchParameterRecord,
    ResearchScenarioRecord, ResearchModelRunRecord, ResearchResultRecord,
    ScenarioLandscapeRecord, ModelCanvasRecord,
    ScenarioComputePlanRecord, ScenarioComputeCaseRecord, ScenarioComputeRequestRecord,
    ScenarioComputeAttemptRecord, ScenarioComputeResultBindingRecord,
)

PLAN_STATES = {"draft", "ready", "closed", "archived"}
EXECUTION_PRODUCTS = {"lab", "workbench", "external"}
CASE_ROLES = {"baseline", "alternative", "reference", "stress", "sensitivity", "custom"}
REQUEST_STATES = {"requested", "accepted", "queued", "running", "completed", "failed", "cancelled"}
ATTEMPT_STATES = {"accepted", "queued", "running", "completed", "failed", "cancelled"}
BINDING_ROLES = {"primary", "diagnostic", "intermediate", "artifact", "summary"}

def _now():
    return datetime.now(timezone.utc)

def _ser(row):
    out = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        out[column.name] = value
    return out

def _hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(raw).hexdigest()

def _plan(db: Session, plan_id: str, *, public_only: bool = False) -> ScenarioComputePlanRecord:
    row = db.get(ScenarioComputePlanRecord, plan_id)
    if row is None or (public_only and row.visibility != "public"):
        raise HTTPException(status_code=404, detail="Scenario compute plan not found.")
    return row

def _entity(db: Session, entity_id: str, entity_type: str, field: str):
    row = db.get(Entity, entity_id)
    if row is None or row.entity_type != entity_type:
        raise ValueError(f"{field} must reference a {entity_type} entity.")
    return row

def _model(db: Session, model_id: str, project_id: str) -> ResearchModelRecord:
    _entity(db, model_id, "model", "model_entity_id")
    model = db.get(ResearchModelRecord, model_id)
    if model is None:
        raise ValueError("model_entity_id must reference a research model.")
    if model.project_entity_id and model.project_entity_id != project_id:
        raise ValueError("model_entity_id belongs to a different research project.")
    if model.execution_target == "not-executable":
        raise ValueError("Scenario compute plans require an executable research model.")
    return model

def _version(db: Session, version_id: str, model_id: str) -> ResearchModelVersionRecord:
    _entity(db, version_id, "model-version", "model_version_entity_id")
    version = db.get(ResearchModelVersionRecord, version_id)
    if version is None or version.model_entity_id != model_id:
        raise ValueError("model_version_entity_id must reference an immutable version of the plan model.")
    if not version.immutable:
        raise ValueError("Scenario compute plans require an immutable model version.")
    return version

def _scenario(db: Session, scenario_id: str, project_id: str) -> ResearchScenarioRecord:
    _entity(db, scenario_id, "scenario", "scenario_entity_id")
    scenario = db.get(ResearchScenarioRecord, scenario_id)
    if scenario is None or scenario.project_entity_id != project_id:
        raise ValueError("scenario_entity_id belongs to a different research project.")
    return scenario

def _parameter_catalog(db: Session, model_id: str) -> dict[str, ResearchParameterRecord]:
    rows = db.scalars(select(ResearchParameterRecord).where(ResearchParameterRecord.model_entity_id == model_id)).all()
    out: dict[str, ResearchParameterRecord] = {}
    for row in rows:
        out[row.entity_id] = row
        out[row.name] = row
    return out

def _unwrap_number(value: Any):
    if isinstance(value, dict) and "value" in value:
        value = value["value"]
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None

def _validate_overrides(db: Session, plan: ScenarioComputePlanRecord, overrides: dict[str, Any]) -> None:
    catalog = _parameter_catalog(db, plan.model_entity_id)
    for key, value in overrides.items():
        parameter = catalog.get(str(key))
        if parameter is None:
            raise ValueError(f"Unknown model parameter override: {key}")
        numeric = _unwrap_number(value)
        if numeric is None:
            continue
        bounds = dict(parameter.bounds_json or {})
        if bounds.get("min") is not None and numeric < float(bounds["min"]):
            raise ValueError(f"Parameter {parameter.name} is below its declared minimum.")
        if bounds.get("max") is not None and numeric > float(bounds["max"]):
            raise ValueError(f"Parameter {parameter.name} is above its declared maximum.")

def readiness(db: Session) -> dict[str, Any]:
    counts = {
        "plans": db.scalar(select(func.count()).select_from(ScenarioComputePlanRecord)) or 0,
        "cases": db.scalar(select(func.count()).select_from(ScenarioComputeCaseRecord)) or 0,
        "requests": db.scalar(select(func.count()).select_from(ScenarioComputeRequestRecord)) or 0,
        "attempts": db.scalar(select(func.count()).select_from(ScenarioComputeAttemptRecord)) or 0,
        "result_bindings": db.scalar(select(func.count()).select_from(ScenarioComputeResultBindingRecord)) or 0,
    }
    return {
        "counts": counts,
        "research_scenarios_reused": True,
        "immutable_model_versions_required": True,
        "parameter_bounds_validation": True,
        "deterministic_input_manifests": True,
        "idempotent_execution_requests": True,
        "lab_workbench_execution_handoff": True,
        "model_run_result_bindings": True,
        "orchestration_by_core": True,
        "network_dispatch_by_core": False,
        "numerical_computation_by_core": False,
        "arbitrary_code_execution_by_core": False,
        "automatic_truth_promotion": False,
    }

def create_plan(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    project_id = str(payload.get("project_entity_id") or "")
    model_id = str(payload.get("model_entity_id") or "")
    version_id = str(payload.get("model_version_entity_id") or "")
    _entity(db, project_id, "research-project", "project_entity_id")
    model = _model(db, model_id, project_id)
    _version(db, version_id, model_id)
    execution_product = str(payload.get("execution_product") or model.execution_target)
    if execution_product not in EXECUTION_PRODUCTS:
        raise ValueError("execution_product must be lab, workbench, or external.")
    if model.execution_target in {"lab", "workbench"} and execution_product != model.execution_target:
        raise ValueError("execution_product must match the model execution target.")
    plan_state = str(payload.get("plan_state") or "draft")
    if plan_state not in PLAN_STATES:
        raise ValueError("Unsupported plan_state.")
    landscape_id = payload.get("scenario_landscape_visual_entity_id")
    if landscape_id:
        landscape = db.get(ScenarioLandscapeRecord, landscape_id)
        if landscape is None or landscape.project_entity_id != project_id:
            raise ValueError("scenario_landscape_visual_entity_id must belong to the plan project.")
    canvas_id = payload.get("model_canvas_visual_entity_id")
    if canvas_id:
        canvas = db.get(ModelCanvasRecord, canvas_id)
        if canvas is None or canvas.project_entity_id != project_id or canvas.model_entity_id != model_id:
            raise ValueError("model_canvas_visual_entity_id must belong to the plan model and project.")
    contract = dict(payload.get("execution_contract") or {})
    if contract.get("execute_by_core") is True:
        raise ValueError("Platform Core cannot be selected as the numerical scenario executor.")
    row = ScenarioComputePlanRecord(
        plan_key=str(payload.get("plan_key") or "scenario-plan"),
        name=str(payload.get("name") or "Scenario compute plan"),
        description=payload.get("description"),
        visibility=str(payload.get("visibility") or "private"),
        project_entity_id=project_id, model_entity_id=model_id, model_version_entity_id=version_id,
        scenario_landscape_visual_entity_id=landscape_id, model_canvas_visual_entity_id=canvas_id,
        plan_state=plan_state, execution_product=execution_product, execution_contract_json=contract,
        output_contract_json=dict(payload.get("output_contract") or {}),
        concurrency_policy_json=dict(payload.get("concurrency_policy") or {}),
        metadata_json=dict(payload.get("metadata") or {}), created_by=str(payload.get("created_by") or "operator"),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Scenario compute plan key already exists for this project.") from exc
    return _ser(row)

def list_plans(db: Session, *, public_only: bool = False, limit: int = 100, offset: int = 0):
    q = select(ScenarioComputePlanRecord)
    cq = select(func.count()).select_from(ScenarioComputePlanRecord)
    if public_only:
        q = q.where(ScenarioComputePlanRecord.visibility == "public")
        cq = cq.where(ScenarioComputePlanRecord.visibility == "public")
    total = int(db.scalar(cq) or 0)
    rows = db.scalars(q.order_by(ScenarioComputePlanRecord.created_at.desc()).limit(limit).offset(offset)).all()
    return [_ser(row) for row in rows], total

def read_plan(db: Session, plan_id: str, *, public_only: bool = False):
    return _ser(_plan(db, plan_id, public_only=public_only))

def add_case(db: Session, plan_id: str, payload: dict[str, Any]):
    plan = _plan(db, plan_id)
    scenario_id = str(payload.get("scenario_entity_id") or "")
    scenario = _scenario(db, scenario_id, plan.project_entity_id)
    role = str(payload.get("comparison_role") or "alternative")
    if role not in CASE_ROLES:
        raise ValueError("Unsupported comparison_role.")
    overrides = dict(payload.get("parameter_overrides") or {})
    _validate_overrides(db, plan, overrides)
    canonical = {
        "model_version_entity_id": plan.model_version_entity_id,
        "scenario_entity_id": scenario_id,
        "scenario_parameter_values": dict(scenario.parameter_values_json or {}),
        "parameter_overrides": overrides,
        "expected_outputs": list(payload.get("expected_outputs") or []),
    }
    row = ScenarioComputeCaseRecord(
        plan_id=plan_id, case_key=str(payload.get("case_key") or scenario_id),
        label=str(payload.get("label") or db.get(Entity, scenario_id).name), scenario_entity_id=scenario_id,
        comparison_role=role, parameter_overrides_json=overrides,
        expected_outputs_json=list(payload.get("expected_outputs") or []), case_hash=_hash(canonical),
        enabled=bool(payload.get("enabled", True)), metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Scenario compute case key already exists for this plan.") from exc
    return _ser(row)

def validate_plan(db: Session, plan_id: str, *, public_only: bool = False):
    plan = _plan(db, plan_id, public_only=public_only)
    cases = db.scalars(select(ScenarioComputeCaseRecord).where(ScenarioComputeCaseRecord.plan_id == plan_id)).all()
    errors: list[str] = []
    warnings: list[str] = []
    if not cases:
        warnings.append("plan_has_no_cases")
    if not any(case.enabled for case in cases):
        warnings.append("plan_has_no_enabled_cases")
    for case in cases:
        try:
            _scenario(db, case.scenario_entity_id, plan.project_entity_id)
            _validate_overrides(db, plan, dict(case.parameter_overrides_json or {}))
        except Exception as exc:
            errors.append(f"case:{case.id}:{exc}")
    return {
        "valid": not errors, "counts": {"cases": len(cases), "enabled_cases": sum(1 for case in cases if case.enabled)},
        "errors": errors, "warnings": sorted(set(warnings)),
        "orchestration_only": True, "network_dispatch_performed": False,
        "numerical_computation_performed": False, "arbitrary_code_execution_performed": False,
        "truth_promotion_performed": False,
    }

def _manifest(plan: ScenarioComputePlanRecord, case: ScenarioComputeCaseRecord, scenario: ResearchScenarioRecord) -> dict[str, Any]:
    merged = dict(scenario.parameter_values_json or {})
    merged.update(dict(case.parameter_overrides_json or {}))
    return {
        "schema": "scenario-compute-input-manifest-v1",
        "plan_id": plan.id, "case_id": case.id,
        "project_entity_id": plan.project_entity_id, "model_entity_id": plan.model_entity_id,
        "model_version_entity_id": plan.model_version_entity_id, "scenario_entity_id": case.scenario_entity_id,
        "execution_product": plan.execution_product, "parameter_values": merged,
        "scenario_parameter_values": dict(scenario.parameter_values_json or {}),
        "parameter_overrides": dict(case.parameter_overrides_json or {}),
        "expected_outputs": list(case.expected_outputs_json or []),
        "execution_contract": dict(plan.execution_contract_json or {}),
        "output_contract": dict(plan.output_contract_json or {}),
        "case_hash": case.case_hash,
        "core_execution": False,
    }

def prepare_requests(db: Session, plan_id: str, *, submitted_by: str = "operator"):
    plan = _plan(db, plan_id)
    validation = validate_plan(db, plan_id)
    if not validation["valid"]:
        raise ValueError("Scenario compute plan is not valid.")
    cases = db.scalars(select(ScenarioComputeCaseRecord).where(ScenarioComputeCaseRecord.plan_id == plan_id, ScenarioComputeCaseRecord.enabled.is_(True)).order_by(ScenarioComputeCaseRecord.created_at)).all()
    prepared = []
    for case in cases:
        scenario = _scenario(db, case.scenario_entity_id, plan.project_entity_id)
        manifest = _manifest(plan, case, scenario)
        request_hash = _hash(manifest)
        key = f"{case.case_hash}:{plan.model_version_entity_id}:{request_hash}"
        existing = db.scalar(select(ScenarioComputeRequestRecord).where(ScenarioComputeRequestRecord.plan_id == plan_id, ScenarioComputeRequestRecord.idempotency_key == key))
        if existing is not None:
            prepared.append(_ser(existing)); continue
        row = ScenarioComputeRequestRecord(
            plan_id=plan_id, case_id=case.id, idempotency_key=key, request_state="requested",
            requested_product=plan.execution_product, input_manifest_json=manifest, request_hash=request_hash,
            submitted_by=submitted_by, metadata_json={"prepared_by_core": True, "network_dispatch_performed": False},
        )
        db.add(row); db.commit(); db.refresh(row); prepared.append(_ser(row))
    return {"plan_id": plan_id, "prepared": prepared, "count": len(prepared), "network_dispatch_performed": False, "numerical_computation_performed": False}

def read_request(db: Session, request_id: str):
    row = db.get(ScenarioComputeRequestRecord, request_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Scenario compute request not found.")
    return _ser(row)

def add_attempt(db: Session, request_id: str, payload: dict[str, Any]):
    request = db.get(ScenarioComputeRequestRecord, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Scenario compute request not found.")
    state = str(payload.get("attempt_state") or "accepted")
    if state not in ATTEMPT_STATES:
        raise ValueError("Unsupported attempt_state.")
    product = str(payload.get("executor_product") or request.requested_product)
    if product not in EXECUTION_PRODUCTS or product != request.requested_product:
        raise ValueError("executor_product must match the execution request product.")
    if bool(payload.get("executed_by_core", False)):
        raise ValueError("Scenario numerical execution cannot be attributed to Platform Core.")
    next_number = int(db.scalar(select(func.count()).select_from(ScenarioComputeAttemptRecord).where(ScenarioComputeAttemptRecord.request_id == request_id)) or 0) + 1
    now = _now()
    row = ScenarioComputeAttemptRecord(
        request_id=request_id, attempt_number=next_number, attempt_state=state, executor_product=product,
        external_execution_id=payload.get("external_execution_id"), runtime_metadata_json=dict(payload.get("runtime_metadata") or {}),
        error_json=dict(payload.get("error") or {}),
        started_at=now if state in {"running", "completed", "failed"} else None,
        completed_at=now if state in {"completed", "failed", "cancelled"} else None,
    )
    db.add(row)
    request.request_state = state if state in REQUEST_STATES else request.request_state
    if payload.get("external_request_id"):
        request.external_request_id = str(payload["external_request_id"])
    db.add(request); db.commit(); db.refresh(row)
    return _ser(row)

def bind_model_run(db: Session, request_id: str, model_run_entity_id: str):
    request = db.get(ScenarioComputeRequestRecord, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Scenario compute request not found.")
    case = db.get(ScenarioComputeCaseRecord, request.case_id); plan = db.get(ScenarioComputePlanRecord, request.plan_id)
    _entity(db, model_run_entity_id, "model-run", "model_run_entity_id")
    run = db.get(ResearchModelRunRecord, model_run_entity_id)
    if run is None or run.model_version_entity_id != plan.model_version_entity_id or run.scenario_entity_id != case.scenario_entity_id:
        raise ValueError("model_run_entity_id must match the request model version and scenario.")
    if run.executor_product != request.requested_product:
        raise ValueError("model run executor_product does not match the request.")
    request.model_run_entity_id = model_run_entity_id
    request.request_state = run.run_status if run.run_status in REQUEST_STATES else request.request_state
    db.add(request); db.commit(); db.refresh(request); return _ser(request)

def bind_result(db: Session, request_id: str, payload: dict[str, Any]):
    request = db.get(ScenarioComputeRequestRecord, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Scenario compute request not found.")
    result_id = str(payload.get("result_entity_id") or "")
    _entity(db, result_id, "result", "result_entity_id")
    result = db.get(ResearchResultRecord, result_id)
    if result is None:
        raise ValueError("result_entity_id must reference a research result.")
    if request.model_run_entity_id and result.model_run_entity_id != request.model_run_entity_id:
        raise ValueError("result_entity_id belongs to a different model run.")
    role = str(payload.get("binding_role") or "primary")
    if role not in BINDING_ROLES:
        raise ValueError("Unsupported binding_role.")
    row = ScenarioComputeResultBindingRecord(
        request_id=request_id, result_entity_id=result_id, output_key=str(payload.get("output_key") or result_id),
        binding_role=role, metadata_json=dict(payload.get("metadata") or {}),
    )
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Scenario compute output key already exists for this request.") from exc
    return _ser(row)

def plan_summary(db: Session, plan_id: str, *, public_only: bool = False):
    _plan(db, plan_id, public_only=public_only)
    requests = db.scalars(select(ScenarioComputeRequestRecord).where(ScenarioComputeRequestRecord.plan_id == plan_id)).all()
    states: dict[str, int] = {}
    for row in requests:
        states[row.request_state] = states.get(row.request_state, 0) + 1
    return {"plan_id": plan_id, "requests": len(requests), "states": states, "all_terminal": bool(requests) and all(r.request_state in {"completed", "failed", "cancelled"} for r in requests), "numerical_computation_performed_by_core": False}

def bundle(db: Session, plan_id: str, *, public_only: bool = False):
    plan = _plan(db, plan_id, public_only=public_only)
    cases = db.scalars(select(ScenarioComputeCaseRecord).where(ScenarioComputeCaseRecord.plan_id == plan_id).order_by(ScenarioComputeCaseRecord.created_at)).all()
    requests = db.scalars(select(ScenarioComputeRequestRecord).where(ScenarioComputeRequestRecord.plan_id == plan_id).order_by(ScenarioComputeRequestRecord.created_at)).all()
    request_ids = [r.id for r in requests]
    attempts = db.scalars(select(ScenarioComputeAttemptRecord).where(ScenarioComputeAttemptRecord.request_id.in_(request_ids)).order_by(ScenarioComputeAttemptRecord.created_at)).all() if request_ids else []
    bindings = db.scalars(select(ScenarioComputeResultBindingRecord).where(ScenarioComputeResultBindingRecord.request_id.in_(request_ids)).order_by(ScenarioComputeResultBindingRecord.created_at)).all() if request_ids else []
    return {
        "plan": _ser(plan), "cases": [_ser(x) for x in cases], "requests": [_ser(x) for x in requests],
        "attempts": [_ser(x) for x in attempts], "result_bindings": [_ser(x) for x in bindings],
        "summary": plan_summary(db, plan_id, public_only=public_only),
        "validation": validate_plan(db, plan_id, public_only=public_only),
    }
