#!/usr/bin/env bash
set -euo pipefail
BASE="${SC_GO_RUNTIME_URL:-http://127.0.0.1:18102}"
echo "=== VERIFY GO RUNTIME HEALTH ==="
curl -fsS "$BASE/health" | tee /tmp/sc-go-health.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-go-health.json'));assert d['ok'] is True;assert d['runtime_id']=='sc-runtime-go';assert d['version']=='1.0.0';assert d['go_version']=='1.22.2';print('PASS - Go runtime health')
PY
echo "=== VERIFY CORE ADAPTER DESCRIPTOR ==="
curl -fsS "$BASE/v1/core-adapter" | tee /tmp/sc-go-adapter.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-go-adapter.json'));assert d['adapter_id']=='adapter:sc-runtime-go';assert d['language']=='go';assert set(d['capabilities'])=={'parallel_sum','parallel_map_affine','concurrent_histogram','parallel_matrix_row_sums','parallel_graph_degrees','batch_sha256'};assert d['boundaries']['arbitrary_go_source'] is False;assert d['boundaries']['go_module_download'] is False;print('PASS - Go adapter descriptor')
PY
echo "=== BOUNDED NATIVE GO PARALLEL SUM SMOKE TEST ==="
cat >/tmp/sc-go-smoke-request.json <<'JSON'
{"operation":"parallel_sum","payload":{"values":[1,2,3,4,5],"workers":3},"timeout_seconds":120,"workers":3,"job_ref":"job:go-runtime-smoke","environment_ref":"environment-package:go-runtime:v1"}
JSON
curl -fsS -X POST "$BASE/v1/core-adapter/prepare" -H 'Content-Type: application/json' --data-binary @/tmp/sc-go-smoke-request.json | tee /tmp/sc-go-prepare.json | python3 -m json.tool
RUN_ID="$(python3 - <<'PY'
import json;print(json.load(open('/tmp/sc-go-prepare.json'))['run_id'])
PY
)"
python3 - "$RUN_ID" <<'PY'
import json,sys;json.dump({'run_id':sys.argv[1]},open('/tmp/sc-go-run.json','w'))
PY
curl -fsS -X POST "$BASE/v1/core-adapter/execute" -H 'Content-Type: application/json' --data-binary @/tmp/sc-go-run.json | tee /tmp/sc-go-execute.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-go-execute.json'));assert d['status']=='completed';r=d['result'];assert r['operation']=='parallel_sum';assert abs(r['native_result']['value']-15)<1e-12;assert len(r['artifacts'])==4;print('PASS - native Go parallel-sum smoke test')
PY
echo "=== BOUNDED NATIVE GO BATCH SHA256 SMOKE TEST ==="
cat >/tmp/sc-go-hash-request.json <<'JSON'
{"operation":"batch_sha256","payload":{"texts":["abc"],"workers":1},"timeout_seconds":120,"workers":1,"job_ref":"job:go-runtime-hash","environment_ref":"environment-package:go-runtime:v1"}
JSON
curl -fsS -X POST "$BASE/v1/core-adapter/prepare" -H 'Content-Type: application/json' --data-binary @/tmp/sc-go-hash-request.json | tee /tmp/sc-go-hash-prepare.json >/dev/null
RUN_ID="$(python3 - <<'PY'
import json;print(json.load(open('/tmp/sc-go-hash-prepare.json'))['run_id'])
PY
)"
python3 - "$RUN_ID" <<'PY'
import json,sys;json.dump({'run_id':sys.argv[1]},open('/tmp/sc-go-hash-run.json','w'))
PY
curl -fsS -X POST "$BASE/v1/core-adapter/execute" -H 'Content-Type: application/json' --data-binary @/tmp/sc-go-hash-run.json | tee /tmp/sc-go-hash-execute.json >/dev/null
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-go-hash-execute.json'));assert d['result']['native_result']['values']==['ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'];print('PASS - native Go SHA-256 batch smoke test')
PY
echo "PASS - SUSTAINABLE CATALYST GO RUNTIME v1.0.0 VERIFIED"
