#!/usr/bin/env bash
set -euo pipefail
BASE="${SC_PYTHON_RUNTIME_URL:-http://127.0.0.1:18103}"
echo "=== VERIFY PYTHON RUNTIME HEALTH ==="
curl -fsS "$BASE/health" | tee /tmp/sc-python-health.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-python-health.json'));assert d['ok'] is True;assert d['runtime_id']=='sc-runtime-python';assert d['version']=='1.0.0';assert d['python_version']=='3.12.3';print('PASS - Python runtime health')
PY
echo "=== VERIFY CORE ADAPTER DESCRIPTOR ==="
curl -fsS "$BASE/v1/core-adapter" | tee /tmp/sc-python-adapter.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-python-adapter.json'));assert d['adapter_id']=='adapter:sc-runtime-python';assert d['language']=='python';assert set(d['capabilities'])=={'descriptive_summary','linear_regression','matrix_multiply','standardize','bootstrap_mean_ci','token_frequency'};assert d['boundaries']['arbitrary_python_source'] is False;assert d['boundaries']['runtime_package_install'] is False;assert d['boundaries']['job_network_access'] is False;print('PASS - Python adapter descriptor')
PY
echo "=== BOUNDED ISOLATED PYTHON DESCRIPTIVE SUMMARY SMOKE TEST ==="
cat >/tmp/sc-python-smoke-request.json <<'JSON'
{"operation":"descriptive_summary","payload":{"values":[1,2,3,4,5]},"timeout_seconds":120,"job_ref":"job:python-runtime-smoke","environment_ref":"environment-package:python-runtime:v1"}
JSON
curl -fsS -X POST "$BASE/v1/core-adapter/prepare" -H 'Content-Type: application/json' --data-binary @/tmp/sc-python-smoke-request.json | tee /tmp/sc-python-prepare.json | python3 -m json.tool
RUN_ID="$(python3 - <<'PY'
import json;print(json.load(open('/tmp/sc-python-prepare.json'))['run_id'])
PY
)"
python3 - "$RUN_ID" <<'PY'
import json,sys;json.dump({'run_id':sys.argv[1]},open('/tmp/sc-python-run.json','w'))
PY
curl -fsS -X POST "$BASE/v1/core-adapter/execute" -H 'Content-Type: application/json' --data-binary @/tmp/sc-python-run.json | tee /tmp/sc-python-execute.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-python-execute.json'));assert d['status']=='completed';r=d['result'];assert r['operation']=='descriptive_summary';assert abs(r['native_result']['mean']-3)<1e-12;assert len(r['artifacts'])==5;assert r['isolated_mode'] is True and r['site_imports_disabled'] is True;print('PASS - isolated Python descriptive-summary smoke test')
PY
echo "=== DETERMINISTIC PYTHON BOOTSTRAP SMOKE TEST ==="
cat >/tmp/sc-python-bootstrap-request.json <<'JSON'
{"operation":"bootstrap_mean_ci","payload":{"values":[1,2,3,4],"iterations":200,"confidence":0.95,"seed":42},"timeout_seconds":120,"job_ref":"job:python-runtime-bootstrap","environment_ref":"environment-package:python-runtime:v1"}
JSON
curl -fsS -X POST "$BASE/v1/core-adapter/prepare" -H 'Content-Type: application/json' --data-binary @/tmp/sc-python-bootstrap-request.json | tee /tmp/sc-python-bootstrap-prepare.json >/dev/null
RUN_ID="$(python3 - <<'PY'
import json;print(json.load(open('/tmp/sc-python-bootstrap-prepare.json'))['run_id'])
PY
)"
python3 - "$RUN_ID" <<'PY'
import json,sys;json.dump({'run_id':sys.argv[1]},open('/tmp/sc-python-bootstrap-run.json','w'))
PY
curl -fsS -X POST "$BASE/v1/core-adapter/execute" -H 'Content-Type: application/json' --data-binary @/tmp/sc-python-bootstrap-run.json | tee /tmp/sc-python-bootstrap-execute.json >/dev/null
python3 - <<'PY'
import json
r=json.load(open('/tmp/sc-python-bootstrap-execute.json'))['result']['native_result'];assert r['seed']==42;assert r['iterations']==200;assert r['lower']<=r['observed_mean']<=r['upper'];print('PASS - deterministic Python bootstrap smoke test')
PY
echo "PASS - SUSTAINABLE CATALYST PYTHON RUNTIME v1.0.0 VERIFIED"
