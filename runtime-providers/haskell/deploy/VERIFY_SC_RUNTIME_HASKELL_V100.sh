#!/usr/bin/env bash
set -euo pipefail
BASE="${SC_HASKELL_RUNTIME_URL:-http://127.0.0.1:18098}"

echo "=== VERIFY HASKELL RUNTIME HEALTH ==="
curl -fsS "$BASE/health" | tee /tmp/sc-haskell-health.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-haskell-health.json'))
assert d['ok'] is True
assert d['runtime_id']=='sc-runtime-haskell'
assert d['version']=='1.0.0'
assert d['ghc_version']=='9.4.7'
assert d['ghc_package_version']=='9.4.7-3'
print('PASS - Haskell runtime health')
PY

echo "=== VERIFY CORE ADAPTER DESCRIPTOR ==="
curl -fsS "$BASE/v1/core-adapter" | tee /tmp/sc-haskell-adapter.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-haskell-adapter.json'))
assert d['adapter_id']=='adapter:sc-runtime-haskell'
assert d['provider_id']=='sc-runtime-haskell'
assert d['provider_version']=='1.0.0'
assert d['language']=='haskell'
assert set(d['capabilities'])=={
'gcd','lcm','rational_reduce','factorial','fibonacci',
'binomial_coefficient','integer_power','graph_reachable'
}
assert d['boundaries']['arbitrary_haskell_source'] is False
assert d['boundaries']['shell_execution'] is False
print('PASS - Haskell adapter descriptor')
PY

echo "=== BOUNDED NATIVE HASKELL EXACT-ARITHMETIC SMOKE TEST ==="
cat >/tmp/sc-haskell-smoke-request.json <<'JSON'
{
  "operation": "rational_reduce",
  "payload": {"numerator": 42, "denominator": 56},
  "timeout_seconds": 60,
  "job_ref": "job:haskell-runtime-smoke",
  "environment_ref": "environment-package:haskell-runtime:v1"
}
JSON
curl -fsS -X POST "$BASE/v1/core-adapter/prepare" \
  -H 'Content-Type: application/json' --data-binary @/tmp/sc-haskell-smoke-request.json \
  | tee /tmp/sc-haskell-prepare.json | python3 -m json.tool
RUN_ID="$(python3 - <<'PY'
import json
print(json.load(open('/tmp/sc-haskell-prepare.json'))['run_id'])
PY
)"
python3 - "$RUN_ID" <<'PY'
import json,sys
json.dump({'run_id':sys.argv[1]},open('/tmp/sc-haskell-run.json','w'))
PY
curl -fsS -X POST "$BASE/v1/core-adapter/execute" \
  -H 'Content-Type: application/json' --data-binary @/tmp/sc-haskell-run.json \
  | tee /tmp/sc-haskell-execute.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-haskell-execute.json'))
assert d['status']=='completed'
r=d['result']
assert r['operation']=='rational_reduce'
native=r['native_result']
assert native['operation']=='rational_reduce'
assert native['numerator']=='3'
assert native['denominator']=='4'
assert len(r['artifacts'])==3
print('PASS - native Haskell exact rational smoke test')
PY

echo "PASS - SUSTAINABLE CATALYST HASKELL RUNTIME v1.0.0 VERIFIED"
