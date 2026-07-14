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
    entities,
    evidence,
    evidence_explorer,
    explorer,
    gateway,
    foundations,
    imports,
    international_law,
    ledger,
    live_data,
    meta,
    predicates,
    public_api,
    relationships,
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
            "limitations, attestations, signature dossiers, end-to-end workflows, a unified service gateway, and a governed free live-data connector gateway, and an international-law and United Nations record layer for Sustainable Catalyst."
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
        ],
        expose_headers=[
            "X-Request-ID",
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
    app.include_router(international_law.router)
    app.include_router(international_law.public_router)
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
