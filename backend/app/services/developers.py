from __future__ import annotations

from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import ipaddress
import json
import secrets
import uuid
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..hashing import canonical_json, sha256_text
from ..models import (
    ApiCredential,
    ApiPlan,
    ApiRequestLog,
    DeveloperApplication,
    WebhookDelivery,
    WebhookEvent,
    WebhookSubscription,
)
from ..schemas import (
    ApiCredentialIssue,
    ApiCredentialIssued,
    ApiCredentialRead,
    ApiUsageSummary,
    DeveloperApplicationCreate,
    DeveloperApplicationUpdate,
    WebhookDispatchResult,
    WebhookEventCreate,
    WebhookSubscriptionCreate,
    WebhookSubscriptionIssued,
    WebhookSubscriptionRead,
    WebhookSubscriptionUpdate,
)
from .ledger import append_ledger_entry


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_plan_or_404(db: Session, plan_id: str) -> ApiPlan:
    plan = db.get(ApiPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"API plan not found: {plan_id}")
    return plan


def get_application_or_404(
    db: Session,
    application_id: str,
) -> DeveloperApplication:
    application = db.get(DeveloperApplication, application_id)
    if application is None:
        raise HTTPException(
            status_code=404,
            detail=f"Developer application not found: {application_id}",
        )
    return application


def get_credential_or_404(
    db: Session,
    credential_id: str,
) -> ApiCredential:
    credential = db.get(ApiCredential, credential_id)
    if credential is None:
        raise HTTPException(
            status_code=404,
            detail=f"API credential not found: {credential_id}",
        )
    return credential


def get_subscription_or_404(
    db: Session,
    subscription_id: str,
) -> WebhookSubscription:
    subscription = db.get(WebhookSubscription, subscription_id)
    if subscription is None:
        raise HTTPException(
            status_code=404,
            detail=f"Webhook subscription not found: {subscription_id}",
        )
    return subscription


def create_application(
    db: Session,
    payload: DeveloperApplicationCreate,
) -> DeveloperApplication:
    get_plan_or_404(db, payload.plan_id)
    application = DeveloperApplication(
        id=payload.id or f"sc:developer-app:{uuid.uuid4()}",
        name=payload.name,
        owner_name=payload.owner_name,
        owner_email=payload.owner_email.strip().lower(),
        organization=payload.organization,
        website_url=str(payload.website_url) if payload.website_url else None,
        use_case=payload.use_case,
        status=payload.status,
        plan_id=payload.plan_id,
        metadata_json=payload.metadata,
    )
    db.add(application)
    db.flush()
    append_ledger_entry(
        db,
        record_type="developer_application",
        record_id=application.id,
        action="created",
        actor=payload.actor,
        payload={
            "name": application.name,
            "owner_name": application.owner_name,
            "owner_email": application.owner_email,
            "organization": application.organization,
            "website_url": application.website_url,
            "use_case": application.use_case,
            "status": application.status,
            "plan_id": application.plan_id,
            "metadata": application.metadata_json,
        },
    )
    db.commit()
    db.refresh(application)
    return application


def update_application(
    db: Session,
    application_id: str,
    payload: DeveloperApplicationUpdate,
) -> DeveloperApplication:
    application = get_application_or_404(db, application_id)
    changes = payload.model_dump(exclude={"actor"}, exclude_unset=True)
    if "plan_id" in changes:
        get_plan_or_404(db, changes["plan_id"])
    if "website_url" in changes and changes["website_url"] is not None:
        changes["website_url"] = str(changes["website_url"])
    if "owner_email" in changes and changes["owner_email"]:
        changes["owner_email"] = changes["owner_email"].strip().lower()
    if "metadata" in changes:
        changes["metadata_json"] = changes.pop("metadata")
    for key, value in changes.items():
        setattr(application, key, value)
    db.add(application)
    db.flush()
    append_ledger_entry(
        db,
        record_type="developer_application",
        record_id=application.id,
        action="updated",
        actor=payload.actor,
        payload={"changes": changes, "status": application.status},
    )
    db.commit()
    db.refresh(application)
    return application


def _generate_api_key() -> tuple[str, str, str, str]:
    prefix = secrets.token_hex(4)
    secret = secrets.token_urlsafe(32)
    api_key = f"scpk_{prefix}_{secret}"
    return api_key, prefix, api_key[-4:], sha256_text(api_key)


def issue_credential(
    db: Session,
    application_id: str,
    payload: ApiCredentialIssue,
) -> ApiCredentialIssued:
    application = get_application_or_404(db, application_id)
    if application.status != "approved":
        raise HTTPException(
            status_code=422,
            detail="Developer application must be approved before issuing a key.",
        )
    plan = get_plan_or_404(db, application.plan_id)
    if not plan.active:
        raise HTTPException(status_code=422, detail="The selected API plan is inactive.")

    if payload.expires_at:
        expires_at = payload.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= utcnow():
            raise HTTPException(
                status_code=422,
                detail="Credential expiration must be in the future.",
            )

    scopes = payload.scopes or list(plan.allowed_scopes)
    unsupported = sorted(set(scopes) - set(plan.allowed_scopes))
    if unsupported:
        raise HTTPException(
            status_code=422,
            detail={"unsupported_scopes": unsupported},
        )

    api_key, prefix, last_four, key_hash = _generate_api_key()
    credential = ApiCredential(
        application_id=application_id,
        label=payload.label,
        key_prefix=prefix,
        key_hash=key_hash,
        key_last_four=last_four,
        scopes=sorted(set(scopes)),
        status="active",
        expires_at=payload.expires_at,
        created_by=payload.created_by,
        metadata_json=payload.metadata,
    )
    db.add(credential)
    db.flush()
    append_ledger_entry(
        db,
        record_type="api_credential",
        record_id=credential.id,
        action="issued",
        actor=payload.created_by,
        payload={
            "application_id": application_id,
            "label": credential.label,
            "key_prefix": credential.key_prefix,
            "key_last_four": credential.key_last_four,
            "scopes": credential.scopes,
            "expires_at": credential.expires_at,
            "metadata": credential.metadata_json,
        },
    )
    db.commit()
    db.refresh(credential)
    return ApiCredentialIssued(
        credential=ApiCredentialRead.model_validate(credential),
        api_key=api_key,
    )


def revoke_credential(
    db: Session,
    credential_id: str,
    revoked_by: str,
) -> ApiCredential:
    credential = get_credential_or_404(db, credential_id)
    credential.status = "revoked"
    credential.revoked_at = utcnow()
    db.add(credential)
    db.flush()
    append_ledger_entry(
        db,
        record_type="api_credential",
        record_id=credential.id,
        action="revoked",
        actor=revoked_by,
        payload={
            "application_id": credential.application_id,
            "label": credential.label,
            "key_prefix": credential.key_prefix,
            "revoked_at": credential.revoked_at,
        },
    )
    db.commit()
    db.refresh(credential)
    return credential


def usage_summary(
    db: Session,
    *,
    application_id: str,
    credential_id: str | None,
    days: int,
) -> ApiUsageSummary:
    get_application_or_404(db, application_id)
    end = utcnow()
    start = end - timedelta(days=max(1, min(days, 366)))
    filters = [
        ApiRequestLog.application_id == application_id,
        ApiRequestLog.created_at >= start,
        ApiRequestLog.created_at <= end,
    ]
    if credential_id:
        credential = get_credential_or_404(db, credential_id)
        if credential.application_id != application_id:
            raise HTTPException(status_code=403, detail="Credential does not belong to the application.")
        filters.append(ApiRequestLog.credential_id == credential_id)

    total = int(
        db.scalar(
            select(func.count(ApiRequestLog.id)).where(*filters)
        ) or 0
    )
    success = int(
        db.scalar(
            select(func.count(ApiRequestLog.id)).where(
                *filters,
                ApiRequestLog.status_code >= 200,
                ApiRequestLog.status_code < 400,
            )
        ) or 0
    )
    client_errors = int(
        db.scalar(
            select(func.count(ApiRequestLog.id)).where(
                *filters,
                ApiRequestLog.status_code >= 400,
                ApiRequestLog.status_code < 500,
            )
        ) or 0
    )
    server_errors = int(
        db.scalar(
            select(func.count(ApiRequestLog.id)).where(
                *filters,
                ApiRequestLog.status_code >= 500,
            )
        ) or 0
    )
    path_rows = db.execute(
        select(ApiRequestLog.path, func.count(ApiRequestLog.id))
        .where(*filters)
        .group_by(ApiRequestLog.path)
        .order_by(func.count(ApiRequestLog.id).desc())
    ).all()
    status_rows = db.execute(
        select(ApiRequestLog.status_code, func.count(ApiRequestLog.id))
        .where(*filters)
        .group_by(ApiRequestLog.status_code)
        .order_by(ApiRequestLog.status_code)
    ).all()

    return ApiUsageSummary(
        application_id=application_id,
        credential_id=credential_id,
        window_start=start,
        window_end=end,
        requests=total,
        successful_requests=success,
        client_error_requests=client_errors,
        server_error_requests=server_errors,
        requests_by_path={key: int(value) for key, value in path_rows},
        requests_by_status={str(key): int(value) for key, value in status_rows},
    )


def _is_private_host(hostname: str) -> bool:
    normalized = hostname.strip().lower().rstrip(".")
    if normalized in {"localhost", "localhost.localdomain"}:
        return True
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        return False
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def validate_webhook_url(url: str, *, production: bool) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"}:
        raise HTTPException(status_code=422, detail="Webhook URL must use HTTP or HTTPS.")
    if production and parsed.scheme != "https":
        raise HTTPException(status_code=422, detail="Production webhook URLs must use HTTPS.")
    if not parsed.hostname or _is_private_host(parsed.hostname):
        raise HTTPException(
            status_code=422,
            detail="Webhook URLs cannot target localhost or private network addresses.",
        )
    if parsed.username or parsed.password:
        raise HTTPException(
            status_code=422,
            detail="Webhook URLs cannot contain embedded credentials.",
        )


def derive_webhook_secret(master_secret: str, subscription_id: str) -> str:
    if not master_secret:
        raise HTTPException(
            status_code=503,
            detail="Webhook signing is disabled because no master secret is configured.",
        )
    digest = hmac.new(
        master_secret.encode("utf-8"),
        subscription_id.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return "scwhsec_" + base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def create_webhook_subscription(
    db: Session,
    *,
    application_id: str,
    credential_id: str,
    payload: WebhookSubscriptionCreate,
    master_secret: str,
    production: bool,
) -> WebhookSubscriptionIssued:
    application = get_application_or_404(db, application_id)
    if application.status != "approved":
        raise HTTPException(status_code=403, detail="Developer application is not approved.")
    validate_webhook_url(str(payload.callback_url), production=production)
    subscription = WebhookSubscription(
        application_id=application_id,
        callback_url=str(payload.callback_url),
        event_types=payload.event_types,
        status="active",
        description=payload.description,
        created_by_credential_id=credential_id,
        metadata_json=payload.metadata,
    )
    db.add(subscription)
    db.flush()
    secret = derive_webhook_secret(master_secret, subscription.id)
    db.commit()
    db.refresh(subscription)
    return WebhookSubscriptionIssued(
        subscription=WebhookSubscriptionRead.model_validate(subscription),
        signing_secret=secret,
    )


def update_webhook_subscription(
    db: Session,
    subscription_id: str,
    application_id: str,
    payload: WebhookSubscriptionUpdate,
    *,
    production: bool,
) -> WebhookSubscription:
    subscription = get_subscription_or_404(db, subscription_id)
    if subscription.application_id != application_id:
        raise HTTPException(status_code=403, detail="Webhook subscription does not belong to this application.")
    changes = payload.model_dump(exclude_unset=True)
    if "metadata" in changes:
        changes["metadata_json"] = changes.pop("metadata")
    for key, value in changes.items():
        setattr(subscription, key, value)
    db.commit()
    db.refresh(subscription)
    return subscription


def emit_webhook_event(
    db: Session,
    *,
    event_type: str,
    resource_type: str,
    resource_id: str,
    payload: dict,
) -> WebhookEvent:
    event = WebhookEvent(
        event_type=event_type.strip().lower(),
        resource_type=resource_type,
        resource_id=resource_id,
        payload_json=payload,
        status="pending",
    )
    db.add(event)
    db.flush()
    return event


def publish_webhook_event(
    db: Session,
    payload: WebhookEventCreate,
) -> WebhookEvent:
    event = emit_webhook_event(
        db,
        event_type=payload.event_type,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        payload=payload.payload,
    )
    append_ledger_entry(
        db,
        record_type="webhook_event",
        record_id=event.id,
        action="published",
        actor=payload.actor,
        payload={
            "event_type": event.event_type,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "payload": event.payload_json,
        },
    )
    db.commit()
    db.refresh(event)
    return event


def event_type_matches(patterns: list[str], event_type: str) -> bool:
    for pattern in patterns:
        if pattern == "*":
            return True
        if pattern.endswith(".*") and event_type.startswith(pattern[:-1]):
            return True
        if pattern == event_type:
            return True
    return False


def build_webhook_signature(
    secret: str,
    timestamp: str,
    body: str,
) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        f"{timestamp}.{body}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"v1={digest}"


def _default_sender(
    *,
    url: str,
    content: str,
    headers: dict[str, str],
    timeout: int,
):
    return httpx.post(
        url,
        content=content,
        headers=headers,
        timeout=timeout,
        follow_redirects=False,
    )


def dispatch_pending_webhooks(
    db: Session,
    *,
    master_secret: str,
    timeout: int,
    limit: int = 100,
    sender=None,
) -> WebhookDispatchResult:
    sender = sender or _default_sender
    events = list(
        db.scalars(
            select(WebhookEvent)
            .where(WebhookEvent.status == "pending")
            .order_by(WebhookEvent.created_at)
            .limit(limit)
        ).all()
    )
    subscriptions = list(
        db.scalars(
            select(WebhookSubscription)
            .where(WebhookSubscription.status == "active")
            .order_by(WebhookSubscription.created_at)
        ).all()
    )

    attempted = succeeded = failed = 0
    for event in events:
        matched = [
            subscription
            for subscription in subscriptions
            if event_type_matches(subscription.event_types, event.event_type)
        ]
        for subscription in matched:
            delivery = db.scalar(
                select(WebhookDelivery).where(
                    WebhookDelivery.subscription_id == subscription.id,
                    WebhookDelivery.event_id == event.id,
                )
            )
            if delivery and delivery.status == "delivered":
                continue
            if delivery is None:
                delivery = WebhookDelivery(
                    subscription_id=subscription.id,
                    event_id=event.id,
                    status="pending",
                )
                db.add(delivery)
                db.flush()

            body = canonical_json(
                {
                    "id": event.id,
                    "type": event.event_type,
                    "created_at": event.created_at,
                    "resource": {
                        "type": event.resource_type,
                        "id": event.resource_id,
                    },
                    "data": event.payload_json,
                }
            )
            timestamp = str(int(utcnow().timestamp()))
            secret = derive_webhook_secret(master_secret, subscription.id)
            signature = build_webhook_signature(secret, timestamp, body)
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Sustainable-Catalyst-Platform-Core/2.4.0",
                "X-SC-Webhook-ID": event.id,
                "X-SC-Webhook-Timestamp": timestamp,
                "X-SC-Webhook-Signature": signature,
            }
            attempted += 1
            delivery.attempts += 1
            delivery.attempted_at = utcnow()
            delivery.signature = signature

            try:
                response = sender(
                    url=subscription.callback_url,
                    content=body,
                    headers=headers,
                    timeout=timeout,
                )
                delivery.http_status = int(response.status_code)
                response_text = getattr(response, "text", "") or ""
                delivery.response_excerpt = response_text[:1000]
                if 200 <= response.status_code < 300:
                    delivery.status = "delivered"
                    delivery.delivered_at = utcnow()
                    delivery.error_message = None
                    succeeded += 1
                else:
                    delivery.status = "failed"
                    delivery.error_message = f"Webhook returned HTTP {response.status_code}."
                    failed += 1
            except Exception as exc:
                delivery.status = "failed"
                delivery.error_message = str(exc)[:2000]
                failed += 1
            db.add(delivery)

        event_failed = any(
            delivery.status == "failed"
            for delivery in db.scalars(
                select(WebhookDelivery).where(
                    WebhookDelivery.event_id == event.id
                )
            ).all()
        )
        event.status = "pending" if event_failed else "processed"
        event.processed_at = None if event_failed else utcnow()
        db.add(event)
        db.commit()

    return WebhookDispatchResult(
        events_processed=len(events),
        deliveries_attempted=attempted,
        deliveries_succeeded=succeeded,
        deliveries_failed=failed,
    )
