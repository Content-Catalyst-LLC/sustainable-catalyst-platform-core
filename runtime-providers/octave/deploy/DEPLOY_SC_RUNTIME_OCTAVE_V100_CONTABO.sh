#!/usr/bin/env bash
set -euo pipefail

SRC="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
INSTALL_ROOT="${SC_OCTAVE_RUNTIME_ROOT:-/opt/sustainable-catalyst/octave-runtime}"
DATA_ROOT="${SC_OCTAVE_DATA_ROOT:-/var/lib/sc-octave-runtime}"
EXPECTED_OCTAVE_VERSION="${SC_OCTAVE_VERSION:-8.4.0}"

echo "=== SUSTAINABLE CATALYST OCTAVE RUNTIME v1.0.0 DEPLOYMENT ==="

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  octave \
  curl \
  python3-venv \
  rsync

OCTAVE_VERSION="$(octave-cli --version | head -n1 | sed -E 's/^GNU Octave, version ([0-9.]+).*$/\1/')"
[[ "$OCTAVE_VERSION" == "$EXPECTED_OCTAVE_VERSION" ]] || {
  echo "ERROR: expected GNU Octave $EXPECTED_OCTAVE_VERSION, got $OCTAVE_VERSION"
  exit 1
}

if [[ -d "$INSTALL_ROOT" ]]; then
  STAMP="$(date +%Y%m%d-%H%M%S)"
  sudo mkdir -p /opt/sustainable-catalyst/backups
  sudo tar -C /opt/sustainable-catalyst \
    -czf "/opt/sustainable-catalyst/backups/octave-runtime-pre-v100-${STAMP}.tar.gz" \
    octave-runtime || true
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

export SC_OCTAVE_VERSION="$EXPECTED_OCTAVE_VERSION"
export SC_OCTAVE_BIN="/usr/bin/octave-cli"
export SC_OCTAVE_ARTIFACT_ROOT="$DATA_ROOT/artifacts"
export SC_OCTAVE_WORK_ROOT="$DATA_ROOT/work"

PYTHONPATH="$INSTALL_ROOT" .venv/bin/python validate_runtime.py
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python -m pytest -q tests/test_runtime.py
.venv/bin/python -m py_compile app/server.py validate_runtime.py

sudo cp deploy/sc-octave-runtime.service /etc/systemd/system/sc-octave-runtime.service
sudo systemctl daemon-reload
sudo systemctl enable sc-octave-runtime.service >/dev/null
sudo systemctl restart sc-octave-runtime.service

READY=0
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:18096/health >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 2
done

if [[ "$READY" != "1" ]]; then
  sudo systemctl status sc-octave-runtime.service --no-pager || true
  sudo journalctl -u sc-octave-runtime.service -n 160 --no-pager || true
  exit 1
fi

bash deploy/VERIFY_SC_RUNTIME_OCTAVE_V100.sh

echo "PASS - SUSTAINABLE CATALYST OCTAVE RUNTIME v1.0.0 BACKEND DEPLOYMENT COMPLETE"
