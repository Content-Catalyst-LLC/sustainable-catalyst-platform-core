#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PY=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text(); META=(ROOT/'backend/app/routers/meta.py').read_text()
assert 'version: str = "2.53.0"' in CFG and 'SustainableCatalystPlatformCore/2.53.0' in CFG
assert 'predictive_intelligence' in MAIN and 'predictive_time_series_forecasting_backtesting' in META
assert '("0057"' in MIG
module=ast.parse(MIG); migrations=None
for n in module.body:
    if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations and migrations[-1][0]=='0057' and len(migrations[-1][1])<=300
assert 'Version: 2.53.0' in WP and 'sc_platform_core_predictive_backtesting_status' in WP
assert '"version": "2.53.0"' in PKG and 'version = "2.53.0"' in PY
for name in ('sc-platform-core-public-python-v2.53.0.zip','sc-platform-core-public-javascript-v2.53.0.zip'): assert (ROOT/'backend/public_sdk/downloads'/name).is_file()
for name in ('predictive-time-series-dataset-v1.schema.json','predictive-backtest-plan-v1.schema.json','predictive-backtest-package-v1.schema.json'): assert (ROOT/'schemas'/name).is_file()
print(f'PASS - dependency-free release contract; migration ledger max=300, 0057 chars={len(migrations[-1][1])}')
print('PASS - v2.53.0 Time-Series Forecasting & Backtesting release contract')
