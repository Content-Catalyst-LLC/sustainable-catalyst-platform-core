#!/usr/bin/env bash
set -euo pipefail

BASE="${SC_OCTAVE_RUNTIME_URL:-http://127.0.0.1:18096}"

echo "=== VERIFY OCTAVE RUNTIME HEALTH ==="
curl -fsS "$BASE/health" | tee /tmp/sc-octave-health.json | python3 -m json.tool

python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-octave-health.json'))
assert d['ok'] is True
assert d['runtime_id']=='sc-runtime-octave'
assert d['version']=='1.0.0'
assert d['octave_version']=='8.4.0'
print('PASS - Octave runtime health')
PY

echo "=== VERIFY CORE ADAPTER DESCRIPTOR ==="
curl -fsS "$BASE/v1/core-adapter" | tee /tmp/sc-octave-adapter.json | python3 -m json.tool

python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-octave-adapter.json'))
assert d['adapter_id']=='adapter:sc-runtime-octave'
assert d['provider_id']=='sc-runtime-octave'
assert set(d['capabilities'])=={
  'matrix_multiply','linear_solve','eigenvalues','svd','fft','polynomial_roots'
}
assert d['boundaries']['arbitrary_octave_source'] is False
assert d['boundaries']['shell_execution'] is False
print('PASS - Octave adapter descriptor')
PY

echo "=== BOUNDED NATIVE OCTAVE LINEAR-SOLVE SMOKE TEST ==="
cat >/tmp/sc-octave-smoke-request.json <<'JSON'
{
  "operation": "linear_solve",
  "values": {
    "A": [[3.0, 1.0], [1.0, 2.0]],
    "b": [9.0, 8.0]
  },
  "precision_digits": 15,
  "timeout_seconds": 120,
  "job_ref": "job:octave-runtime-smoke",
  "environment_ref": "environment-package:octave-runtime:v1"
}
JSON

curl -fsS -X POST \
  "$BASE/v1/core-adapter/prepare" \
  -H "Content-Type: application/json" \
  --data-binary @/tmp/sc-octave-smoke-request.json \
  | tee /tmp/sc-octave-prepare.json \
  | python3 -m json.tool

RUN_ID="$(python3 - <<'PY'
import json
print(json.load(open('/tmp/sc-octave-prepare.json'))['run_id'])
PY
)"

python3 - "$RUN_ID" <<'PY'
import json,sys
json.dump({'run_id':sys.argv[1]}, open('/tmp/sc-octave-run.json','w'))
PY

curl -fsS -X POST \
  "$BASE/v1/core-adapter/execute" \
  -H "Content-Type: application/json" \
  --data-binary @/tmp/sc-octave-run.json \
  | tee /tmp/sc-octave-execute.json \
  | python3 -m json.tool

python3 - <<'PY'
import json, math
d=json.load(open('/tmp/sc-octave-execute.json'))
assert d['status']=='completed'
r=d['result']
assert r['operation']=='linear_solve'
v=r['result']['value']
if isinstance(v[0], list):
    v=[x[0] for x in v]
assert len(v)==2
assert abs(v[0]-2.0) < 1e-9
assert abs(v[1]-3.0) < 1e-9
assert r['result']['residual_norm'] < 1e-9
assert len(r['artifacts'])==2
print('PASS - native Octave linear solve smoke test')
PY

echo "PASS - SUSTAINABLE CATALYST OCTAVE RUNTIME v1.0.0 VERIFIED"
