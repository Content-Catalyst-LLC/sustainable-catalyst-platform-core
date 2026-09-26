#!/usr/bin/env bash
set -euo pipefail

BASE="${SC_GRETL_RUNTIME_URL:-http://127.0.0.1:18097}"

echo "=== VERIFY GRETL/HANSL RUNTIME HEALTH ==="
curl -fsS "$BASE/health" | tee /tmp/sc-gretl-health.json | python3 -m json.tool

python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-gretl-health.json'))
assert d['ok'] is True
assert d['runtime_id']=='sc-runtime-gretl'
assert d['version']=='1.0.0'
assert d['gretl_version']=='2023c'
assert d['gretl_package_version']=='2023c-2.1build3'
print('PASS - gretl/hansl runtime health')
PY

echo "=== VERIFY CORE ADAPTER DESCRIPTOR ==="
curl -fsS "$BASE/v1/core-adapter" | tee /tmp/sc-gretl-adapter.json | python3 -m json.tool

python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-gretl-adapter.json'))
assert d['adapter_id']=='adapter:sc-runtime-gretl'
assert d['provider_id']=='sc-runtime-gretl'
assert d['provider_version']=='1.0.0'
assert d['language']=='hansl'
assert set(d['capabilities'])=={
  'ols','robust_ols','logit','probit',
  'descriptive_summary','correlation_matrix'
}
assert d['boundaries']['arbitrary_hansl_source'] is False
assert d['boundaries']['shell_execution'] is False
print('PASS - gretl/hansl adapter descriptor')
PY

echo "=== BOUNDED NATIVE GRETL OLS SMOKE TEST ==="
cat >/tmp/sc-gretl-smoke-request.json <<'JSON'
{
  "operation": "ols",
  "columns": {
    "y": [1.0, 2.0, 3.0, 4.0, 5.0],
    "x": [0.0, 1.0, 2.0, 3.0, 4.0]
  },
  "dependent_variable": "y",
  "predictors": ["x"],
  "include_constant": true,
  "variables": [],
  "timeout_seconds": 120,
  "job_ref": "job:gretl-runtime-smoke",
  "environment_ref": "environment-package:gretl-hansl-runtime:v1"
}
JSON

curl -fsS -X POST \
  "$BASE/v1/core-adapter/prepare" \
  -H "Content-Type: application/json" \
  --data-binary @/tmp/sc-gretl-smoke-request.json \
  | tee /tmp/sc-gretl-prepare.json \
  | python3 -m json.tool

RUN_ID="$(python3 - <<'PY'
import json
print(json.load(open('/tmp/sc-gretl-prepare.json'))['run_id'])
PY
)"

python3 - "$RUN_ID" <<'PY'
import json,sys
json.dump({'run_id':sys.argv[1]}, open('/tmp/sc-gretl-run.json','w'))
PY

curl -fsS -X POST \
  "$BASE/v1/core-adapter/execute" \
  -H "Content-Type: application/json" \
  --data-binary @/tmp/sc-gretl-run.json \
  | tee /tmp/sc-gretl-execute.json \
  | python3 -m json.tool

python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-gretl-execute.json'))
assert d['status']=='completed'
r=d['result']
assert r['operation']=='ols'
assert r['observation_count']==5
coef=r['coefficients']
assert 'const' in coef and 'x' in coef, coef
assert abs(coef['const']-1.0) < 1e-8, coef
assert abs(coef['x']-1.0) < 1e-8, coef
assert len(r['artifacts'])==3
print('PASS - native gretl OLS smoke test')
PY

echo "PASS - SUSTAINABLE CATALYST GRETL/HANSL RUNTIME v1.0.0 VERIFIED"
