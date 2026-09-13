#!/usr/bin/env python3
from pathlib import Path
import ast, hashlib, json, re, sys
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text()
MIG=(ROOT/'backend/app/migrations.py').read_text()
MOD=(ROOT/'backend/app/models.py').read_text()
MAIN=(ROOT/'backend/app/main.py').read_text()
ROUTER=(ROOT/'backend/app/routers/spatial_temporal.py').read_text()
SERVICE=(ROOT/'backend/app/services/spatial_temporal.py').read_text()
WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text()
assert 'version: str = "2.38.0"' in CFG
assert 'spatial_temporal_visual_reasoning_enabled' in CFG
# Parse MIGRATIONS without importing sqlalchemy/app modules.
tree=ast.parse(MIG); migrations=None
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in node.targets):
        migrations=ast.literal_eval(node.value); break
assert migrations is not None
versions=[v for v,_ in migrations]; assert versions[-1]=='0042' and len(versions)==len(set(versions))
d=dict(migrations); assert len(d['0040'])<=300 and len(d['0041'])<=300 and len(d['0042'])<=300
for name in ['SpatialTemporalSceneRecord','SpatialFeatureRecord','TemporalEventRecord','TrajectoryRecord','TrajectoryPointRecord','SpatialTemporalChangeRecord','SpatialTemporalViewRecord']:
    assert f'class {name}' in MOD
assert "prefix='/v1/spatial-temporal'" in ROUTER and "prefix='/api/v1/spatial-temporal'" in ROUTER
assert 'spatial_temporal.router' in MAIN and 'spatial_temporal.public_router' in MAIN
for boundary in ['spatial_analysis_by_core','raster_processing_by_core','remote_sensing_by_core','temporal_model_execution_by_core','automatic_truth_promotion']:
    assert boundary in SERVICE
assert "Version: 2.38.0" in WP and 'sc_platform_core_spatial_temporal_status' in WP
print(f"PASS - dependency-free release contract; migration ledger max=300, 0042 chars={len(d['0042'])}")
print('PASS - v2.38.0 Spatial & Temporal Visual Reasoning release contract')
