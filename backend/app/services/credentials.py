from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from ..models import (
    CredentialKeyVersion,
    CredentialLifecycleEvent,
    CredentialRegistryRecord,
    CredentialRotationRecord,
    CredentialUseEvent,
)

SAFE_REFERENCE_PREFIXES = ("env:", "vault:", "kms:", "secret-manager:", "external:")
CREDENTIAL_TYPES = {
    "service-api-key",
    "service-token",
    "developer-api-key",
    "webhook-signing-key",
    "dossier-signing-key",
    "federation-shared-secret",
    "hmac-signing-key",
    "cryptographic-key",
}
KEY_STATES = {"staged", "active", "retiring", "retired", "revoked", "expired", "compromised"}
SENSITIVE_KEY_PARTS = (
    "secret_value", "private_key", "password", "bearer_token", "access_token",
    "api_key", "token", "secret", "credential_value", "authorization",
)
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def now() -> datetime:
    return datetime.now(timezone.utc)


def aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def sanitize_metadata(value: Any) -> Any:
    """Strip credential material from durable metadata/context payloads.

    Metadata may describe where a secret lives or how it is governed, but never
    contain the secret/private-key material itself.
    """
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in SENSITIVE_KEY_PARTS):
                continue
            result[str(key)] = sanitize_metadata(item)
        return result
    if isinstance(value, list):
        return [sanitize_metadata(item) for item in value]
    return value


def validate_reference(reference: str) -> str:
    reference = reference.strip()
    if not reference.startswith(SAFE_REFERENCE_PREFIXES):
        raise ValueError("secret_reference must be a locator beginning with env:, vault:, kms:, secret-manager:, or external:")
    if "\n" in reference or "\r" in reference or len(reference) > 1000:
        raise ValueError("invalid secret_reference")
    return reference


def credential_dict(row: CredentialRegistryRecord) -> dict:
    return {
        "id": row.id,
        "credential_key": row.credential_key,
        "name": row.name,
        "credential_type": row.credential_type,
        "purpose": row.purpose,
        "owner_scope": row.owner_scope,
        "provider": row.provider,
        "secret_reference": row.secret_reference,
        "allowed_consumers": row.allowed_consumers_json,
        "allowed_operations": row.allowed_operations_json,
        "rotation_interval_days": row.rotation_interval_days,
        "overlap_minutes": row.overlap_minutes,
        "status": row.status,
        "enabled": row.enabled,
        "public_summary": row.public_summary,
        "metadata": row.metadata_json,
        "secret_value_persisted": False,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def key_version_dict(row: CredentialKeyVersion) -> dict:
    return {
        "id": row.id,
        "credential_id": row.credential_id,
        "version": row.version,
        "key_id": row.key_id,
        "algorithm": row.algorithm,
        "fingerprint_sha256": row.fingerprint_sha256,
        "state": row.state,
        "issued_at": row.issued_at,
        "activates_at": row.activates_at,
        "expires_at": row.expires_at,
        "retire_after": row.retire_after,
        "revoked_at": row.revoked_at,
        "revocation_reason": row.revocation_reason,
        "compromise_reported_at": row.compromise_reported_at,
        "secret_value_persisted": False,
        "metadata": row.metadata_json,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def rotation_dict(row: CredentialRotationRecord) -> dict:
    return {
        "id": row.id,
        "credential_id": row.credential_id,
        "from_key_version_id": row.from_key_version_id,
        "to_key_version_id": row.to_key_version_id,
        "state": row.state,
        "reason": row.reason,
        "requested_by": row.requested_by,
        "requested_at": row.requested_at,
        "overlap_starts_at": row.overlap_starts_at,
        "overlap_ends_at": row.overlap_ends_at,
        "completed_at": row.completed_at,
        "automatic_secret_generation": False,
        "automatic_secret_distribution": False,
        "automatic_activation": False,
        "metadata": row.metadata_json,
    }


def lifecycle_event_dict(row: CredentialLifecycleEvent) -> dict:
    return {
        "id": row.id,
        "credential_id": row.credential_id,
        "key_version_id": row.key_version_id,
        "event_type": row.event_type,
        "actor": row.actor,
        "detail": row.detail,
        "metadata": row.metadata_json,
        "created_at": row.created_at,
    }


def use_event_dict(row: CredentialUseEvent) -> dict:
    return {
        "id": row.id,
        "credential_id": row.credential_id,
        "key_version_id": row.key_version_id,
        "service_id": row.service_id,
        "operation": row.operation,
        "success": row.success,
        "context": row.context_json,
        "occurred_at": row.occurred_at,
    }


def _event(db: Session, credential_id: str, event_type: str, *, key_version_id: str | None = None,
           actor: str = "operator", detail: str = "", metadata: dict | None = None, commit: bool = False) -> CredentialLifecycleEvent:
    row = CredentialLifecycleEvent(
        credential_id=credential_id,
        key_version_id=key_version_id,
        event_type=event_type,
        actor=actor[:255],
        detail=detail[:1000],
        metadata_json=sanitize_metadata(metadata or {}),
    )
    db.add(row)
    if commit:
        db.commit(); db.refresh(row)
    else:
        db.flush()
    return row


def upsert_credential(db: Session, settings, *, credential_key: str, name: str, credential_type: str,
                      purpose: str, owner_scope: str = "platform-core", provider: str = "environment",
                      secret_reference: str, allowed_consumers: list[str] | None = None,
                      allowed_operations: list[str] | None = None, rotation_interval_days: int | None = None,
                      overlap_minutes: int | None = None, status: str = "active", enabled: bool = True,
                      public_summary: bool = False, metadata: dict | None = None) -> CredentialRegistryRecord:
    if credential_type not in CREDENTIAL_TYPES:
        raise ValueError(f"unsupported credential_type: {credential_type}")
    if status not in {"active", "inactive", "retired"}:
        raise ValueError("credential status must be active, inactive, or retired")
    reference = validate_reference(secret_reference)
    interval = int(rotation_interval_days or settings.credential_default_rotation_days)
    overlap = int(overlap_minutes if overlap_minutes is not None else settings.credential_default_overlap_minutes)
    if interval < 1 or interval > 3650:
        raise ValueError("rotation_interval_days must be between 1 and 3650")
    if overlap < 0 or overlap > 10080:
        raise ValueError("overlap_minutes must be between 0 and 10080")
    row = db.scalar(select(CredentialRegistryRecord).where(CredentialRegistryRecord.credential_key == credential_key.strip()))
    values = dict(
        credential_key=credential_key.strip(), name=name.strip(), credential_type=credential_type,
        purpose=purpose.strip(), owner_scope=owner_scope.strip() or "platform-core", provider=provider.strip() or "environment",
        secret_reference=reference, allowed_consumers_json=sorted(set(allowed_consumers or [])),
        allowed_operations_json=sorted(set(allowed_operations or [])), rotation_interval_days=interval,
        overlap_minutes=overlap, status=status, enabled=bool(enabled), public_summary=bool(public_summary),
        metadata_json=sanitize_metadata(metadata or {}),
    )
    if row is None:
        row = CredentialRegistryRecord(**values)
        db.add(row); db.flush()
        _event(db, row.id, "credential-registered", detail="Secret-free credential metadata registered")
    else:
        for key, value in values.items(): setattr(row, key, value)
        _event(db, row.id, "credential-updated", detail="Credential governance metadata updated")
    db.commit(); db.refresh(row)
    return row


def list_credentials(db: Session, *, enabled_only: bool = False) -> list[CredentialRegistryRecord]:
    q = select(CredentialRegistryRecord).order_by(CredentialRegistryRecord.credential_key)
    if enabled_only: q = q.where(CredentialRegistryRecord.enabled.is_(True))
    return list(db.scalars(q).all())


def register_key_version(db: Session, settings, credential_id: str, *, key_id: str | None = None,
                         algorithm: str = "opaque", fingerprint_sha256: str | None = None,
                         issued_at: datetime | None = None, expires_at: datetime | None = None,
                         metadata: dict | None = None) -> CredentialKeyVersion:
    credential = db.get(CredentialRegistryRecord, credential_id)
    if credential is None: raise ValueError("credential not found")
    if fingerprint_sha256 is not None and not HEX64.fullmatch(fingerprint_sha256):
        raise ValueError("fingerprint_sha256 must be exactly 64 hexadecimal characters")
    max_version = db.scalar(select(func.max(CredentialKeyVersion.version)).where(CredentialKeyVersion.credential_id == credential_id)) or 0
    version = int(max_version) + 1
    issued = aware(issued_at) or now()
    expires = aware(expires_at) or (issued + timedelta(days=credential.rotation_interval_days))
    if expires <= issued: raise ValueError("expires_at must be after issued_at")
    resolved_key_id = (key_id or f"{credential.credential_key}-v{version}").strip()
    if db.scalar(select(CredentialKeyVersion).where(CredentialKeyVersion.key_id == resolved_key_id)) is not None:
        raise ValueError("key_id already exists")
    row = CredentialKeyVersion(
        credential_id=credential_id, version=version, key_id=resolved_key_id,
        algorithm=algorithm.strip() or "opaque", fingerprint_sha256=fingerprint_sha256.lower() if fingerprint_sha256 else None,
        state="staged", issued_at=issued, expires_at=expires, secret_value_persisted=False,
        metadata_json=sanitize_metadata(metadata or {}),
    )
    db.add(row); db.flush()
    _event(db, credential_id, "key-version-registered", key_version_id=row.id,
           detail=f"Registered key version {version} metadata without secret material")
    db.commit(); db.refresh(row)
    return row


def list_key_versions(db: Session, credential_id: str) -> list[CredentialKeyVersion]:
    if db.get(CredentialRegistryRecord, credential_id) is None: raise ValueError("credential not found")
    return list(db.scalars(select(CredentialKeyVersion).where(CredentialKeyVersion.credential_id == credential_id).order_by(CredentialKeyVersion.version)).all())


def active_key(db: Session, credential_id: str) -> CredentialKeyVersion | None:
    return db.scalar(select(CredentialKeyVersion).where(
        CredentialKeyVersion.credential_id == credential_id,
        CredentialKeyVersion.state == "active",
    ).order_by(desc(CredentialKeyVersion.version)))


def rotate(db: Session, credential_id: str, to_key_version_id: str, *, requested_by: str = "operator",
           reason: str = "scheduled-rotation", overlap_minutes: int | None = None, metadata: dict | None = None) -> CredentialRotationRecord:
    credential = db.get(CredentialRegistryRecord, credential_id)
    target = db.get(CredentialKeyVersion, to_key_version_id)
    if credential is None: raise ValueError("credential not found")
    if target is None or target.credential_id != credential_id: raise ValueError("target key version not found for credential")
    if target.state not in {"staged", "retired"}: raise ValueError("target key version must be staged or retired")
    current = active_key(db, credential_id)
    overlap = credential.overlap_minutes if overlap_minutes is None else int(overlap_minutes)
    if overlap < 0 or overlap > 10080: raise ValueError("overlap_minutes must be between 0 and 10080")
    timestamp = now()
    target.state = "active"; target.activates_at = timestamp; target.retire_after = None
    if current is not None and current.id != target.id:
        current.state = "retiring"; current.retire_after = timestamp + timedelta(minutes=overlap)
    row = CredentialRotationRecord(
        credential_id=credential_id,
        from_key_version_id=current.id if current and current.id != target.id else None,
        to_key_version_id=target.id,
        state="overlap" if current and current.id != target.id else "complete",
        reason=reason[:500], requested_by=requested_by[:255], requested_at=timestamp,
        overlap_starts_at=timestamp if current and current.id != target.id else None,
        overlap_ends_at=(timestamp + timedelta(minutes=overlap)) if current and current.id != target.id else None,
        completed_at=None if current and current.id != target.id else timestamp,
        automatic_secret_generation=False, automatic_secret_distribution=False, automatic_activation=False,
        metadata_json=sanitize_metadata(metadata or {}),
    )
    db.add(row); db.flush()
    _event(db, credential_id, "rotation-started" if row.state == "overlap" else "key-activated",
           key_version_id=target.id, actor=requested_by,
           detail="Operator-triggered key activation; Core did not generate or distribute secret material")
    db.commit(); db.refresh(row)
    return row


def complete_rotation(db: Session, rotation_id: str, *, actor: str = "operator") -> CredentialRotationRecord:
    row = db.get(CredentialRotationRecord, rotation_id)
    if row is None: raise ValueError("rotation not found")
    if row.state == "complete": return row
    if row.state != "overlap": raise ValueError("rotation is not in overlap state")
    if row.from_key_version_id:
        previous = db.get(CredentialKeyVersion, row.from_key_version_id)
        if previous and previous.state == "retiring":
            previous.state = "retired"; previous.retire_after = now()
    row.state = "complete"; row.completed_at = now()
    _event(db, row.credential_id, "rotation-completed", key_version_id=row.to_key_version_id,
           actor=actor, detail="Operator confirmed rotation completion")
    db.commit(); db.refresh(row)
    return row


def revoke_key(db: Session, key_version_id: str, *, reason: str, actor: str = "operator", compromised: bool = False) -> CredentialKeyVersion:
    row = db.get(CredentialKeyVersion, key_version_id)
    if row is None: raise ValueError("key version not found")
    timestamp = now()
    row.state = "compromised" if compromised else "revoked"
    row.revoked_at = timestamp; row.revocation_reason = reason[:500]
    row.compromise_reported_at = timestamp if compromised else row.compromise_reported_at
    _event(db, row.credential_id, "key-compromised" if compromised else "key-revoked",
           key_version_id=row.id, actor=actor, detail=reason)
    db.commit(); db.refresh(row)
    return row


def record_use(db: Session, credential_id: str, *, service_id: str, operation: str,
               key_version_id: str | None = None, success: bool = True,
               context: dict | None = None, occurred_at: datetime | None = None) -> CredentialUseEvent:
    credential = db.get(CredentialRegistryRecord, credential_id)
    if credential is None: raise ValueError("credential not found")
    if key_version_id:
        version = db.get(CredentialKeyVersion, key_version_id)
        if version is None or version.credential_id != credential_id: raise ValueError("key version not found for credential")
    row = CredentialUseEvent(
        credential_id=credential_id, key_version_id=key_version_id,
        service_id=service_id.strip(), operation=operation.strip(), success=bool(success),
        context_json=sanitize_metadata(context or {}), occurred_at=aware(occurred_at) or now(),
    )
    db.add(row); db.commit(); db.refresh(row)
    return row


def list_use_events(db: Session, credential_id: str | None = None, *, limit: int = 200) -> list[CredentialUseEvent]:
    q = select(CredentialUseEvent).order_by(desc(CredentialUseEvent.occurred_at)).limit(limit)
    if credential_id: q = q.where(CredentialUseEvent.credential_id == credential_id)
    return list(db.scalars(q).all())


def list_lifecycle_events(db: Session, credential_id: str | None = None, *, limit: int = 200) -> list[CredentialLifecycleEvent]:
    q = select(CredentialLifecycleEvent).order_by(desc(CredentialLifecycleEvent.created_at)).limit(limit)
    if credential_id: q = q.where(CredentialLifecycleEvent.credential_id == credential_id)
    return list(db.scalars(q).all())


def list_rotations(db: Session, credential_id: str | None = None, *, limit: int = 200) -> list[CredentialRotationRecord]:
    q = select(CredentialRotationRecord).order_by(desc(CredentialRotationRecord.requested_at)).limit(limit)
    if credential_id: q = q.where(CredentialRotationRecord.credential_id == credential_id)
    return list(db.scalars(q).all())


def bootstrap_core_credentials(db: Session, settings) -> list[CredentialRegistryRecord]:
    definitions = [
        dict(credential_key="platform-core-write-api-key", name="Platform Core write API key", credential_type="service-api-key",
             purpose="Authenticate privileged Core write operations", secret_reference="env:SC_CORE_WRITE_API_KEY",
             allowed_consumers=["platform-core-operators"], allowed_operations=["core-write"]),
        dict(credential_key="platform-core-webhook-signing", name="Platform Core webhook signing key", credential_type="webhook-signing-key",
             purpose="Sign outbound developer webhook deliveries", secret_reference="env:SC_CORE_WEBHOOK_SIGNING_SECRET",
             allowed_consumers=["platform-core-webhooks"], allowed_operations=["webhook-sign"]),
        dict(credential_key="platform-core-dossier-signing", name="Platform Core dossier signing key", credential_type="dossier-signing-key",
             purpose="Sign governed dossier manifests", secret_reference="env:SC_CORE_DOSSIER_SIGNING_SECRET",
             allowed_consumers=["platform-core-dossiers"], allowed_operations=["dossier-sign"]),
        dict(credential_key="platform-core-federation-trust", name="Platform Core federation trust secret set", credential_type="federation-shared-secret",
             purpose="Authenticate trusted-node federation manifests", secret_reference="env:SC_CORE_FEDERATION_TRUST_SECRETS_JSON",
             allowed_consumers=["platform-core-federation"], allowed_operations=["federation-sign", "federation-verify"]),
    ]
    return [upsert_credential(db, settings, **item) for item in definitions]


def runtime_binding_status(settings) -> dict:
    return {
        "write_api_key_configured": bool(settings.write_api_key),
        "webhook_signing_secret_configured": bool(settings.webhook_signing_secret),
        "dossier_signing_secret_configured": bool(settings.dossier_signing_secret),
        "federation_trust_secrets_configured": bool(settings.federation_trust_secrets_json and settings.federation_trust_secrets_json.strip() not in {"", "{}"}),
        "secret_values_exposed": False,
    }


def readiness(db: Session, settings) -> dict:
    timestamp = now()
    soon = timestamp + timedelta(days=settings.credential_expiry_warning_days)
    credentials = list(db.scalars(select(CredentialRegistryRecord).where(CredentialRegistryRecord.enabled.is_(True))).all())
    versions = list(db.scalars(select(CredentialKeyVersion)).all())
    by_credential: dict[str, list[CredentialKeyVersion]] = {}
    for version in versions: by_credential.setdefault(version.credential_id, []).append(version)
    missing_active = 0; expired_active = 0; expiring_soon = 0; overdue_rotation = 0; compromised = 0
    for credential in credentials:
        items = by_credential.get(credential.id, [])
        active = [v for v in items if v.state == "active"]
        if not active:
            missing_active += 1
        for v in active:
            expires = aware(v.expires_at)
            if expires and expires <= timestamp: expired_active += 1
            elif expires and expires <= soon: expiring_soon += 1
        if items:
            latest_issued = max((aware(v.issued_at) or timestamp) for v in items)
            if latest_issued + timedelta(days=credential.rotation_interval_days) < timestamp:
                overdue_rotation += 1
        compromised += sum(1 for v in items if v.state == "compromised")
    persisted = sum(1 for v in versions if v.secret_value_persisted)
    lifecycle_ready = not (missing_active or expired_active or overdue_rotation or compromised or persisted)
    return {
        "enabled": settings.credential_key_lifecycle_enabled,
        "state": "ready" if lifecycle_ready else "attention-required",
        "credential_lifecycle_ready": lifecycle_ready,
        "credential_records": len(credentials),
        "key_versions": len(versions),
        "missing_active_versions": missing_active,
        "expired_active_versions": expired_active,
        "expiring_soon_versions": expiring_soon,
        "overdue_rotations": overdue_rotation,
        "compromised_versions": compromised,
        "persisted_secret_values": persisted,
        "secret_values_persisted": False,
        "automatic_secret_generation": False,
        "automatic_secret_distribution": False,
        "automatic_key_rotation": False,
        "runtime_bindings": runtime_binding_status(settings),
    }


def public_status(db: Session, settings) -> dict:
    snapshot = readiness(db, settings)
    return {
        "state": snapshot["state"],
        "credential_lifecycle_ready": snapshot["credential_lifecycle_ready"],
        "tracked_credentials": snapshot["credential_records"],
        "expiring_soon_versions": snapshot["expiring_soon_versions"],
        "overdue_rotations": snapshot["overdue_rotations"],
        "compromised_versions": snapshot["compromised_versions"],
        "secret_values_exposed": False,
        "secret_references_exposed": False,
        "key_ids_exposed": False,
        "fingerprints_exposed": False,
        "automatic_key_rotation": False,
    }


def certification_snapshot(db: Session, settings) -> dict:
    return readiness(db, settings)
