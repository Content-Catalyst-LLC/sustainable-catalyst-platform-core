#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PY=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text(); META=(ROOT/'backend/app/routers/meta.py').read_text(); SVC=(ROOT/'backend/app/services/predictive_intelligence.py').read_text(); ROUTER=(ROOT/'backend/app/routers/predictive_intelligence.py').read_text(); MODELS=(ROOT/'backend/app/models.py').read_text()
assert 'version: str = "2.60.0"' in CFG and 'SustainableCatalystPlatformCore/2.60.0' in CFG
assert 'predictive_intelligence' in MAIN and 'reproducible_predictive_intelligence_packages' in META
module=ast.parse(MIG); migrations=None
for n in module.body:
    if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations and migrations[-1][0]=='0064' and len(migrations[-1][1])<=300
assert 'Version: 2.60.0' in WP and 'sc_platform_core_predictive_package_status' in WP
assert '"version": "2.60.0"' in PKG and 'version = "2.60.0"' in PY
for name in ('sc-platform-core-public-python-v2.60.0.zip','sc-platform-core-public-javascript-v2.60.0.zip'): assert (ROOT/'backend/public_sdk/downloads'/name).is_file(),name
assert 'PredictiveIntelligencePackageRecord' in MODELS and 'predictive_intelligence_package_snapshots' in MODELS
for name in ('predictive-reproducible-package-v1.schema.json','predictive-package-component-v1.schema.json','predictive-package-snapshot-v1.schema.json'): assert (ROOT/'schemas'/name).is_file(),name
for marker in ('reproducible_predictive_package_registry_by_core','predictive_package_component_manifest_by_core','predictive_package_artifact_registry_by_core','predictive_package_environment_registry_by_core','predictive_package_verification_registry_by_core','predictive_package_review_registry_by_core','immutable_predictive_package_snapshots_by_core','cross_predictive_layer_packaging_by_core','automatic_reproduction_by_core'): assert marker in SVC,marker
for marker in ('/packages','/components','/artifacts','/environments','/verifications','/reviews','/snapshots'): assert marker in ROUTER,marker
print(f'PASS - dependency-free release contract; migration ledger max=300, 0064 chars={len(migrations[-1][1])}')
print('PASS - v2.60.0 Reproducible Predictive Intelligence Packages release contract')
