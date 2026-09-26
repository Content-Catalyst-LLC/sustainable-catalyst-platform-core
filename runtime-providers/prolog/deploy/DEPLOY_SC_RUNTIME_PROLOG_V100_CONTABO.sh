#!/usr/bin/env bash
set -euo pipefail
SRC="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
INSTALL_ROOT="${SC_PROLOG_RUNTIME_ROOT:-/opt/sustainable-catalyst/prolog-runtime}"
DATA_ROOT="${SC_PROLOG_DATA_ROOT:-/var/lib/sc-prolog-runtime}"
EXPECTED_VERSION="9.0.4"
EXPECTED_PACKAGE="9.0.4+dfsg-3.1ubuntu4"
echo "=== SUSTAINABLE CATALYST PROLOG RUNTIME v1.0.0 DEPLOYMENT ==="
sudo apt-get update
CANDIDATE="$(apt-cache policy swi-prolog-nox | awk '/Candidate:/ {candidate=$2} END {print candidate}')"
[[ "$CANDIDATE" == "$EXPECTED_PACKAGE" ]] || { echo "ERROR: expected swi-prolog-nox candidate $EXPECTED_PACKAGE, got $CANDIDATE"; exit 1; }
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "swi-prolog-nox=$EXPECTED_PACKAGE" python3-venv curl rsync
/usr/bin/swipl --version | grep -F "SWI-Prolog version $EXPECTED_VERSION" >/dev/null || { echo "ERROR: SWI-Prolog version mismatch"; /usr/bin/swipl --version; exit 1; }
PACKAGE_VERSION="$(dpkg-query -W -f='${Version}' swi-prolog-nox)"
[[ "$PACKAGE_VERSION" == "$EXPECTED_PACKAGE" ]] || { echo "ERROR: Prolog package mismatch: $PACKAGE_VERSION"; exit 1; }
if [[ -d "$INSTALL_ROOT" ]];then STAMP="$(date +%Y%m%d-%H%M%S)";sudo mkdir -p /opt/sustainable-catalyst/backups;sudo tar -C /opt/sustainable-catalyst -czf "/opt/sustainable-catalyst/backups/prolog-runtime-pre-v100-${STAMP}.tar.gz" prolog-runtime || true;fi
sudo mkdir -p "$INSTALL_ROOT" "$DATA_ROOT/artifacts" "$DATA_ROOT/work"
sudo rsync -a --delete --exclude '.venv' "$SRC/" "$INSTALL_ROOT/"
sudo chown -R catalystadmin:catalystadmin "$INSTALL_ROOT" "$DATA_ROOT"
cd "$INSTALL_ROOT"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip >/dev/null
.venv/bin/pip install -r requirements.txt >/dev/null
.venv/bin/pip install 'pytest>=8,<10' >/dev/null
export SC_PROLOG_VERSION="$EXPECTED_VERSION" SC_PROLOG_PACKAGE_VERSION="$PACKAGE_VERSION" SC_PROLOG_BIN=/usr/bin/swipl SC_PROLOG_ARTIFACT_ROOT="$DATA_ROOT/artifacts" SC_PROLOG_WORK_ROOT="$DATA_ROOT/work"
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python validate_runtime.py
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python -m pytest -q tests/test_runtime.py
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python validate_native_kernels.py
.venv/bin/python -m py_compile app/server.py validate_runtime.py validate_native_kernels.py
sudo cp deploy/sc-prolog-runtime.service /etc/systemd/system/sc-prolog-runtime.service
sudo systemctl daemon-reload
sudo systemctl enable sc-prolog-runtime.service >/dev/null
sudo systemctl restart sc-prolog-runtime.service
READY=0
for i in $(seq 1 30);do if curl -fsS http://127.0.0.1:18104/health >/dev/null 2>&1;then READY=1;break;fi;sleep 2;done
[[ "$READY" == "1" ]] || { sudo systemctl status sc-prolog-runtime.service --no-pager -l || true;sudo journalctl -u sc-prolog-runtime.service -n 160 --no-pager || true;exit 1; }
bash deploy/VERIFY_SC_RUNTIME_PROLOG_V100.sh
echo "PASS - SUSTAINABLE CATALYST PROLOG RUNTIME v1.0.0 BACKEND DEPLOYMENT COMPLETE"
