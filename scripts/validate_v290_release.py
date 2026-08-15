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
        "backend/app/models.py",
        "backend/app/services/reliability.py",
        "backend/app/routers/reliability.py",
        "backend/app/services/live_data.py",
        "backend/app/routers/meta.py",
        "backend/app/migrations.py",
        "backend/scripts/run_connector_worker.py",
        "backend/tests/test_streaming_alerts_reliability_v290.py",
        "deployment/platform-core-v290.env.example",
        "docs/STREAMING_ALERTS_SOURCE_RELIABILITY_V290.md",
        "RELEASE_NOTES_V290.md",
        "PLATFORM_CORE_V290_INSTALL_AND_TEST.md",
        "PLATFORM_CORE_V290_STREAMING_RELIABILITY_AUDIT.md",
        "render.yaml",
        "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php",
        "backend/public_sdk/downloads/sc-platform-core-public-python-v2.9.0.zip",
        "backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.9.0.zip",
        "schemas/connector-work-item-v1.schema.json",
        "schemas/dead-letter-record-v1.schema.json",
        "schemas/stream-event-v1.schema.json",
        "schemas/alert-rule-v1.schema.json",
        "schemas/geographic-subscription-v1.schema.json",
    ]
    for path in required:
        require(path)

    contains("backend/app/config.py", 'version: str = "2.9.0"')
    contains("backend/app/config.py", "streaming_enabled: bool = True")
    contains("backend/app/config.py", "reliability_worker_enabled: bool = True")
    contains("backend/app/config.py", "provider_failover_enabled: bool = True")
    contains("backend/app/migrations.py", '("0012", "Streaming event log')
    for cls in ["ConnectorWorkItem", "DeadLetterRecord", "StreamEvent", "AlertRule", "GeographicSubscription"]:
        contains("backend/app/models.py", f"class {cls}(Base):")
    contains("backend/app/services/reliability.py", "sanitize_queue_parameters")
    contains("backend/app/services/reliability.py", "failover_parameters_compatible")
    contains("backend/app/services/reliability.py", "replay_dead_letter")
    contains("backend/app/services/reliability.py", "stale_connectors")
    contains("backend/app/services/reliability.py", "evaluate_alerts")
    contains("backend/app/routers/reliability.py", '@router.get("/stream"')
    contains("backend/app/routers/reliability.py", '@public_router.get("/stream"')
    contains("backend/app/routers/reliability.py", "last-event-id")
    contains("backend/app/routers/meta.py", '"external_provider_health_release_blocking": False')
    contains("render.yaml", "SC_CORE_STREAMING_ENABLED")
    contains("render.yaml", "SC_CORE_RELIABILITY_WORKER_ENABLED")
    contains("render.yaml", "SC_CORE_PROVIDER_FAILOVER_ENABLED")
    contains("deployment/platform-core-v290.env.example", "SC_CORE_STREAMING_ENABLED=true")
    contains("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "Version: 2.9.0")
    contains("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "sc_platform_core_reliability_status")

    package = json.loads(require("backend/public_sdk/javascript/package.json").read_text())
    if package.get("version") != "2.9.0":
        raise SystemExit("ERROR - JavaScript public SDK version is not 2.9.0")
    pyproject = require("backend/public_sdk/python/pyproject.toml").read_text()
    if not re.search(r'^version\s*=\s*"2\.9\.0"\s*$', pyproject, re.M):
        raise SystemExit("ERROR - Python public SDK version is not 2.9.0")

    for schema in [
        "schemas/connector-work-item-v1.schema.json",
        "schemas/dead-letter-record-v1.schema.json",
        "schemas/stream-event-v1.schema.json",
        "schemas/alert-rule-v1.schema.json",
        "schemas/geographic-subscription-v1.schema.json",
    ]:
        json.loads(require(schema).read_text())

    print("PASS - v2.9.0 release contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
