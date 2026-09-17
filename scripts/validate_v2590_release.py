#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PY=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text(); META=(ROOT/'backend/app/routers/meta.py').read_text(); SVC=(ROOT/'backend/app/services/predictive_intelligence.py').read_text(); ROUTER=(ROOT/'backend/app/routers/predictive_intelligence.py').read_text()
assert 'version: str = "2.59.0"' in CFG and 'SustainableCatalystPlatformCore/2.59.0' in CFG
assert 'predictive_intelligence' in MAIN and 'predictive_decision_intelligence' in META
assert '("0063"' in MIG
module=ast.parse(MIG); migrations=None
for n in module.body:
    if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations and migrations[-1][0]=='0063' and len(migrations[-1][1])<=300
assert 'Version: 2.59.0' in WP and 'sc_platform_core_predictive_decision_status' in WP
assert '"version": "2.59.0"' in PKG and 'version = "2.59.0"' in PY
for name in ('sc-platform-core-public-python-v2.59.0.zip','sc-platform-core-public-javascript-v2.59.0.zip'): assert (ROOT/'backend/public_sdk/downloads'/name).is_file(),name
for name in ('predictive-decision-study-v1.schema.json','predictive-decision-evidence-v1.schema.json','predictive-decision-package-v1.schema.json'): assert (ROOT/'schemas'/name).is_file(),name
for marker in ('predictive_decision_study_registry_by_core','decision_option_registry_by_core','decision_criterion_registry_by_core','decision_evidence_binding_registry_by_core','decision_scenario_assessment_registry_by_core','decision_evaluation_evidence_registry_by_core','decision_handoff_registry_by_core','reproducible_predictive_decision_packages_by_core','decision_ranking_by_core','decision_recommendation_by_core','decision_optimization_by_core','automatic_action_selection'): assert marker in SVC,marker
for marker in ('/decision-studies','/options','/criteria','/evidence-bindings','/scenario-assessments','/evaluations','/handoffs'): assert marker in ROUTER,marker
print(f'PASS - dependency-free release contract; migration ledger max=300, 0063 chars={len(migrations[-1][1])}')
print('PASS - v2.59.0 Predictive Decision Intelligence release contract')
