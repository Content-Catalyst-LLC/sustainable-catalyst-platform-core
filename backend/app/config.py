from __future__ import annotations
from dataclasses import dataclass
import os

def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default

@dataclass(frozen=True)
class Settings:
    app_name: str = "Sustainable Catalyst Platform Core"
    version: str = "2.6.0"
    environment: str = "development"
    database_url: str = "sqlite:///./platform_core.db"
    write_api_key: str = ""
    public_reads: bool = True
    cors_origins: tuple[str, ...] = ("http://127.0.0.1:8090",)
    log_level: str = "INFO"
    max_graph_depth: int = 4
    page_size_max: int = 200
    explorer_enabled: bool = True
    evidence_explorer_enabled: bool = True
    snapshot_excerpt_max: int = 1200
    public_api_enabled: bool = True
    developer_portal_enabled: bool = True
    public_api_default_plan: str = "free"
    api_log_salt: str = "development-api-log-salt"
    webhook_signing_secret: str = "development-webhook-signing-secret"
    webhook_delivery_timeout: int = 10
    trust_center_enabled: bool = True
    trust_public_status_enabled: bool = True
    trust_stale_after_days: int = 90
    workflow_engine_enabled: bool = True
    dossier_center_enabled: bool = True
    dossier_signing_secret: str = "development-dossier-signing-secret"
    dossier_signing_key_id: str = "sc-platform-core-development"
    dossier_required_approvals: int = 1
    dossier_max_records: int = 500

    @classmethod
    def from_env(cls) -> "Settings":
        origins = tuple(
            value.strip()
            for value in os.getenv(
                "SC_CORE_CORS_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:8090",
            ).split(",")
            if value.strip()
        )
        database_url = os.getenv("SC_CORE_DATABASE_URL", "sqlite:///./platform_core.db")
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        environment = os.getenv(
            "SC_CORE_ENVIRONMENT",
            "development",
        ).strip().lower()
        production = environment == "production"
        return cls(
            environment=environment,
            database_url=database_url,
            write_api_key=os.getenv("SC_CORE_WRITE_API_KEY", "").strip(),
            public_reads=_bool("SC_CORE_PUBLIC_READS", True),
            cors_origins=origins,
            log_level=os.getenv("SC_CORE_LOG_LEVEL", "INFO").strip().upper(),
            max_graph_depth=max(1, min(_int("SC_CORE_MAX_GRAPH_DEPTH", 4), 6)),
            page_size_max=max(10, min(_int("SC_CORE_PAGE_SIZE_MAX", 200), 1000)),
            explorer_enabled=_bool("SC_CORE_EXPLORER_ENABLED", True),
            evidence_explorer_enabled=_bool("SC_CORE_EVIDENCE_EXPLORER_ENABLED", True),
            snapshot_excerpt_max=max(0, min(_int("SC_CORE_SNAPSHOT_EXCERPT_MAX", 1200), 10000)),
            public_api_enabled=_bool("SC_CORE_PUBLIC_API_ENABLED", True),
            developer_portal_enabled=_bool("SC_CORE_DEVELOPER_PORTAL_ENABLED", True),
            public_api_default_plan=os.getenv("SC_CORE_PUBLIC_API_DEFAULT_PLAN", "free").strip(),
            api_log_salt=os.getenv(
                "SC_CORE_API_LOG_SALT",
                "" if production else "development-api-log-salt",
            ).strip(),
            webhook_signing_secret=os.getenv(
                "SC_CORE_WEBHOOK_SIGNING_SECRET",
                "" if production else "development-webhook-signing-secret",
            ).strip(),
            webhook_delivery_timeout=max(
                1,
                min(_int("SC_CORE_WEBHOOK_DELIVERY_TIMEOUT", 10), 60),
            ),
            trust_center_enabled=_bool("SC_CORE_TRUST_CENTER_ENABLED", True),
            trust_public_status_enabled=_bool("SC_CORE_TRUST_PUBLIC_STATUS_ENABLED", True),
            trust_stale_after_days=max(1, min(_int("SC_CORE_TRUST_STALE_AFTER_DAYS", 90), 3650)),
            workflow_engine_enabled=_bool("SC_CORE_WORKFLOW_ENGINE_ENABLED", True),
            dossier_center_enabled=_bool("SC_CORE_DOSSIER_CENTER_ENABLED", True),
            dossier_signing_secret=os.getenv(
                "SC_CORE_DOSSIER_SIGNING_SECRET",
                "" if production else "development-dossier-signing-secret",
            ).strip(),
            dossier_signing_key_id=os.getenv(
                "SC_CORE_DOSSIER_SIGNING_KEY_ID",
                "sc-platform-core-development",
            ).strip(),
            dossier_required_approvals=max(
                0,
                min(_int("SC_CORE_DOSSIER_REQUIRED_APPROVALS", 1), 20),
            ),
            dossier_max_records=max(
                1,
                min(_int("SC_CORE_DOSSIER_MAX_RECORDS", 500), 5000),
            ),
        )
