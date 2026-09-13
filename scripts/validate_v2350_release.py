#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def req(path: str) -> Path:
    p = ROOT / path
    assert p.is_file(), f"missing required file: {path}"
    return p

def has(path: str, text: str) -> None:
    assert text in req(path).read_text(errors="replace"), f"{path} missing: {text}"

for path in [
    "RELEASE_NOTES_V2350.md",
    "PLATFORM_CORE_V2350_INSTALL_AND_TEST.md",
    "PLATFORM_CORE_V2350_SCENARIO_COMPUTE_ENGINE_AUDIT.md",
    "PLATFORM_CORE_V2350_TERMINAL_COMMANDS.txt",
    "docs/SCENARIO_COMPUTE_ENGINE_V2350.md",
    "backend/app/services/scenario_compute.py",
    "backend/app/routers/scenario_compute.py",
    "backend/tests/test_scenario_compute_engine_v2350.py",
    "backend/scripts/validate_scenario_compute_engine.py",
    "deploy_and_validate_platform_core_v2_35_0_macos.sh",
    "PUSH_PLATFORM_CORE_V2350_FINAL.sh",
    "DEPLOY_PLATFORM_CORE_V2350_CONTABO.sh",
    "platform-core-v2350.env.example",
    "backend/public_sdk/downloads/sc-platform-core-public-python-v2.35.0.zip",
    "backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.35.0.zip",
]:
    req(path)

has("backend/app/config.py", 'version: str = "2.35.0"')
has("backend/app/migrations.py", '("0038", "Governed Scenario Compute Engine orchestration')
has("backend/app/main.py", "scenario_compute.router")
has("backend/app/routers/meta.py", '"scenario_compute_engine"')
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "Version: 2.35.0")
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "sc_platform_core_scenario_compute_status")
has("wordpress-plugin/sustainable-catalyst-platform-core/readme.txt", "Stable tag: 2.35.0")
has("backend/public_sdk/javascript/package.json", '"version": "2.35.0"')
has("backend/public_sdk/javascript/index.mjs", "scenarioComputeReadiness()")
has("backend/public_sdk/python/pyproject.toml", 'version = "2.35.0"')
has("backend/public_sdk/python/sc_platform_core_public/client.py", "scenario_compute_readiness")
has("backend/app/routers/developer_portal.py", "sc-platform-core-public-python-v2.35.0.zip")
has("backend/app/routers/developer_portal.py", "sc-platform-core-public-javascript-v2.35.0.zip")
has("README.md", "Next planned: **v2.36.0 — Uncertainty, Sensitivity & Ensemble Reasoning**")
has("docs/ROADMAP.md", "v2.42.0 — Forensic Object Model & Evidence Provenance")

models = req("backend/app/models.py").read_text()
for cls in [
    "ScenarioComputePlanRecord",
    "ScenarioComputeCaseRecord",
    "ScenarioComputeRequestRecord",
    "ScenarioComputeAttemptRecord",
    "ScenarioComputeResultBindingRecord",
]:
    assert f"class {cls}(Base):" in models, f"missing model {cls}"

for name in [
    "scenario-compute-plan-v1.schema.json",
    "scenario-compute-case-v1.schema.json",
    "scenario-compute-request-v1.schema.json",
    "scenario-compute-attempt-v1.schema.json",
    "scenario-compute-result-binding-v1.schema.json",
]:
    doc = json.loads(req("schemas/" + name).read_text())
    assert doc["type"] == "object", name

print("PASS - v2.35.0 Scenario Compute Engine release contract")
