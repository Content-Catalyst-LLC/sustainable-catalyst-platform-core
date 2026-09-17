#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def req(path: str) -> Path:
    p = ROOT / path
    assert p.is_file(), f"missing required file: {path}"
    return p


def has(path: str, text: str) -> None:
    body = req(path).read_text(errors="replace")
    assert text in body, f"{path} missing: {text}"


required = [
    "RELEASE_NOTES_V2280.md",
    "PLATFORM_CORE_V2280_INSTALL_AND_TEST.md",
    "PLATFORM_CORE_V2280_RESEARCH_OBJECT_MODEL_FOUNDATION_AUDIT.md",
    "PLATFORM_CORE_V2280_TERMINAL_COMMANDS.txt",
    "docs/RESEARCH_OBJECT_MODEL_FOUNDATION_V2280.md",
    "backend/app/services/research_objects.py",
    "backend/app/routers/research_objects.py",
    "backend/tests/test_research_object_model_foundation_v2280.py",
    "backend/scripts/validate_research_object_model_foundation.py",
    "backend/public_sdk/downloads/sc-platform-core-public-python-v2.28.0.zip",
    "backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.28.0.zip",
    "deploy_and_validate_platform_core_v2_28_0_macos.sh",
    "PUSH_PLATFORM_CORE_V2280_FINAL.sh",
    "platform-core-v2280.env.example",
]
for path in required:
    req(path)

has("backend/app/config.py", 'version: str = "2.28.0"')
has("backend/app/config.py", "research_object_model_enabled: bool = True")
has("backend/app/migrations.py", '("0031", "Research projects, models, immutable model versions')
has("backend/app/main.py", "research_objects.router")
has("backend/app/main.py", "research_objects.public_router")
has("backend/app/routers/meta.py", '"research_object_model_foundation"')
has("backend/app/services/research_objects.py", '"model_execution_by_core": False')
has("backend/app/services/research_objects.py", '"visual_renderer_in_core": False')
has("backend/app/services/research_objects.py", '"automatic_truth_promotion": False')
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "Version: 2.28.0")
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "sc_platform_core_research_object_status")
has("wordpress-plugin/sustainable-catalyst-platform-core/readme.txt", "Stable tag: 2.28.0")
has("render.yaml", "SustainableCatalystPlatformCore/2.28.0")
has("render.yaml", "SC_CORE_RESEARCH_OBJECT_MODEL_ENABLED")
has("backend/.env.example", "SC_CORE_RESEARCH_OBJECT_MODEL_ENABLED=true")
has("README.md", "# Sustainable Catalyst Platform Core v2.28.0")
has("README.md", "Next planned: **v2.29.0 — Visual Reasoning Object Model**")
has("docs/ROADMAP.md", "## v2.28.0 — Research Object & Model Foundation")
has("docs/ROADMAP.md", "Next planned: v2.29.0 — Visual Reasoning Object Model")
has("CHANGELOG.md", "## 2.28.0 — 2026-09-11")
has("backend/public_sdk/javascript/package.json", '"version": "2.28.0"')
has("backend/public_sdk/python/pyproject.toml", 'version = "2.28.0"')
has("backend/public_sdk/javascript/index.mjs", "researchObjectReadiness()")
has("backend/public_sdk/python/sc_platform_core_public/client.py", "research_object_readiness")

schemas = [
    "research-project-v1.schema.json",
    "research-model-v1.schema.json",
    "research-model-version-v1.schema.json",
    "research-variable-v1.schema.json",
    "research-parameter-v1.schema.json",
    "research-scenario-v1.schema.json",
    "research-model-run-v1.schema.json",
    "research-result-v1.schema.json",
]
for name in schemas:
    data = json.loads(req(f"schemas/{name}").read_text())
    assert data["$schema"].endswith("2020-12/schema")
    assert data["type"] == "object"

for zpath in (
    "backend/public_sdk/downloads/sc-platform-core-public-python-v2.28.0.zip",
    "backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.28.0.zip",
):
    with ZipFile(req(zpath)) as zf:
        assert zf.testzip() is None, f"bad SDK zip: {zpath}"

models = req("backend/app/models.py").read_text()
for cls in (
    "ResearchProjectRecord", "ResearchModelRecord", "ResearchModelVersionRecord",
    "ResearchVariableRecord", "ResearchParameterRecord", "ResearchScenarioRecord",
    "ResearchModelRunRecord", "ResearchResultRecord",
):
    assert f"class {cls}(Base):" in models

print("PASS - v2.28.0 Research Object & Model Foundation release contract")
