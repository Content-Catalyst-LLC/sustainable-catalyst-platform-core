#!/usr/bin/env bash
set -euo pipefail
SRC="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
DEST="${SC_SPARK_RUNTIME_DIR:-/opt/sustainable-catalyst/spark-runtime}"
STATE="/var/lib/sc-spark-runtime"
echo "=== SUSTAINABLE CATALYST SPARK RUNTIME v1.0.0 DEPLOYMENT ==="
echo "SOURCE=$SRC"; echo "DEST=$DEST"
sudo apt-get update
sudo apt-get install -y openjdk-21-jdk-headless python3.12-venv curl rsync ca-certificates
java -version
python3.12 --version
sudo mkdir -p "$DEST" "$STATE/tmp"
sudo chown -R catalystadmin:catalystadmin "$DEST" "$STATE"
rsync -a --delete --exclude='.venv/' --exclude='__pycache__/' "$SRC/" "$DEST/"
if [[ ! -x "$DEST/.venv/bin/python" ]]; then python3.12 -m venv "$DEST/.venv"; fi
"$DEST/.venv/bin/pip" install --disable-pip-version-check --upgrade pip
"$DEST/.venv/bin/pip" install --disable-pip-version-check -r "$DEST/requirements.txt" -r "$DEST/requirements-runtime.txt" pytest 'httpx==0.27.2'
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export SPARK_LOCAL_IP=127.0.0.1
export SC_SPARK_MASTER='local[2]'
export SC_SPARK_LOCAL_DIR="$STATE/tmp"
cd "$DEST"
PYTHONPATH=. "$DEST/.venv/bin/python" validate_runtime.py
PYTHONPATH=. "$DEST/.venv/bin/python" -m pytest -q tests/test_runtime.py
"$DEST/.venv/bin/python" - <<'PY_PYSPARK_VERSION'
import importlib.metadata
assert importlib.metadata.version('pyspark')=='4.2.0'
print('PASS - PySpark 4.2.0 installed')
PY_PYSPARK_VERSION
sudo cp "$DEST/deploy/sc-spark-runtime.service" /etc/systemd/system/sc-spark-runtime.service
sudo systemctl daemon-reload
sudo systemctl enable sc-spark-runtime
sudo systemctl restart sc-spark-runtime
READY=0
for i in $(seq 1 60); do if curl -fsS http://127.0.0.1:18106/health >/tmp/sc-spark-runtime-health.json 2>/dev/null; then READY=1; break; fi; sleep 2; done
if [[ "$READY" != 1 ]]; then sudo systemctl status sc-spark-runtime --no-pager || true; sudo journalctl -u sc-spark-runtime -n 150 --no-pager || true; exit 1; fi
chmod +x "$DEST/deploy/VERIFY_SC_RUNTIME_SPARK_V100.sh"
"$DEST/deploy/VERIFY_SC_RUNTIME_SPARK_V100.sh"
echo "PASS - SUSTAINABLE CATALYST SPARK RUNTIME v1.0.0 BACKEND DEPLOYMENT COMPLETE"
