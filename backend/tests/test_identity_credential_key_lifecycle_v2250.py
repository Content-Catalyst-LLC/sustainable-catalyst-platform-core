from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient


def create_credential(client, headers, **overrides):
    payload = {
        "credential_key": "core-webhook-signing",
        "name": "Core webhook signing",
        "credential_type": "webhook-signing-key",
        "purpose": "Sign outbound webhooks",
        "owner_scope": "platform-core",
        "provider": "environment",
        "secret_reference": "env:SC_CORE_WEBHOOK_SIGNING_SECRET",
        "allowed_consumers": ["platform-core-webhooks"],
        "allowed_operations": ["webhook-sign"],
        "rotation_interval_days": 90,
        "overlap_minutes": 30,
    }
    payload.update(overrides)
    response = client.post("/v1/credentials/registry", headers=headers, json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def create_version(client, headers, credential_id, key_id, **overrides):
    payload = {"key_id": key_id, "algorithm": "hmac-sha256", "fingerprint_sha256": "a" * 64}
    payload.update(overrides)
    response = client.post(f"/v1/credentials/registry/{credential_id}/versions", headers=headers, json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_v2250_release_migration_and_non_actuation(client):
    assert client.get("/health").json()["version"] == "2.26.0"
    body = client.get("/v1/credentials/readiness").json()
    assert body["release"] == "2.26.0"
    assert body["migration_0028_applied"] is True
    assert body["pending_migrations"] == []
    assert body["secret_values_persisted"] is False
    assert body["automatic_secret_generation"] is False
    assert body["automatic_secret_distribution"] is False
    assert body["automatic_key_rotation"] is False


def test_registry_persists_reference_and_policy_but_not_secret_value(client, write_headers):
    row = create_credential(client, write_headers)
    assert row["secret_reference"] == "env:SC_CORE_WEBHOOK_SIGNING_SECRET"
    assert row["secret_value_persisted"] is False
    assert row["allowed_consumers"] == ["platform-core-webhooks"]
    assert row["allowed_operations"] == ["webhook-sign"]

    bad = client.post("/v1/credentials/registry", headers=write_headers, json={
        "credential_key": "bad", "name": "Bad", "credential_type": "service-token", "purpose": "test",
        "secret_reference": "actual-secret-value",
    })
    assert bad.status_code == 422


def test_request_model_rejects_direct_secret_material_fields(client, write_headers):
    response = client.post("/v1/credentials/registry", headers=write_headers, json={
        "credential_key": "bad-extra", "name": "Bad extra", "credential_type": "service-token", "purpose": "test",
        "secret_reference": "env:SC_CORE_TEST_TOKEN", "secret_value": "do-not-store-me",
    })
    assert response.status_code == 422


def test_key_version_is_metadata_only_and_fingerprint_validated(client, write_headers):
    credential = create_credential(client, write_headers)
    version = create_version(client, write_headers, credential["id"], "webhook-2026-08")
    assert version["version"] == 1
    assert version["state"] == "staged"
    assert version["secret_value_persisted"] is False
    assert version["fingerprint_sha256"] == "a" * 64

    invalid = client.post(f"/v1/credentials/registry/{credential['id']}/versions", headers=write_headers, json={
        "key_id": "bad-fingerprint", "fingerprint_sha256": "abc"
    })
    assert invalid.status_code == 422


def test_operator_rotation_supports_overlap_and_completion(client, write_headers):
    credential = create_credential(client, write_headers, overlap_minutes=45)
    v1 = create_version(client, write_headers, credential["id"], "webhook-v1")
    first = client.post(f"/v1/credentials/registry/{credential['id']}/rotate", headers=write_headers, json={"to_key_version_id": v1["id"]})
    assert first.status_code == 200
    assert first.json()["state"] == "complete"
    assert first.json()["automatic_secret_generation"] is False

    v2 = create_version(client, write_headers, credential["id"], "webhook-v2")
    second = client.post(f"/v1/credentials/registry/{credential['id']}/rotate", headers=write_headers, json={
        "to_key_version_id": v2["id"], "reason": "scheduled-quarterly-rotation"
    })
    assert second.status_code == 200, second.text
    rotation = second.json()
    assert rotation["state"] == "overlap"
    assert rotation["from_key_version_id"] == v1["id"]
    assert rotation["to_key_version_id"] == v2["id"]
    assert rotation["automatic_secret_distribution"] is False
    done = client.post(f"/v1/credentials/rotations/{rotation['id']}/complete", headers=write_headers, json={"actor": "security-operator"})
    assert done.status_code == 200
    assert done.json()["state"] == "complete"
    versions = client.get(f"/v1/credentials/registry/{credential['id']}/versions").json()["items"]
    assert {row["key_id"]: row["state"] for row in versions} == {"webhook-v1": "retired", "webhook-v2": "active"}


def test_compromise_revocation_is_explicit_and_readiness_degrades(client, write_headers):
    credential = create_credential(client, write_headers)
    v1 = create_version(client, write_headers, credential["id"], "webhook-compromise")
    client.post(f"/v1/credentials/registry/{credential['id']}/rotate", headers=write_headers, json={"to_key_version_id": v1["id"]})
    response = client.post(f"/v1/credentials/versions/{v1['id']}/revoke", headers=write_headers, json={
        "reason": "suspected exposure", "actor": "incident-commander", "compromised": True
    })
    assert response.status_code == 200
    assert response.json()["state"] == "compromised"
    assert response.json()["compromise_reported_at"] is not None
    readiness = client.get("/v1/credentials/readiness").json()
    assert readiness["credential_lifecycle_ready"] is False
    assert readiness["compromised_versions"] == 1
    assert readiness["missing_active_versions"] == 1


def test_usage_audit_strips_credential_like_context(client, write_headers):
    credential = create_credential(client, write_headers)
    response = client.post(f"/v1/credentials/registry/{credential['id']}/use-events", headers=write_headers, json={
        "service_id": "webhook-dispatcher", "operation": "sign", "success": True,
        "context": {"delivery_id": "abc", "api_key": "must-not-persist", "nested": {"access_token": "must-not-persist", "attempt": 1}}
    })
    assert response.status_code == 200, response.text
    context = response.json()["context"]
    assert context == {"delivery_id": "abc", "nested": {"attempt": 1}}


def test_bootstrap_tracks_core_secret_bindings_without_values(client, write_headers):
    response = client.post("/v1/credentials/bootstrap/core", headers=write_headers)
    assert response.status_code == 200, response.text
    rows = response.json()["items"]
    assert len(rows) == 4
    refs = {row["secret_reference"] for row in rows}
    assert "env:SC_CORE_FEDERATION_TRUST_SECRETS_JSON" in refs
    assert "env:SC_CORE_WEBHOOK_SIGNING_SECRET" in refs
    assert all(row["secret_value_persisted"] is False for row in rows)
    assert response.json()["secret_values_persisted"] is False


def test_public_status_is_aggregate_only(client):
    response = client.get("/api/v1/credentials/status")
    assert response.status_code in (200, 401, 403)
    if response.status_code == 200:
        data = response.json()["data"]
        assert data["secret_values_exposed"] is False
        assert data["secret_references_exposed"] is False
        assert data["key_ids_exposed"] is False
        assert data["fingerprints_exposed"] is False
        assert "secret_reference" not in data
        assert "key_id" not in data
        assert "fingerprint_sha256" not in data


def test_expiry_and_rotation_overdue_diagnostics(client, write_headers):
    credential = create_credential(client, write_headers, rotation_interval_days=10)
    issued = datetime.now(timezone.utc) - timedelta(days=30)
    expires = datetime.now(timezone.utc) + timedelta(days=3)
    version = create_version(client, write_headers, credential["id"], "old-key", issued_at=issued.isoformat(), expires_at=expires.isoformat())
    client.post(f"/v1/credentials/registry/{credential['id']}/rotate", headers=write_headers, json={"to_key_version_id": version["id"]})
    body = client.get("/v1/credentials/readiness").json()
    assert body["expiring_soon_versions"] == 1
    assert body["overdue_rotations"] == 1
    assert body["credential_lifecycle_ready"] is False


def test_credential_certification_gate_is_optional_and_can_block(tmp_path):
    db_path = tmp_path / "cert.db"
    app = create_app(Settings(
        environment="test", database_url=f"sqlite:///{db_path}", write_api_key="test-secret",
        certification_require_credential_lifecycle_ready=True,
    ))
    headers = {"X-SC-API-Key": "test-secret"}
    with TestClient(app) as client:
        create_credential(client, headers)
        response = client.post("/v1/certification/runs", headers=headers)
        assert response.status_code == 200, response.text
        detail = response.json()["detail"]
        assert detail["state"] == "blocked"
        assert "credential_key_lifecycle" in detail["blockers"]
        assert detail["checks"]["credential_lifecycle_ready"] is False


def test_meta_promotes_v2250_capabilities_and_keeps_public_key_crypto_deferred(client):
    body = client.get("/v1/meta").json()
    expected = {
        "identity_credential_key_lifecycle", "secret_free_credential_registry",
        "cryptographic_key_version_metadata", "credential_expiry_and_revocation",
        "overlap_aware_key_rotation", "credential_use_audit_events",
        "public_safe_credential_health", "credential_lifecycle_certification_gate",
    }
    assert expected.issubset(set(body["capabilities"]))
    assert expected.isdisjoint(set(body["deferred_capabilities"]))
    assert "external_public_key_signature_verification" in set(body["deferred_capabilities"])


def test_lifecycle_events_are_auditable_without_secret_material(client, write_headers):
    credential = create_credential(client, write_headers, metadata={"team": "platform", "secret": "should-strip"})
    version = create_version(client, write_headers, credential["id"], "audit-v1", metadata={"ticket": "SEC-25", "private_key": "strip"})
    client.post(f"/v1/credentials/registry/{credential['id']}/rotate", headers=write_headers, json={"to_key_version_id": version["id"]})
    events = client.get(f"/v1/credentials/events?credential_id={credential['id']}", headers=write_headers).json()["items"]
    assert len(events) >= 3
    serialized = str(events).lower()
    assert "should-strip" not in serialized
    assert "private_key" not in serialized
