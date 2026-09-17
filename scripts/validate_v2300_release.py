#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]

def req(path: str) -> Path:
    p=ROOT/path
    assert p.is_file(), f"missing required file: {path}"
    return p

def has(path: str, text: str) -> None:
    body=req(path).read_text(errors='replace')
    assert text in body, f"{path} missing: {text}"

required=[
    'RELEASE_NOTES_V2300.md',
    'PLATFORM_CORE_V2300_INSTALL_AND_TEST.md',
    'PLATFORM_CORE_V2300_VISUALIZATION_RENDERER_REGISTRY_AUDIT.md',
    'PLATFORM_CORE_V2300_TERMINAL_COMMANDS.txt',
    'docs/VISUALIZATION_SPEC_RENDERER_REGISTRY_V2300.md',
    'backend/app/services/visualization_registry.py',
    'backend/app/routers/visualization_registry.py',
    'backend/tests/test_visualization_spec_renderer_registry_v2300.py',
    'backend/scripts/validate_visualization_spec_renderer_registry.py',
    'backend/public_sdk/downloads/sc-platform-core-public-python-v2.30.0.zip',
    'backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.30.0.zip',
    'deploy_and_validate_platform_core_v2_30_0_macos.sh',
    'PUSH_PLATFORM_CORE_V2300_FINAL.sh',
    'DEPLOY_PLATFORM_CORE_V2300_CONTABO.sh',
    'platform-core-v2300.env.example',
]
for path in required: req(path)

has('backend/app/config.py','version: str = "2.30.0"')
has('backend/app/config.py','visualization_renderer_registry_enabled: bool = True')
has('backend/app/migrations.py','("0033", "Immutable visualization specifications')
has('backend/app/main.py','visualization_registry.router')
has('backend/app/main.py','visualization_registry.public_router')
has('backend/app/routers/meta.py','"visualization_specification_renderer_registry"')
has('backend/app/services/visualization_registry.py','"renderer_execution_by_core": False')
has('backend/app/services/visualization_registry.py','"layout_execution_by_core": False')
has('backend/app/services/visualization_registry.py','"render_output_storage_by_core": False')
has('backend/app/services/visualization_registry.py','"selection_is_advisory": True')
has('backend/app/services/visual_reasoning.py','"renderer_registry_in_core": True')
has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.30.0')
has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','sc_platform_core_visualization_registry_status')
has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Platform Core backend URL is not configured.')
has('wordpress-plugin/sustainable-catalyst-platform-core/readme.txt','Stable tag: 2.30.0')
has('render.yaml','SustainableCatalystPlatformCore/2.30.0')
has('backend/.env.example','SC_CORE_VISUALIZATION_RENDERER_REGISTRY_ENABLED=true')
has('README.md','# Sustainable Catalyst Platform Core v2.30.0')
has('README.md','Next planned: **v2.31.0 — System Maps**')
has('docs/ROADMAP.md','## v2.30.0 — Visualization Specification & Renderer Registry')
has('CHANGELOG.md','## 2.30.0 — 2026-09-11')
has('backend/public_sdk/javascript/package.json','"version": "2.30.0"')
has('backend/public_sdk/python/pyproject.toml','version = "2.30.0"')
has('backend/public_sdk/javascript/index.mjs','visualizationReadiness()')
has('backend/public_sdk/python/sc_platform_core_public/client.py','visualization_readiness')
has('DEPLOY_PLATFORM_CORE_V2300_CONTABO.sh','compose.yml -f compose.vps.yml')
has('DEPLOY_PLATFORM_CORE_V2300_CONTABO.sh','migration 0033')
has('DEPLOY_PLATFORM_CORE_V2300_CONTABO.sh','https://core.sustainablecatalyst.com/v1/visualization/readiness')

for name in (
    'visualization-specification-v1.schema.json','renderer-definition-v1.schema.json',
    'renderer-version-v1.schema.json','renderer-compatibility-rule-v1.schema.json','renderer-resolution-v1.schema.json',
):
    data=json.loads(req(f'schemas/{name}').read_text())
    assert data['$schema'].endswith('2020-12/schema')
    assert data['type']=='object'

for zpath in (
    'backend/public_sdk/downloads/sc-platform-core-public-python-v2.30.0.zip',
    'backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.30.0.zip',
):
    with ZipFile(req(zpath)) as zf:
        assert zf.testzip() is None, f'bad SDK zip: {zpath}'

models=req('backend/app/models.py').read_text()
for cls in (
    'VisualizationSpecificationRecord','RendererDefinitionRecord','RendererVersionRecord',
    'RendererCompatibilityRuleRecord','RendererResolutionRecord',
):
    assert f'class {cls}(Base):' in models

migrations=req('backend/app/migrations.py').read_text()
for key in ('contract.d3','contract.vega-lite','contract.plotly','contract.maplibre'):
    assert key in migrations
assert 'installed_runtime_asserted": False' in migrations

print('PASS - v2.30.0 Visualization Specification & Renderer Registry release contract')
