from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from typing import Iterable
from urllib.parse import urlsplit


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name)
    try:
        value = int(raw) if raw is not None else default
    except ValueError:
        value = default
    return max(minimum, min(value, maximum))


def _csv(name: str, default: Iterable[str]) -> tuple[str, ...]:
    raw = os.getenv(name)
    if not raw:
        return tuple(default)
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class GatewaySettings:
    enabled: bool = True
    request_timeout_seconds: int = 30
    health_timeout_seconds: int = 5
    max_request_bytes: int = 2_000_000
    max_response_bytes: int = 8_000_000
    circuit_failure_threshold: int = 3
    circuit_cooldown_seconds: int = 30
    expose_upstream_errors: bool = False

    @classmethod
    def from_env(cls) -> "GatewaySettings":
        return cls(
            enabled=_bool("SC_CORE_GATEWAY_ENABLED", True),
            request_timeout_seconds=_int(
                "SC_CORE_GATEWAY_REQUEST_TIMEOUT", 30, 1, 180
            ),
            health_timeout_seconds=_int(
                "SC_CORE_GATEWAY_HEALTH_TIMEOUT", 5, 1, 30
            ),
            max_request_bytes=_int(
                "SC_CORE_GATEWAY_MAX_REQUEST_BYTES", 2_000_000, 1_024, 25_000_000
            ),
            max_response_bytes=_int(
                "SC_CORE_GATEWAY_MAX_RESPONSE_BYTES", 8_000_000, 1_024, 50_000_000
            ),
            circuit_failure_threshold=_int(
                "SC_CORE_GATEWAY_CIRCUIT_FAILURES", 3, 1, 20
            ),
            circuit_cooldown_seconds=_int(
                "SC_CORE_GATEWAY_CIRCUIT_COOLDOWN", 30, 1, 900
            ),
            expose_upstream_errors=_bool(
                "SC_CORE_GATEWAY_EXPOSE_UPSTREAM_ERRORS", False
            ),
        )


@dataclass(frozen=True)
class ServiceDefinition:
    service_id: str
    name: str
    route_prefix: str
    base_url: str
    health_path: str = "/health"
    enabled: bool = False
    service_token: str = ""
    public_reads: bool = True
    public_invocation: bool = False
    allowed_methods: tuple[str, ...] = ("GET", "HEAD", "OPTIONS")
    capabilities: tuple[str, ...] = ()

    @property
    def configured(self) -> bool:
        if not self.base_url.strip():
            return False
        parsed = urlsplit(self.base_url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    def public_dict(self) -> dict:
        payload = asdict(self)
        payload.pop("base_url", None)
        payload.pop("service_token", None)
        payload["configured"] = self.configured
        return payload


_DEFAULTS: tuple[dict, ...] = (
    {
        "service_id": "site-intelligence",
        "name": "Site Intelligence",
        "route_prefix": "site-intelligence",
        "capabilities": (
            "external-connectors",
            "source-health",
            "country-intelligence",
            "indicators",
        ),
    },
    {
        "service_id": "workbench",
        "name": "Sustainable Catalyst Workbench",
        "route_prefix": "workbench",
        "capabilities": ("calculations", "models", "visual-analysis"),
    },
    {
        "service_id": "decision-studio",
        "name": "Decision Studio",
        "route_prefix": "decision-studio",
        "capabilities": ("decision-briefs", "scenarios", "exports"),
    },
    {
        "service_id": "research-librarian",
        "name": "Research Librarian",
        "route_prefix": "research-librarian",
        "capabilities": ("site-scoped-retrieval", "research-routes"),
    },
    {
        "service_id": "finance",
        "name": "Catalyst Finance",
        "route_prefix": "finance",
        "capabilities": ("financial-analysis", "valuation", "sensitivity"),
    },
    {
        "service_id": "narrative-risk",
        "name": "Narrative Risk",
        "route_prefix": "narrative-risk",
        "capabilities": (
            "claims",
            "economic-narratives",
            "market-narratives",
            "humanitarian-narratives",
        ),
    },
)


class ServiceRegistry:
    def __init__(self, services: Iterable[ServiceDefinition]):
        items = list(services)
        self._by_id = {service.service_id: service for service in items}
        self._by_prefix = {service.route_prefix: service for service in items}
        if len(self._by_id) != len(items):
            raise ValueError("Duplicate service_id in service registry.")
        if len(self._by_prefix) != len(items):
            raise ValueError("Duplicate route_prefix in service registry.")

    @classmethod
    def from_env(cls) -> "ServiceRegistry":
        services: list[ServiceDefinition] = []
        for default in _DEFAULTS:
            service_id = default["service_id"]
            env_prefix = "SC_CORE_" + service_id.upper().replace("-", "_")
            base_url = os.getenv(f"{env_prefix}_URL", "").strip().rstrip("/")
            enabled = _bool(f"{env_prefix}_ENABLED", bool(base_url))
            methods = _csv(
                f"{env_prefix}_ALLOWED_METHODS",
                ("GET", "HEAD", "OPTIONS", "POST"),
            )
            services.append(
                ServiceDefinition(
                    **default,
                    base_url=base_url,
                    health_path=os.getenv(
                        f"{env_prefix}_HEALTH_PATH", "/health"
                    ).strip()
                    or "/health",
                    enabled=enabled,
                    service_token=os.getenv(
                        f"{env_prefix}_SERVICE_TOKEN", ""
                    ).strip(),
                    public_reads=_bool(f"{env_prefix}_PUBLIC_READS", True),
                    public_invocation=_bool(
                        f"{env_prefix}_PUBLIC_INVOCATION", False
                    ),
                    allowed_methods=tuple(method.upper() for method in methods),
                )
            )
        return cls(services)

    def list(self) -> list[ServiceDefinition]:
        return sorted(self._by_id.values(), key=lambda item: item.service_id)

    def get(self, service_id: str) -> ServiceDefinition | None:
        return self._by_id.get(service_id)

    def resolve_prefix(self, route_prefix: str) -> ServiceDefinition | None:
        return self._by_prefix.get(route_prefix)

    def public_catalog(self) -> list[dict]:
        return [service.public_dict() for service in self.list()]
