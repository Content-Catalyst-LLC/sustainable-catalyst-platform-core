#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PY=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text(); META=(ROOT/'backend/app/routers/meta.py').read_text(); SVC=(ROOT/'backend/app/services/predictive_intelligence.py').read_text()
assert 'version: str = "2.55.0"' in CFG and 'SustainableCatalystPlatformCore/2.55.0' in CFG
assert 'predictive_intelligence' in MAIN and 'predictive_ensembles_model_comparison' in META
assert '("0059"' in MIG
module=ast.parse(MIG); migrations=None
for n in module.body:
    if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations and migrations[-1][0]=='0059' and len(migrations[-1][1])<=300
assert 'Version: 2.55.0' in WP and 'sc_platform_core_predictive_ensembles_status' in WP
assert '"version": "2.55.0"' in PKG and 'version = "2.55.0"' in PY
for name in ('sc-platform-core-public-python-v2.55.0.zip','sc-platform-core-public-javascript-v2.55.0.zip'): assert (ROOT/'backend/public_sdk/downloads'/name).is_file()
for name in ('predictive-ensemble-v1.schema.json','predictive-model-comparison-v1.schema.json','predictive-model-comparison-package-v1.schema.json'): assert (ROOT/'schemas'/name).is_file()
for marker in ('ensemble_registry_by_core','ensemble_weight_optimization_by_core','reproducible_model_comparison_packages_by_core'): assert marker in SVC
print(f'PASS - dependency-free release contract; migration ledger max=300, 0059 chars={len(migrations[-1][1])}')
print('PASS - v2.55.0 Predictive Ensembles & Model Comparison release contract')
