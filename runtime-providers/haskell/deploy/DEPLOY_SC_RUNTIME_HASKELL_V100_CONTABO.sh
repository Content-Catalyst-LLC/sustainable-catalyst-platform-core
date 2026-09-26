#!/usr/bin/env bash
set -euo pipefail
SRC="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
INSTALL_ROOT="${SC_HASKELL_RUNTIME_ROOT:-/opt/sustainable-catalyst/haskell-runtime}"
DATA_ROOT="${SC_HASKELL_DATA_ROOT:-/var/lib/sc-haskell-runtime}"
EXPECTED_GHC_VERSION="${SC_HASKELL_GHC_VERSION:-9.4.7}"
EXPECTED_PACKAGE_VERSION="${SC_HASKELL_GHC_PACKAGE_VERSION:-9.4.7-3}"

echo "=== SUSTAINABLE CATALYST HASKELL RUNTIME v1.0.0 DEPLOYMENT ==="
sudo apt-get update
CANDIDATE="$(apt-cache policy ghc | awk '/Candidate:/ {candidate=$2} END {print candidate}')"
[[ "$CANDIDATE" == "$EXPECTED_PACKAGE_VERSION" ]] || {
  echo "ERROR: expected Ubuntu 24.04 ghc candidate $EXPECTED_PACKAGE_VERSION, got $CANDIDATE"
  exit 1
}
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  "ghc=$EXPECTED_PACKAGE_VERSION" curl python3-venv rsync
ACTUAL_GHC="$(ghc --numeric-version)"
[[ "$ACTUAL_GHC" == "$EXPECTED_GHC_VERSION" ]] || {
  echo "ERROR: expected GHC $EXPECTED_GHC_VERSION, got $ACTUAL_GHC"
  exit 1
}
command -v runghc >/dev/null

if [[ -d "$INSTALL_ROOT" ]]; then
  STAMP="$(date +%Y%m%d-%H%M%S)"
  sudo mkdir -p /opt/sustainable-catalyst/backups
  sudo tar -C /opt/sustainable-catalyst \
    -czf "/opt/sustainable-catalyst/backups/haskell-runtime-pre-v100-${STAMP}.tar.gz" \
    haskell-runtime || true
fi
sudo mkdir -p "$INSTALL_ROOT" "$DATA_ROOT/artifacts" "$DATA_ROOT/work"
sudo rsync -a --delete --exclude '.venv' "$SRC/" "$INSTALL_ROOT/"
sudo chown -R catalystadmin:catalystadmin "$INSTALL_ROOT" "$DATA_ROOT"
cd "$INSTALL_ROOT"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip >/dev/null
.venv/bin/pip install -r requirements.txt >/dev/null
.venv/bin/pip install "pytest>=8,<10" >/dev/null
export SC_HASKELL_GHC_VERSION="$EXPECTED_GHC_VERSION"
export SC_HASKELL_GHC_PACKAGE_VERSION="$EXPECTED_PACKAGE_VERSION"
export SC_HASKELL_GHC_BIN=/usr/bin/ghc
export SC_HASKELL_RUNGHC_BIN=/usr/bin/runghc
export SC_HASKELL_ARTIFACT_ROOT="$DATA_ROOT/artifacts"
export SC_HASKELL_WORK_ROOT="$DATA_ROOT/work"
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python validate_runtime.py
PYTHONPATH="$INSTALL_ROOT" .venv/bin/python -m pytest -q tests/test_runtime.py
.venv/bin/python -m py_compile app/server.py validate_runtime.py

sudo cp deploy/sc-haskell-runtime.service /etc/systemd/system/sc-haskell-runtime.service
sudo systemctl daemon-reload
sudo systemctl enable sc-haskell-runtime.service >/dev/null
sudo systemctl restart sc-haskell-runtime.service
READY=0
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:18098/health >/dev/null 2>&1; then READY=1; break; fi
  sleep 2
done
if [[ "$READY" != "1" ]]; then
  sudo systemctl status sc-haskell-runtime.service --no-pager || true
  sudo journalctl -u sc-haskell-runtime.service -n 160 --no-pager || true
  exit 1
fi
bash deploy/VERIFY_SC_RUNTIME_HASKELL_V100.sh

echo "PASS - SUSTAINABLE CATALYST HASKELL RUNTIME v1.0.0 BACKEND DEPLOYMENT COMPLETE"
