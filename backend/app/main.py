import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .database import Database
from .migrations import run_migrations
from .public_api_auth import PublicApiMiddleware
from .routers import (
    developer_admin,
    developer_portal,
    entities,
    evidence,
    evidence_explorer,
    explorer,
    foundations,
    imports,
    ledger,
    meta,
    predicates,
    public_api,
    relationships,
    trust_admin,
    trust_center,
    trust_public,
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
            "limitations, and attestations for Sustainable Catalyst."
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
        ],
    )

    app.include_router(meta.router)
    app.include_router(trust_center.router)
    app.include_router(developer_portal.router)
    app.include_router(explorer.router)
    app.include_router(evidence_explorer.router)
    app.include_router(predicates.router)
    app.include_router(public_api.router)
    app.include_router(trust_public.router)
    app.include_router(entities.router)
    app.include_router(relationships.router)
    app.include_router(evidence.router)
    app.include_router(ledger.router)
    app.include_router(foundations.router)
    app.include_router(imports.router)
    app.include_router(developer_admin.router)
    app.include_router(trust_admin.router)

    return app


app = create_app()
