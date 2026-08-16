from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import sqrt
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..models import (
    CapacityBudget,
    CapacityForecastRecord,
    CapacityGovernanceDecision,
    CapacityObservation,
    CapacityResourceProfile,
    ConnectorWorkItem,
    ScaleProcessingJob,
    ScaleProcessingPartition,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


def _thresholds(settings) -> tuple[float, float]:
    warning = settings.capacity_default_warning_utilization_percent / 100.0
    critical = settings.capacity_default_critical_utilization_percent / 100.0
    if critical <= warning:
        critical = min(1.0, warning + 0.05)
    return warning, critical


def _safe_profile(row: CapacityResourceProfile) -> dict:
    return {
        "id": row.id,
        "resource_type": row.resource_type,
        "resource_key": row.resource_key,
        "product_scope": row.product_scope,
        "unit": row.unit,
        "capacity_limit": row.capacity_limit,
        "warning_utilization": row.warning_utilization,
        "critical_utilization": row.critical_utilization,
        "forecast_horizon_hours": row.forecast_horizon_hours,
        "enabled": row.enabled,
        "public_summary": row.public_summary,
        "metadata": row.metadata_json,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _safe_budget(row: CapacityBudget) -> dict:
    return {
        "id": row.id,
        "budget_key": row.budget_key,
        "name": row.name,
        "product_scope": row.product_scope,
        "resource_type": row.resource_type,
        "resource_key": row.resource_key,
        "unit": row.unit,
        "budget_limit": row.budget_limit,
        "warning_fraction": row.warning_fraction,
        "enforcement_mode": row.enforcement_mode,
        "enabled": row.enabled,
        "public_summary": row.public_summary,
        "metadata": row.metadata_json,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def profile_dict(row: CapacityResourceProfile) -> dict:
    return _safe_profile(row)


def budget_dict(row: CapacityBudget) -> dict:
    return _safe_budget(row)


def observation_dict(row: CapacityObservation) -> dict:
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "used_value": row.used_value,
        "demand_value": row.demand_value,
        "source": row.source,
        "observed_at": row.observed_at,
        "metadata": row.metadata_json,
    }


def forecast_dict(row: CapacityForecastRecord) -> dict:
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "method": row.method,
        "window_hours": row.window_hours,
        "horizon_hours": row.horizon_hours,
        "observed_points": row.observed_points,
        "current_value": row.current_value,
        "slope_per_hour": row.slope_per_hour,
        "predicted_value": row.predicted_value,
        "predicted_utilization": row.predicted_utilization,
        "confidence": row.confidence,
        "state": row.state,
        "hours_to_capacity": row.hours_to_capacity,
        "evidence": row.evidence_json,
        "generated_at": row.generated_at,
    }


def decision_dict(row: CapacityGovernanceDecision) -> dict:
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "budget_id": row.budget_id,
        "product_scope": row.product_scope,
        "action": row.action,
        "reason": row.reason,
        "current_value": row.current_value,
        "forecast_value": row.forecast_value,
        "limit_value": row.limit_value,
        "automatic_actuation": row.automatic_actuation,
        "evidence": row.evidence_json,
        "created_at": row.created_at,
    }


def upsert_profile(
    db: Session,
    settings,
    *,
    resource_type: str,
    resource_key: str,
    capacity_limit: float,
    unit: str = "count",
    product_scope: str | None = None,
    warning_utilization: float | None = None,
    critical_utilization: float | None = None,
    forecast_horizon_hours: int | None = None,
    enabled: bool = True,
    public_summary: bool = True,
    metadata: dict | None = None,
) -> CapacityResourceProfile:
    resource_type = resource_type.strip().lower().replace(" ", "-")
    resource_key = resource_key.strip()
    product_scope = product_scope.strip() if product_scope else None
    if not resource_type or not resource_key:
        raise ValueError("resource_type and resource_key are required.")
    if capacity_limit <= 0:
        raise ValueError("capacity_limit must be greater than zero.")
    default_warning, default_critical = _thresholds(settings)
    warning = default_warning if warning_utilization is None else float(warning_utilization)
    critical = default_critical if critical_utilization is None else float(critical_utilization)
    if not 0 < warning < critical <= 1.0:
        raise ValueError("utilization thresholds must satisfy 0 < warning < critical <= 1.")
    horizon = int(forecast_horizon_hours or settings.capacity_default_forecast_horizon_hours)
    if horizon < 1:
        raise ValueError("forecast_horizon_hours must be positive.")
    row = db.scalar(
        select(CapacityResourceProfile).where(
            CapacityResourceProfile.resource_type == resource_type,
            CapacityResourceProfile.resource_key == resource_key,
            CapacityResourceProfile.product_scope == product_scope,
        )
    )
    if row is None:
        row = CapacityResourceProfile(
            resource_type=resource_type,
            resource_key=resource_key,
            product_scope=product_scope,
            unit=unit,
            capacity_limit=float(capacity_limit),
            warning_utilization=warning,
            critical_utilization=critical,
            forecast_horizon_hours=horizon,
            enabled=enabled,
            public_summary=public_summary,
            metadata_json=metadata or {},
        )
    else:
        row.unit = unit
        row.capacity_limit = float(capacity_limit)
        row.warning_utilization = warning
        row.critical_utilization = critical
        row.forecast_horizon_hours = horizon
        row.enabled = bool(enabled)
        row.public_summary = bool(public_summary)
        row.metadata_json = metadata or row.metadata_json or {}
        row.updated_at = now()
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_profiles(db: Session, *, enabled_only: bool = False, product_scope: str | None = None) -> list[CapacityResourceProfile]:
    q = select(CapacityResourceProfile)
    if enabled_only:
        q = q.where(CapacityResourceProfile.enabled.is_(True))
    if product_scope is not None:
        q = q.where(CapacityResourceProfile.product_scope == product_scope)
    return list(db.scalars(q.order_by(CapacityResourceProfile.resource_type, CapacityResourceProfile.resource_key)).all())


def record_observation(
    db: Session,
    settings,
    profile_id: str,
    *,
    used_value: float,
    demand_value: float | None = None,
    source: str = "operator",
    observed_at: datetime | None = None,
    metadata: dict | None = None,
) -> CapacityObservation:
    profile = db.get(CapacityResourceProfile, profile_id)
    if profile is None:
        raise ValueError("Capacity resource profile not found.")
    if used_value < 0 or (demand_value is not None and demand_value < 0):
        raise ValueError("Capacity observations cannot be negative.")
    row = CapacityObservation(
        profile_id=profile.id,
        used_value=float(used_value),
        demand_value=None if demand_value is None else float(demand_value),
        source=(source or "operator")[:120],
        observed_at=observed_at or now(),
        metadata_json=metadata or {},
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    prune_observations(db, settings)
    return row


def list_observations(db: Session, profile_id: str, *, limit: int = 500) -> list[CapacityObservation]:
    return list(
        db.scalars(
            select(CapacityObservation)
            .where(CapacityObservation.profile_id == profile_id)
            .order_by(CapacityObservation.observed_at.desc())
            .limit(limit)
        ).all()
    )


def prune_observations(db: Session, settings, *, at: datetime | None = None) -> int:
    cutoff = (at or now()) - timedelta(hours=settings.capacity_observation_retention_hours)
    statement = delete(CapacityObservation).where(CapacityObservation.observed_at < cutoff).execution_options(synchronize_session=False)
    result = db.execute(statement)
    db.commit()
    return int(result.rowcount or 0)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _linear_forecast(points: list[CapacityObservation], capacity_limit: float, horizon_hours: int) -> tuple[float, float, float]:
    first = _aware(points[0].observed_at)
    xs = [(_aware(p.observed_at) - first).total_seconds() / 3600.0 for p in points]
    ys = [float(p.used_value) for p in points]
    xbar = sum(xs) / len(xs)
    ybar = sum(ys) / len(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    slope = 0.0 if denom <= 0 else sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom
    intercept = ybar - slope * xbar
    fitted = [intercept + slope * x for x in xs]
    rmse = sqrt(sum((y - f) ** 2 for y, f in zip(ys, fitted)) / len(ys))
    current = ys[-1]
    predicted = max(0.0, current + slope * horizon_hours)
    normalized_error = min(1.0, rmse / max(capacity_limit, abs(ybar), 1.0))
    return slope, predicted, normalized_error


def generate_forecast(
    db: Session,
    settings,
    profile_id: str,
    *,
    window_hours: int | None = None,
    horizon_hours: int | None = None,
    at: datetime | None = None,
) -> CapacityForecastRecord:
    profile = db.get(CapacityResourceProfile, profile_id)
    if profile is None:
        raise ValueError("Capacity resource profile not found.")
    at = at or now()
    window = max(1, int(window_hours or settings.capacity_forecast_window_hours))
    horizon = max(1, int(horizon_hours or profile.forecast_horizon_hours or settings.capacity_default_forecast_horizon_hours))
    start = at - timedelta(hours=window)
    points = list(
        db.scalars(
            select(CapacityObservation)
            .where(CapacityObservation.profile_id == profile.id, CapacityObservation.observed_at >= start, CapacityObservation.observed_at <= at)
            .order_by(CapacityObservation.observed_at)
        ).all()
    )
    current = float(points[-1].used_value) if points else None
    current_util = (current / profile.capacity_limit) if current is not None else None
    slope = predicted = predicted_util = hours_to_capacity = None
    confidence = 0.0
    state = "insufficient-data"
    normalized_error = None

    if current_util is not None and current_util >= profile.critical_utilization:
        state = "critical"
    elif current_util is not None and current_util >= profile.warning_utilization:
        state = "warning"

    if len(points) >= settings.capacity_min_forecast_points:
        slope, predicted, normalized_error = _linear_forecast(points, profile.capacity_limit, horizon)
        predicted_util = predicted / profile.capacity_limit
        sample_factor = min(1.0, len(points) / max(settings.capacity_min_forecast_points * 2, 6))
        confidence = round(sample_factor * (1.0 - normalized_error), 4)
        risk_util = max(current_util or 0.0, predicted_util)
        if risk_util >= profile.critical_utilization:
            state = "critical"
        elif risk_util >= profile.warning_utilization:
            state = "warning"
        else:
            state = "stable"
        if slope > 0 and current is not None and current < profile.capacity_limit:
            hours_to_capacity = max(0.0, (profile.capacity_limit - current) / slope)

    evidence = {
        "capacity_limit": profile.capacity_limit,
        "unit": profile.unit,
        "current_utilization": current_util,
        "warning_utilization": profile.warning_utilization,
        "critical_utilization": profile.critical_utilization,
        "normalized_fit_error": normalized_error,
        "forecast_is_advisory": True,
        "automatic_scaling": False,
        "automatic_infrastructure_purchase": False,
    }
    row = CapacityForecastRecord(
        profile_id=profile.id,
        window_hours=window,
        horizon_hours=horizon,
        observed_points=len(points),
        current_value=current,
        slope_per_hour=slope,
        predicted_value=predicted,
        predicted_utilization=predicted_util,
        confidence=confidence,
        state=state,
        hours_to_capacity=hours_to_capacity,
        evidence_json=evidence,
        generated_at=at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_forecasts(db: Session, *, profile_id: str | None = None, limit: int = 200) -> list[CapacityForecastRecord]:
    q = select(CapacityForecastRecord)
    if profile_id:
        q = q.where(CapacityForecastRecord.profile_id == profile_id)
    return list(db.scalars(q.order_by(CapacityForecastRecord.generated_at.desc()).limit(limit)).all())


def upsert_budget(
    db: Session,
    *,
    budget_key: str,
    name: str,
    resource_type: str,
    budget_limit: float,
    unit: str = "count",
    product_scope: str | None = None,
    resource_key: str | None = None,
    warning_fraction: float = 0.80,
    enforcement_mode: str = "advisory",
    enabled: bool = True,
    public_summary: bool = False,
    metadata: dict | None = None,
) -> CapacityBudget:
    budget_key = budget_key.strip()
    if not budget_key or not name.strip():
        raise ValueError("budget_key and name are required.")
    if budget_limit <= 0:
        raise ValueError("budget_limit must be greater than zero.")
    if not 0 < warning_fraction < 1:
        raise ValueError("warning_fraction must be between zero and one.")
    if enforcement_mode not in {"advisory", "soft-limit"}:
        raise ValueError("enforcement_mode must be advisory or soft-limit.")
    row = db.scalar(select(CapacityBudget).where(CapacityBudget.budget_key == budget_key))
    values = dict(
        name=name.strip(), product_scope=product_scope, resource_type=resource_type.strip().lower().replace(" ", "-"),
        resource_key=resource_key, unit=unit, budget_limit=float(budget_limit), warning_fraction=float(warning_fraction),
        enforcement_mode=enforcement_mode, enabled=enabled, public_summary=public_summary, metadata_json=metadata or {},
    )
    if row is None:
        row = CapacityBudget(budget_key=budget_key, **values)
    else:
        for key, value in values.items():
            setattr(row, key, value)
        row.updated_at = now()
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_budgets(db: Session, *, enabled_only: bool = False) -> list[CapacityBudget]:
    q = select(CapacityBudget)
    if enabled_only:
        q = q.where(CapacityBudget.enabled.is_(True))
    return list(db.scalars(q.order_by(CapacityBudget.product_scope, CapacityBudget.resource_type, CapacityBudget.name)).all())


def matching_budget(db: Session, profile: CapacityResourceProfile) -> CapacityBudget | None:
    rows = list(
        db.scalars(
            select(CapacityBudget).where(
                CapacityBudget.enabled.is_(True),
                CapacityBudget.resource_type == profile.resource_type,
            )
        ).all()
    )
    candidates = [
        row for row in rows
        if (row.product_scope is None or row.product_scope == profile.product_scope)
        and (row.resource_key is None or row.resource_key == profile.resource_key)
    ]
    candidates.sort(key=lambda row: (row.resource_key is None, row.product_scope is None))
    return candidates[0] if candidates else None


def assess_profile(db: Session, settings, profile_id: str, *, generate: bool = True) -> CapacityGovernanceDecision:
    profile = db.get(CapacityResourceProfile, profile_id)
    if profile is None:
        raise ValueError("Capacity resource profile not found.")
    forecast = generate_forecast(db, settings, profile.id) if generate else db.scalar(
        select(CapacityForecastRecord).where(CapacityForecastRecord.profile_id == profile.id).order_by(CapacityForecastRecord.generated_at.desc()).limit(1)
    )
    budget = matching_budget(db, profile)
    current = forecast.current_value if forecast else None
    predicted = forecast.predicted_value if forecast else None
    risk_value = max(v for v in (current, predicted) if v is not None) if any(v is not None for v in (current, predicted)) else None
    profile_fraction = (risk_value / profile.capacity_limit) if risk_value is not None else 0.0
    budget_fraction = (risk_value / budget.budget_limit) if budget and risk_value is not None else 0.0
    action = "allow"
    reason = "within-governed-capacity"
    limit = profile.capacity_limit
    if budget and budget_fraction >= 1.0:
        action = "advisory-soft-block" if budget.enforcement_mode == "soft-limit" else "warn"
        reason = "budget-limit-reached"
        limit = budget.budget_limit
    elif profile_fraction >= profile.critical_utilization:
        action = "advisory-soft-block"
        reason = "critical-capacity-risk"
    elif budget and budget_fraction >= budget.warning_fraction:
        action = "warn"
        reason = "budget-warning-threshold"
        limit = budget.budget_limit
    elif profile_fraction >= profile.warning_utilization:
        action = "warn"
        reason = "capacity-warning-threshold"
    elif forecast and forecast.state == "insufficient-data":
        action = "observe"
        reason = "insufficient-forecast-data"

    evidence = {
        "profile_state": forecast.state if forecast else "none",
        "profile_fraction": profile_fraction,
        "budget_fraction": budget_fraction if budget else None,
        "forecast_confidence": forecast.confidence if forecast else 0.0,
        "decision_is_advisory": True,
        "automatic_rejection": False,
        "automatic_scaling": False,
        "automatic_infrastructure_purchase": False,
    }
    row = CapacityGovernanceDecision(
        profile_id=profile.id,
        budget_id=budget.id if budget else None,
        product_scope=profile.product_scope,
        action=action,
        reason=reason,
        current_value=current,
        forecast_value=predicted,
        limit_value=limit,
        automatic_actuation=False,
        evidence_json=evidence,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def ensure_runtime_profiles(db: Session, settings) -> dict[str, CapacityResourceProfile]:
    common = {"product_scope": "platform-core", "public_summary": True, "metadata": {"managed_by": "core-runtime", "release": settings.version}}
    return {
        "active_jobs": upsert_profile(db, settings, resource_type="processing", resource_key="active-jobs", unit="jobs", capacity_limit=settings.scale_max_active_jobs, **common),
        "queued_partitions": upsert_profile(db, settings, resource_type="queue", resource_key="queued-partitions", unit="partitions", capacity_limit=settings.scale_queue_backpressure_threshold, **common),
        "connector_backlog": upsert_profile(db, settings, resource_type="connector-queue", resource_key="pending-work-items", unit="items", capacity_limit=settings.scale_queue_backpressure_threshold, **common),
    }


def collect_runtime_observations(db: Session, settings, *, observed_at: datetime | None = None) -> list[CapacityObservation]:
    profiles = ensure_runtime_profiles(db, settings)
    active_jobs = db.scalar(select(func.count()).select_from(ScaleProcessingJob).where(ScaleProcessingJob.state.in_(["queued", "running"]))) or 0
    queued_partitions = db.scalar(select(func.count()).select_from(ScaleProcessingPartition).where(ScaleProcessingPartition.state == "queued")) or 0
    pending_work = db.scalar(select(func.count()).select_from(ConnectorWorkItem).where(ConnectorWorkItem.status.in_(["pending", "leased"]))) or 0
    at = observed_at or now()
    values = {"active_jobs": float(active_jobs), "queued_partitions": float(queued_partitions), "connector_backlog": float(pending_work)}
    return [record_observation(db, settings, profiles[key].id, used_value=value, source="core-runtime", observed_at=at, metadata={"automatic_collection": True, "automatic_actuation": False}) for key, value in values.items()]


def _latest_forecasts_by_profile(db: Session) -> dict[str, CapacityForecastRecord]:
    rows = list(db.scalars(select(CapacityForecastRecord).order_by(CapacityForecastRecord.generated_at.desc())).all())
    latest: dict[str, CapacityForecastRecord] = {}
    for row in rows:
        latest.setdefault(row.profile_id, row)
    return latest


def readiness(db: Session, settings) -> dict:
    profiles = list_profiles(db, enabled_only=True)
    latest = _latest_forecasts_by_profile(db)
    coverage = 0
    critical = warning = insufficient = 0
    for profile in profiles:
        point_count = db.scalar(select(func.count()).select_from(CapacityObservation).where(CapacityObservation.profile_id == profile.id)) or 0
        forecast = latest.get(profile.id)
        if point_count >= settings.capacity_min_forecast_points and forecast is not None and forecast.state != "insufficient-data":
            coverage += 1
        if forecast:
            if forecast.state == "critical": critical += 1
            elif forecast.state == "warning": warning += 1
            elif forecast.state == "insufficient-data": insufficient += 1
    budgets = db.scalar(select(func.count()).select_from(CapacityBudget).where(CapacityBudget.enabled.is_(True))) or 0
    decisions = db.scalar(select(func.count()).select_from(CapacityGovernanceDecision)) or 0
    state = "disabled" if not settings.capacity_resource_governance_enabled else (
        "critical" if critical else "warning" if warning else "unconfigured" if not profiles else "observing" if coverage < len(profiles) else "ready"
    )
    capacity_ready = bool(settings.capacity_resource_governance_enabled and profiles and coverage == len(profiles) and critical == 0)
    return {
        "enabled": settings.capacity_resource_governance_enabled,
        "state": state,
        "capacity_ready": capacity_ready,
        "resource_profiles": len(profiles),
        "forecast_covered_profiles": coverage,
        "active_budgets": int(budgets),
        "critical_profiles": critical,
        "warning_profiles": warning,
        "insufficient_forecast_profiles": insufficient,
        "governance_decisions": int(decisions),
        "forecast_method": "bounded-linear",
        "forecast_uncertainty_exposed": True,
        "soft_limit_governance": True,
        "automatic_scaling": False,
        "automatic_infrastructure_purchase": False,
        "automatic_deployment_mutation": False,
        "hard_admission_control": False,
    }


def public_status(db: Session, settings) -> dict:
    s = readiness(db, settings)
    return {
        "enabled": s["enabled"] and settings.capacity_public_status_enabled,
        "state": s["state"],
        "capacity_ready": s["capacity_ready"],
        "resource_profiles": s["resource_profiles"],
        "forecast_covered_profiles": s["forecast_covered_profiles"],
        "critical_profiles": s["critical_profiles"],
        "warning_profiles": s["warning_profiles"],
        "forecast_uncertainty_exposed": True,
        "automatic_scaling": False,
        "automatic_infrastructure_purchase": False,
        "private_capacity_values_exposed": False,
    }


def certification_snapshot(db: Session, settings) -> dict:
    s = readiness(db, settings)
    return {
        "state": s["state"],
        "capacity_ready": s["capacity_ready"],
        "critical_profiles": s["critical_profiles"],
        "forecast_covered_profiles": s["forecast_covered_profiles"],
        "resource_profiles": s["resource_profiles"],
        "automatic_scaling": False,
        "automatic_infrastructure_purchase": False,
        "hard_admission_control": False,
    }
