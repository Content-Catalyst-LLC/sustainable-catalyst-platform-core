#!/usr/bin/env bash
set -euo pipefail
SRC="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
INSTALL_ROOT="${SC_PYTHON_RUNTIME_ROOT:-/opt/sustainable-catalyst/python-runtime}"
DATA_ROOT="${SC_PYTHON_DATA_ROOT:-/var/lib/sc-python-runtime}"
EXPECTED_PYTHON_VERSION="${SC_PYTHON_VERSION:-3.12.3}"
PYTHON_BIN="${SC_PYTHON_BIN:-/usr/bin/python3.12}"
echo "=== SUSTAINABLE CATALYST PYTHON RUNTIME v1.0.0 DEPLOYMENT ==="
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3.12 python3.12-venv curl rsync
"$PYTHON_BIN" --version | grep -F "Python $EXPECTED_PYTHON_VERSION" >/dev/null || { echo "ERROR: Python version mismatch"; "$PYTHON_BIN" --version; exit 1; }
PACKAGE_VERSION="$(dpkg-query -W -f='${Version}' python3.12)"
[[ "$PACKAGE_VERSION" == 3.12.3-* ]] || { echo "ERROR: expected Noble Python 3.12.3 package family, got $PACKAGE_VERSION"; exit 1; }
echo "Python package: $PACKAGE_VERSION"
if [[ -d "$INSTALL_ROOT" ]]; then STAMP="$(date +%Y%m%d-%H%M%S)";sudo mkdir -p /opt/sustainable-catalyst/backups;sudo tar -C /opt/sustainable-catalyst -czf "/opt/sustainable-catalyst/backups/python-runtime-pre-v100-${STAMP}.tar.gz" python-runtime || true;fi
sudo mkdir -p "$INSTALL_ROOT" "$DATA_ROOT/artifacts" "$DATA_ROOT/work";sudo rsync -a --delete --exclude '.venv' "$SRC/" "$INSTALL_ROOT/";sudo chown -R catalystadmin:catalystadmin "$INSTALL_ROOT" "$DATA_ROOT";cd "$INSTALL_ROOT"
"$PYTHON_BIN" -m venv .venv;.venv/bin/python -m pip install --upgrade pip >/dev/null;.venv/bin/pip install -r requirements.txt >/dev/null;.venv/bin/pip install 'pytest>=8,<10' >/dev/null
export SC_PYTHON_VERSION="$EXPECTED_PYTHON_VERSION" SC_PYTHON_PACKAGE_VERSION="$PACKAGE_VERSION" SC_PYTHON_BIN="$PYTHON_BIN" SC_PYTHON_ARTIFACT_ROOT="$DATA_ROOT/artifacts" SC_PYTHON_WORK_ROOT="$DATA_ROOT/work"
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python validate_runtime.py;PYTHONPATH="$INSTALL_ROOT" .venv/bin/python -m pytest -q tests/test_runtime.py;PYTHONPATH="$INSTALL_ROOT" .venv/bin/python validate_native_kernels.py;.venv/bin/python -m py_compile app/server.py validate_runtime.py validate_native_kernels.py
sudo cp deploy/sc-python-runtime.service /etc/systemd/system/sc-python-runtime.service
sudo sed -i "s|Environment=SC_PYTHON_VERSION=.*|Environment=SC_PYTHON_VERSION=$EXPECTED_PYTHON_VERSION|" /etc/systemd/system/sc-python-runtime.service
sudo sed -i "/Environment=SC_PYTHON_VERSION=/a Environment=SC_PYTHON_PACKAGE_VERSION=$PACKAGE_VERSION" /etc/systemd/system/sc-python-runtime.service
sudo systemctl daemon-reload;sudo systemctl enable sc-python-runtime.service >/dev/null;sudo systemctl restart sc-python-runtime.service
READY=0;for i in $(seq 1 30);do if curl -fsS http://127.0.0.1:18103/health >/dev/null 2>&1;then READY=1;break;fi;sleep 2;done
if [[ "$READY" != "1" ]];then sudo systemctl status sc-python-runtime.service --no-pager || true;sudo journalctl -u sc-python-runtime.service -n 160 --no-pager || true;exit 1;fi
bash deploy/VERIFY_SC_RUNTIME_PYTHON_V100.sh
echo "PASS - SUSTAINABLE CATALYST PYTHON RUNTIME v1.0.0 BACKEND DEPLOYMENT COMPLETE"
