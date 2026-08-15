import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .request_tracing import RequestTraceMiddleware
from .service_registry import GatewaySettings, ServiceRegistry
from .services.gateway import GatewayRuntime
from .services.live_data import LiveDataRuntime
from .database import Database
from .migrations import run_migrations
from .public_api_auth import PublicApiMiddleware
from .routers import (
    developer_admin,
    dossier_center,
    dossier_public_site,
    developer_portal,
    data_fabric,
    entities,
    economic_data,
    evidence,
    evidence_explorer,
    explorer,
    gateway,
    facilities,
    humanitarian,
    country_evidence,
    cross_product_exchange,
    scale,
    governance,
    certification,
    observability,
    foundations,
    imports,
    international_law,
    scientific_data,
    scientific_service_fabric,
    ledger,
    live_data,
    meta,
    predicates,
    public_api,
    relationships,
    reliability,
    trust_admin,
    trust_center,
    trust_public,
    workflow_public,
    workflows,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=(
            "Universal Entity Registry, governed Knowledge Graph, Evidence Ledger, "
            "source snapshots, calculation traces, provenance records, review "
            "workflows, tamper-evident audit infrastructure, a unified public API, "
            "developer applications, scoped credentials, usage controls, webhooks, "
            "SDK assets, a public Trust Center, evaluation runs, incidents, "
            "limitations, attestations, signature dossiers, end-to-end workflows, a unified service gateway, and a governed free live-data connector gateway, an international-law and United Nations record layer, a scientific data connector and discovery layer, an economics and official-statistics record layer, a geospatial, time-series, STAC, map-layer, and scientific-asset fabric, a streaming, alerts, connector-worker, replay, stale-source, and provider-failover reliability plane, and a provenance-preserving operational facility and status-observation registry, and a humanitarian access and essential-services evidence fabric, plus a country evidence federation and reconciliation plane, and an Earth, Ocean, Space, and Scientific Service Fabric, plus a governed Cross-Product Evidence Exchange for Sustainable Catalyst, and a distributed processing, storage, backpressure, retention, and scale-control plane, plus a governance, access-decision, retention-policy, and tamper-evident audit control plane, and a production certification, migration-assurance, and recovery-readiness control plane, plus a first-party observability, service-level-objective, and production-operations control plane."
        ),
        contact={
            "name": "Sustainable Catalyst",
            "url": "https://sustainablecatalyst.com/",
        },
        license_info={"name": "MIT"},
    )

    database = Database(settings.database_url)
    run_migrations(database)
    app.state.database = database
    app.state.settings = settings
    gateway_settings = GatewaySettings.from_env()
    app.state.gateway_settings = gateway_settings
    app.state.service_registry = ServiceRegistry.from_env()
    app.state.gateway_runtime = GatewayRuntime(
        app.state.service_registry,
        gateway_settings,
        core_version=settings.version,
    )
    app.state.live_data_runtime = LiveDataRuntime(settings)

    app.add_middleware(PublicApiMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-SC-API-Key",
            "X-SC-Public-Key",
            "X-Request-ID",
            "Last-Event-ID",
            "X-SC-Principal",
            "X-SC-Principal-Type",
            "X-SC-Product",
        ],
        expose_headers=[
            "X-Request-ID",
            "Last-Event-ID",
            "X-SC-Principal",
            "X-SC-Principal-Type",
            "X-SC-Product",
            "X-SC-API-Version",
            "X-RateLimit-Limit-Minute",
            "X-RateLimit-Remaining-Minute",
            "X-RateLimit-Limit-Day",
            "X-RateLimit-Remaining-Day",
            "Retry-After",
            "X-SC-Core-Version",
            "X-SC-Gateway-Service",
            "X-SC-Upstream-Latency-Ms",
            "Server-Timing",
        ],
    )

    app.add_middleware(RequestTraceMiddleware)

    app.include_router(meta.router)
    app.include_router(dossier_center.router)
    app.include_router(dossier_public_site.router)
    app.include_router(trust_center.router)
    app.include_router(developer_portal.router)
    app.include_router(explorer.router)
    app.include_router(evidence_explorer.router)
    app.include_router(predicates.router)
    app.include_router(public_api.router)
    app.include_router(gateway.router)
    app.include_router(live_data.router)
    app.include_router(live_data.public_router)
    app.include_router(reliability.router)
    app.include_router(reliability.public_router)
    app.include_router(facilities.router)
    app.include_router(facilities.public_router)
    app.include_router(humanitarian.router)
    app.include_router(humanitarian.public_router)
    app.include_router(country_evidence.router)
    app.include_router(country_evidence.public_router)
    app.include_router(cross_product_exchange.router)
    app.include_router(cross_product_exchange.public_router)
    app.include_router(scale.router)
    app.include_router(scale.public_router)
    app.include_router(governance.router)
    app.include_router(governance.public_router)
    app.include_router(certification.router)
    app.include_router(certification.public_router)
    app.include_router(observability.router)
    app.include_router(observability.public_router)
    app.include_router(international_law.router)
    app.include_router(international_law.public_router)
    app.include_router(scientific_data.router)
    app.include_router(scientific_data.public_router)
    app.include_router(scientific_service_fabric.router)
    app.include_router(scientific_service_fabric.public_router)
    app.include_router(economic_data.router)
    app.include_router(economic_data.public_router)
    app.include_router(data_fabric.router)
    app.include_router(data_fabric.public_router)
    app.include_router(data_fabric.stac_router)
    app.include_router(data_fabric.public_stac_router)
    app.include_router(trust_public.router)
    app.include_router(workflow_public.router)
    app.include_router(entities.router)
    app.include_router(relationships.router)
    app.include_router(evidence.router)
    app.include_router(ledger.router)
    app.include_router(foundations.router)
    app.include_router(imports.router)
    app.include_router(developer_admin.router)
    app.include_router(trust_admin.router)
    app.include_router(workflows.router)

    return app


app = create_app()
