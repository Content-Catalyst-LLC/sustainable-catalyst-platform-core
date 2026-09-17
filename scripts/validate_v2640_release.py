#!/usr/bin/env python3
from pathlib import Path
import ast,json
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text();MIG=(ROOT/'backend/app/migrations.py').read_text();MAIN=(ROOT/'backend/app/main.py').read_text();WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text();PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text();PYPROJ=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text();SVC=(ROOT/'backend/app/services/visual_linked_views.py').read_text();ROUTER=(ROOT/'backend/app/routers/visual_linked_views.py').read_text();MODELS=(ROOT/'backend/app/models.py').read_text();SCHEMA=json.loads((ROOT/'schemas/linked-views-cross-filtering-v1.schema.json').read_text())
assert 'version: str = "2.64.0"' in CFG and 'SustainableCatalystPlatformCore/2.64.0' in CFG
assert 'visual_linked_views' in MAIN and 'linked_views_cross_filtering_enabled' in CFG
module=ast.parse(MIG);migrations=None
for n in module.body:
    if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets):migrations=ast.literal_eval(n.value)
assert migrations and migrations[-1][0]=='0068' and len(migrations[-1][1])<=300
assert 'Version: 2.64.0' in WP and 'sc_platform_core_linked_views_status' in WP
assert '"version": "2.64.0"' in PKG and 'version = "2.64.0"' in PYPROJ
for marker in ('VisualLinkPolicyRecord','VisualSelectionSetRecord','VisualCrossFilterRecord','VisualBrushRangeRecord','VisualFocusHighlightRecord','VisualPropagationRecord','VisualLinkedViewSnapshotRecord'):assert marker in MODELS,marker
for marker in ('link_policy_registry_by_core','selection_set_registry_by_core','cross_filter_predicate_registry_by_core','immutable_linked_view_snapshots_by_core','query_execution_by_core','data_filtering_by_core','automatic_cross_filter_execution'):assert marker in SVC,marker
for marker in ('/link-policies','/selection-sets','/cross-filters','/brush-ranges','/focus-highlights','/propagations','/snapshots'):assert marker in ROUTER,marker
assert SCHEMA['properties']['contract']['const']=='sc.visual-runtime.linked-views.v1'
print(f'PASS - dependency-free release contract; migration ledger max=300, 0068 chars={len(migrations[-1][1])}')
print('PASS - v2.64.0 Linked Views & Cross-Filtering release contract')
