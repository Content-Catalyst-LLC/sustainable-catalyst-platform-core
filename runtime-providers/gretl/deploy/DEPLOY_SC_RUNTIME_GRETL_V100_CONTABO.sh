#!/usr/bin/env bash
set -euo pipefail

SRC="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
INSTALL_ROOT="${SC_GRETL_RUNTIME_ROOT:-/opt/sustainable-catalyst/gretl-runtime}"
DATA_ROOT="${SC_GRETL_DATA_ROOT:-/var/lib/sc-gretl-runtime}"
EXPECTED_GRETL_VERSION="${SC_GRETL_VERSION:-2023c}"
EXPECTED_PACKAGE_VERSION="${SC_GRETL_PACKAGE_VERSION:-2023c-2.1build3}"

echo "=== SUSTAINABLE CATALYST GRETL/HANSL RUNTIME v1.0.0 DEPLOYMENT ==="

sudo apt-get update

CANDIDATE="$(apt-cache policy gretl | awk '/Candidate:/ {print $2; exit}')"
[[ "$CANDIDATE" == "$EXPECTED_PACKAGE_VERSION" ]] || {
  echo "ERROR: expected Ubuntu 24.04 gretl candidate $EXPECTED_PACKAGE_VERSION, got $CANDIDATE"
  exit 1
}

sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  "gretl=$EXPECTED_PACKAGE_VERSION" \
  "gretl-common=$EXPECTED_PACKAGE_VERSION" \
  curl \
  python3-venv \
  rsync

GRETL_TEXT="$(gretlcli --version 2>&1 || true)"
echo "$GRETL_TEXT"
grep -qi "$EXPECTED_GRETL_VERSION" <<<"$GRETL_TEXT" || {
  echo "ERROR: gretlcli does not report expected native version $EXPECTED_GRETL_VERSION"
  exit 1
}

if [[ -d "$INSTALL_ROOT" ]]; then
  STAMP="$(date +%Y%m%d-%H%M%S)"
  sudo mkdir -p /opt/sustainable-catalyst/backups
  sudo tar -C /opt/sustainable-catalyst \
    -czf "/opt/sustainable-catalyst/backups/gretl-runtime-pre-v100-${STAMP}.tar.gz" \
    gretl-runtime || true
fi

sudo mkdir -p "$INSTALL_ROOT" "$DATA_ROOT/artifacts" "$DATA_ROOT/work"
sudo rsync -a --delete \
  --exclude '.venv' \
  "$SRC/" "$INSTALL_ROOT/"

sudo chown -R catalystadmin:catalystadmin "$INSTALL_ROOT" "$DATA_ROOT"

cd "$INSTALL_ROOT"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip >/dev/null
.venv/bin/pip install -r requirements.txt >/dev/null
.venv/bin/pip install "pytest>=8,<10" >/dev/null

export SC_GRETL_VERSION="$EXPECTED_GRETL_VERSION"
export SC_GRETL_PACKAGE_VERSION="$EXPECTED_PACKAGE_VERSION"
export SC_GRETL_BIN="/usr/bin/gretlcli"
export SC_GRETL_ARTIFACT_ROOT="$DATA_ROOT/artifacts"
export SC_GRETL_WORK_ROOT="$DATA_ROOT/work"

PYTHONPATH="$INSTALL_ROOT" .venv/bin/python validate_runtime.py
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python -m pytest -q tests/test_runtime.py
.venv/bin/python -m py_compile app/server.py validate_runtime.py

sudo cp deploy/sc-gretl-runtime.service /etc/systemd/system/sc-gretl-runtime.service
sudo systemctl daemon-reload
sudo systemctl enable sc-gretl-runtime.service >/dev/null
sudo systemctl restart sc-gretl-runtime.service

READY=0
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:18097/health >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 2
done

if [[ "$READY" != "1" ]]; then
  sudo systemctl status sc-gretl-runtime.service --no-pager || true
  sudo journalctl -u sc-gretl-runtime.service -n 160 --no-pager || true
  exit 1
fi

bash deploy/VERIFY_SC_RUNTIME_GRETL_V100.sh

echo "PASS - SUSTAINABLE CATALYST GRETL/HANSL RUNTIME v1.0.0 BACKEND DEPLOYMENT COMPLETE"
