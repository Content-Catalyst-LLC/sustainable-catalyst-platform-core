from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import EvidenceRecord, WebhookDelivery
from .ledger import verify_ledger


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_percent(value: Any, *, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if 0.0 <= number <= 1.0:
        number *= 100.0
    return max(0.0, min(number, 100.0))


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _check(
    key: str,
    name: str,
    status: str,
    score: float | None,
    *,
    severity: str = "info",
    observed: dict | None = None,
    expected: dict | None = None,
    details: dict | None = None,
    evidence_references: list[str] | None = None,
) -> dict:
    return {
        "check_key": key,
        "name": name,
        "status": status,
        "score": None if score is None else round(float(score), 3),
        "severity": severity,
        "observed": observed or {},
        "expected": expected or {},
        "details": details or {},
        "evidence_references": evidence_references or [],
    }


def evaluate_ledger_integrity(db: Session, observations: dict, settings) -> list[dict]:
    result = verify_ledger(db)
    return [
        _check(
            "hash-chain",
            "Tamper-evident ledger hash chain",
            "passed" if result.valid else "failed",
            100.0 if result.valid else 0.0,
            severity="critical" if not result.valid else "info",
            observed={
                "valid": result.valid,
                "entries_checked": result.entries_checked,
                "head_hash": result.head_hash,
                "errors": result.errors,
            },
            expected={"valid": True},
            details={
                "first_sequence": result.first_sequence,
                "last_sequence": result.last_sequence,
            },
        )
    ]


def evaluate_public_api_readiness(db: Session, observations: dict, settings) -> list[dict]:
    production = settings.environment == "production"
    return [
        _check(
            "public-api-enabled",
            "Unified public API enabled",
            "passed" if settings.public_api_enabled else "failed",
            100.0 if settings.public_api_enabled else 0.0,
            severity="high" if not settings.public_api_enabled else "info",
            observed={"enabled": settings.public_api_enabled},
            expected={"enabled": True},
        ),
        _check(
            "developer-portal-enabled",
            "Developer Portal enabled",
            "passed" if settings.developer_portal_enabled else "warning",
            100.0 if settings.developer_portal_enabled else 50.0,
            severity="medium" if not settings.developer_portal_enabled else "info",
            observed={"enabled": settings.developer_portal_enabled},
            expected={"enabled": True},
        ),
        _check(
            "request-log-salt",
            "Production request-log salt configured",
            "passed" if (settings.api_log_salt or not production) else "failed",
            100.0 if (settings.api_log_salt or not production) else 0.0,
            severity="high" if production and not settings.api_log_salt else "info",
            observed={"configured": bool(settings.api_log_salt), "environment": settings.environment},
            expected={"configured_in_production": True},
        ),
        _check(
            "webhook-signing-secret",
            "Production webhook signing secret configured",
            "passed" if (settings.webhook_signing_secret or not production) else "failed",
            100.0 if (settings.webhook_signing_secret or not production) else 0.0,
            severity="high" if production and not settings.webhook_signing_secret else "info",
            observed={"configured": bool(settings.webhook_signing_secret), "environment": settings.environment},
            expected={"configured_in_production": True},
        ),
    ]


def evaluate_evidence_review_coverage(db: Session, observations: dict, settings) -> list[dict]:
    total = int(db.scalar(select(func.count(EvidenceRecord.id))) or 0)
    verified = int(
        db.scalar(
            select(func.count(EvidenceRecord.id)).where(
                EvidenceRecord.review_status == "verified"
            )
        )
        or 0
    )
    if total == 0:
        return [
            _check(
                "verified-coverage",
                "Verified evidence coverage",
                "not_applicable",
                None,
                observed={"total": 0, "verified": 0},
                expected={"minimum_percent": 90.0},
                details={"reason": "No evidence records exist."},
            )
        ]
    score = verified / total * 100.0
    status = "passed" if score >= 90.0 else "warning" if score >= 70.0 else "failed"
    return [
        _check(
            "verified-coverage",
            "Verified evidence coverage",
            status,
            score,
            severity="high" if status == "failed" else "medium" if status == "warning" else "info",
            observed={"total": total, "verified": verified, "percent": score},
            expected={"minimum_percent": 90.0},
        )
    ]


def evaluate_connector_freshness(db: Session, observations: dict, settings) -> list[dict]:
    last_success = _parse_datetime(observations.get("last_success_at"))
    max_age = float(observations.get("max_age_hours", 48))
    connector_status = str(observations.get("connector_status", "active"))
    if last_success is None:
        return [
            _check(
                "last-success",
                "Latest successful connector refresh",
                "failed",
                0.0,
                severity="high",
                observed={"last_success_at": observations.get("last_success_at"), "connector_status": connector_status},
                expected={"max_age_hours": max_age},
                details={"reason": "No valid last_success_at timestamp was provided."},
            )
        ]
    age_hours = max((_utcnow() - last_success).total_seconds() / 3600.0, 0.0)
    if connector_status not in {"active", "operational", "healthy"}:
        status, score = "failed", 0.0
    elif age_hours <= max_age:
        status, score = "passed", 100.0
    elif age_hours <= max_age * 1.5:
        status, score = "warning", max(50.0, 100.0 - ((age_hours - max_age) / max_age * 50.0))
    else:
        status, score = "failed", max(0.0, 50.0 - ((age_hours - max_age * 1.5) / max_age * 50.0))
    return [
        _check(
            "freshness-window",
            "Connector freshness window",
            status,
            score,
            severity="high" if status == "failed" else "medium" if status == "warning" else "info",
            observed={"last_success_at": last_success.isoformat(), "age_hours": round(age_hours, 3), "connector_status": connector_status},
            expected={"max_age_hours": max_age, "healthy_statuses": ["active", "operational", "healthy"]},
        )
    ]


def evaluate_calculator_validation(db: Session, observations: dict, settings) -> list[dict]:
    total = int(observations.get("total_cases", 0) or 0)
    passed = int(observations.get("passed_cases", 0) or 0)
    tolerance_failures = int(observations.get("tolerance_failures", 0) or 0)
    edge_total = int(observations.get("edge_cases_total", 0) or 0)
    edge_passed = int(observations.get("edge_cases_passed", 0) or 0)
    if total <= 0:
        return [_check("test-coverage", "Calculator validation cases", "not_applicable", None, observed={"total_cases": total}, expected={"minimum_cases": 1}, details={"reason": "No validation cases were supplied."})]
    case_score = max(0.0, min(passed / total * 100.0, 100.0))
    edge_score = 100.0 if edge_total <= 0 else max(0.0, min(edge_passed / edge_total * 100.0, 100.0))
    tolerance_score = 100.0 if tolerance_failures == 0 else max(0.0, 100.0 - tolerance_failures * 20.0)
    return [
        _check("expected-output-agreement", "Expected-output agreement", "passed" if case_score >= 95 else "warning" if case_score >= 80 else "failed", case_score, severity="high" if case_score < 80 else "medium" if case_score < 95 else "info", observed={"total_cases": total, "passed_cases": passed}, expected={"minimum_percent": 95.0}),
        _check("numerical-tolerance", "Numerical tolerance compliance", "passed" if tolerance_failures == 0 else "failed", tolerance_score, severity="high" if tolerance_failures else "info", observed={"tolerance_failures": tolerance_failures}, expected={"tolerance_failures": 0}),
        _check("edge-case-coverage", "Edge-case validation", "not_applicable" if edge_total <= 0 else "passed" if edge_score >= 90 else "warning" if edge_score >= 70 else "failed", None if edge_total <= 0 else edge_score, severity="medium" if edge_total > 0 and edge_score < 90 else "info", observed={"edge_cases_total": edge_total, "edge_cases_passed": edge_passed}, expected={"minimum_percent": 90.0}),
    ]


def evaluate_ai_grounding(db: Session, observations: dict, settings) -> list[dict]:
    citation = _as_percent(observations.get("citation_coverage"))
    unsupported = _as_percent(observations.get("unsupported_claim_rate"))
    relevance = _as_percent(observations.get("source_relevance"))
    scope_gate = _as_percent(observations.get("scope_gate_pass_rate"))
    return [
        _check("citation-coverage", "Citation coverage", "passed" if citation >= 95 else "warning" if citation >= 80 else "failed", citation, severity="high" if citation < 80 else "medium" if citation < 95 else "info", observed={"percent": citation}, expected={"minimum_percent": 95.0}),
        _check("unsupported-claims", "Unsupported claim rate", "passed" if unsupported <= 2 else "warning" if unsupported <= 5 else "failed", 100.0 - unsupported, severity="critical" if unsupported > 10 else "high" if unsupported > 5 else "medium" if unsupported > 2 else "info", observed={"percent": unsupported}, expected={"maximum_percent": 2.0}),
        _check("source-relevance", "Source relevance", "passed" if relevance >= 90 else "warning" if relevance >= 75 else "failed", relevance, severity="high" if relevance < 75 else "medium" if relevance < 90 else "info", observed={"percent": relevance}, expected={"minimum_percent": 90.0}),
        _check("scope-gate", "Sustainable Catalyst scope-gate performance", "passed" if scope_gate >= 98 else "warning" if scope_gate >= 90 else "failed", scope_gate, severity="high" if scope_gate < 90 else "medium" if scope_gate < 98 else "info", observed={"percent": scope_gate}, expected={"minimum_percent": 98.0}),
    ]


def evaluate_accessibility_conformance(db: Session, observations: dict, settings) -> list[dict]:
    total = int(observations.get("total_checks", 0) or 0)
    passed = int(observations.get("passed_checks", 0) or 0)
    critical = int(observations.get("critical_failures", 0) or 0)
    pending = int(observations.get("manual_checks_pending", 0) or 0)
    target = observations.get("target", "WCAG 2.2 AA")
    if total <= 0:
        return [_check("conformance-checks", "Accessibility conformance checks", "not_applicable", None, observed={"total_checks": total, "target": target}, expected={"minimum_checks": 1}, details={"reason": "No accessibility checks were supplied."})]
    score = max(0.0, min(passed / total * 100.0, 100.0))
    if critical > 0:
        status = "failed"
    elif score >= 95 and pending == 0:
        status = "passed"
    elif score >= 80:
        status = "warning"
    else:
        status = "failed"
    return [
        _check("automated-and-manual-checks", "Accessibility conformance checks", status, score, severity="critical" if critical else "high" if status == "failed" else "medium" if status == "warning" else "info", observed={"target": target, "total_checks": total, "passed_checks": passed, "critical_failures": critical, "manual_checks_pending": pending}, expected={"minimum_percent": 95.0, "critical_failures": 0, "manual_checks_pending": 0})
    ]


def evaluate_webhook_delivery_reliability(db: Session, observations: dict, settings) -> list[dict]:
    delivered = observations.get("delivered")
    failed = observations.get("failed")
    if delivered is None or failed is None:
        delivered = int(db.scalar(select(func.count(WebhookDelivery.id)).where(WebhookDelivery.status == "delivered")) or 0)
        failed = int(db.scalar(select(func.count(WebhookDelivery.id)).where(WebhookDelivery.status == "failed")) or 0)
    delivered, failed = int(delivered or 0), int(failed or 0)
    total = delivered + failed
    if total == 0:
        return [_check("delivery-success-rate", "Webhook delivery success rate", "not_applicable", None, observed={"delivered": 0, "failed": 0}, expected={"minimum_percent": 99.0}, details={"reason": "No completed webhook delivery attempts exist."})]
    score = delivered / total * 100.0
    status = "passed" if score >= 99 else "warning" if score >= 95 else "failed"
    return [_check("delivery-success-rate", "Webhook delivery success rate", status, score, severity="high" if status == "failed" else "medium" if status == "warning" else "info", observed={"delivered": delivered, "failed": failed, "total": total}, expected={"minimum_percent": 99.0})]


def evaluate_recorded(db: Session, observations: dict, settings) -> list[dict]:
    raw_checks = observations.get("checks") or []
    if not raw_checks:
        return [_check("recorded-evaluation", "Recorded evaluation", "not_applicable", None, details={"reason": "No recorded checks were supplied."})]
    checks = []
    for index, raw in enumerate(raw_checks, start=1):
        checks.append(_check(
            str(raw.get("check_key") or f"check-{index}"),
            str(raw.get("name") or f"Recorded check {index}"),
            str(raw.get("status") or "unknown"),
            raw.get("score"),
            severity=str(raw.get("severity") or "info"),
            observed=raw.get("observed") or {},
            expected=raw.get("expected") or {},
            details=raw.get("details") or {},
            evidence_references=raw.get("evidence_references") or [],
        ))
    return checks


EVALUATORS = {
    "ledger_integrity": evaluate_ledger_integrity,
    "public_api_readiness": evaluate_public_api_readiness,
    "evidence_review_coverage": evaluate_evidence_review_coverage,
    "connector_freshness": evaluate_connector_freshness,
    "calculator_validation": evaluate_calculator_validation,
    "ai_grounding": evaluate_ai_grounding,
    "accessibility_conformance": evaluate_accessibility_conformance,
    "webhook_delivery_reliability": evaluate_webhook_delivery_reliability,
    "recorded": evaluate_recorded,
}


def run_evaluator(kind: str, db: Session, observations: dict, settings) -> list[dict]:
    evaluator = EVALUATORS.get(kind)
    if evaluator is None:
        return [_check("unsupported-evaluator", "Evaluator availability", "error", 0.0, severity="high", observed={"evaluator_kind": kind}, expected={"supported": sorted(EVALUATORS)})]
    return evaluator(db, observations, settings)
