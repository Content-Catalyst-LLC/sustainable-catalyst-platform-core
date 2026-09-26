#!/usr/bin/env bash
set -euo pipefail
BASE="${SC_RUST_RUNTIME_URL:-http://127.0.0.1:18101}"

echo "=== VERIFY RUST RUNTIME HEALTH ==="
curl -fsS "$BASE/health" | tee /tmp/sc-rust-health.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-rust-health.json'))
assert d['ok'] is True
assert d['runtime_id']=='sc-runtime-rust'
assert d['version']=='1.0.0'
assert d['rustc_version']=='1.75.0'
assert d['cargo_version']=='1.75.0'
print('PASS - Rust runtime health')

# Continued verify script after embedded Python block.
PY

echo "=== VERIFY CORE ADAPTER DESCRIPTOR ==="
curl -fsS "$BASE/v1/core-adapter" | tee /tmp/sc-rust-adapter.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-rust-adapter.json'))
assert d['adapter_id']=='adapter:sc-runtime-rust'
assert d['provider_id']=='sc-runtime-rust'
assert d['provider_version']=='1.0.0'
assert d['language']=='rust'
assert d['edition']=='2021'
assert set(d['capabilities'])=={'prefix_sum','moving_average','connected_components','topological_sort','levenshtein_distance','fnv1a_64'}
assert d['boundaries']['arbitrary_rust_source'] is False
assert d['boundaries']['unsafe_rust_code'] is False
print('PASS - Rust adapter descriptor')
PY

echo "=== BOUNDED NATIVE RUST PREFIX SUM SMOKE TEST ==="
cat >/tmp/sc-rust-smoke-request.json <<'JSON'
{"operation":"prefix_sum","payload":{"integers":[1,2,3,4,5]},"timeout_seconds":120,"optimization_level":2,"job_ref":"job:rust-runtime-smoke","environment_ref":"environment-package:rust-runtime:v1"}
JSON
curl -fsS -X POST "$BASE/v1/core-adapter/prepare" -H 'Content-Type: application/json' --data-binary @/tmp/sc-rust-smoke-request.json | tee /tmp/sc-rust-prepare.json | python3 -m json.tool
RUN_ID="$(python3 - <<'PY'
import json
print(json.load(open('/tmp/sc-rust-prepare.json'))['run_id'])
PY
)"
python3 - "$RUN_ID" <<'PY'
import json,sys
json.dump({'run_id':sys.argv[1]},open('/tmp/sc-rust-run.json','w'))
PY
curl -fsS -X POST "$BASE/v1/core-adapter/execute" -H 'Content-Type: application/json' --data-binary @/tmp/sc-rust-run.json | tee /tmp/sc-rust-execute.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-rust-execute.json'))
assert d['status']=='completed'
r=d['result']
assert r['operation']=='prefix_sum'
assert r['edition']=='2021'
assert r['native_result']=={'kind':'int_vector','values':[1,3,6,10,15]}
assert len(r['artifacts'])==4
print('PASS - native Rust prefix-sum smoke test')
PY

echo "=== BOUNDED NATIVE RUST FNV-1A SMOKE TEST ==="
cat >/tmp/sc-rust-fnv-request.json <<'JSON'
{"operation":"fnv1a_64","payload":{"text":"abc"},"timeout_seconds":120,"optimization_level":2,"job_ref":"job:rust-runtime-fnv","environment_ref":"environment-package:rust-runtime:v1"}
JSON
curl -fsS -X POST "$BASE/v1/core-adapter/prepare" -H 'Content-Type: application/json' --data-binary @/tmp/sc-rust-fnv-request.json | tee /tmp/sc-rust-fnv-prepare.json >/dev/null
RUN_ID="$(python3 - <<'PY'
import json
print(json.load(open('/tmp/sc-rust-fnv-prepare.json'))['run_id'])
PY
)"
python3 - "$RUN_ID" <<'PY'
import json,sys
json.dump({'run_id':sys.argv[1]},open('/tmp/sc-rust-fnv-run.json','w'))
PY
curl -fsS -X POST "$BASE/v1/core-adapter/execute" -H 'Content-Type: application/json' --data-binary @/tmp/sc-rust-fnv-run.json | tee /tmp/sc-rust-fnv-execute.json >/dev/null
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-rust-fnv-execute.json'))
assert d['result']['native_result']['value']=='e71fa2190541574b'
print('PASS - native Rust FNV-1a smoke test')
PY

echo "PASS - SUSTAINABLE CATALYST RUST RUNTIME v1.0.0 VERIFIED"
