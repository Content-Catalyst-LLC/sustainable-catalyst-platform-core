#!/usr/bin/env bash
set -euo pipefail
SRC="${1:-$(pwd)}";DEST="${SC_JVM_RUNTIME_ROOT:-/opt/sustainable-catalyst/jvm-runtime}"
echo "=== SUSTAINABLE CATALYST JVM RUNTIME v1.0.0 DEPLOYMENT ==="
sudo apt-get update
sudo apt-get install -y openjdk-21-jdk-headless python3 python3-venv curl rsync
java -version 2>&1 | head -2
javac -version
JAVA_MAJOR="$(java -XshowSettings:properties -version 2>&1 | awk -F'= ' '/java.specification.version/ {v=$2} END {print v}')"
[[ "$JAVA_MAJOR" == "21" ]] || { echo "ERROR: expected JVM major 21, got $JAVA_MAJOR"; exit 1; }
PKG_VER="$(dpkg-query -W -f='${Version}' openjdk-21-jdk-headless)"
echo "Installed openjdk-21-jdk-headless=$PKG_VER"
sudo mkdir -p "$DEST" /var/lib/sc-jvm-runtime/artifacts /var/lib/sc-jvm-runtime/work
sudo rsync -a --delete --exclude '.venv' "$SRC/" "$DEST/"
sudo chown -R catalystadmin:catalystadmin "$DEST" /var/lib/sc-jvm-runtime
python3 -m venv "$DEST/.venv"
"$DEST/.venv/bin/pip" install --disable-pip-version-check --no-cache-dir -r "$DEST/requirements.txt" pytest >/dev/null
cd "$DEST"
PYTHONPATH="$DEST" "$DEST/.venv/bin/python" validate_runtime.py
PYTHONPATH="$DEST" "$DEST/.venv/bin/python" -m pytest -q tests/test_runtime.py
PYTHONPATH="$DEST" "$DEST/.venv/bin/python" validate_native_kernels.py
python3 - <<DEPLOYJSON
import json
json.dump({'openjdk_package':'openjdk-21-jdk-headless','package_version':'$PKG_VER','jvm_major':'21'},open('/var/lib/sc-jvm-runtime/deployment-environment.json','w'),indent=2)
DEPLOYJSON
sudo install -m 0644 "$DEST/deploy/sc-jvm-runtime.service" /etc/systemd/system/sc-jvm-runtime.service
sudo systemctl daemon-reload
sudo systemctl enable --now sc-jvm-runtime.service
READY=0
for i in $(seq 1 30);do if curl -fsS http://127.0.0.1:18105/health >/dev/null 2>&1;then READY=1;break;fi;sleep 1;done
[[ "$READY" == "1" ]] || { sudo systemctl status sc-jvm-runtime.service --no-pager -l || true;sudo journalctl -u sc-jvm-runtime.service -n 100 --no-pager || true;exit 1; }
chmod +x "$DEST/deploy/VERIFY_SC_RUNTIME_JVM_V100.sh";"$DEST/deploy/VERIFY_SC_RUNTIME_JVM_V100.sh"
