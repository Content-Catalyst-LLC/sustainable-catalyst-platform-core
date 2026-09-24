#!/usr/bin/env bash
set -euo pipefail
BASE="${SC_JULIA_URL:-http://127.0.0.1:18093}"

echo "=== HEALTH ==="
curl -fsS "$BASE/health" | python3 -m json.tool

echo "=== VERSION ==="
curl -fsS "$BASE/version" | python3 -m json.tool

echo "=== CAPABILITIES ==="
curl -fsS "$BASE/capabilities" | python3 -m json.tool

echo "=== CORE ADAPTER DESCRIPTOR ==="
curl -fsS "$BASE/v1/core-adapter" | tee /tmp/catalyst-julia-core-adapter-v030.json | python3 -m json.tool

python3 - <<'PY'
import json
d=json.load(open('/tmp/catalyst-julia-core-adapter-v030.json'))
assert d['adapter_id']=='adapter:catalyst-julia-runtime'
assert d['adapter_contract']=='sc.core.runtime-adapter.v1'
assert d['runtime']['provider_version']=='0.3.0'
assert d['status']=='registered'
assert len(d['methods'])==10
print('PASS - native Core adapter descriptor')
PY

echo "=== PREPARE ==="
curl -fsS -X POST "$BASE/v1/core-adapter/prepare" \
  -H 'Content-Type: application/json' \
  -d '{"request_id":"request:julia-v030-prepare","runtime_id":"catalyst-julia-runtime","operation":"sum","inputs":{"values":[1,2,3,4]},"provenance":{"purpose":"v0.3.0-prepare-proof"}}' \
  | tee /tmp/catalyst-julia-prepare-v030.json | python3 -m json.tool

RUN_ID="$(python3 - <<'PY'
import json
d=json.load(open('/tmp/catalyst-julia-prepare-v030.json'))
assert d['run']['state']=='prepared'
print(d['run']['run_id'])
PY
)"

echo "=== EXECUTE ==="
curl -fsS -X POST "$BASE/v1/core-adapter/execute" \
  -H 'Content-Type: application/json' \
  -d "{\"request_id\":\"request:julia-v030-prepare\",\"runtime_id\":\"catalyst-julia-runtime\",\"run_id\":\"${RUN_ID}\",\"operation\":\"sum\",\"inputs\":{\"values\":[1,2,3,4]},\"provenance\":{\"purpose\":\"v0.3.0-execute-proof\"}}" \
  | tee /tmp/catalyst-julia-execute-v030.json | python3 -m json.tool

python3 - <<'PY'
import json
d=json.load(open('/tmp/catalyst-julia-execute-v030.json'))
assert d['run']['state']=='completed'
assert d['result']['state']=='completed'
assert d['result']['scalar_result']==10.0
print('PASS - Core adapter execution proof result=10.0')
PY

echo "=== INSPECT ==="
curl -fsS "$BASE/v1/core-adapter/inspect?run_id=${RUN_ID}" | python3 -m json.tool

echo "=== COLLECT RESULTS ==="
curl -fsS "$BASE/v1/core-adapter/results?run_id=${RUN_ID}" | python3 -m json.tool

echo "=== COLLECT ARTIFACTS ==="
curl -fsS "$BASE/v1/core-adapter/artifacts?run_id=${RUN_ID}" | python3 -m json.tool

echo "=== DIAGNOSE ==="
curl -fsS "$BASE/v1/core-adapter/diagnose?run_id=${RUN_ID}" | python3 -m json.tool

echo "=== ENVIRONMENT FINGERPRINT ==="
curl -fsS "$BASE/v1/environment/fingerprint" | python3 -m json.tool

echo "PASS - Catalyst Julia Runtime v0.3.0 Core Runtime Contract Adapter verified."
