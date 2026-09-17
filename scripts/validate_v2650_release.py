#!/usr/bin/env python3
from pathlib import Path
import ast,json
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text();MIG=(ROOT/'backend/app/migrations.py').read_text();MAIN=(ROOT/'backend/app/main.py').read_text();WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text();PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text();PYPROJ=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text();SVC=(ROOT/'backend/app/services/visual_query_exploration.py').read_text();ROUTER=(ROOT/'backend/app/routers/visual_query_exploration.py').read_text();MODELS=(ROOT/'backend/app/models.py').read_text();SCHEMA=json.loads((ROOT/'schemas/visual-query-exploration-v1.schema.json').read_text())
assert 'version: str = "2.65.0"' in CFG and 'SustainableCatalystPlatformCore/2.65.0' in CFG
assert 'visual_query_exploration' in MAIN and 'visual_query_exploration_enabled' in CFG
module=ast.parse(MIG);migrations=None
for n in module.body:
    if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets):migrations=ast.literal_eval(n.value)
assert migrations and migrations[-1][0]=='0069' and len(migrations[-1][1])<=300
assert 'Version: 2.65.0' in WP and 'sc_platform_core_visual_query_status' in WP
assert '"version": "2.65.0"' in PKG and 'version = "2.65.0"' in PYPROJ
for marker in ('VisualExplorationSessionRecord','VisualQueryTargetRecord','VisualQueryRequestRecord','VisualQueryPredicateRecord','VisualTraversalRequestRecord','VisualQueryResultBindingRecord','VisualExplorationStateRecord','VisualQuerySnapshotRecord'):assert marker in MODELS,marker
for marker in ('visual_query_request_registry_by_core','visual_traversal_request_registry_by_core','visual_query_result_evidence_binding_by_core','immutable_visual_query_snapshots_by_core','query_execution_by_core','graph_traversal_by_core','result_ranking_by_core'):assert marker in SVC,marker
for marker in ('/sessions','/targets','/queries','/predicates','/traversals','/results','/saved-states','/snapshots'):assert marker in ROUTER,marker
assert SCHEMA['properties']['contract']['const']=='sc.visual-runtime.visual-query.v1'
print(f'PASS - dependency-free release contract; migration ledger max=300, 0069 chars={len(migrations[-1][1])}')
print('PASS - v2.65.0 Visual Query & Exploration Engine release contract')
