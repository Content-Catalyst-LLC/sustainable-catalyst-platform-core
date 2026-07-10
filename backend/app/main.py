from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .database import Database
from .migrations import run_migrations
from .routers import entities, foundations, imports, meta, relationships


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=(
            "Shared entity, relationship, evidence-foundation, validation-event, "
            "and integration infrastructure for Sustainable Catalyst."
        ),
        contact={
            "name": "Sustainable Catalyst",
            "url": "https://sustainablecatalyst.com/",
        },
        license_info={"name": "MIT"},
        openapi_tags=[
            {"name": "Service", "description": "Health, readiness, metadata, and statistics."},
            {"name": "Entities", "description": "Universal Entity Registry and aliases."},
            {"name": "Relationships and Graph", "description": "Typed relationships and graph traversal."},
            {"name": "Imports", "description": "Registry import adapters and import history."},
            {
                "name": "Evidence and Validation Foundations",
                "description": "Foundation records for later Evidence Ledger and Trust Center builds.",
            },
        ],
    )

    database = Database(settings.database_url)
    run_migrations(database)
    app.state.database = database
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "X-SC-API-Key"],
    )

    app.include_router(meta.router)
    app.include_router(entities.router)
    app.include_router(relationships.router)
    app.include_router(foundations.router)
    app.include_router(imports.router)

    return app


app = create_app()
