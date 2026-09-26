#!/usr/bin/env bash
set -euo pipefail
echo "=== VERIFY JVM RUNTIME HEALTH ==="
curl -fsS http://127.0.0.1:18105/health | tee /tmp/sc-jvm-health.json | python3 -m json.tool
python3 - <<'VERIFYJSON'
import json
d=json.load(open('/tmp/sc-jvm-health.json'));assert d['ok'] is True;assert d['runtime_id']=='sc-runtime-jvm';assert d['version']=='1.0.0';assert d['jvm_major_version']=='21';print('PASS - JVM runtime health')
VERIFYJSON
echo "=== JVM ADAPTER ==="
curl -fsS http://127.0.0.1:18105/v1/core-adapter | tee /tmp/sc-jvm-adapter.json | python3 -m json.tool
python3 - <<'VERIFYJSON'
import json
a=json.load(open('/tmp/sc-jvm-adapter.json'));assert a['adapter_id']=='adapter:sc-runtime-jvm';assert a['runtime_kind']=='execution-target';assert a['boundaries']['arbitrary_jvm_bytecode'] is False;assert a['boundaries']['caller_classpath'] is False;print('PASS - JVM adapter descriptor')
VERIFYJSON
echo "=== NATIVE JVM PARALLEL SUM SMOKE ==="
PREP="$(curl -fsS -X POST http://127.0.0.1:18105/v1/core-adapter/prepare -H 'Content-Type: application/json' -d '{"operation":"parallel_sum","payload":{"values":[1,2,3,4,5]},"job_ref":"job:jvm-smoke"}')"
RUN_ID="$(python3 -c 'import json,sys;print(json.loads(sys.stdin.read())["run_id"])' <<<"$PREP")"
curl -fsS -X POST http://127.0.0.1:18105/v1/core-adapter/execute -H 'Content-Type: application/json' -d "{\"run_id\":\"$RUN_ID\"}" | tee /tmp/sc-jvm-exec.json | python3 -m json.tool
python3 - <<'VERIFYJSON'
import json
d=json.load(open('/tmp/sc-jvm-exec.json'));assert d['status']=='completed';assert d['result']['result']['sum']==15.0;print('PASS - native JVM parallel sum')
VERIFYJSON
echo "=== NATIVE JVM SHA-256 SMOKE ==="
PREP="$(curl -fsS -X POST http://127.0.0.1:18105/v1/core-adapter/prepare -H 'Content-Type: application/json' -d '{"operation":"batch_sha256","payload":{"strings":["abc"]},"job_ref":"job:jvm-sha"}')"
RUN_ID="$(python3 -c 'import json,sys;print(json.loads(sys.stdin.read())["run_id"])' <<<"$PREP")"
curl -fsS -X POST http://127.0.0.1:18105/v1/core-adapter/execute -H 'Content-Type: application/json' -d "{\"run_id\":\"$RUN_ID\"}" | tee /tmp/sc-jvm-sha.json | python3 -m json.tool
python3 - <<'VERIFYJSON'
import json
d=json.load(open('/tmp/sc-jvm-sha.json'));assert d['result']['result']['sha256'][0]=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad';print('PASS - native JVM SHA-256')
VERIFYJSON
echo "PASS - SUSTAINABLE CATALYST JVM RUNTIME v1.0.0 BACKEND DEPLOYMENT COMPLETE"
