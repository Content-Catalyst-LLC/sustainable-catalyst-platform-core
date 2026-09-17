#!/usr/bin/env python3
from pathlib import Path
import ast,json
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PY=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text(); META=(ROOT/'backend/app/routers/meta.py').read_text(); SVC=(ROOT/'backend/app/services/predictive_intelligence.py').read_text(); ROUTER=(ROOT/'backend/app/routers/predictive_intelligence.py').read_text()
assert 'version: str = "2.57.0"' in CFG and 'SustainableCatalystPlatformCore/2.57.0' in CFG
assert 'predictive_intelligence' in MAIN and 'predictive_spatial_temporal_intelligence' in META
assert '("0061"' in MIG
module=ast.parse(MIG); migrations=None
for n in module.body:
    if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations and migrations[-1][0]=='0061' and len(migrations[-1][1])<=300
assert 'Version: 2.57.0' in WP and 'sc_platform_core_predictive_spatial_temporal_status' in WP
assert '"version": "2.57.0"' in PKG and 'version = "2.57.0"' in PY
for name in ('sc-platform-core-public-python-v2.57.0.zip','sc-platform-core-public-javascript-v2.57.0.zip'): assert (ROOT/'backend/public_sdk/downloads'/name).is_file(),name
for name in ('predictive-spatial-temporal-study-v1.schema.json','predictive-spatial-temporal-evidence-v1.schema.json','predictive-spatial-temporal-package-v1.schema.json'): assert (ROOT/'schemas'/name).is_file(),name
for marker in ('spatial_temporal_study_registry_by_core','spatial_unit_registry_by_core','spatial_temporal_forecast_provenance_by_core','propagation_evidence_registry_by_core','hotspot_evidence_registry_by_core','spatial_interpolation_by_core','trajectory_prediction_by_core'): assert marker in SVC,marker
for marker in ('/spatial-temporal-studies','/units','/forecasts','/propagation-evidence','/hotspot-evidence'): assert marker in ROUTER,marker
print(f'PASS - dependency-free release contract; migration ledger max=300, 0061 chars={len(migrations[-1][1])}')
print('PASS - v2.57.0 Spatial-Temporal Predictive Intelligence release contract')
