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
    "RELEASE_NOTES_V2360.md",
    "PLATFORM_CORE_V2360_INSTALL_AND_TEST.md",
    "PLATFORM_CORE_V2360_UNCERTAINTY_SENSITIVITY_ENSEMBLE_AUDIT.md",
    "PLATFORM_CORE_V2360_TERMINAL_COMMANDS.txt",
    "docs/UNCERTAINTY_SENSITIVITY_ENSEMBLE_V2360.md",
    "backend/app/services/uncertainty_reasoning.py",
    "backend/app/routers/uncertainty_reasoning.py",
    "backend/tests/test_uncertainty_sensitivity_ensemble_v2360.py",
    "backend/scripts/validate_uncertainty_reasoning.py",
    "deploy_and_validate_platform_core_v2_36_0_macos.sh",
    "PUSH_PLATFORM_CORE_V2360_FINAL.sh",
    "DEPLOY_PLATFORM_CORE_V2360_CONTABO.sh",
    "platform-core-v2360.env.example",
    "backend/public_sdk/downloads/sc-platform-core-public-python-v2.36.0.zip",
    "backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.36.0.zip",
]:
    req(path)

has("backend/app/config.py", 'version: str = "2.36.0"')
has("backend/app/migrations.py", '("0039", "First-class uncertainty definitions')
has("backend/app/main.py", "uncertainty_reasoning.router")
has("backend/app/routers/meta.py", '"uncertainty_sensitivity_ensemble_reasoning"')
has("backend/app/services/visual_reasoning.py", "sensitivity-map")
has("backend/app/services/visual_reasoning.py", "ensemble-view")
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "Version: 2.36.0")
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "sc_platform_core_uncertainty_reasoning_status")
has("wordpress-plugin/sustainable-catalyst-platform-core/readme.txt", "Stable tag: 2.36.0")
has("backend/public_sdk/javascript/package.json", '"version": "2.36.0"')
has("backend/public_sdk/javascript/index.mjs", "uncertaintyReasoningReadiness()")
has("backend/public_sdk/python/pyproject.toml", 'version = "2.36.0"')
has("backend/public_sdk/python/sc_platform_core_public/client.py", "uncertainty_reasoning_readiness")
has("backend/app/routers/developer_portal.py", "sc-platform-core-public-python-v2.36.0.zip")
has("backend/app/routers/developer_portal.py", "sc-platform-core-public-javascript-v2.36.0.zip")
has("README.md", "Next planned: **v2.37.0 — Causal Systems Explorer**")
has("docs/ROADMAP.md", "v2.42.0 — Forensic Object Model & Evidence Provenance")

models = req("backend/app/models.py").read_text()
for cls in [
    "UncertaintyDefinitionRecord",
    "SensitivityStudyRecord",
    "SensitivityFactorRecord",
    "SensitivityResultRecord",
    "EnsembleRecord",
    "EnsembleMemberRecord",
    "EnsembleStatisticRecord",
]:
    assert f"class {cls}(Base):" in models, f"missing model {cls}"

for name in [
    "uncertainty-definition-v1.schema.json",
    "sensitivity-study-v1.schema.json",
    "sensitivity-factor-v1.schema.json",
    "sensitivity-result-v1.schema.json",
    "ensemble-v1.schema.json",
    "ensemble-member-v1.schema.json",
    "ensemble-statistic-v1.schema.json",
]:
    doc = json.loads(req("schemas/" + name).read_text())
    assert doc["type"] == "object", name

print("PASS - v2.36.0 Uncertainty, Sensitivity & Ensemble Reasoning release contract")
