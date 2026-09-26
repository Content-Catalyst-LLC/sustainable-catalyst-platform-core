#!/usr/bin/env bash
set -euo pipefail
SRC="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
INSTALL_ROOT="${SC_GO_RUNTIME_ROOT:-/opt/sustainable-catalyst/go-runtime}"
DATA_ROOT="${SC_GO_DATA_ROOT:-/var/lib/sc-go-runtime}"
EXPECTED_GO_VERSION="${SC_GO_VERSION:-1.22.2}"
EXPECTED_PACKAGE_VERSION="${SC_GO_PACKAGE_VERSION:-1.22.2-2ubuntu0.4}"
GO_BIN="${SC_GO_BIN:-/usr/lib/go-1.22/bin/go}"
echo "=== SUSTAINABLE CATALYST GO RUNTIME v1.0.0 DEPLOYMENT ==="
sudo apt-get update
CANDIDATE="$(apt-cache policy golang-1.22-go | awk '/Candidate:/ {candidate=$2} END {print candidate}')"
[[ "$CANDIDATE" == "$EXPECTED_PACKAGE_VERSION" ]] || { echo "ERROR: expected golang-1.22-go candidate $EXPECTED_PACKAGE_VERSION, got $CANDIDATE"; exit 1; }
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "golang-1.22-go=$EXPECTED_PACKAGE_VERSION" curl python3-venv rsync
"$GO_BIN" version
"$GO_BIN" version | grep -F "go$EXPECTED_GO_VERSION" >/dev/null || { echo "ERROR: Go version mismatch"; exit 1; }
if [[ -d "$INSTALL_ROOT" ]]; then STAMP="$(date +%Y%m%d-%H%M%S)";sudo mkdir -p /opt/sustainable-catalyst/backups;sudo tar -C /opt/sustainable-catalyst -czf "/opt/sustainable-catalyst/backups/go-runtime-pre-v100-${STAMP}.tar.gz" go-runtime || true;fi
sudo mkdir -p "$INSTALL_ROOT" "$DATA_ROOT/artifacts" "$DATA_ROOT/work";sudo rsync -a --delete --exclude '.venv' "$SRC/" "$INSTALL_ROOT/";sudo chown -R catalystadmin:catalystadmin "$INSTALL_ROOT" "$DATA_ROOT";cd "$INSTALL_ROOT"
python3 -m venv .venv;.venv/bin/python -m pip install --upgrade pip >/dev/null;.venv/bin/pip install -r requirements.txt >/dev/null;.venv/bin/pip install 'pytest>=8,<10' >/dev/null
export SC_GO_VERSION="$EXPECTED_GO_VERSION" SC_GO_PACKAGE_VERSION="$EXPECTED_PACKAGE_VERSION" SC_GO_BIN="$GO_BIN" SC_GO_ARTIFACT_ROOT="$DATA_ROOT/artifacts" SC_GO_WORK_ROOT="$DATA_ROOT/work"
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python validate_runtime.py;PYTHONPATH="$INSTALL_ROOT" .venv/bin/python -m pytest -q tests/test_runtime.py;GO="$GO_BIN" PYTHONPATH="$INSTALL_ROOT" .venv/bin/python validate_native_kernels.py;.venv/bin/python -m py_compile app/server.py validate_runtime.py validate_native_kernels.py
sudo cp deploy/sc-go-runtime.service /etc/systemd/system/sc-go-runtime.service;sudo systemctl daemon-reload;sudo systemctl enable sc-go-runtime.service >/dev/null;sudo systemctl restart sc-go-runtime.service
READY=0;for i in $(seq 1 30);do if curl -fsS http://127.0.0.1:18102/health >/dev/null 2>&1;then READY=1;break;fi;sleep 2;done
if [[ "$READY" != "1" ]];then sudo systemctl status sc-go-runtime.service --no-pager || true;sudo journalctl -u sc-go-runtime.service -n 160 --no-pager || true;exit 1;fi
bash deploy/VERIFY_SC_RUNTIME_GO_V100.sh
echo "PASS - SUSTAINABLE CATALYST GO RUNTIME v1.0.0 BACKEND DEPLOYMENT COMPLETE"
