#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PY=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text(); META=(ROOT/'backend/app/routers/meta.py').read_text(); SVC=(ROOT/'backend/app/services/predictive_intelligence.py').read_text(); ROUTER=(ROOT/'backend/app/routers/predictive_intelligence.py').read_text()
assert 'version: str = "2.58.0"' in CFG and 'SustainableCatalystPlatformCore/2.58.0' in CFG
assert 'predictive_intelligence' in MAIN and 'predictive_causal_predictive_integration' in META
assert '("0062"' in MIG
module=ast.parse(MIG); migrations=None
for n in module.body:
    if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations and migrations[-1][0]=='0062' and len(migrations[-1][1])<=300
assert 'Version: 2.58.0' in WP and 'sc_platform_core_predictive_causal_status' in WP
assert '"version": "2.58.0"' in PKG and 'version = "2.58.0"' in PY
for name in ('sc-platform-core-public-python-v2.58.0.zip','sc-platform-core-public-javascript-v2.58.0.zip'): assert (ROOT/'backend/public_sdk/downloads'/name).is_file(),name
for name in ('predictive-causal-study-v1.schema.json','predictive-causal-evidence-v1.schema.json','predictive-causal-package-v1.schema.json'): assert (ROOT/'schemas'/name).is_file(),name
for marker in ('causal_predictive_study_registry_by_core','causal_variable_binding_registry_by_core','intervention_scenario_registry_by_core','counterfactual_forecast_provenance_by_core','causal_effect_evidence_registry_by_core','reproducible_causal_predictive_packages_by_core','causal_effect_estimation_by_core','counterfactual_execution_by_core','decision_optimization_by_core'): assert marker in SVC,marker
for marker in ('/causal-predictive-studies','/variable-bindings','/intervention-scenarios','/counterfactual-forecasts','/effect-evidence','/handoffs'): assert marker in ROUTER,marker
print(f'PASS - dependency-free release contract; migration ledger max=300, 0062 chars={len(migrations[-1][1])}')
print('PASS - v2.58.0 Causal-Predictive Integration release contract')
