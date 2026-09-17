#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PYPROJ=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text(); SVC=(ROOT/'backend/app/services/visual_composition.py').read_text(); ROUTER=(ROOT/'backend/app/routers/visual_composition.py').read_text(); MODELS=(ROOT/'backend/app/models.py').read_text()
assert 'version: str = "2.62.0"' in CFG and 'SustainableCatalystPlatformCore/2.62.0' in CFG
assert 'visual_composition' in MAIN and 'interactive_renderer_composition_enabled' in CFG
module=ast.parse(MIG); migrations=None
for n in module.body:
    if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations and migrations[-1][0]=='0066' and len(migrations[-1][1])<=300
assert 'Version: 2.62.0' in WP and 'sc_platform_core_visual_composition_status' in WP
assert '"version": "2.62.0"' in PKG and 'version = "2.62.0"' in PYPROJ
for marker in ('VisualRendererProfileRecord','VisualViewCompositionRecord','VisualViewAssignmentRecord','VisualViewLinkGroupRecord','VisualInteractionStateRecord','VisualRendererResolutionRecord','VisualCompositionSnapshotRecord'): assert marker in MODELS,marker
for marker in ('view_composition_registry_by_core','renderer_capability_resolution_by_core','immutable_composition_snapshots_by_core','svg_canvas_webgl_drawing_by_core','automatic_renderer_execution'): assert marker in SVC,marker
for marker in ('/renderers','/compositions','/assignments','/link-groups','/interaction-states','/renderer-resolutions','/snapshots'): assert marker in ROUTER,marker
print(f'PASS - dependency-free release contract; migration ledger max=300, 0066 chars={len(migrations[-1][1])}')
print('PASS - v2.62.0 Interactive Renderer & View Composition release contract')
