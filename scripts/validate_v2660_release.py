#!/usr/bin/env python3
from pathlib import Path
import ast,json
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text();MIG=(ROOT/'backend/app/migrations.py').read_text();MAIN=(ROOT/'backend/app/main.py').read_text();WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text();PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text();PYPROJ=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text();SVC=(ROOT/'backend/app/services/visual_model_construction.py').read_text();ROUTER=(ROOT/'backend/app/routers/visual_model_construction.py').read_text();MODELS=(ROOT/'backend/app/models.py').read_text();SCHEMA=json.loads((ROOT/'schemas/visual-model-construction-v1.schema.json').read_text())
assert 'version: str = "2.66.0"' in CFG and 'SustainableCatalystPlatformCore/2.66.0' in CFG
assert 'visual_model_construction' in MAIN and 'visual_model_construction_enabled' in CFG
module=ast.parse(MIG);migrations=None
for n in module.body:
    if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets):migrations=ast.literal_eval(n.value)
assert migrations and migrations[-1][0]=='0070' and len(migrations[-1][1])<=300
assert 'Version: 2.66.0' in WP and 'sc_platform_core_visual_model_status' in WP
assert '"version": "2.66.0"' in PKG and 'version = "2.66.0"' in PYPROJ
for marker in ('VisualModelConstructionRecord','VisualModelComponentRecord','VisualModelRelationshipRecord','VisualModelAssumptionRecord','VisualModelConstraintRecord','VisualModelInterventionRecord','VisualModelHandoffRecord','VisualModelSnapshotRecord'):assert marker in MODELS,marker
for marker in ('visual_model_construction_registry_by_core','visual_model_component_registry_by_core','visual_model_relationship_registry_by_core','visual_model_handoff_registry_by_core','immutable_visual_model_snapshots_by_core','equation_execution_by_core','constraint_optimization_by_core','simulation_execution_by_core','model_execution_by_core'):assert marker in SVC,marker
for marker in ('/constructions','/components','/relationships','/assumptions','/constraints','/interventions','/handoffs','/snapshots'):assert marker in ROUTER,marker
assert SCHEMA['properties']['contract']['const']=='sc.visual-runtime.model-construction.v1'
print(f'PASS - dependency-free release contract; migration ledger max=300, 0070 chars={len(migrations[-1][1])}')
print('PASS - v2.66.0 Visual Model Construction release contract')
