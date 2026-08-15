from __future__ import annotations

from urllib.parse import urlsplit

from app.config import Settings
from app.service_registry import ServiceRegistry


def valid_http_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def main() -> int:
    settings = Settings.from_env()
    registry = ServiceRegistry.from_env()
    errors: list[str] = []

    if settings.public_base_url_required and not valid_http_url(settings.public_base_url):
        errors.append("SC_CORE_PUBLIC_BASE_URL is required and must be an HTTP(S) URL")

    if (
        settings.required_cors_origin
        and settings.required_cors_origin not in settings.cors_origins
    ):
        errors.append(
            "SC_CORE_REQUIRED_CORS_ORIGIN is not present in SC_CORE_CORS_ORIGINS"
        )

    for service in registry.list():
        if not service.required:
            continue
        if not service.configured:
            errors.append(f"{service.service_id}: required service URL is not configured")
        if not service.enabled:
            errors.append(f"{service.service_id}: required service is disabled")
        if service.token_required and not service.service_token:
            errors.append(f"{service.service_id}: required service token is missing")

    if errors:
        for error in errors:
            print(f"ERROR - {error}")
        return 1

    print("PASS - Platform Core production integration configuration is structurally valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
