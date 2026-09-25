#!/usr/bin/env bash
set -euo pipefail
BASE="${SC_R_RUNTIME_URL:-http://127.0.0.1:18094}"

curl -fsS "$BASE/health" | tee /tmp/sc-r-runtime-health.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-r-runtime-health.json'))
assert d['runtime_id']=='sc-runtime-r'
assert d['version']=='1.0.0'
assert d['ok'] is True
assert d['rscript']
assert d['r_version']
print('PASS - R runtime health')
PY

curl -fsS "$BASE/v1/core-adapter" | tee /tmp/sc-r-runtime-adapter.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-r-runtime-adapter.json'))
assert d['adapter_id']=='adapter:sc-runtime-r'
assert d['provider_version']=='1.0.0'
assert d['status']=='registered'
assert len(d['capabilities'])==6
assert d['boundaries']['arbitrary_r_source'] is False
print('PASS - R runtime adapter')
PY

curl -fsS -X POST "$BASE/v1/core-adapter/prepare" \
  -H 'Content-Type: application/json' \
  -d '{"operation":"descriptive_summary","inputs":{"values":[1,2,3,4,5]},"job_ref":"job:r-runtime-v100-smoke","environment_ref":"environment:r-runtime-v100"}' \
  | tee /tmp/sc-r-runtime-prepare.json | python3 -m json.tool

RUN_ID="$(python3 - <<'PY'
import json
print(json.load(open('/tmp/sc-r-runtime-prepare.json'))['run_id'])
PY
)"

curl -fsS -X POST "$BASE/v1/core-adapter/execute" \
  -H 'Content-Type: application/json' \
  -d "{\"run_id\":\"$RUN_ID\"}" \
  | tee /tmp/sc-r-runtime-execute.json | python3 -m json.tool

python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-r-runtime-execute.json'))
assert d['status']=='completed'
r=d['result']['result']
assert r['n']==5
assert abs(r['mean']-3) < 1e-12
assert r['min']==1
assert r['max']==5
print('PASS - R runtime execution proof')
PY

curl -fsS "$BASE/v1/core-adapter/inspect?run_id=$RUN_ID" | python3 -m json.tool
curl -fsS "$BASE/v1/core-adapter/results?run_id=$RUN_ID" | python3 -m json.tool
curl -fsS "$BASE/v1/core-adapter/artifacts?run_id=$RUN_ID" | python3 -m json.tool
curl -fsS "$BASE/v1/core-adapter/diagnose?run_id=$RUN_ID" | python3 -m json.tool

echo "PASS - SUSTAINABLE CATALYST R RUNTIME v1.0.0 LIVE VERIFICATION COMPLETE"
