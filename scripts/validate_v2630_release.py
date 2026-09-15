#!/usr/bin/env python3
from pathlib import Path
import ast,json
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text();MIG=(ROOT/'backend/app/migrations.py').read_text();MAIN=(ROOT/'backend/app/main.py').read_text();WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text();PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text();PYPROJ=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text();SVC=(ROOT/'backend/app/services/visual_grammar.py').read_text();ROUTER=(ROOT/'backend/app/routers/visual_grammar.py').read_text();MODELS=(ROOT/'backend/app/models.py').read_text();SCHEMA=json.loads((ROOT/'schemas/analytical-visualization-grammar-v1.schema.json').read_text())
assert 'version: str = "2.63.0"' in CFG and 'SustainableCatalystPlatformCore/2.63.0' in CFG
assert 'visual_grammar' in MAIN and 'analytical_visualization_grammar_enabled' in CFG
module=ast.parse(MIG);migrations=None
for n in module.body:
    if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets):migrations=ast.literal_eval(n.value)
assert migrations and migrations[-1][0]=='0067' and len(migrations[-1][1])<=300
assert 'Version: 2.63.0' in WP and 'sc_platform_core_visual_grammar_status' in WP
assert '"version": "2.63.0"' in PKG and 'version = "2.63.0"' in PYPROJ
for marker in ('VisualGrammarSpecificationRecord','VisualGrammarDataBindingRecord','VisualGrammarMarkRecord','VisualGrammarEncodingRecord','VisualGrammarScaleRecord','VisualGrammarTransformRecord','VisualGrammarGuideRecord','VisualGrammarSnapshotRecord'):assert marker in MODELS,marker
for marker in ('grammar_specification_registry_by_core','encoding_registry_by_core','transform_spec_registry_by_core','immutable_grammar_snapshots_by_core','mark_drawing_by_core','automatic_chart_generation_by_core'):assert marker in SVC,marker
for marker in ('/specifications','/data-bindings','/marks','/encodings','/scales','/transforms','/guides','/snapshots'):assert marker in ROUTER,marker
assert SCHEMA['properties']['contract']['const']=='sc.visual-runtime.grammar.v1'
print(f'PASS - dependency-free release contract; migration ledger max=300, 0067 chars={len(migrations[-1][1])}')
print('PASS - v2.63.0 Analytical Visualization Grammar release contract')
