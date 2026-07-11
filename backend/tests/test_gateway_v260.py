from __future__ import annotations

import asyncio

import httpx
import pytest

from app.request_tracing import _request_id_from_header
from app.service_registry import GatewaySettings, ServiceDefinition, ServiceRegistry
from app.services.gateway import GatewayError, GatewayRuntime


def registry() -> ServiceRegistry:
    return ServiceRegistry(
        [
            ServiceDefinition(
                service_id="workbench",
                name="Workbench",
                route_prefix="workbench",
                base_url="https://workbench.internal",
                enabled=True,
                allowed_methods=("GET", "POST"),
                capabilities=("calculations",),
            )
        ]
    )


def test_gateway_proxies_json_and_preserves_request_id():
    async def scenario():
        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["X-Request-ID"] == "req-123"
            assert request.url.path == "/health/detail"
            return httpx.Response(200, json={"ok": True, "version": "1.0.0"})

        runtime = GatewayRuntime(
            registry(),
            GatewaySettings(),
            core_version="2.6.0",
            transport=httpx.MockTransport(handler),
        )
        result = await runtime.proxy(
            "workbench",
            method="GET",
            path="health/detail",
            query=[],
            incoming_headers={"Accept": "application/json"},
            body=b"",
            request_id="req-123",
        )
        assert result.status_code == 200
        assert result.json_data == {"ok": True, "version": "1.0.0"}
        assert result.headers["X-Request-ID"] == "req-123"

    asyncio.run(scenario())


def test_gateway_rejects_unsafe_path():
    async def scenario():
        runtime = GatewayRuntime(registry(), GatewaySettings(), core_version="2.6.0")
        with pytest.raises(GatewayError) as exc:
            await runtime.proxy(
                "workbench",
                method="GET",
                path="../secrets",
                query=[],
                incoming_headers={},
                body=b"",
                request_id="req-unsafe",
            )
        assert exc.value.status_code == 400

    asyncio.run(scenario())


def test_gateway_circuit_opens_after_failures():
    async def scenario():
        async def handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("offline")

        runtime = GatewayRuntime(
            registry(),
            GatewaySettings(circuit_failure_threshold=2, circuit_cooldown_seconds=60),
            core_version="2.6.0",
            transport=httpx.MockTransport(handler),
        )
        for _ in range(2):
            with pytest.raises(GatewayError):
                await runtime.proxy(
                    "workbench",
                    method="GET",
                    path="health",
                    query=[],
                    incoming_headers={},
                    body=b"",
                    request_id="req-fail",
                )
        with pytest.raises(GatewayError) as exc:
            await runtime.proxy(
                "workbench",
                method="GET",
                path="health",
                query=[],
                incoming_headers={},
                body=b"",
                request_id="req-open",
            )
        assert exc.value.status_code == 503
        assert "circuit" in str(exc.value).lower()

    asyncio.run(scenario())


def test_aggregated_health_reports_operational_service():
    async def scenario():
        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/health"
            return httpx.Response(200, json={"ok": True})

        runtime = GatewayRuntime(
            registry(),
            GatewaySettings(),
            core_version="2.6.0",
            transport=httpx.MockTransport(handler),
        )
        snapshot = await runtime.health_snapshot()
        assert snapshot["overall_status"] == "operational"
        assert snapshot["services"][0]["status"] == "operational"

    asyncio.run(scenario())


def test_public_catalog_hides_internal_url_and_service_token():
    service = ServiceDefinition(
        service_id="finance",
        name="Catalyst Finance",
        route_prefix="finance",
        base_url="https://finance.internal",
        enabled=True,
        service_token="do-not-expose",
    )
    payload = ServiceRegistry([service]).public_catalog()[0]
    assert "base_url" not in payload
    assert "service_token" not in payload
    assert payload["configured"] is True


def test_disabled_gateway_health_does_not_call_downstream():
    async def scenario():
        runtime = GatewayRuntime(
            registry(),
            GatewaySettings(enabled=False),
            core_version="2.6.0",
        )
        snapshot = await runtime.health_snapshot()
        assert snapshot["gateway"] == "disabled"
        assert snapshot["overall_status"] == "disabled"
        assert snapshot["services"][0]["status"] == "gateway_disabled"

    asyncio.run(scenario())


def test_gateway_rejects_disallowed_method_before_network_call():
    async def scenario():
        runtime = GatewayRuntime(registry(), GatewaySettings(), core_version="2.6.0")
        with pytest.raises(GatewayError) as exc:
            await runtime.proxy(
                "workbench",
                method="DELETE",
                path="records/1",
                query=[],
                incoming_headers={},
                body=b"",
                request_id="req-method",
            )
        assert exc.value.status_code == 405

    asyncio.run(scenario())


def test_gateway_stops_oversized_upstream_response():
    async def scenario():
        async def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=b"12345")

        runtime = GatewayRuntime(
            registry(),
            GatewaySettings(max_response_bytes=4),
            core_version="2.6.0",
            transport=httpx.MockTransport(handler),
        )
        with pytest.raises(GatewayError) as exc:
            await runtime.proxy(
                "workbench",
                method="GET",
                path="large",
                query=[],
                incoming_headers={},
                body=b"",
                request_id="req-large",
            )
        assert exc.value.status_code == 502
        assert "too large" in str(exc.value).lower()

    asyncio.run(scenario())


def test_request_id_header_is_strictly_sanitized():
    assert _request_id_from_header("trace-123:edge") == "trace-123:edge"
    assert _request_id_from_header("bad\nheader") is None
    assert _request_id_from_header("x" * 65) == "x" * 64


def test_registry_rejects_non_http_service_url():
    service = ServiceDefinition(
        service_id="unsafe",
        name="Unsafe",
        route_prefix="unsafe",
        base_url="file:///etc/passwd",
        enabled=True,
    )
    assert service.configured is False
    runtime = GatewayRuntime(
        ServiceRegistry([service]), GatewaySettings(), core_version="2.6.0"
    )

    async def scenario():
        with pytest.raises(GatewayError) as exc:
            await runtime.proxy(
                "unsafe",
                method="GET",
                path="",
                query=[],
                incoming_headers={},
                body=b"",
                request_id="req-url",
            )
        assert exc.value.status_code == 503

    asyncio.run(scenario())
