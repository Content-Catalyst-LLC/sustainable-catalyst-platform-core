from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import time
import uuid

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from starlette.middleware.base import BaseHTTPMiddleware

from .hashing import sha256_text
from .models import (
    ApiCredential,
    ApiPlan,
    ApiRequestLog,
    DeveloperApplication,
)


@dataclass
class PublicApiContext:
    credential: ApiCredential
    application: DeveloperApplication
    plan: ApiPlan
    request_id: str
    minute_count: int
    day_count: int


def _extract_api_key(request: Request) -> str | None:
    direct = request.headers.get("X-SC-Public-Key")
    if direct:
        return direct.strip()
    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hash_client_value(value: str | None, salt: str) -> str | None:
    if not value:
        return None
    return sha256_text(f"{salt}:{value}")


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else None


def require_public_scope(scope: str):
    def dependency(request: Request):
        context: PublicApiContext | None = getattr(
            request.state,
            "public_api_context",
            None,
        )
        request.state.required_scope = scope
        if context is None:
            raise HTTPException(status_code=401, detail="A public API key is required.")
        if scope not in context.credential.scopes:
            raise HTTPException(
                status_code=403,
                detail=f"API credential does not include required scope: {scope}",
            )
        return context
    return dependency


class PublicApiMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/v1"):
            return await call_next(request)

        settings = request.app.state.settings
        request_id = (
            request.headers.get("X-Request-ID", "").strip()[:64]
            or uuid.uuid4().hex
        )
        request.state.request_id = request_id
        request.state.required_scope = None
        started = time.perf_counter()
        context: PublicApiContext | None = None
        response = None

        if not settings.public_api_enabled:
            return JSONResponse(
                status_code=404,
                content={"detail": "The unified public API is disabled."},
                headers={"X-Request-ID": request_id},
            )

        if settings.environment == "production" and not settings.api_log_salt:
            return JSONResponse(
                status_code=503,
                content={
                    "detail": (
                        "The public API is unavailable because the production "
                        "request-log salt is not configured."
                    )
                },
                headers={"X-Request-ID": request_id},
            )

        key = _extract_api_key(request)
        if not key:
            response = JSONResponse(
                status_code=401,
                content={
                    "detail": (
                        "A public API key is required. Use X-SC-Public-Key "
                        "or Authorization: Bearer."
                    )
                },
            )
        else:
            key_hash = sha256_text(key)
            with request.app.state.database.session_factory() as db:
                credential = db.scalar(
                    select(ApiCredential).where(
                        ApiCredential.key_hash == key_hash
                    )
                )
                if credential is None or credential.status != "active":
                    response = JSONResponse(
                        status_code=401,
                        content={"detail": "The public API key is invalid or inactive."},
                    )
                else:
                    application = db.get(
                        DeveloperApplication,
                        credential.application_id,
                    )
                    plan = (
                        db.get(ApiPlan, application.plan_id)
                        if application
                        else None
                    )
                    now = _utcnow()
                    expires_at = credential.expires_at
                    if expires_at and expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)

                    if (
                        application is None
                        or application.status != "approved"
                        or plan is None
                        or not plan.active
                        or (expires_at and expires_at <= now)
                    ):
                        response = JSONResponse(
                            status_code=403,
                            content={
                                "detail": (
                                    "The developer application, API plan, "
                                    "or credential is not active."
                                )
                            },
                        )
                    else:
                        minute_start = now - timedelta(minutes=1)
                        day_start = now.replace(
                            hour=0,
                            minute=0,
                            second=0,
                            microsecond=0,
                        )
                        minute_count = int(
                            db.scalar(
                                select(func.count(ApiRequestLog.id)).where(
                                    ApiRequestLog.credential_id == credential.id,
                                    ApiRequestLog.created_at >= minute_start,
                                )
                            )
                            or 0
                        )
                        day_count = int(
                            db.scalar(
                                select(func.count(ApiRequestLog.id)).where(
                                    ApiRequestLog.credential_id == credential.id,
                                    ApiRequestLog.created_at >= day_start,
                                )
                            )
                            or 0
                        )
                        if (
                            plan.requests_per_minute > 0
                            and minute_count >= plan.requests_per_minute
                        ):
                            response = JSONResponse(
                                status_code=429,
                                content={
                                    "detail": "Per-minute API rate limit exceeded."
                                },
                                headers={"Retry-After": "60"},
                            )
                        elif (
                            plan.requests_per_day > 0
                            and day_count >= plan.requests_per_day
                        ):
                            seconds_to_reset = int(
                                (
                                    day_start
                                    + timedelta(days=1)
                                    - now
                                ).total_seconds()
                            )
                            response = JSONResponse(
                                status_code=429,
                                content={"detail": "Daily API quota exceeded."},
                                headers={
                                    "Retry-After": str(max(seconds_to_reset, 1))
                                },
                            )
                        else:
                            context = PublicApiContext(
                                credential=credential,
                                application=application,
                                plan=plan,
                                request_id=request_id,
                                minute_count=minute_count,
                                day_count=day_count,
                            )
                            request.state.public_api_context = context

        if response is None:
            response = await call_next(request)

        duration_ms = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-SC-API-Version"] = "1"

        if context:
            minute_limit = context.plan.requests_per_minute
            day_limit = context.plan.requests_per_day
            response.headers["X-RateLimit-Limit-Minute"] = str(minute_limit)
            response.headers["X-RateLimit-Remaining-Minute"] = str(
                max(minute_limit - context.minute_count - 1, 0)
                if minute_limit > 0
                else -1
            )
            response.headers["X-RateLimit-Limit-Day"] = str(day_limit)
            response.headers["X-RateLimit-Remaining-Day"] = str(
                max(day_limit - context.day_count - 1, 0)
                if day_limit > 0
                else -1
            )

        with request.app.state.database.session_factory() as db:
            if context:
                credential = db.get(ApiCredential, context.credential.id)
                if credential:
                    credential.last_used_at = _utcnow()
                    db.add(credential)
            log = ApiRequestLog(
                request_id=request_id,
                credential_id=context.credential.id if context else None,
                application_id=context.application.id if context else None,
                method=request.method,
                path=request.url.path,
                query_string=request.url.query or None,
                status_code=response.status_code,
                required_scope=getattr(request.state, "required_scope", None),
                ip_hash=_hash_client_value(
                    _client_ip(request),
                    settings.api_log_salt,
                ),
                user_agent_hash=_hash_client_value(
                    request.headers.get("User-Agent"),
                    settings.api_log_salt,
                ),
                duration_ms=round(duration_ms, 3),
                response_bytes=(
                    int(response.headers["content-length"])
                    if response.headers.get("content-length", "").isdigit()
                    else None
                ),
            )
            db.add(log)
            db.commit()

        return response
