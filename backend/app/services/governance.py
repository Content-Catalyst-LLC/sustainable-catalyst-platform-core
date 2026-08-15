from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..config import Settings
from ..hashing import sha256_payload
from ..models import (
    GovernanceAuditEvent,
    GovernanceDecision,
    GovernancePolicy,
    GovernanceRetentionPolicy,
    GovernanceRoleBinding,
)

EFFECTS = {"allow", "deny"}
ACTIONS = {"read", "create", "update", "delete", "execute", "manage", "evaluate", "export", "*"}
VISIBILITY_RANK = {"public": 0, "internal": 1, "private": 2, "restricted": 3}
ROLES = {"viewer", "analyst", "editor", "operator", "admin", "service"}
ROLE_ACTIONS = {
    "viewer": {"read"},
    "analyst": {"read", "evaluate", "export"},
    "editor": {"read", "create", "update", "evaluate", "export"},
    "operator": {"read", "create", "update", "execute", "evaluate", "export"},
    "admin": {"*"},
    "service": {"read", "create", "execute", "evaluate"},
}
SENSITIVE_PARTS = ("password", "secret", "token", "authorization", "api_key", "apikey", "credential", "cookie")


def _now() -> datetime:
    return datetime.now(timezone.utc)

def _stable_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in SENSITIVE_PARTS):
                out[str(key)] = "[REDACTED]"
            else:
                out[str(key)] = _sanitize(item)
        return out
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize(item) for item in value]
    return value


def readiness(settings: Settings) -> dict[str, Any]:
    return {
        "enabled": settings.governance_control_plane_enabled,
        "enforcement_mode": settings.governance_enforcement_mode,
        "policy_effects": sorted(EFFECTS),
        "roles": sorted(ROLES),
        "visibility_levels": list(VISIBILITY_RANK),
        "audit_chain": "sha256-linked",
        "audit_append_only_api": True,
        "default_private_access": "deny",
        "public_read_fallback": "allow",
        "policy_tie_break": "deny-wins",
        "secret_values_persisted_in_audit": False,
        "automatic_evidence_authority_change": False,
        "audit_retention_hours": settings.governance_audit_retention_hours,
        "decision_retention_hours": settings.governance_decision_retention_hours,
    }


def create_policy(db: Session, *, name: str, effect: str, principal_type: str = "any", principal_id: str | None = None,
                  product_scope: str | None = None, resource_type: str = "*", action: str = "*",
                  visibility_ceiling: str = "internal", priority: int = 100, enabled: bool = True,
                  conditions: dict | None = None, description: str | None = None, created_by: str = "operator") -> GovernancePolicy:
    effect = effect.strip().lower(); action = action.strip().lower(); visibility_ceiling = visibility_ceiling.strip().lower()
    if effect not in EFFECTS: raise ValueError("effect must be allow or deny")
    if action not in ACTIONS: raise ValueError("unsupported governance action")
    if visibility_ceiling not in VISIBILITY_RANK: raise ValueError("unsupported visibility ceiling")
    row = GovernancePolicy(name=name.strip(), description=description, effect=effect, principal_type=principal_type.strip().lower() or "any",
        principal_id=(principal_id or None), product_scope=(product_scope or None), resource_type=resource_type.strip() or "*",
        action=action, visibility_ceiling=visibility_ceiling, priority=priority, enabled=enabled,
        conditions_json=_sanitize(conditions or {}), created_by=created_by or "operator")
    db.add(row); db.flush()
    append_audit_event(db, event_type="governance.policy.created", actor_type="operator", actor_id=created_by or "operator",
        action="create", resource_type="governance-policy", resource_id=row.id,
        details={"name": row.name, "effect": row.effect, "resource_type": row.resource_type, "action": row.action, "priority": row.priority})
    db.commit(); db.refresh(row); return row


def bind_role(db: Session, *, principal_type: str, principal_id: str, role: str, product_scope: str | None = None,
              metadata: dict | None = None, active: bool = True) -> GovernanceRoleBinding:
    role = role.strip().lower()
    if role not in ROLES: raise ValueError("unsupported governance role")
    row = GovernanceRoleBinding(principal_type=principal_type.strip().lower(), principal_id=principal_id.strip(), role=role,
        product_scope=product_scope or None, active=active, metadata_json=_sanitize(metadata or {}))
    db.add(row); db.flush()
    append_audit_event(db, event_type="governance.role.bound", actor_type="operator", actor_id="operator", action="create",
        resource_type="governance-role-binding", resource_id=row.id,
        details={"principal_type": row.principal_type, "principal_id": row.principal_id, "role": row.role, "product_scope": row.product_scope})
    db.commit(); db.refresh(row); return row


def _policy_matches(row: GovernancePolicy, *, principal_type: str, principal_id: str, product: str | None,
                    resource_type: str, action: str, requested_visibility: str) -> bool:
    if not row.enabled: return False
    if row.principal_type not in {"any", "*", principal_type}: return False
    if row.principal_id not in {None, "*", principal_id}: return False
    if row.product_scope not in {None, "*", product}: return False
    if row.resource_type not in {"*", resource_type}: return False
    if row.action not in {"*", action}: return False
    if row.effect == "allow" and VISIBILITY_RANK[requested_visibility] > VISIBILITY_RANK[row.visibility_ceiling]: return False
    return True


def _roles_for(db: Session, *, principal_type: str, principal_id: str, product: str | None) -> list[str]:
    rows = db.scalars(select(GovernanceRoleBinding).where(
        GovernanceRoleBinding.principal_type == principal_type,
        GovernanceRoleBinding.principal_id == principal_id,
        GovernanceRoleBinding.active.is_(True),
    )).all()
    return [row.role for row in rows if row.product_scope in {None, "*", product}]


def evaluate_access(db: Session, settings: Settings, *, principal_type: str, principal_id: str, resource_type: str,
                    action: str, requested_visibility: str = "internal", product: str | None = None,
                    resource_id: str | None = None, request_id: str | None = None, context: dict | None = None) -> dict[str, Any]:
    principal_type = principal_type.strip().lower(); principal_id = principal_id.strip(); action = action.strip().lower(); requested_visibility = requested_visibility.strip().lower()
    if not principal_type or not principal_id: raise ValueError("principal_type and principal_id are required")
    if action not in ACTIONS - {"*"}: raise ValueError("unsupported governance action")
    if requested_visibility not in VISIBILITY_RANK: raise ValueError("unsupported requested visibility")
    safe_context = _sanitize(context or {})
    policies = db.scalars(select(GovernancePolicy).where(GovernancePolicy.enabled.is_(True))).all()
    matches = [p for p in policies if _policy_matches(p, principal_type=principal_type, principal_id=principal_id, product=product,
                                                      resource_type=resource_type, action=action, requested_visibility=requested_visibility)]
    matched = None; decision = "deny"; reason = "default-deny"
    if matches:
        matches.sort(key=lambda p: (p.priority, 0 if p.effect == "deny" else 1, p.created_at, p.id))
        matched = matches[0]; decision = matched.effect; reason = f"policy:{matched.id}"
    else:
        roles = _roles_for(db, principal_type=principal_type, principal_id=principal_id, product=product)
        if "admin" in roles:
            decision = "allow"; reason = "role:admin"
        elif action == "read" and requested_visibility == "public":
            decision = "allow"; reason = "public-read-fallback"
        elif any("*" in ROLE_ACTIONS.get(role, set()) or action in ROLE_ACTIONS.get(role, set()) for role in roles):
            if requested_visibility in {"public", "internal"} or "admin" in roles:
                decision = "allow"; reason = "role:" + sorted(roles)[0]
    decision_row = GovernanceDecision(request_id=request_id, principal_type=principal_type, principal_id=principal_id, product=product,
        resource_type=resource_type, resource_id=resource_id, action=action, requested_visibility=requested_visibility,
        decision=decision, matched_policy_id=matched.id if matched else None, reason=reason,
        enforcement_mode=settings.governance_enforcement_mode, context_hash=sha256_payload(safe_context))
    db.add(decision_row); db.flush()
    append_audit_event(db, event_type="governance.access.decision", actor_type=principal_type, actor_id=principal_id,
        action=action, resource_type=resource_type, resource_id=resource_id, decision_id=decision_row.id,
        details={"decision": decision, "reason": reason, "product": product, "requested_visibility": requested_visibility, "context": safe_context})
    db.commit(); db.refresh(decision_row)
    return {"decision_id": decision_row.id, "decision": decision, "allowed": decision == "allow",
            "reason": reason, "matched_policy_id": decision_row.matched_policy_id,
            "enforcement_mode": settings.governance_enforcement_mode, "context_hash": decision_row.context_hash}


def append_audit_event(db: Session, *, event_type: str, actor_type: str, actor_id: str, action: str,
                       resource_type: str, resource_id: str | None = None, decision_id: str | None = None,
                       details: dict | None = None) -> GovernanceAuditEvent:
    previous = db.scalar(select(GovernanceAuditEvent).order_by(desc(GovernanceAuditEvent.sequence)).limit(1))
    created_at = _now(); event_id = str(uuid.uuid4()); safe = _sanitize(details or {}); details_hash = sha256_payload(safe)
    previous_hash = previous.event_hash if previous else None
    event_hash = sha256_payload({"event_id": event_id, "event_type": event_type, "actor_type": actor_type, "actor_id": actor_id,
        "action": action, "resource_type": resource_type, "resource_id": resource_id, "decision_id": decision_id,
        "details_hash": details_hash, "previous_event_hash": previous_hash, "created_at": _stable_datetime(created_at)})
    row = GovernanceAuditEvent(event_id=event_id, event_type=event_type, actor_type=actor_type, actor_id=actor_id, action=action,
        resource_type=resource_type, resource_id=resource_id, decision_id=decision_id, details_json=safe, details_hash=details_hash,
        previous_event_hash=previous_hash, event_hash=event_hash, created_at=created_at)
    db.add(row); db.flush(); return row


def verify_audit_chain(db: Session) -> dict[str, Any]:
    rows = list(db.scalars(select(GovernanceAuditEvent).order_by(GovernanceAuditEvent.sequence)).all())
    errors=[]; previous=None
    for row in rows:
        if row.previous_event_hash != previous: errors.append(f"sequence {row.sequence}: previous hash mismatch")
        if sha256_payload(row.details_json) != row.details_hash: errors.append(f"sequence {row.sequence}: details hash mismatch")
        expected = sha256_payload({"event_id": row.event_id, "event_type": row.event_type, "actor_type": row.actor_type, "actor_id": row.actor_id,
            "action": row.action, "resource_type": row.resource_type, "resource_id": row.resource_id, "decision_id": row.decision_id,
            "details_hash": row.details_hash, "previous_event_hash": row.previous_event_hash, "created_at": _stable_datetime(row.created_at)})
        if expected != row.event_hash: errors.append(f"sequence {row.sequence}: event hash mismatch")
        previous=row.event_hash
    return {"valid": not errors, "events_checked": len(rows), "head_hash": rows[-1].event_hash if rows else None, "errors": errors}


def create_retention_policy(db: Session, *, resource_type: str, retention_hours: int, disposition: str = "compact", metadata: dict | None = None) -> GovernanceRetentionPolicy:
    disposition = disposition.strip().lower()
    if retention_hours < 24: raise ValueError("retention_hours must be at least 24")
    if disposition not in {"retain", "compact", "archive", "delete"}: raise ValueError("unsupported retention disposition")
    if resource_type == "governance-audit" and (disposition == "delete" or retention_hours < 8760):
        raise ValueError("governance audit events require at least 8760 hours and cannot use delete disposition")
    row=GovernanceRetentionPolicy(resource_type=resource_type, retention_hours=retention_hours, disposition=disposition, metadata_json=_sanitize(metadata or {}))
    db.add(row); db.flush(); append_audit_event(db, event_type="governance.retention.created", actor_type="operator", actor_id="operator",
        action="create", resource_type="governance-retention-policy", resource_id=row.id,
        details={"resource_type": resource_type, "retention_hours": retention_hours, "disposition": disposition})
    db.commit(); db.refresh(row); return row


def list_policies(db: Session, limit: int = 200):
    return list(db.scalars(select(GovernancePolicy).order_by(GovernancePolicy.priority, GovernancePolicy.created_at).limit(limit)).all())

def list_roles(db: Session, limit: int = 200):
    return list(db.scalars(select(GovernanceRoleBinding).order_by(GovernanceRoleBinding.created_at).limit(limit)).all())

def list_decisions(db: Session, limit: int = 200):
    return list(db.scalars(select(GovernanceDecision).order_by(desc(GovernanceDecision.created_at)).limit(limit)).all())

def list_audit_events(db: Session, limit: int = 200):
    return list(db.scalars(select(GovernanceAuditEvent).order_by(desc(GovernanceAuditEvent.sequence)).limit(limit)).all())
