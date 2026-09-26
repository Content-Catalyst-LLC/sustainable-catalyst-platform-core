#!/usr/bin/env bash
set -euo pipefail
echo "=== VERIFY PROLOG RUNTIME HEALTH ==="
curl -fsS http://127.0.0.1:18104/health | tee /tmp/sc-prolog-health.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-prolog-health.json'));assert d['ok'] is True;assert d['runtime_id']=='sc-runtime-prolog';assert d['version']=='1.0.0';assert d['swi_prolog_version']=='9.0.4';print('PASS - Prolog runtime health')
PY
echo "=== VERIFY CORE ADAPTER DESCRIPTOR ==="
curl -fsS http://127.0.0.1:18104/v1/core-adapter | tee /tmp/sc-prolog-adapter.json | python3 -m json.tool
python3 - <<'PY'
import json
a=json.load(open('/tmp/sc-prolog-adapter.json'));assert a['adapter_id']=='adapter:sc-runtime-prolog';assert a['language']=='prolog';assert a['boundaries']['arbitrary_prolog_source'] is False;assert a['boundaries']['runtime_package_install'] is False;print('PASS - Prolog adapter descriptor')
PY
echo "=== NATIVE RELATION REACHABILITY SMOKE ==="
PREP="$(curl -fsS -X POST http://127.0.0.1:18104/v1/core-adapter/prepare -H 'Content-Type: application/json' -d '{"operation":"relation_reachable","payload":{"edges":[{"source":"a","target":"b"},{"source":"b","target":"c"}],"source":"a","target":"c"},"job_ref":"job:prolog-reachability-smoke","environment_ref":"environment-package:prolog-runtime:v1"}')"
RUN_ID="$(python3 -c 'import json,sys;print(json.loads(sys.stdin.read())["run_id"])' <<<"$PREP")"
curl -fsS -X POST http://127.0.0.1:18104/v1/core-adapter/execute -H 'Content-Type: application/json' -d "{\"run_id\":\"$RUN_ID\"}" | tee /tmp/sc-prolog-exec.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-prolog-exec.json'));assert d['status']=='completed';assert d['result']['result']['reachable'] is True;print('PASS - native Prolog relation reachability smoke')
PY
echo "=== NATIVE CONTRADICTION SMOKE ==="
PREP="$(curl -fsS -X POST http://127.0.0.1:18104/v1/core-adapter/prepare -H 'Content-Type: application/json' -d '{"operation":"contradiction_scan","payload":{"assertions":["claim_a","claim_b"],"negations":["claim_b"]},"job_ref":"job:prolog-contradiction-smoke"}')"
RUN_ID="$(python3 -c 'import json,sys;print(json.loads(sys.stdin.read())["run_id"])' <<<"$PREP")"
curl -fsS -X POST http://127.0.0.1:18104/v1/core-adapter/execute -H 'Content-Type: application/json' -d "{\"run_id\":\"$RUN_ID\"}" | tee /tmp/sc-prolog-contradiction.json | python3 -m json.tool
python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-prolog-contradiction.json'));r=d['result']['result'];assert r['contradictions']==['claim_b'];assert r['count']==1;print('PASS - native Prolog contradiction smoke')
PY
echo "PASS - SUSTAINABLE CATALYST PROLOG RUNTIME v1.0.0 BACKEND DEPLOYMENT COMPLETE"
