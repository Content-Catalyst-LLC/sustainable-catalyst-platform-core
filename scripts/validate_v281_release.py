from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(path: str) -> Path:
    target = ROOT / path
    if not target.is_file():
        raise SystemExit(f"ERROR - required file missing: {path}")
    return target


def contains(path: str, needle: str) -> None:
    text = require(path).read_text(errors="replace")
    if needle not in text:
        raise SystemExit(f"ERROR - {path} missing required marker: {needle}")


def main() -> int:
    required = [
        "backend/app/config.py",
        "backend/app/service_registry.py",
        "backend/app/services/gateway.py",
        "backend/app/routers/meta.py",
        "backend/scripts/validate_production_integration.py",
        "backend/tests/test_production_integration_v281.py",
        "deployment/platform-core-v281.env.example",
        "docs/PRODUCTION_INTEGRATION_READINESS_V281.md",
        "RELEASE_NOTES_V281.md",
        "PLATFORM_CORE_V281_TERMINAL_COMMANDS.txt",
        "render.yaml",
        "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php",
        "backend/public_sdk/downloads/sc-platform-core-public-python-v2.8.1.zip",
        "backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.8.1.zip",
    ]
    for path in required:
        require(path)

    contains("backend/app/config.py", 'version: str = "2.8.1"')
    contains("backend/app/service_registry.py", "required: bool = False")
    contains("backend/app/service_registry.py", "token_required: bool = False")
    contains("backend/app/service_registry.py", "expected_version_prefix: str = \"\"")
    contains("backend/app/services/gateway.py", '"status": "unconfigured"')
    contains("backend/app/services/gateway.py", 'status = "version_unreported"')
    contains("backend/app/services/gateway.py", 'status = "version_mismatch"')
    contains("backend/app/routers/meta.py", '@router.get("/integration/readiness")')
    contains("backend/app/routers/meta.py", '"configuration_blockers"')
    contains("render.yaml", "SC_CORE_SITE_INTELLIGENCE_REQUIRED")
    contains("render.yaml", "SC_CORE_PUBLIC_BASE_URL_REQUIRED")
    contains("render.yaml", "SC_CORE_REQUIRED_CORS_ORIGIN")
    contains("deployment/platform-core-v281.env.example", "SC_CORE_SITE_INTELLIGENCE_REQUIRED=true")
    contains("deployment/platform-core-v281.env.example", "SC_CORE_SITE_INTELLIGENCE_EXPECTED_VERSION_PREFIX=4.")
    contains("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "Version: 2.8.1")
    contains("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "sc_platform_core_integration_readiness")

    package = json.loads(require("backend/public_sdk/javascript/package.json").read_text())
    if package.get("version") != "2.8.1":
        raise SystemExit("ERROR - JavaScript public SDK version is not 2.8.1")
    pyproject = require("backend/public_sdk/python/pyproject.toml").read_text()
    if not re.search(r'^version\s*=\s*"2\.8\.1"\s*$', pyproject, re.M):
        raise SystemExit("ERROR - Python public SDK version is not 2.8.1")

    render = require("render.yaml").read_text()
    if "SC_CORE_SITE_INTELLIGENCE_URL\n        sync: false" not in render:
        raise SystemExit("ERROR - Render must keep Site Intelligence URL deployment-supplied")
    if "SC_CORE_SITE_INTELLIGENCE_SERVICE_TOKEN\n        sync: false" not in render:
        raise SystemExit("ERROR - Render must keep Site Intelligence token deployment-supplied")

    print("PASS - v2.8.1 release contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
