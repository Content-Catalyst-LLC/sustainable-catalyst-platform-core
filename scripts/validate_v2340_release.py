#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def req(x):
    p=ROOT/x;assert p.is_file(),f'missing required file: {x}';return p
def has(x,t):assert t in req(x).read_text(errors='replace'),f'{x} missing: {t}'
for x in [
    'RELEASE_NOTES_V2340.md','PLATFORM_CORE_V2340_INSTALL_AND_TEST.md','PLATFORM_CORE_V2340_INTERACTIVE_MODEL_CANVAS_AUDIT.md','PLATFORM_CORE_V2340_TERMINAL_COMMANDS.txt',
    'docs/INTERACTIVE_MODEL_CANVAS_V2340.md','backend/app/services/model_canvas.py','backend/app/routers/model_canvas.py','backend/tests/test_interactive_model_canvas_v2340.py','backend/scripts/validate_model_canvas.py',
    'deploy_and_validate_platform_core_v2_34_0_macos.sh','PUSH_PLATFORM_CORE_V2340_FINAL.sh','DEPLOY_PLATFORM_CORE_V2340_CONTABO.sh','platform-core-v2340.env.example',
    'backend/public_sdk/downloads/sc-platform-core-public-python-v2.34.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.34.0.zip']:
    req(x)
has('backend/app/config.py','version: str = "2.34.0"')
has('backend/app/migrations.py','("0037", "Governed Interactive Model Canvas')
has('backend/app/main.py','model_canvas.router')
has('backend/app/routers/meta.py','"interactive_model_canvas"')
has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.34.0')
has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','sc_platform_core_model_canvas_status')
has('wordpress-plugin/sustainable-catalyst-platform-core/readme.txt','Stable tag: 2.34.0')
has('backend/public_sdk/javascript/package.json','"version": "2.34.0"')
has('backend/public_sdk/python/pyproject.toml','version = "2.34.0"')
models=req('backend/app/models.py').read_text()
for cls in ['ModelCanvasRecord','ModelCanvasNodeRecord','ModelCanvasEdgeRecord','ModelCanvasControlRecord','ModelCanvasStateRecord','ModelCanvasViewRecord']:
    assert f'class {cls}(Base):' in models
for name in ['model-canvas-v1.schema.json','model-canvas-node-v1.schema.json','model-canvas-edge-v1.schema.json','model-canvas-control-v1.schema.json','model-canvas-state-v1.schema.json','model-canvas-view-v1.schema.json']:
    d=json.loads(req('schemas/'+name).read_text());assert d['type']=='object'
has('README.md','Next planned: **v2.35.0 — Scenario Compute Engine**')
print('PASS - v2.34.0 Interactive Model Canvas release contract')
