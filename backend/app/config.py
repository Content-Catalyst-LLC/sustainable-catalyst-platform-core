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
    version: str = "2.1.0"
    environment: str = "development"
    database_url: str = "sqlite:///./platform_core.db"
    write_api_key: str = ""
    public_reads: bool = True
    cors_origins: tuple[str, ...] = ("http://127.0.0.1:8090",)
    log_level: str = "INFO"
    max_graph_depth: int = 4
    page_size_max: int = 200
    explorer_enabled: bool = True

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
        return cls(
            environment=os.getenv("SC_CORE_ENVIRONMENT", "development").strip().lower(),
            database_url=database_url,
            write_api_key=os.getenv("SC_CORE_WRITE_API_KEY", "").strip(),
            public_reads=_bool("SC_CORE_PUBLIC_READS", True),
            cors_origins=origins,
            log_level=os.getenv("SC_CORE_LOG_LEVEL", "INFO").strip().upper(),
            max_graph_depth=max(1, min(_int("SC_CORE_MAX_GRAPH_DEPTH", 4), 6)),
            page_size_max=max(10, min(_int("SC_CORE_PAGE_SIZE_MAX", 200), 1000)),
            explorer_enabled=_bool("SC_CORE_EXPLORER_ENABLED", True),
        )
