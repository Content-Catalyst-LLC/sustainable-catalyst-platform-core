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
    "backend/app/models.py",
    "backend/app/migrations.py",
    "backend/app/routers/capacity.py",
    "backend/app/services/capacity.py",
    "backend/app/services/certification.py",
    "backend/scripts/validate_capacity_resource_governance.py",
    "backend/tests/test_capacity_forecasting_resource_governance_v2240.py",
    "schemas/capacity-resource-profile-v1.schema.json",
    "schemas/capacity-forecast-v1.schema.json",
    "docs/CAPACITY_FORECASTING_RESOURCE_GOVERNANCE_V2240.md",
    "RELEASE_NOTES_V2240.md",
    "PLATFORM_CORE_V2240_INSTALL_AND_TEST.md",
    "PLATFORM_CORE_V2240_CAPACITY_FORECASTING_RESOURCE_GOVERNANCE_AUDIT.md",
    "PLATFORM_CORE_V2240_TERMINAL_COMMANDS.txt",
    "deployment/platform-core-v2240.env.example",
    "render.yaml",
    "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php",
    "backend/public_sdk/downloads/sc-platform-core-public-python-v2.24.0.zip",
    "backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.24.0.zip",
    "PUSH_PLATFORM_CORE_V2240_FINAL.sh",
    "deploy_and_validate_platform_core_v2_24_0_macos.sh",
]
for path in required:
    req(path)

has("backend/app/config.py", 'version: str = "2.24.0"')
has("backend/app/migrations.py", '("0027", "Capacity resource profiles')
has("backend/app/main.py", "capacity.public_router")
has("backend/app/routers/meta.py", '"capacity_forecasting_resource_governance"')
has("backend/app/routers/capacity.py", 'prefix="/v1/capacity"')
has("backend/app/routers/capacity.py", 'prefix="/api/v1/capacity"')
has("backend/app/services/capacity.py", '"forecast_method": "bounded-linear"')
has("backend/app/services/capacity.py", '"automatic_scaling": False')
has("backend/app/services/capacity.py", '"automatic_infrastructure_purchase": False')
has("backend/app/services/capacity.py", '"hard_admission_control": False')
has("backend/app/services/certification.py", "certification_require_capacity_ready")
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "Version: 2.24.0")
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "sc_platform_core_capacity_status")
has("render.yaml", "SustainableCatalystPlatformCore/2.24.0")
has("render.yaml", "SC_CORE_CAPACITY_RESOURCE_GOVERNANCE_ENABLED")
has("render.yaml", "SC_CORE_CERTIFICATION_REQUIRE_CAPACITY_READY")
assert json.loads(req("backend/public_sdk/javascript/package.json").read_text())["version"] == "2.24.0"
assert 'version = "2.24.0"' in req("backend/public_sdk/python/pyproject.toml").read_text()
assert req("README.md").read_text().startswith("# Sustainable Catalyst Platform Core v2.24.0")
has("docs/ROADMAP.md", "v2.24.0 — Capacity Forecasting & Resource Governance")
has("docs/ROADMAP.md", "Next planned: v2.25.0 — Identity, Credential & Cryptographic Key Lifecycle")

meta = req("backend/app/routers/meta.py").read_text()
implemented_block = meta.split("capabilities=[", 1)[1].split("deferred_capabilities=[", 1)[0]
deferred_block = meta.split("deferred_capabilities=[", 1)[1].split("]", 1)[0]
implemented = re.findall(r'"([a-z0-9_]+)"', implemented_block)
deferred = re.findall(r'"([a-z0-9_]+)"', deferred_block)
assert len(implemented) == len(set(implemented)), "duplicate implemented capability"
assert len(deferred) == len(set(deferred)), "duplicate deferred capability"
assert set(implemented).isdisjoint(deferred), "implemented/deferred overlap"
for capability in (
    "capacity_forecasting_resource_governance",
    "capacity_resource_profiles",
    "bounded_linear_capacity_forecasts",
    "resource_budgets",
    "advisory_soft_limit_governance",
    "capacity_certification_gate",
):
    assert capability in implemented, capability
    assert capability not in deferred, capability

for schema in ("schemas/capacity-resource-profile-v1.schema.json", "schemas/capacity-forecast-v1.schema.json"):
    json.loads(req(schema).read_text())

for z in (
    "backend/public_sdk/downloads/sc-platform-core-public-python-v2.24.0.zip",
    "backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.24.0.zip",
):
    with zipfile.ZipFile(req(z)) as archive:
        assert archive.testzip() is None

for script in ("PUSH_PLATFORM_CORE_V2240_FINAL.sh", "deploy_and_validate_platform_core_v2_24_0_macos.sh"):
    text = req(script).read_text()
    assert "v2.24.0" in text and "v2240" in text
    assert "validate_capacity_resource_governance.py" in text

print("PASS - v2.24.0 capacity forecasting/resource governance release contract")
