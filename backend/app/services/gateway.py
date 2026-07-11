from __future__ import annotations

from dataclasses import dataclass
import asyncio
import json
import time
from typing import Any
from urllib.parse import quote

import httpx

from ..service_registry import GatewaySettings, ServiceDefinition, ServiceRegistry


class GatewayError(RuntimeError):
    def __init__(self, message: str, *, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class CircuitState:
    consecutive_failures: int = 0
    opened_at: float | None = None


@dataclass
class GatewayResult:
    service_id: str
    status_code: int
    latency_ms: float
    content_type: str
    content: bytes
    json_data: Any | None
    headers: dict[str, str]


class GatewayRuntime:
    HOP_BY_HOP = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }
    FORWARDED_REQUEST_HEADERS = {
        "accept",
        "accept-language",
        "content-type",
        "if-match",
        "if-none-match",
        "if-modified-since",
        "range",
        "user-agent",
    }
    FORWARDED_RESPONSE_HEADERS = {
        "cache-control",
        "content-disposition",
        "content-language",
        "content-length",
        "content-type",
        "etag",
        "last-modified",
        "location",
        "retry-after",
    }

    def __init__(
        self,
        registry: ServiceRegistry,
        settings: GatewaySettings,
        *,
        core_version: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.registry = registry
        self.settings = settings
        self.core_version = core_version
        self.transport = transport
        self._circuits: dict[str, CircuitState] = {}
        self._circuit_lock = asyncio.Lock()

    def _service_or_error(self, service_id: str) -> ServiceDefinition:
        if not self.settings.enabled:
            raise GatewayError("The service gateway is disabled.", status_code=503)
        service = self.registry.get(service_id)
        if service is None:
            raise GatewayError("Unknown gateway service.", status_code=404)
        if not service.enabled or not service.configured:
            raise GatewayError(
                f"Gateway service '{service_id}' is not configured.",
                status_code=503,
            )
        return service

    async def _circuit_is_open(self, service_id: str) -> bool:
        async with self._circuit_lock:
            state = self._circuits.setdefault(service_id, CircuitState())
            if state.opened_at is None:
                return False
            if (
                time.monotonic() - state.opened_at
                >= self.settings.circuit_cooldown_seconds
            ):
                state.opened_at = None
                state.consecutive_failures = 0
                return False
            return True

    async def _record_success(self, service_id: str) -> None:
        async with self._circuit_lock:
            self._circuits[service_id] = CircuitState()

    async def _record_failure(self, service_id: str) -> None:
        async with self._circuit_lock:
            state = self._circuits.setdefault(service_id, CircuitState())
            state.consecutive_failures += 1
            if (
                state.consecutive_failures
                >= self.settings.circuit_failure_threshold
                and state.opened_at is None
            ):
                state.opened_at = time.monotonic()

    @staticmethod
    def _safe_path(path: str) -> str:
        clean = path.strip().lstrip("/")
        segments = [segment for segment in clean.split("/") if segment]
        if any(segment in {".", ".."} for segment in segments):
            raise GatewayError("Unsafe gateway path.", status_code=400)
        return "/".join(quote(segment, safe="-._~:@") for segment in segments)

    def _request_headers(
        self,
        incoming: dict[str, str],
        service: ServiceDefinition,
        request_id: str,
    ) -> dict[str, str]:
        headers = {
            key: value
            for key, value in incoming.items()
            if key.lower() in self.FORWARDED_REQUEST_HEADERS
            and key.lower() not in self.HOP_BY_HOP
        }
        headers["X-Request-ID"] = request_id
        headers["X-SC-Gateway-Service"] = service.service_id
        headers["X-SC-Core-Version"] = self.core_version
        if service.service_token:
            headers["X-SC-Service-Token"] = service.service_token
        return headers

    async def proxy(
        self,
        service_id: str,
        *,
        method: str,
        path: str,
        query: list[tuple[str, str]],
        incoming_headers: dict[str, str],
        body: bytes,
        request_id: str,
    ) -> GatewayResult:
        service = self._service_or_error(service_id)
        method = method.upper()
        if method not in service.allowed_methods:
            raise GatewayError(
                f"Method {method} is not enabled for {service_id}.",
                status_code=405,
            )
        if len(body) > self.settings.max_request_bytes:
            raise GatewayError("Gateway request body is too large.", status_code=413)
        if await self._circuit_is_open(service_id):
            raise GatewayError(
                f"Gateway circuit for '{service_id}' is temporarily open.",
                status_code=503,
            )

        safe_path = self._safe_path(path)
        url = service.base_url.rstrip("/")
        if safe_path:
            url = f"{url}/{safe_path}"
        headers = self._request_headers(incoming_headers, service, request_id)
        started = time.perf_counter()
        timeout = httpx.Timeout(self.settings.request_timeout_seconds)

        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                async with client.stream(
                    method,
                    url,
                    params=query,
                    headers=headers,
                    content=body or None,
                ) as response:
                    declared_length = response.headers.get("content-length", "")
                    if (
                        declared_length.isdigit()
                        and int(declared_length) > self.settings.max_response_bytes
                    ):
                        await self._record_failure(service_id)
                        raise GatewayError(
                            "Gateway response is too large.", status_code=502
                        )
                    chunks: list[bytes] = []
                    response_size = 0
                    async for chunk in response.aiter_bytes():
                        response_size += len(chunk)
                        if response_size > self.settings.max_response_bytes:
                            await self._record_failure(service_id)
                            raise GatewayError(
                                "Gateway response is too large.", status_code=502
                            )
                        chunks.append(chunk)
                    content = b"".join(chunks)
                    status_code = response.status_code
                    response_encoding = response.encoding or "utf-8"
                    raw_headers = dict(response.headers)
        except httpx.TimeoutException as exc:
            await self._record_failure(service_id)
            raise GatewayError(
                f"Gateway service '{service_id}' timed out.",
                status_code=504,
            ) from exc
        except httpx.HTTPError as exc:
            await self._record_failure(service_id)
            raise GatewayError(
                f"Gateway service '{service_id}' is unavailable.",
                status_code=502,
            ) from exc

        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        if status_code >= 500:
            await self._record_failure(service_id)
        else:
            await self._record_success(service_id)

        content_type = raw_headers.get("content-type", "application/octet-stream")
        json_data: Any | None = None
        if "json" in content_type.lower() and content:
            try:
                json_data = json.loads(content.decode(response_encoding))
            except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
                json_data = None

        response_headers = {
            key: value
            for key, value in raw_headers.items()
            if key.lower() in self.FORWARDED_RESPONSE_HEADERS
            and key.lower() not in self.HOP_BY_HOP
        }
        response_headers["X-Request-ID"] = request_id
        response_headers["X-SC-Gateway-Service"] = service_id
        response_headers["X-SC-Upstream-Latency-Ms"] = str(latency_ms)
        return GatewayResult(
            service_id=service_id,
            status_code=status_code,
            latency_ms=latency_ms,
            content_type=content_type,
            content=content,
            json_data=json_data,
            headers=response_headers,
        )

    async def check_health(self, service: ServiceDefinition) -> dict:
        base = service.public_dict()
        if not service.enabled or not service.configured:
            return {**base, "status": "disabled", "latency_ms": None}
        if await self._circuit_is_open(service.service_id):
            return {**base, "status": "circuit_open", "latency_ms": None}

        path = service.health_path.strip() or "/health"
        url = f"{service.base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = self._request_headers({}, service, "gateway-health-check")
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.settings.health_timeout_seconds),
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                response = await client.get(url, headers=headers)
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            status = "operational" if response.status_code < 400 else "degraded"
            if response.status_code >= 500:
                await self._record_failure(service.service_id)
            else:
                await self._record_success(service.service_id)
            return {
                **base,
                "status": status,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
            }
        except (httpx.TimeoutException, httpx.HTTPError):
            await self._record_failure(service.service_id)
            return {**base, "status": "unavailable", "latency_ms": None}

    async def health_snapshot(self) -> dict:
        services = self.registry.list()
        if not self.settings.enabled:
            return {
                "gateway": "disabled",
                "overall_status": "disabled",
                "service_count": len(services),
                "active_service_count": 0,
                "services": [
                    {**service.public_dict(), "status": "gateway_disabled", "latency_ms": None}
                    for service in services
                ],
            }
        results = await asyncio.gather(*(self.check_health(item) for item in services))
        active = [item for item in results if item["status"] != "disabled"]
        statuses = {item["status"] for item in active}
        if not active:
            overall = "unconfigured"
        elif statuses <= {"operational"}:
            overall = "operational"
        elif "operational" in statuses:
            overall = "degraded"
        else:
            overall = "unavailable"
        return {
            "gateway": "operational" if self.settings.enabled else "disabled",
            "overall_status": overall,
            "service_count": len(results),
            "active_service_count": len(active),
            "services": results,
        }
