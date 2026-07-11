from __future__ import annotations

import logging
import re
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

LOGGER = logging.getLogger("sustainable_catalyst.gateway")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")


def _request_id_from_header(value: str) -> str | None:
    candidate = value.strip()[:64]
    return candidate if REQUEST_ID_PATTERN.fullmatch(candidate) else None


class RequestTraceMiddleware(BaseHTTPMiddleware):
    """Attach one correlation ID to Core and all downstream service calls."""

    async def dispatch(self, request: Request, call_next):
        request_id = (
            getattr(request.state, "request_id", None)
            or _request_id_from_header(request.headers.get("X-Request-ID", ""))
            or uuid.uuid4().hex
        )
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        final_request_id = getattr(request.state, "request_id", request_id)
        response.headers["X-Request-ID"] = final_request_id
        response.headers["X-SC-Core-Version"] = request.app.state.settings.version
        response.headers["Server-Timing"] = f"core;dur={elapsed_ms}"
        LOGGER.info(
            "core_request request_id=%s method=%s path=%s status=%s duration_ms=%s",
            final_request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
