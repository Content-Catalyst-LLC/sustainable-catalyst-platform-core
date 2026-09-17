#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def req(x):
 p=ROOT/x; assert p.is_file(),f"missing required file: {x}"; return p
def has(x,t): assert t in req(x).read_text(errors='replace'),f"{x} missing: {t}"
for x in [
'RELEASE_NOTES_V2320.md','PLATFORM_CORE_V2320_INSTALL_AND_TEST.md','PLATFORM_CORE_V2320_FLOW_MAPS_AUDIT.md','PLATFORM_CORE_V2320_TERMINAL_COMMANDS.txt',
'docs/FLOW_MAPS_V2320.md','backend/app/services/flow_maps.py','backend/app/routers/flow_maps.py','backend/tests/test_flow_maps_v2320.py','backend/scripts/validate_flow_maps.py',
'deploy_and_validate_platform_core_v2_32_0_macos.sh','PUSH_PLATFORM_CORE_V2320_FINAL.sh','DEPLOY_PLATFORM_CORE_V2320_CONTABO.sh','platform-core-v2320.env.example',
'backend/public_sdk/downloads/sc-platform-core-public-python-v2.32.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.32.0.zip']:
 req(x)
has('backend/app/config.py','version: str = "2.32.0"')
has('backend/app/migrations.py','("0035", "Governed Flow Maps')
has('backend/app/main.py','flow_maps.router')
has('backend/app/routers/meta.py','"flow_maps"')
has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.32.0')
has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','sc_platform_core_flow_maps_status')
has('wordpress-plugin/sustainable-catalyst-platform-core/readme.txt','Stable tag: 2.32.0')
has('backend/public_sdk/javascript/package.json','"version": "2.32.0"')
has('backend/public_sdk/python/pyproject.toml','version = "2.32.0"')
models=req('backend/app/models.py').read_text()
for cls in ['FlowMapRecord','FlowMapChannelRecord','FlowMapFlowRecord','FlowMapNodeStateRecord','FlowMapViewRecord']:
 assert f'class {cls}(Base):' in models
for name in ['flow-map-v1.schema.json','flow-map-channel-v1.schema.json','flow-map-flow-v1.schema.json','flow-map-node-state-v1.schema.json','flow-map-view-v1.schema.json']:
 d=json.loads(req('schemas/'+name).read_text()); assert d['type']=='object'
has('README.md','Next planned: **v2.33.0 — Scenario Landscapes**')
print('PASS - v2.32.0 Flow Maps release contract')
