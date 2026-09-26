#!/usr/bin/env bash
set -euo pipefail
BASE="${SC_CPP_RUNTIME_URL:-http://127.0.0.1:18100}"

echo "=== VERIFY C/C++ RUNTIME HEALTH ==="
curl -fsS "$BASE/health" | tee /tmp/sc-cpp-health.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-cpp-health.json'))
assert d['ok'] is True
assert d['runtime_id']=='sc-runtime-cpp'
assert d['version']=='1.0.0'
assert d['gcc_version']=='13.3.0'
assert d['gpp_version']=='13.3.0'
print('PASS - C/C++ runtime health')
PY

echo "=== VERIFY C/C++ CORE ADAPTER ==="
curl -fsS "$BASE/v1/core-adapter" | tee /tmp/sc-cpp-adapter.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-cpp-adapter.json'))
assert d['adapter_id']=='adapter:sc-runtime-cpp'
assert d['provider_id']=='sc-runtime-cpp'
assert d['provider_version']=='1.0.0'
assert d['language']=='c-cpp'
assert d['language_profiles']==['c11','cpp17']
assert set(d['capabilities'])=={'dot_product','matrix_multiply','linear_interpolation','polynomial_evaluate','fir_filter','dijkstra_shortest_path'}
assert d['boundaries']['arbitrary_c_cpp_source'] is False
assert d['boundaries']['provider_managed_compilation'] is True
print('PASS - C/C++ adapter descriptor')
PY

echo "=== NATIVE C11 DOT PRODUCT SMOKE ==="
cat >/tmp/sc-cpp-c-smoke.json <<'JSON'
{"operation":"dot_product","payload":{"a":[1,2,3],"b":[4,5,6]},"timeout_seconds":120,"optimization_level":2,"job_ref":"job:cpp-c11-smoke","environment_ref":"environment-package:c-cpp-runtime:v1"}
JSON
curl -fsS -X POST "$BASE/v1/core-adapter/prepare" -H 'Content-Type: application/json' --data-binary @/tmp/sc-cpp-c-smoke.json | tee /tmp/sc-cpp-c-prep.json | python3 -m json.tool
python3 - <<'PY'
import json
p=json.load(open('/tmp/sc-cpp-c-prep.json'));json.dump({'run_id':p['run_id']},open('/tmp/sc-cpp-c-run.json','w'))
PY
curl -fsS -X POST "$BASE/v1/core-adapter/execute" -H 'Content-Type: application/json' --data-binary @/tmp/sc-cpp-c-run.json | tee /tmp/sc-cpp-c-exec.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-cpp-c-exec.json'))
assert d['status']=='completed'
r=d['result']
assert r['language_profile']=='c11'
assert abs(r['native_result']['value']-32.0)<1e-12
assert len(r['artifacts'])==4
print('PASS - native C11 dot-product smoke')
PY

echo "=== NATIVE C++17 MATRIX MULTIPLY SMOKE ==="
cat >/tmp/sc-cpp-cpp-smoke.json <<'JSON'
{"operation":"matrix_multiply","payload":{"a":[[1,2],[3,4]],"b":[[5,6],[7,8]]},"timeout_seconds":120,"optimization_level":2,"job_ref":"job:cpp-cpp17-smoke","environment_ref":"environment-package:c-cpp-runtime:v1"}
JSON
curl -fsS -X POST "$BASE/v1/core-adapter/prepare" -H 'Content-Type: application/json' --data-binary @/tmp/sc-cpp-cpp-smoke.json | tee /tmp/sc-cpp-cpp-prep.json | python3 -m json.tool
python3 - <<'PY'
import json
p=json.load(open('/tmp/sc-cpp-cpp-prep.json'));json.dump({'run_id':p['run_id']},open('/tmp/sc-cpp-cpp-run.json','w'))
PY
curl -fsS -X POST "$BASE/v1/core-adapter/execute" -H 'Content-Type: application/json' --data-binary @/tmp/sc-cpp-cpp-run.json | tee /tmp/sc-cpp-cpp-exec.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-cpp-cpp-exec.json'))
assert d['status']=='completed'
r=d['result']
assert r['language_profile']=='cpp17'
assert r['native_result']['values']==[[19.0,22.0],[43.0,50.0]]
assert len(r['artifacts'])==4
print('PASS - native C++17 matrix-multiply smoke')
PY

echo "PASS - SUSTAINABLE CATALYST C/C++ RUNTIME v1.0.0 VERIFIED"
