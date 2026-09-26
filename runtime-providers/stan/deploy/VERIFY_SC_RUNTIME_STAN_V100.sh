#!/usr/bin/env bash
set -euo pipefail

BASE="${SC_STAN_RUNTIME_URL:-http://127.0.0.1:18095}"

echo "=== VERIFY STAN RUNTIME HEALTH ==="
curl -fsS "$BASE/health" | tee /tmp/sc-stan-health.json | python3 -m json.tool

python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-stan-health.json'))
assert d['ok'] is True
assert d['runtime_id']=='sc-runtime-stan'
assert d['version']=='1.0.0'
assert d['cmdstan_version']=='2.36.0'
print('PASS - Stan runtime health')
PY

echo "=== VERIFY CORE ADAPTER DESCRIPTOR ==="
curl -fsS "$BASE/v1/core-adapter" | tee /tmp/sc-stan-adapter.json | python3 -m json.tool

python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-stan-adapter.json'))
assert d['adapter_id']=='adapter:sc-runtime-stan'
assert d['provider_id']=='sc-runtime-stan'
assert d['provider_version']=='1.0.0'
assert d['native_runtime']=='CmdStan'
assert set(d['capabilities'])=={
  'compile_model','sample','optimize','variational','diagnose'
}
assert d['boundaries']['arbitrary_shell'] is False
assert d['boundaries']['stan_include_directives'] is False
print('PASS - Stan adapter descriptor')
PY

echo "=== BOUNDED NATIVE STAN SAMPLE SMOKE TEST ==="
cat >/tmp/sc-stan-smoke-request.json <<'JSON'
{
  "operation": "sample",
  "model_id": "stan-smoke-normal",
  "model_source": "data { int<lower=1> N; array[N] real y; } parameters { real mu; } model { mu ~ normal(0, 1); y ~ normal(mu, 1); }",
  "data": {"N": 4, "y": [0.9, 1.1, 1.0, 1.2]},
  "seed": 12345,
  "chains": 1,
  "num_warmup": 20,
  "num_samples": 20,
  "thin": 1,
  "refresh": 0,
  "timeout_seconds": 300,
  "options": {"adapt_delta": 0.8},
  "job_ref": "job:stan-runtime-smoke",
  "environment_ref": "environment-package:stan-runtime:v1"
}
JSON

curl -fsS -X POST \
  "$BASE/v1/core-adapter/prepare" \
  -H "Content-Type: application/json" \
  --data-binary @/tmp/sc-stan-smoke-request.json \
  | tee /tmp/sc-stan-prepare.json \
  | python3 -m json.tool

RUN_ID="$(python3 - <<'PY'
import json
print(json.load(open('/tmp/sc-stan-prepare.json'))['run_id'])
PY
)"

python3 - "$RUN_ID" <<'PY'
import json,sys
json.dump({'run_id':sys.argv[1]}, open('/tmp/sc-stan-run.json','w'))
PY

curl -fsS -X POST \
  "$BASE/v1/core-adapter/execute" \
  -H "Content-Type: application/json" \
  --data-binary @/tmp/sc-stan-run.json \
  | tee /tmp/sc-stan-execute.json \
  | python3 -m json.tool

python3 - <<'PY'
import json
d=json.load(open('/tmp/sc-stan-execute.json'))
assert d['status']=='completed'
r=d['result']
assert r['operation']=='sample'
assert r['output_summary']['row_count'] >= 20
assert 'mu' in r['output_summary']['columns']
assert len(r['artifacts']) >= 2
print('PASS - native CmdStan sample smoke test')
PY

echo "PASS - SUSTAINABLE CATALYST STAN RUNTIME v1.0.0 VERIFIED"
