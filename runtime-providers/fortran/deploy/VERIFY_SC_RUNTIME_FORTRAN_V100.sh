#!/usr/bin/env bash
set -euo pipefail
BASE="${SC_FORTRAN_RUNTIME_URL:-http://127.0.0.1:18099}"

echo "=== VERIFY FORTRAN RUNTIME HEALTH ==="
curl -fsS "$BASE/health" | tee /tmp/sc-fortran-health.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-fortran-health.json'))
assert d['ok'] is True
assert d['runtime_id']=='sc-runtime-fortran'
assert d['version']=='1.0.0'
assert d['gfortran_version']=='13.3.0'
assert d['gfortran_package_version']=='13.3.0-6ubuntu2~24.04.1'
print('PASS - Fortran runtime health')
PY

echo "=== VERIFY CORE ADAPTER DESCRIPTOR ==="
curl -fsS "$BASE/v1/core-adapter" | tee /tmp/sc-fortran-adapter.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-fortran-adapter.json'))
assert d['adapter_id']=='adapter:sc-runtime-fortran'
assert d['provider_id']=='sc-runtime-fortran'
assert d['provider_version']=='1.0.0'
assert d['language']=='fortran'
assert set(d['capabilities'])=={'dot_product','matrix_multiply','trapezoidal_integral','central_difference','rk4_linear_step','heat_step_1d'}
assert d['boundaries']['arbitrary_fortran_source'] is False
assert d['boundaries']['shell_execution'] is False
assert d['boundaries']['provider_managed_compilation'] is True
print('PASS - Fortran adapter descriptor')
PY

echo "=== BOUNDED NATIVE FORTRAN DOT-PRODUCT SMOKE TEST ==="
cat >/tmp/sc-fortran-smoke-request.json <<'JSON'
{
  "operation": "dot_product",
  "payload": {"a": [1.0,2.0,3.0], "b": [4.0,5.0,6.0]},
  "timeout_seconds": 120,
  "optimization_level": 2,
  "job_ref": "job:fortran-runtime-smoke",
  "environment_ref": "environment-package:fortran-runtime:v1"
}
JSON
curl -fsS -X POST "$BASE/v1/core-adapter/prepare" -H 'Content-Type: application/json' --data-binary @/tmp/sc-fortran-smoke-request.json | tee /tmp/sc-fortran-prepare.json | python3 -m json.tool
RUN_ID="$(python3 - <<'PY'
import json
print(json.load(open('/tmp/sc-fortran-prepare.json'))['run_id'])
PY
)"
python3 - "$RUN_ID" <<'PY'
import json,sys
json.dump({'run_id':sys.argv[1]},open('/tmp/sc-fortran-run.json','w'))
PY
curl -fsS -X POST "$BASE/v1/core-adapter/execute" -H 'Content-Type: application/json' --data-binary @/tmp/sc-fortran-run.json | tee /tmp/sc-fortran-execute.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-fortran-execute.json'))
assert d['status']=='completed'
r=d['result']; assert r['operation']=='dot_product'
n=r['native_result']; assert n['kind']=='scalar'; assert abs(n['value']-32.0)<1e-12
assert len(r['artifacts'])==4
print('PASS - native Fortran dot-product smoke test')
PY

echo "PASS - SUSTAINABLE CATALYST FORTRAN RUNTIME v1.0.0 VERIFIED"
