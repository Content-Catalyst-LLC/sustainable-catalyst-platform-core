from __future__ import annotations

import asyncio

import httpx
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.service_registry import GatewaySettings, ServiceDefinition, ServiceRegistry
from app.services.gateway import GatewayRuntime


def _service(**overrides) -> ServiceDefinition:
    values = dict(
        service_id="site-intelligence",
        name="Site Intelligence",
        route_prefix="site-intelligence",
        base_url="https://site-intelligence.internal",
        enabled=True,
        required=True,
        capabilities=("country-intelligence",),
    )
    values.update(overrides)
    return ServiceDefinition(**values)


def test_required_unconfigured_service_blocks_release_readiness():
    async def scenario():
        runtime = GatewayRuntime(
            ServiceRegistry([_service(base_url="")]),
            GatewaySettings(),
            core_version="2.8.1",
        )
        snapshot = await runtime.health_snapshot()
        assert snapshot["release_ready"] is False
        assert snapshot["required_blockers"] == ["site-intelligence"]
        assert snapshot["services"][0]["status"] == "unconfigured"
        assert snapshot["services"][0]["readiness"] == "blocked"

    asyncio.run(scenario())


def test_optional_unconfigured_service_does_not_block_core():
    async def scenario():
        runtime = GatewayRuntime(
            ServiceRegistry([_service(base_url="", required=False)]),
            GatewaySettings(),
            core_version="2.8.1",
        )
        snapshot = await runtime.health_snapshot()
        assert snapshot["release_ready"] is True
        assert snapshot["required_blockers"] == []
        assert snapshot["overall_status"] == "unconfigured"

    asyncio.run(scenario())


def test_required_operational_service_is_ready_and_reports_version():
    async def scenario():
        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["X-SC-Core-Version"] == "2.8.1"
            return httpx.Response(200, json={"ok": True, "version": "4.35.25"})

        runtime = GatewayRuntime(
            ServiceRegistry([_service(expected_version_prefix="4.")]),
            GatewaySettings(),
            core_version="2.8.1",
            transport=httpx.MockTransport(handler),
        )
        snapshot = await runtime.health_snapshot()
        assert snapshot["release_ready"] is True
        item = snapshot["services"][0]
        assert item["status"] == "operational"
        assert item["readiness"] == "ready"
        assert item["upstream_version"] == "4.35.25"

    asyncio.run(scenario())


def test_required_version_mismatch_blocks_release_readiness():
    async def scenario():
        async def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"version": "3.99.0"})

        runtime = GatewayRuntime(
            ServiceRegistry([_service(expected_version_prefix="4.")]),
            GatewaySettings(),
            core_version="2.8.1",
            transport=httpx.MockTransport(handler),
        )
        snapshot = await runtime.health_snapshot()
        assert snapshot["release_ready"] is False
        assert snapshot["services"][0]["status"] == "version_mismatch"
        assert snapshot["required_blockers"] == ["site-intelligence"]

    asyncio.run(scenario())


def test_required_disabled_service_is_distinct_from_unconfigured():
    async def scenario():
        runtime = GatewayRuntime(
            ServiceRegistry([_service(enabled=False)]),
            GatewaySettings(),
            core_version="2.8.1",
        )
        snapshot = await runtime.health_snapshot()
        assert snapshot["services"][0]["status"] == "disabled"
        assert snapshot["release_ready"] is False

    asyncio.run(scenario())


def test_registry_reads_required_and_expected_version_from_env(monkeypatch):
    monkeypatch.setenv("SC_CORE_SITE_INTELLIGENCE_URL", "https://si.example")
    monkeypatch.setenv("SC_CORE_SITE_INTELLIGENCE_ENABLED", "true")
    monkeypatch.setenv("SC_CORE_SITE_INTELLIGENCE_REQUIRED", "true")
    monkeypatch.setenv("SC_CORE_SITE_INTELLIGENCE_EXPECTED_VERSION_PREFIX", "4.")
    registry = ServiceRegistry.from_env()
    service = registry.get("site-intelligence")
    assert service is not None
    assert service.configured is True
    assert service.required is True
    assert service.expected_version_prefix == "4."


def test_ready_endpoint_exposes_unconfigured_required_service_without_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("SC_CORE_SITE_INTELLIGENCE_URL", "")
    monkeypatch.setenv("SC_CORE_SITE_INTELLIGENCE_ENABLED", "true")
    monkeypatch.setenv("SC_CORE_SITE_INTELLIGENCE_REQUIRED", "true")
    monkeypatch.setenv("SC_CORE_SITE_INTELLIGENCE_SERVICE_TOKEN", "secret-token")
    settings = Settings(
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'v281.db'}",
        write_api_key="test",
        cors_origins=("http://testserver",),
    )
    app = create_app(settings)
    with TestClient(app) as client:
        body = client.get("/ready").json()
        assert body["ok"] is False
        assert body["unified_service_gateway"] == "blocked"
        assert body["required_blockers"] == ["site-intelligence"]
        raw = str(body)
        assert "secret-token" not in raw


def test_public_integration_readiness_is_safe_and_distinguishes_states(tmp_path, monkeypatch):
    monkeypatch.setenv("SC_CORE_SITE_INTELLIGENCE_URL", "")
    monkeypatch.setenv("SC_CORE_SITE_INTELLIGENCE_ENABLED", "true")
    monkeypatch.setenv("SC_CORE_SITE_INTELLIGENCE_REQUIRED", "true")
    settings = Settings(
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'v281-public.db'}",
        write_api_key="test",
        cors_origins=("http://testserver",),
    )
    app = create_app(settings)
    with TestClient(app) as client:
        response = client.get("/integration/readiness")
        assert response.status_code == 200
        body = response.json()
        assert body["core_version"] == "2.20.0"
        service = next(x for x in body["services"] if x["service_id"] == "site-intelligence")
        assert service["status"] == "unconfigured"
        assert "base_url" not in service
        assert "service_token" not in service


def test_health_remains_liveness_even_when_required_integration_is_unconfigured(tmp_path, monkeypatch):
    monkeypatch.setenv("SC_CORE_SITE_INTELLIGENCE_URL", "")
    monkeypatch.setenv("SC_CORE_SITE_INTELLIGENCE_ENABLED", "true")
    monkeypatch.setenv("SC_CORE_SITE_INTELLIGENCE_REQUIRED", "true")
    settings = Settings(
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'v281-health.db'}",
        write_api_key="test",
        cors_origins=("http://testserver",),
    )
    app = create_app(settings)
    with TestClient(app) as client:
        health = client.get("/health")
        ready = client.get("/ready")
        assert health.status_code == 200
        assert health.json()["ok"] is True
        assert ready.status_code == 200
        assert ready.json()["ok"] is False


def test_public_catalog_never_exposes_service_url_or_token_with_readiness_metadata():
    service = _service(service_token="hidden")
    payload = ServiceRegistry([service]).public_catalog()[0]
    assert payload["required"] is True
    assert payload["configured"] is True
    assert "base_url" not in payload
    assert "service_token" not in payload


def test_token_required_without_token_is_configuration_error():
    async def scenario():
        runtime = GatewayRuntime(
            ServiceRegistry([_service(token_required=True, service_token="")]),
            GatewaySettings(),
            core_version="2.8.1",
        )
        snapshot = await runtime.health_snapshot()
        item = snapshot["services"][0]
        assert item["status"] == "configuration_error"
        assert item["configuration_issue"] == "service_token_required"
        assert snapshot["release_ready"] is False

    asyncio.run(scenario())


def test_required_public_base_url_blocks_ready_when_missing(tmp_path):
    settings = Settings(
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'v281-base-url.db'}",
        write_api_key="test",
        cors_origins=("https://sustainablecatalyst.com",),
        public_base_url="",
        public_base_url_required=True,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        body = client.get("/ready").json()
        assert body["ok"] is False
        assert "public_base_url" in body["configuration_blockers"]


def test_required_cors_origin_is_verified(tmp_path):
    settings = Settings(
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'v281-cors.db'}",
        write_api_key="test",
        cors_origins=("http://testserver",),
        required_cors_origin="https://sustainablecatalyst.com",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        body = client.get("/integration/readiness").json()
        assert body["ok"] is False
        assert "required_cors_origin" in body["configuration_blockers"]


def test_required_service_with_expected_version_must_report_version():
    async def scenario():
        async def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"ok": True})

        runtime = GatewayRuntime(
            ServiceRegistry([_service(expected_version_prefix="4.")]),
            GatewaySettings(),
            core_version="2.8.1",
            transport=httpx.MockTransport(handler),
        )
        snapshot = await runtime.health_snapshot()
        assert snapshot["services"][0]["status"] == "version_unreported"
        assert snapshot["release_ready"] is False

    asyncio.run(scenario())


def test_ready_reports_gateway_disabled_without_calling_it_ready(tmp_path, monkeypatch):
    monkeypatch.setenv("SC_CORE_GATEWAY_ENABLED", "false")
    settings = Settings(
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'v281-gateway-disabled.db'}",
        write_api_key="test",
        cors_origins=("http://testserver",),
    )
    app = create_app(settings)
    with TestClient(app) as client:
        body = client.get("/ready").json()
        assert body["ok"] is True
        assert body["unified_service_gateway"] == "disabled"
