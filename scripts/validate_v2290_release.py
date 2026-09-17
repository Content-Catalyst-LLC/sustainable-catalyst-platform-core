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
    "RELEASE_NOTES_V2290.md",
    "PLATFORM_CORE_V2290_INSTALL_AND_TEST.md",
    "PLATFORM_CORE_V2290_RESEARCH_VISUAL_REASONING_AUDIT.md",
    "PLATFORM_CORE_V2290_TERMINAL_COMMANDS.txt",
    "docs/VISUAL_REASONING_OBJECT_MODEL_V2290.md",
    "backend/app/services/visual_reasoning.py",
    "backend/app/routers/visual_reasoning.py",
    "backend/tests/test_visual_reasoning_object_model_v2290.py",
    "backend/scripts/validate_visual_reasoning_object_model.py",
    "backend/public_sdk/downloads/sc-platform-core-public-python-v2.29.0.zip",
    "backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.29.0.zip",
    "deploy_and_validate_platform_core_v2_29_0_macos.sh",
    "PUSH_PLATFORM_CORE_V2290_FINAL.sh",
    "platform-core-v2290.env.example",
]
for path in required:
    req(path)

has("backend/app/config.py", 'version: str = "2.29.0"')
has("backend/app/config.py", "visual_reasoning_object_model_enabled: bool = True")
has("backend/app/migrations.py", '("0032", "Renderer-neutral visual reasoning objects')
has("backend/app/main.py", "visual_reasoning.router")
has("backend/app/main.py", "visual_reasoning.public_router")
has("backend/app/routers/meta.py", '"visual_reasoning_object_model"')
has("backend/app/services/visual_reasoning.py", '"renderer_neutral": True')
has("backend/app/services/visual_reasoning.py", '"renderer_registry_in_core": False')
has("backend/app/services/visual_reasoning.py", '"layout_engine_in_core": False')
has("backend/app/services/visual_reasoning.py", '"automatic_truth_promotion": False')
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "Version: 2.29.0")
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "sc_platform_core_visual_reasoning_status")
has("wordpress-plugin/sustainable-catalyst-platform-core/readme.txt", "Stable tag: 2.29.0")
has("render.yaml", "SustainableCatalystPlatformCore/2.29.0")
has("backend/.env.example", "SC_CORE_VISUAL_REASONING_OBJECT_MODEL_ENABLED=true")
has("README.md", "# Sustainable Catalyst Platform Core v2.29.0")
has("README.md", "Next planned: **v2.30.0 — Visualization Specification & Renderer Registry**")
has("docs/ROADMAP.md", "## v2.29.0 — Visual Reasoning Object Model")
has("docs/ROADMAP.md", "Next planned: v2.30.0 — Visualization Specification & Renderer Registry")
has("CHANGELOG.md", "## 2.29.0 — 2026-09-11")
has("backend/public_sdk/javascript/package.json", '"version": "2.29.0"')
has("backend/public_sdk/python/pyproject.toml", 'version = "2.29.0"')
has("backend/public_sdk/javascript/index.mjs", "visualReasoningReadiness()")
has("backend/public_sdk/python/sc_platform_core_public/client.py", "visual_reasoning_readiness")

for name in (
    "visual-reasoning-object-v1.schema.json",
    "visual-reasoning-element-v1.schema.json",
    "visual-reasoning-relation-v1.schema.json",
    "visual-reasoning-layer-v1.schema.json",
    "visual-reasoning-annotation-v1.schema.json",
    "visual-reasoning-snapshot-v1.schema.json",
):
    data = json.loads(req(f"schemas/{name}").read_text())
    assert data["$schema"].endswith("2020-12/schema")
    assert data["type"] == "object"

for zpath in (
    "backend/public_sdk/downloads/sc-platform-core-public-python-v2.29.0.zip",
    "backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.29.0.zip",
):
    with ZipFile(req(zpath)) as zf:
        assert zf.testzip() is None, f"bad SDK zip: {zpath}"

models = req("backend/app/models.py").read_text()
for cls in (
    "VisualReasoningObjectRecord", "VisualReasoningElementRecord", "VisualReasoningRelationRecord",
    "VisualReasoningLayerRecord", "VisualReasoningAnnotationRecord", "VisualReasoningSnapshotRecord",
):
    assert f"class {cls}(Base):" in models

print("PASS - v2.29.0 Visual Reasoning Object Model release contract")
