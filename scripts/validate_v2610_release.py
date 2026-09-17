#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PYPROJ=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text(); META=(ROOT/'backend/app/routers/meta.py').read_text(); SVC=(ROOT/'backend/app/services/visual_runtime.py').read_text(); ROUTER=(ROOT/'backend/app/routers/visual_runtime.py').read_text(); MODELS=(ROOT/'backend/app/models.py').read_text()
assert 'version: str = "2.61.0"' in CFG and 'SustainableCatalystPlatformCore/2.61.0' in CFG
assert 'visual_runtime' in MAIN and 'visual_reasoning_runtime_scene_graph' in META
module=ast.parse(MIG); migrations=None
for n in module.body:
    if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations and migrations[-1][0]=='0065' and len(migrations[-1][1])<=300
assert 'Version: 2.61.0' in WP and 'sc_platform_core_visual_runtime_status' in WP
assert '"version": "2.61.0"' in PKG and 'version = "2.61.0"' in PYPROJ
for name in ('sc-platform-core-public-python-v2.61.0.zip','sc-platform-core-public-javascript-v2.61.0.zip'): assert (ROOT/'backend/public_sdk/downloads'/name).is_file(),name
for marker in ('VisualRuntimeSceneRecord','VisualRuntimeNodeRecord','VisualRuntimeEdgeRecord','VisualRuntimeLayerRecord','VisualRuntimeAnnotationRecord','VisualRuntimeViewRecord','VisualRuntimeBindingRecord','VisualRuntimeSnapshotRecord'): assert marker in MODELS,marker
assert (ROOT/'schemas/visual-runtime-scene-v1.schema.json').is_file()
for marker in ('scene_registry_by_core','scene_graph_node_registry_by_core','scene_graph_edge_registry_by_core','viewport_selection_state_by_core','cross_product_visual_bindings_by_core','immutable_scene_snapshots_by_core','layout_computation_by_core','canvas_svg_webgl_rendering_by_core','visual_inference_by_core'): assert marker in SVC,marker
for marker in ("/scenes","/layers","/nodes","/edges","/annotations","/views","/bindings","/snapshots","/bundle"): assert marker in ROUTER,marker
print(f'PASS - dependency-free release contract; migration ledger max=300, 0065 chars={len(migrations[-1][1])}')
print('PASS - v2.61.0 Visual Reasoning Runtime & Scene Graph release contract')
