from __future__ import annotations

from types import SimpleNamespace

from sqlalchemy import select

from app.hashing import sha256_text
from app.models import (
    ApiCredential,
    ApiPlan,
    LedgerEntry,
    WebhookDelivery,
    WebhookEvent,
)
from app.services.developers import dispatch_pending_webhooks


def create_application(
    client,
    write_headers,
    *,
    status="approved",
    plan_id="free",
    name="Test Developer Application",
):
    response = client.post(
        "/v1/developer/applications",
        headers=write_headers,
        json={
            "name": name,
            "owner_name": "Test Developer",
            "owner_email": "developer@example.com",
            "organization": "Example Organization",
            "website_url": "https://example.com",
            "use_case": (
                "Build a public-interest integration that uses the Sustainable "
                "Catalyst registry, graph, and evidence records."
            ),
            "status": status,
            "plan_id": plan_id,
            "metadata": {},
            "actor": "platform-administrator",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def issue_key(
    client,
    write_headers,
    application_id,
    *,
    scopes=None,
    label="Test key",
):
    response = client.post(
        f"/v1/developer/applications/{application_id}/credentials",
        headers=write_headers,
        json={
            "label": label,
            "scopes": scopes or [],
            "created_by": "platform-administrator",
            "metadata": {},
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def public_headers(api_key):
    return {"Authorization": f"Bearer {api_key}"}


def test_plans_are_seeded_and_portal_assets_are_public(client):
    plans = client.get("/developers/plans.json")
    assert plans.status_code == 200
    plan_ids = {plan["id"] for plan in plans.json()}
    assert {"free", "standard"}.issubset(plan_ids)
    assert "internal" not in plan_ids

    portal = client.get("/developers")
    assert portal.status_code == 200
    assert "Developer Portal" in portal.text
    assert "/api/v1" in portal.text

    console = client.get("/developers/console")
    assert console.status_code == 200
    assert "API Console" in console.text

    openapi = client.get("/developers/openapi.json")
    assert openapi.status_code == 200
    assert openapi.json()["paths"]
    assert all(
        path.startswith("/api/v1")
        for path in openapi.json()["paths"]
    )
    security_schemes = openapi.json()["components"]["securitySchemes"]
    assert "SCPublicKey" in security_schemes
    assert "BearerAuth" in security_schemes

    python_sdk = client.get("/developers/sdk/python.zip")
    javascript_sdk = client.get("/developers/sdk/javascript.zip")
    postman = client.get("/developers/postman.json")
    assert python_sdk.status_code == 200
    assert javascript_sdk.status_code == 200
    assert postman.status_code == 200
    assert len(python_sdk.content) > 100
    assert len(javascript_sdk.content) > 100


def test_key_is_returned_once_and_stored_only_as_hash(client, write_headers):
    application = create_application(client, write_headers)
    raw_response = client.post(
        f"/v1/developer/applications/{application['id']}/credentials",
        headers=write_headers,
        json={
            "label": "Test key",
            "scopes": [],
            "created_by": "platform-administrator",
            "metadata": {},
        },
    )
    assert raw_response.status_code == 201
    assert raw_response.headers["Cache-Control"] == "no-store"
    issued = raw_response.json()
    api_key = issued["api_key"]
    credential = issued["credential"]

    assert api_key.startswith("scpk_")
    assert credential["key_prefix"] in api_key
    assert credential["key_last_four"] == api_key[-4:]
    assert "key_hash" not in credential

    database = client.app.state.database
    with database.session_factory() as db:
        stored = db.get(ApiCredential, credential["id"])
        assert stored.key_hash == sha256_text(api_key)
        assert stored.key_hash != api_key
        assert api_key not in stored.metadata_json.values()

    listed = client.get(
        f"/v1/developer/applications/{application['id']}/credentials",
        headers=write_headers,
    )
    assert listed.status_code == 200
    assert "api_key" not in listed.text
    assert "key_hash" not in listed.text


def test_public_api_auth_envelope_headers_and_usage(client, write_headers):
    application = create_application(client, write_headers)
    issued = issue_key(
        client,
        write_headers,
        application["id"],
        scopes=["public:status", "developer:read", "registry:read"],
    )
    api_key = issued["api_key"]

    unauthorized = client.get("/api/v1/status")
    assert unauthorized.status_code == 401
    assert unauthorized.headers["X-Request-ID"]

    first = client.get("/api/v1/status", headers=public_headers(api_key))
    second = client.get(
        "/api/v1/entities",
        headers={"X-SC-Public-Key": api_key},
    )
    assert first.status_code == 200
    assert second.status_code == 200

    body = first.json()
    assert body["data"]["status"] == "operational"
    assert body["meta"]["api_version"] == "v1"
    assert body["meta"]["request_id"] == first.headers["X-Request-ID"]
    assert first.headers["X-SC-API-Version"] == "1"
    assert int(first.headers["X-RateLimit-Remaining-Minute"]) >= 0

    usage = client.get(
        "/api/v1/developer/usage?days=30",
        headers=public_headers(api_key),
    )
    assert usage.status_code == 200
    usage_data = usage.json()["data"]
    assert usage_data["requests"] >= 2
    assert usage_data["requests_by_path"]["/api/v1/status"] >= 1
    assert usage_data["requests_by_path"]["/api/v1/entities"] >= 1


def test_scope_enforcement_and_key_revocation(client, write_headers):
    application = create_application(client, write_headers)
    issued = issue_key(
        client,
        write_headers,
        application["id"],
        scopes=["public:status"],
    )
    api_key = issued["api_key"]
    credential_id = issued["credential"]["id"]

    status_response = client.get(
        "/api/v1/status",
        headers=public_headers(api_key),
    )
    entities_response = client.get(
        "/api/v1/entities",
        headers=public_headers(api_key),
    )
    assert status_response.status_code == 200
    assert entities_response.status_code == 403
    assert "registry:read" in entities_response.json()["detail"]

    revoked = client.post(
        f"/v1/developer/credentials/{credential_id}/revoke",
        headers=write_headers,
        json={"revoked_by": "platform-administrator"},
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"

    after_revoke = client.get(
        "/api/v1/status",
        headers=public_headers(api_key),
    )
    assert after_revoke.status_code == 401


def test_plan_rate_limit_is_enforced(client, write_headers):
    database = client.app.state.database
    with database.session_factory() as db:
        plan = db.get(ApiPlan, "free")
        plan.requests_per_minute = 2
        plan.requests_per_day = 100
        db.commit()

    application = create_application(client, write_headers)
    api_key = issue_key(
        client,
        write_headers,
        application["id"],
        scopes=["public:status"],
    )["api_key"]

    first = client.get("/api/v1/status", headers=public_headers(api_key))
    second = client.get("/api/v1/status", headers=public_headers(api_key))
    third = client.get("/api/v1/status", headers=public_headers(api_key))

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.headers["Retry-After"] == "60"


def test_public_ledger_filters_developer_application_records(
    client,
    write_headers,
):
    application = create_application(client, write_headers)
    api_key = issue_key(
        client,
        write_headers,
        application["id"],
        scopes=["ledger:read"],
    )["api_key"]

    database = client.app.state.database
    with database.session_factory() as db:
        internal_entries = list(
            db.scalars(
                select(LedgerEntry).where(
                    LedgerEntry.record_type == "developer_application"
                )
            ).all()
        )
        assert internal_entries

    public_entries = client.get(
        "/api/v1/ledger/entries",
        headers=public_headers(api_key),
    )
    assert public_entries.status_code == 200
    assert all(
        entry["record_type"] != "developer_application"
        for entry in public_entries.json()["data"]
    )

    explicit_internal = client.get(
        "/api/v1/ledger/entries?record_type=developer_application",
        headers=public_headers(api_key),
    )
    assert explicit_internal.status_code == 404


def test_webhook_subscription_signature_and_delivery(
    client,
    write_headers,
):
    application = create_application(client, write_headers)
    issued = issue_key(
        client,
        write_headers,
        application["id"],
        scopes=["webhooks:manage", "developer:read"],
    )
    api_key = issued["api_key"]

    subscription_response = client.post(
        "/api/v1/developer/webhooks",
        headers=public_headers(api_key),
        json={
            "callback_url": "https://example.com/webhooks/platform-core",
            "event_types": ["claim.*"],
            "description": "Claim event integration",
            "metadata": {},
        },
    )
    assert subscription_response.status_code == 200, subscription_response.text
    subscription_payload = subscription_response.json()["data"]
    subscription = subscription_payload["subscription"]
    signing_secret = subscription_payload["signing_secret"]
    assert signing_secret.startswith("scwhsec_")

    claim_response = client.post(
        "/v1/claims",
        headers=write_headers,
        json={
            "actor": "decision-studio",
            "claim_text": "A public API webhook test claim.",
            "claim_type": "factual",
            "status": "published",
            "visibility": "public",
            "language": "en",
            "metadata": {},
        },
    )
    assert claim_response.status_code == 201

    captured = {}

    def fake_sender(*, url, content, headers, timeout):
        captured["url"] = url
        captured["content"] = content
        captured["headers"] = headers
        captured["timeout"] = timeout
        return SimpleNamespace(status_code=204, text="")

    database = client.app.state.database
    with database.session_factory() as db:
        result = dispatch_pending_webhooks(
            db,
            master_secret=client.app.state.settings.webhook_signing_secret,
            timeout=5,
            limit=100,
            sender=fake_sender,
        )
        assert result.deliveries_succeeded >= 1

    assert captured["url"] == subscription["callback_url"]
    assert captured["headers"]["X-SC-Webhook-Signature"].startswith("v1=")
    assert captured["headers"]["X-SC-Webhook-Timestamp"]
    assert '"type":"claim.created"' in captured["content"]

    deliveries = client.get(
        f"/api/v1/developer/webhooks/{subscription['id']}/deliveries",
        headers=public_headers(api_key),
    )
    assert deliveries.status_code == 200
    assert deliveries.json()["data"][0]["status"] == "delivered"

    database = client.app.state.database
    with database.session_factory() as db:
        event = db.scalar(
            select(WebhookEvent)
            .where(WebhookEvent.event_type == "claim.created")
            .order_by(WebhookEvent.created_at.desc())
        )
        delivery = db.scalar(
            select(WebhookDelivery)
            .where(WebhookDelivery.event_id == event.id)
        )
        assert event.status == "processed"
        assert delivery.signature == captured["headers"]["X-SC-Webhook-Signature"]


def test_failed_webhook_delivery_remains_pending_for_retry(
    client,
    write_headers,
):
    application = create_application(
        client,
        write_headers,
        name="Webhook Retry Application",
    )
    api_key = issue_key(
        client,
        write_headers,
        application["id"],
        scopes=["webhooks:manage"],
        label="Retry key",
    )["api_key"]

    subscription = client.post(
        "/api/v1/developer/webhooks",
        headers=public_headers(api_key),
        json={
            "callback_url": "https://example.com/retry",
            "event_types": ["evidence.*"],
            "metadata": {},
        },
    )
    assert subscription.status_code == 200

    event = client.post(
        "/v1/developer/events",
        headers=write_headers,
        json={
            "event_type": "evidence.created",
            "resource_type": "evidence",
            "resource_id": "sc:evidence:test",
            "payload": {"id": "sc:evidence:test"},
            "actor": "platform-administrator",
        },
    )
    assert event.status_code == 201

    def failing_sender(**kwargs):
        return SimpleNamespace(status_code=503, text="Unavailable")

    database = client.app.state.database
    with database.session_factory() as db:
        result = dispatch_pending_webhooks(
            db,
            master_secret=client.app.state.settings.webhook_signing_secret,
            timeout=5,
            sender=failing_sender,
        )
        assert result.deliveries_failed >= 1
        stored_event = db.get(WebhookEvent, event.json()["id"])
        assert stored_event.status == "pending"
        assert stored_event.processed_at is None


def test_private_webhook_targets_are_rejected(client, write_headers):
    application = create_application(
        client,
        write_headers,
        name="Private Target Application",
    )
    api_key = issue_key(
        client,
        write_headers,
        application["id"],
        scopes=["webhooks:manage"],
    )["api_key"]

    response = client.post(
        "/api/v1/developer/webhooks",
        headers=public_headers(api_key),
        json={
            "callback_url": "http://127.0.0.1:9000/internal",
            "event_types": ["*"],
            "metadata": {},
        },
    )
    assert response.status_code == 422
    assert "private network" in response.json()["detail"]
