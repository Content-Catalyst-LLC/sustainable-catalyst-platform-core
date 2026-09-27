#!/usr/bin/env bash
set -euo pipefail
BASE="${SC_SPARK_BASE_URL:-http://127.0.0.1:18106}"
echo "=== VERIFY SPARK RUNTIME HEALTH ==="
curl -fsS "$BASE/health" | tee /tmp/sc-spark-health.json | python3 -m json.tool
python3 - <<'PY_VERIFY_HEALTH'
import json
h=json.load(open('/tmp/sc-spark-health.json')); assert h['ok'] is True; assert h['runtime_id']=='sc-runtime-spark'; assert h['version']=='1.0.0'; assert h['spark_version_target']=='4.2.0'; assert h['pyspark_installed_version']=='4.2.0',h['pyspark_installed_version']; assert h['pyspark_ready'] is True; assert h['scala_binary_version']=='2.13'; assert h['master']=='local[2]'; print('PASS - Spark runtime health')
PY_VERIFY_HEALTH
echo "=== VERIFY SPARK ADAPTER ==="
curl -fsS "$BASE/v1/adapter" | tee /tmp/sc-spark-adapter.json | python3 -m json.tool
python3 - <<'PY_VERIFY_ADAPTER'
import json
a=json.load(open('/tmp/sc-spark-adapter.json')); assert a['adapter_id']=='adapter:sc-runtime-spark'; assert a['provider_version']=='1.0.0'; assert a['native_runtime_version']=='4.2.0'; assert a['scala_binary_version']=='2.13'; assert all(v is False for v in a['boundaries'].values()); print('PASS - Spark adapter descriptor')
PY_VERIFY_ADAPTER
echo "=== NATIVE SPARK DISTRIBUTED SUM ==="
curl --max-time 120 -fsS -H 'Content-Type: application/json' -d '{"operation":"distributed_sum","values":[1,2,3,4,5],"partitions":2}' "$BASE/v1/execute" | tee /tmp/sc-spark-sum.json | python3 -m json.tool
python3 - <<'PY_VERIFY_SUM'
import json
r=json.load(open('/tmp/sc-spark-sum.json')); x=r['result']['result']; assert r['ok'] is True; assert x['sum']==15.0; assert x['count']==5; assert x['partitions']==2; print('PASS - native Spark distributed sum')
PY_VERIFY_SUM
echo "=== NATIVE SPARK GROUP AGGREGATE ==="
curl --max-time 120 -fsS -H 'Content-Type: application/json' -d '{"operation":"dataframe_group_aggregate","rows":[{"group":"a","value":1},{"group":"a","value":2},{"group":"b","value":4}],"partitions":2,"group_by":"group","value_column":"value","aggregate":"sum"}' "$BASE/v1/execute" | tee /tmp/sc-spark-group.json | python3 -m json.tool
python3 - <<'PY_VERIFY_GROUP'
import json
r=json.load(open('/tmp/sc-spark-group.json')); rows=r['result']['result']['rows']; assert rows==[{'group':'a','value':3},{'group':'b','value':4}],rows; print('PASS - native Spark DataFrame group aggregate')
PY_VERIFY_GROUP
echo "PASS - SUSTAINABLE CATALYST SPARK RUNTIME v1.0.0 VERIFIED"
