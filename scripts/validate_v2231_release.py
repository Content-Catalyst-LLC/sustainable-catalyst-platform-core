from __future__ import annotations

from pathlib import Path
import json
import re
import zipfile

R = Path(__file__).resolve().parents[1]


def req(path: str) -> Path:
    p = R / path
    assert p.is_file(), path
    return p


def has(path: str, text: str) -> None:
    assert text in req(path).read_text(), (path, text)


required = [
    "backend/app/config.py",
    "backend/app/routers/meta.py",
    "backend/app/routers/reliability.py",
    "backend/app/services/reliability.py",
    "backend/scripts/run_connector_worker.py",
    "backend/tests/test_capability_metadata_release_lineage_v2231.py",
    "docs/CAPABILITY_METADATA_RELEASE_LINEAGE_V2231.md",
    "RELEASE_NOTES_V2231.md",
    "PLATFORM_CORE_V2231_INSTALL_AND_TEST.md",
    "PLATFORM_CORE_V2231_CAPABILITY_METADATA_RELEASE_LINEAGE_AUDIT.md",
    "PLATFORM_CORE_V2231_TERMINAL_COMMANDS.txt",
    "deployment/platform-core-v2231.env.example",
    "render.yaml",
    "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php",
    "backend/public_sdk/downloads/sc-platform-core-public-python-v2.23.1.zip",
    "backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.23.1.zip",
]
for path in required:
    req(path)

has("backend/app/config.py", 'version: str = "2.23.1"')
has("backend/app/migrations.py", '("0026",')
assert '("0027",' not in req("backend/app/migrations.py").read_text()
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "Version: 2.23.1")
has("render.yaml", "SustainableCatalystPlatformCore/2.23.1")
assert json.loads(req("backend/public_sdk/javascript/package.json").read_text())["version"] == "2.23.1"
assert 'version = "2.23.1"' in req("backend/public_sdk/python/pyproject.toml").read_text()
assert req("README.md").read_text().startswith("# Sustainable Catalyst Platform Core v2.23.1")
has("docs/ROADMAP.md", "v2.23.1 — Capability Metadata, Documentation & Release-Lineage Repair")

meta = req("backend/app/routers/meta.py").read_text()
implemented_block = meta.split("capabilities=[", 1)[1].split("deferred_capabilities=[", 1)[0]
deferred_block = meta.split("deferred_capabilities=[", 1)[1].split("]", 1)[0]
for capability in ("distributed_connector_workers", "server_sent_live_data_events"):
    assert f'"{capability}"' in implemented_block, capability
    assert f'"{capability}"' not in deferred_block, capability

implemented = re.findall(r'"([a-z0-9_]+)"', implemented_block)
deferred = re.findall(r'"([a-z0-9_]+)"', deferred_block)
assert len(implemented) == len(set(implemented)), "duplicate implemented capability"
assert len(deferred) == len(set(deferred)), "duplicate deferred capability"
assert set(implemented).isdisjoint(deferred), "implemented/deferred overlap"

reliability_router = req("backend/app/routers/reliability.py").read_text()
worker = req("backend/scripts/run_connector_worker.py").read_text()
reliability_service = req("backend/app/services/reliability.py").read_text()
assert "StreamingResponse" in reliability_router
assert 'media_type="text/event-stream"' in reliability_router
assert "process_next_work" in worker
assert "claim_next_work" in reliability_service and "lease_expires_at" in reliability_service

for z in (
    "backend/public_sdk/downloads/sc-platform-core-public-python-v2.23.1.zip",
    "backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.23.1.zip",
):
    with zipfile.ZipFile(req(z)) as archive:
        assert archive.testzip() is None

for script in ("PUSH_PLATFORM_CORE_V2231_FINAL.sh", "deploy_and_validate_platform_core_v2_23_1_macos.sh"):
    text = req(script).read_text()
    assert "v2.23.1" in text and "v2_23_1" in text

print("PASS - v2.23.1 capability metadata/documentation/release-lineage contract")
